"""Central configuration for the Email Spam Classifier app."""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"

# Paths can be overridden with environment variables (useful for deployment).
CLASSIFIER_PATH = Path(os.getenv("SPAM_MODEL_PATH", MODELS_DIR / "spam_classifier.pkl"))
WORD2VEC_PATH = Path(os.getenv("WORD2VEC_MODEL_PATH", MODELS_DIR / "word2vec.model"))

# Label encoding used when the model was trained (LabelEncoder: ham -> 0, spam -> 1).
HAM_CLASS = 0
SPAM_CLASS = 1
LABEL_SPAM = "Spam"
LABEL_HAM = "Not Spam"

# Decision threshold on the spam probability. 0.5 matches `model.predict()`.
DEFAULT_THRESHOLD = 0.5

# Safety limits.
MAX_EMAIL_CHARS = 20_000
MAX_BATCH_ROWS = 50_000
MAX_HISTORY = 100

# Likely names for the column that holds the email text in an uploaded CSV.
TEXT_COLUMN_CANDIDATES = (
    "message", "email", "text", "body", "content", "email_text", "email_body", "mail",
)

# If fewer than this share of an email's words are in the Word2Vec vocabulary,
# the result is flagged as low-reliability.
LOW_COVERAGE_WARNING = 0.30

APP_TITLE = "Email Spam Classifier"
APP_ICON = "📮"
