"""Model loading and prediction.

``SpamClassifier`` wraps the pre-trained XGBoost model and the Word2Vec
vectoriser. It never trains anything and has no Streamlit dependency.
"""

from __future__ import annotations

import pickle
import warnings
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np

from . import config
from .preprocessing import vectorize, vectorize_many


class ModelLoadError(RuntimeError):
    """Raised when a model file is missing, unreadable or incompatible."""


class PredictionError(RuntimeError):
    """Raised when an input cannot be classified."""


@dataclass(frozen=True)
class Prediction:
    """Result of classifying one email."""

    is_spam: bool
    spam_probability: float
    threshold: float
    n_tokens: int
    n_known: int

    @property
    def label(self) -> str:
        return config.LABEL_SPAM if self.is_spam else config.LABEL_HAM

    @property
    def confidence(self) -> float:
        """Probability of the predicted class (always >= 0.5 at threshold 0.5)."""
        return self.spam_probability if self.is_spam else 1.0 - self.spam_probability

    @property
    def coverage(self) -> float:
        """Share of the email's words that the Word2Vec vocabulary recognises."""
        return self.n_known / self.n_tokens if self.n_tokens else 0.0

    @property
    def low_reliability(self) -> bool:
        return self.n_known == 0 or self.coverage < config.LOW_COVERAGE_WARNING


class SpamClassifier:
    """Pre-trained XGBoost classifier on top of averaged Word2Vec vectors."""

    def __init__(self, model, word2vec) -> None:
        self.model = model
        self.word2vec = word2vec
        self.wv = word2vec.wv
        self._validate()
        self._spam_col = list(self.model.classes_).index(config.SPAM_CLASS)

    # ------------------------------------------------------------------ loading
    @classmethod
    def load(
        cls,
        classifier_path: Path = config.CLASSIFIER_PATH,
        word2vec_path: Path = config.WORD2VEC_PATH,
    ) -> "SpamClassifier":
        """Load both artefacts from disk with clear error messages."""
        classifier_path, word2vec_path = Path(classifier_path), Path(word2vec_path)
        for path, what in ((classifier_path, "classifier"), (word2vec_path, "Word2Vec")):
            if not path.is_file():
                raise ModelLoadError(
                    f"The {what} file was not found at '{path}'. "
                    "Place your model files in the 'models/' folder (see README)."
                )

        try:
            from gensim.models import Word2Vec

            word2vec = Word2Vec.load(str(word2vec_path))
        except Exception as exc:
            raise ModelLoadError(f"Could not read the Word2Vec model: {exc}") from exc

        try:
            # The model was trained on a GPU; XGBoost prints harmless "GPU -> CPU"
            # notices while unpickling on a CPU-only machine. Silence only those.
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore",
                    message=r".*(No visible GPU|Changing updater|Device is changed).*",
                    category=UserWarning,
                )
                try:
                    model = joblib.load(classifier_path)
                except Exception:
                    with open(classifier_path, "rb") as fh:  # plain pickle fallback
                        model = pickle.load(fh)
        except Exception as exc:
            raise ModelLoadError(
                f"Could not read the classifier file: {exc}. "
                "Make sure the installed xgboost/scikit-learn versions are compatible "
                "with the ones used for training."
            ) from exc

        cls._force_cpu(model)
        return cls(model, word2vec)

    @staticmethod
    def _force_cpu(model) -> None:
        """The notebook trained with ``device='cuda'``; serve on CPU everywhere."""
        try:
            model.set_params(device="cpu")
            model.get_booster().set_param({"device": "cpu"})
        except Exception:
            # Not an XGBoost model (or an older version): nothing to change.
            pass

    def _validate(self) -> None:
        if not hasattr(self.model, "predict_proba"):
            raise ModelLoadError("The classifier must provide a 'predict_proba' method.")
        expected = getattr(self.model, "n_features_in_", None)
        if expected is not None and expected != self.word2vec.vector_size:
            raise ModelLoadError(
                f"Feature mismatch: the classifier expects {expected} features but the "
                f"Word2Vec model produces {self.word2vec.vector_size}-dimensional vectors."
            )
        if config.SPAM_CLASS not in list(getattr(self.model, "classes_", [])):
            raise ModelLoadError(
                f"Class label {config.SPAM_CLASS} (spam) not found in model classes."
            )

    # --------------------------------------------------------------- properties
    @property
    def vocabulary_size(self) -> int:
        return len(self.wv)

    @property
    def vector_size(self) -> int:
        return self.word2vec.vector_size

    # -------------------------------------------------------------- predictions
    def _spam_probabilities(self, matrix: np.ndarray) -> np.ndarray:
        try:
            return self.model.predict_proba(matrix)[:, self._spam_col]
        except Exception as exc:
            raise PredictionError(f"The model failed to score the input: {exc}") from exc

    def predict(self, text: str, threshold: float = config.DEFAULT_THRESHOLD) -> Prediction:
        """Classify a single email."""
        if text is None or not str(text).strip():
            raise PredictionError("The email is empty. Paste or type some text first.")
        text = str(text)[: config.MAX_EMAIL_CHARS]

        doc = vectorize(text, self.wv)
        if doc.n_tokens == 0:
            raise PredictionError(
                "No readable words were found. The text may contain only symbols, "
                "numbers or stop words."
            )
        p_spam = float(self._spam_probabilities(doc.vector.reshape(1, -1))[0])
        return Prediction(
            is_spam=p_spam >= threshold,
            spam_probability=p_spam,
            threshold=threshold,
            n_tokens=doc.n_tokens,
            n_known=doc.n_known,
        )

    def predict_many(
        self, texts: list[str], threshold: float = config.DEFAULT_THRESHOLD
    ) -> list[Prediction]:
        """Classify many emails in one vectorised call (blank texts are not allowed)."""
        if not texts:
            return []
        trimmed = [str(t)[: config.MAX_EMAIL_CHARS] for t in texts]
        matrix, n_tokens, n_known = vectorize_many(trimmed, self.wv)
        probs = self._spam_probabilities(matrix)
        return [
            Prediction(
                is_spam=bool(p >= threshold),
                spam_probability=float(p),
                threshold=threshold,
                n_tokens=int(nt),
                n_known=int(nk),
            )
            for p, nt, nk in zip(probs, n_tokens, n_known)
        ]
