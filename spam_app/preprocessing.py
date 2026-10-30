"""Text preprocessing and Word2Vec vectorisation.

This mirrors the inference path used in the training notebook exactly:

    lowercase -> NLTK English stop-word removal (whitespace split)
              -> gensim ``simple_preprocess`` tokenisation
              -> mean of the Word2Vec vectors of the in-vocabulary tokens
              -> zero vector if no token is in the vocabulary

Nothing in this module depends on Streamlit, so it is easy to unit-test.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable

import numpy as np
from gensim.utils import simple_preprocess

# Snapshot of nltk.corpus.stopwords.words("english"). Used only when the NLTK
# corpus is not installed and cannot be downloaded (e.g. offline deployments).
_FALLBACK_STOPWORDS = frozenset((
    'a', 'about', 'above', 'after', 'again', 'against', 'ain', 'all', 'am', 'an', 'and', 'any',
    'are', 'aren', "aren't", 'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below',
    'between', 'both', 'but', 'by', 'can', 'couldn', "couldn't", 'd', 'did', 'didn', "didn't",
    'do', 'does', 'doesn', "doesn't", 'doing', 'don', "don't", 'down', 'during', 'each', 'few',
    'for', 'from', 'further', 'had', 'hadn', "hadn't", 'has', 'hasn', "hasn't", 'have', 'haven',
    "haven't", 'having', 'he', "he'd", "he'll", "he's", 'her', 'here', 'hers', 'herself', 'him',
    'himself', 'his', 'how', 'i', "i'd", "i'll", "i'm", "i've", 'if', 'in', 'into', 'is', 'isn',
    "isn't", 'it', "it'd", "it'll", "it's", 'its', 'itself', 'just', 'll', 'm', 'ma', 'me',
    'mightn', "mightn't", 'more', 'most', 'mustn', "mustn't", 'my', 'myself', 'needn',
    "needn't", 'no', 'nor', 'not', 'now', 'o', 'of', 'off', 'on', 'once', 'only', 'or', 'other',
    'our', 'ours', 'ourselves', 'out', 'over', 'own', 're', 's', 'same', 'shan', "shan't",
    'she', "she'd", "she'll", "she's", 'should', "should've", 'shouldn', "shouldn't", 'so',
    'some', 'such', 't', 'than', 'that', "that'll", 'the', 'their', 'theirs', 'them',
    'themselves', 'then', 'there', 'these', 'they', "they'd", "they'll", "they're", "they've",
    'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 've', 'very', 'was',
    'wasn', "wasn't", 'we', "we'd", "we'll", "we're", "we've", 'were', 'weren', "weren't",
    'what', 'when', 'where', 'which', 'while', 'who', 'whom', 'why', 'will', 'with', 'won',
    "won't", 'wouldn', "wouldn't", 'y', 'you', "you'd", "you'll", "you're", "you've", 'your',
    'yours', 'yourself', 'yourselves',
))


@lru_cache(maxsize=1)
def get_stopwords() -> frozenset[str]:
    """Return the English stop-word set (NLTK if available, else the snapshot)."""
    try:
        from nltk.corpus import stopwords

        return frozenset(stopwords.words("english"))
    except LookupError:
        pass
    except Exception:  # pragma: no cover - nltk missing or broken
        return _FALLBACK_STOPWORDS

    try:  # corpus missing: try a quiet one-off download
        import nltk

        if nltk.download("stopwords", quiet=True):
            from nltk.corpus import stopwords

            return frozenset(stopwords.words("english"))
    except Exception:
        pass
    return _FALLBACK_STOPWORDS


def clean_text(text: object) -> str:
    """Lowercase the text and drop English stop words (same as the notebook)."""
    stop = get_stopwords()
    return " ".join(w for w in str(text).lower().split() if w not in stop)


def tokenize(text: object) -> list[str]:
    """Clean and tokenise a raw email into model-ready tokens."""
    return simple_preprocess(clean_text(text))


@dataclass(frozen=True)
class Vectorized:
    """A document vector together with vocabulary-coverage statistics."""

    vector: np.ndarray
    n_tokens: int
    n_known: int

    @property
    def coverage(self) -> float:
        return self.n_known / self.n_tokens if self.n_tokens else 0.0


def vectorize(text: object, wv) -> Vectorized:
    """Convert one email into an averaged Word2Vec document vector.

    ``wv`` is the ``KeyedVectors`` object of the loaded Word2Vec model.
    """
    tokens = tokenize(text)
    known = [t for t in tokens if t in wv.key_to_index]
    if not known:
        vec = np.zeros(wv.vector_size, dtype=np.float32)
    else:
        vec = np.mean(wv[known], axis=0).astype(np.float32)
    return Vectorized(vec, len(tokens), len(known))


def vectorize_many(texts: Iterable[object], wv) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Vectorise many emails.

    Returns ``(matrix, n_tokens, n_known)`` where ``matrix`` has shape
    ``(n_emails, vector_size)``.
    """
    results = [vectorize(t, wv) for t in texts]
    if not results:
        return (
            np.zeros((0, wv.vector_size), dtype=np.float32),
            np.zeros(0, dtype=int),
            np.zeros(0, dtype=int),
        )
    matrix = np.vstack([r.vector for r in results])
    n_tokens = np.array([r.n_tokens for r in results], dtype=int)
    n_known = np.array([r.n_known for r in results], dtype=int)
    return matrix, n_tokens, n_known
