"""HTML fragments for the dashboard. All user-supplied text is escaped."""

from __future__ import annotations

from html import escape

import pandas as pd

from . import config
from .batch import SKIPPED_LABEL
from .classifier import Prediction


def _pct(x: float, digits: int = 1) -> str:
    """Format a share as a percentage without overstating certainty.

    Values are truncated rather than rounded, so 0.99996 shows as 99.9% and not 100.0%;
    non-zero values below the display precision show as "under 0.1%".
    """
    scale = 10 ** digits
    value = int(x * 100 * scale) / scale
    if x > 0 and value == 0:
        return f"under {1 / scale:.{digits}f}%"
    return f"{value:.{digits}f}%"


def header(title: str, subtitle: str) -> str:
    return (
        f'<div class="app-head"><div><h1 class="app-title">{escape(title)}</h1>'
        f'<p class="app-sub">{escape(subtitle)}</p></div></div>'
    )


def kpi_strip(stats: dict, total_label: str = "Emails checked this session") -> str:
    items = (
        ("", f"{int(stats['total'])}", total_label),
        ("spam", f"{int(stats['spam'])}", "Marked as spam"),
        ("safe", f"{int(stats['ham'])}", "Marked as not spam"),
        ("", _pct(stats["spam_rate"], 0), "Spam share"),
    )
    cells = "".join(f'<div class="kpi {c}"><b>{v}</b><span>{escape(l)}</span></div>' for c, v, l in items)
    return f'<div class="kpis">{cells}</div>'


def notice(kind: str, message: str) -> str:
    """kind: 'warn' | 'error' | 'info'."""
    return f'<div class="notice {kind}" role="alert">{escape(message)}</div>'


def empty_state(title: str, body: str) -> str:
    return f'<div class="empty"><b>{escape(title)}</b>{escape(body)}</div>'


def result_panel(pred: Prediction) -> str:
    kind = "spam" if pred.is_spam else "safe"
    p_spam, p_ham = pred.spam_probability, 1 - pred.spam_probability
    html = (
        f'<div class="panel"><div class="verdict {kind}" aria-live="polite">'
        f'<div class="stamp" aria-label="Verdict: {escape(pred.label)}">{escape(pred.label.upper())}</div>'
        f'<div class="conf"><b>{_pct(pred.confidence)}</b><span>confidence</span></div></div>'
        f'<div class="split" role="img" aria-label="Not spam {_pct(p_ham)}, spam {_pct(p_spam)}">'
        f'<i class="s-safe" style="width:{p_ham * 100:.2f}%"></i>'
        f'<i class="s-spam" style="width:{p_spam * 100:.2f}%"></i></div>'
        f'<div class="split-legend"><span class="a">Not spam {_pct(p_ham)}</span>'
        f'<span class="b">Spam {_pct(p_spam)}</span></div>'
        f'<div class="facts">'
        f'<div class="fact"><b>{pred.n_tokens}</b><span>Words</span></div>'
        f'<div class="fact"><b>{pred.n_known}</b><span>Known</span></div>'
        f'<div class="fact"><b>{_pct(pred.coverage, 0)}</b><span>Match</span></div></div>'
    )
    if abs(pred.threshold - config.DEFAULT_THRESHOLD) > 1e-9:
        html += notice("info", f"Custom threshold in use: flagged as spam at {_pct(pred.threshold, 0)} or higher.")
    if pred.low_reliability:
        html += notice(
            "warn",
            "Few words in this email are in the model's vocabulary, so this result may be unreliable. "
            "The model was trained on short messages.",
        )
    return html + "</div>"


def _chip(label: str) -> str:
    cls = {config.LABEL_SPAM: "spam", config.LABEL_HAM: "safe"}.get(label, "skip")
    return f'<span class="chip {cls}">{escape(label)}</span>'


def _cell(value, truncate: int = 160) -> str:
    text = "" if pd.isna(value) else str(value)
    if len(text) > truncate:
        text = text[:truncate].rstrip() + "…"
    return escape(text)


def history_table(entries: list[dict]) -> str:
    rows = "".join(
        f'<tr><td class="num">{escape(e["time"])}</td><td class="txt">{_cell(e["email"])}</td>'
        f'<td>{_chip(e["prediction"])}</td><td class="num">{_pct(e["confidence"])}</td></tr>'
        for e in entries
    )
    return (
        '<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Time</th><th>Email</th>'
        f'<th>Result</th><th>Confidence</th></tr></thead><tbody>{rows}</tbody></table></div>'
    )


def share_bar(spam: int, ham: int) -> str:
    total = spam + ham
    if not total:
        return ""
    ham_w, spam_w = ham / total * 100, spam / total * 100
    return (
        f'<div class="split" role="img" aria-label="{ham} not spam, {spam} spam">'
        f'<i class="s-safe" style="width:{ham_w:.2f}%"></i><i class="s-spam" style="width:{spam_w:.2f}%"></i></div>'
        f'<div class="split-legend"><span class="a">Not spam {ham}</span><span class="b">Spam {spam}</span></div>'
    )


def results_table(frame: pd.DataFrame, text_col: str, pred_col: str, prob_col: str, conf_col: str) -> str:
    """Compact preview of batch results (full data is in the CSV download)."""
    rows = ""
    for idx, row in frame.iterrows():
        conf = row[conf_col]
        conf_txt = "–" if pd.isna(conf) else _pct(float(conf))
        prob = row[prob_col]
        prob_txt = "–" if pd.isna(prob) else _pct(float(prob))
        rows += (
            f'<tr><td class="num">{idx + 1}</td><td class="txt">{_cell(row[text_col])}</td>'
            f'<td>{_chip(row[pred_col])}</td><td class="num">{prob_txt}</td><td class="num">{conf_txt}</td></tr>'
        )
    return (
        '<div class="tbl-wrap"><table class="tbl"><thead><tr><th>#</th><th>Email</th><th>Result</th>'
        f'<th>Spam probability</th><th>Confidence</th></tr></thead><tbody>{rows}</tbody></table></div>'
    )


__all__ = [n for n in dir() if not n.startswith("_")] + ["SKIPPED_LABEL"]
