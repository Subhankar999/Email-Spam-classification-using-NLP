"""Prediction history kept in the user's session (never written to disk)."""

from __future__ import annotations

import io
from collections.abc import MutableMapping
from datetime import datetime
from typing import Any

import pandas as pd

from . import config
from .classifier import Prediction

HISTORY_KEY = "prediction_history"
PREVIEW_CHARS = 140

COLUMNS = ["time", "email", "prediction", "spam_probability", "confidence"]


def get_history(state: MutableMapping[str, Any]) -> list[dict[str, Any]]:
    return state.setdefault(HISTORY_KEY, [])


def add_entry(state: MutableMapping[str, Any], text: str, prediction: Prediction) -> None:
    """Add a prediction to the front of the history, keeping the newest entries."""
    history = get_history(state)
    history.insert(
        0,
        {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "email": " ".join(text.split()),
            "prediction": prediction.label,
            "spam_probability": round(prediction.spam_probability, 6),
            "confidence": round(prediction.confidence, 6),
        },
    )
    del history[config.MAX_HISTORY:]


def clear_history(state: MutableMapping[str, Any]) -> None:
    state[HISTORY_KEY] = []


def history_frame(state: MutableMapping[str, Any]) -> pd.DataFrame:
    return pd.DataFrame(get_history(state), columns=COLUMNS)


def history_to_csv(state: MutableMapping[str, Any]) -> bytes:
    buffer = io.StringIO()
    history_frame(state).to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8-sig")


def session_stats(state: MutableMapping[str, Any]) -> dict[str, float]:
    """Counts for the dashboard header."""
    history = get_history(state)
    total = len(history)
    spam = sum(1 for h in history if h["prediction"] == config.LABEL_SPAM)
    return {
        "total": total,
        "spam": spam,
        "ham": total - spam,
        "spam_rate": (spam / total) if total else 0.0,
    }
