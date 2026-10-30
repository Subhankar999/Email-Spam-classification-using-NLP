"""Bulk classification of emails from an uploaded CSV file."""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import BinaryIO

import numpy as np
import pandas as pd

from . import config
from .classifier import SpamClassifier

SKIPPED_LABEL = "Skipped (empty)"


class BatchError(ValueError):
    """Raised for problems with the uploaded file that the user can fix."""


@dataclass(frozen=True)
class LoadedCsv:
    frame: pd.DataFrame
    truncated: bool  # True if rows beyond MAX_BATCH_ROWS were dropped


@dataclass(frozen=True)
class BatchResult:
    """Classified table plus the names of the columns that were added to it."""

    frame: pd.DataFrame
    prediction_col: str
    probability_col: str
    confidence_col: str
    reliability_col: str


def _candidate_encodings(raw: bytes) -> tuple[str, ...]:
    # UTF-16 is only attempted when a BOM says so; otherwise it can "succeed" on
    # unrelated bytes and return garbage.
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return ("utf-16",)
    return ("utf-8-sig", "cp1252", "latin-1")


def read_csv_upload(file: BinaryIO | bytes) -> LoadedCsv:
    """Read an uploaded CSV, trying common encodings and giving friendly errors."""
    raw = file if isinstance(file, bytes) else file.read()
    if not raw or not raw.strip():
        raise BatchError("The uploaded file is empty.")

    frame: pd.DataFrame | None = None
    parse_error: Exception | None = None
    for encoding in _candidate_encodings(raw):
        try:
            frame = pd.read_csv(
                io.BytesIO(raw),
                encoding=encoding,
                sep=None,  # sniff comma / semicolon / tab
                engine="python",
                dtype=str,
                keep_default_na=False,
            )
            break
        except UnicodeError:
            continue  # try the next encoding
        except pd.errors.EmptyDataError as exc:
            raise BatchError("The uploaded file has no readable rows.") from exc
        except Exception as exc:  # malformed CSV: another encoding will not help
            parse_error = exc
            break

    if frame is None:
        detail = f" ({parse_error})" if parse_error else ""
        raise BatchError(
            "The file could not be read as a CSV. Check that it is a text CSV "
            f"with a header row.{detail}"
        )

    if frame.empty or frame.shape[1] == 0:
        raise BatchError("The CSV has a header but no data rows.")

    frame.columns = [str(c).strip() or f"column_{i + 1}" for i, c in enumerate(frame.columns)]
    truncated = len(frame) > config.MAX_BATCH_ROWS
    if truncated:
        frame = frame.head(config.MAX_BATCH_ROWS)
    return LoadedCsv(frame.reset_index(drop=True), truncated)


def detect_text_column(frame: pd.DataFrame) -> str:
    """Guess which column holds the email text."""
    lowered = {str(c).strip().lower(): c for c in frame.columns}
    for candidate in config.TEXT_COLUMN_CANDIDATES:
        if candidate in lowered:
            return lowered[candidate]
    # Otherwise: the column with the longest average text.
    lengths = {c: frame[c].astype(str).str.len().mean() for c in frame.columns}
    return max(lengths, key=lengths.get)


def _unique_name(name: str, existing: set[str]) -> str:
    candidate = name
    while candidate in existing:
        candidate = f"{candidate}_model"
    return candidate


def classify_frame(
    frame: pd.DataFrame,
    text_column: str,
    classifier: SpamClassifier,
    threshold: float = config.DEFAULT_THRESHOLD,
) -> BatchResult:
    """Return a copy of ``frame`` with prediction columns appended."""
    if text_column not in frame.columns:
        raise BatchError(f"Column '{text_column}' was not found in the file.")

    texts = frame[text_column].fillna("").astype(str)
    valid_mask = texts.str.strip() != ""
    if not valid_mask.any():
        raise BatchError(f"Column '{text_column}' has no text to classify.")

    predictions = classifier.predict_many(texts[valid_mask].tolist(), threshold)

    n = len(frame)
    label = np.full(n, SKIPPED_LABEL, dtype=object)
    p_spam = np.full(n, np.nan)
    confidence = np.full(n, np.nan)
    coverage = np.full(n, np.nan)
    reliability = np.full(n, "", dtype=object)

    positions = np.flatnonzero(valid_mask.to_numpy())
    for pos, pred in zip(positions, predictions):
        label[pos] = pred.label
        p_spam[pos] = round(pred.spam_probability, 6)
        confidence[pos] = round(pred.confidence, 6)
        coverage[pos] = round(pred.coverage, 3)
        reliability[pos] = "Low" if pred.low_reliability else "OK"

    existing = set(frame.columns)
    out = frame.copy()
    names: dict[str, str] = {}
    for name, values in (
        ("prediction", label),
        ("spam_probability", p_spam),
        ("confidence", confidence),
        ("word_coverage", coverage),
        ("reliability", reliability),
    ):
        unique = _unique_name(name, existing)
        existing.add(unique)
        out[unique] = values
        names[name] = unique
    return BatchResult(
        frame=out,
        prediction_col=names["prediction"],
        probability_col=names["spam_probability"],
        confidence_col=names["confidence"],
        reliability_col=names["reliability"],
    )


def summarize(result: BatchResult) -> dict[str, float]:
    counts = result.frame[result.prediction_col].value_counts()
    spam = int(counts.get(config.LABEL_SPAM, 0))
    ham = int(counts.get(config.LABEL_HAM, 0))
    skipped = int(counts.get(SKIPPED_LABEL, 0))
    classified = spam + ham
    low = int((result.frame[result.reliability_col] == "Low").sum())
    return {
        "total": len(result.frame),
        "spam": spam,
        "ham": ham,
        "skipped": skipped,
        "low_reliability": low,
        "spam_rate": (spam / classified) if classified else 0.0,
    }


def to_csv_bytes(frame: pd.DataFrame) -> bytes:
    """UTF-8 with BOM so Excel shows non-ASCII characters (e.g. the rupee sign) correctly."""
    return frame.to_csv(index=False).encode("utf-8-sig")
