"""Email Spam Classifier: Streamlit app.

Run with:  streamlit run app.py
"""

from __future__ import annotations

import logging

import streamlit as st

from spam_app import batch, components, config, history, theme
from spam_app.classifier import ModelLoadError, PredictionError, SpamClassifier
from spam_app.samples import SAMPLE_EMAILS, SAMPLES_BY_KEY

logger = logging.getLogger("spam_app")

st.set_page_config(page_title=config.APP_TITLE, page_icon=config.APP_ICON, layout="wide")

SAMPLE_CSV_PATH = config.BASE_DIR / "sample_data" / "sample_emails.csv"


@st.cache_resource(show_spinner="Loading models…")
def load_classifier() -> SpamClassifier:
    return SpamClassifier.load()


def html(fragment: str) -> None:
    st.markdown(fragment, unsafe_allow_html=True)


# ----------------------------------------------------------------- callbacks
def use_sample(key: str) -> None:
    st.session_state["email_text"] = SAMPLES_BY_KEY[key]
    st.session_state.pop("last_result", None)
    st.session_state.pop("last_error", None)


def clear_input() -> None:
    st.session_state["email_text"] = ""
    st.session_state.pop("last_result", None)
    st.session_state.pop("last_error", None)


# ------------------------------------------------------------------- sidebar
def render_sidebar(clf: SpamClassifier | None) -> float:
    with st.sidebar:
        st.markdown("### Settings")
        st.toggle("Dark mode", key="dark_mode")
        threshold = st.slider(
            "Spam threshold",
            0.05, 0.95, config.DEFAULT_THRESHOLD, 0.05,
            help="An email is marked as spam when its spam probability is at or above this value. "
                 "0.50 matches the model's default decision.",
        )
        st.markdown("### Model")
        if clf is not None:
            st.caption(
                f"XGBoost classifier \n\n"
                f"Vocabulary: {clf.vocabulary_size:,} words · Vector size: {clf.vector_size}"
            )
        # else:
        #     st.caption("Model not loaded.")
        # st.caption("History lives only in this browser session and is never saved to disk.")
    return threshold


# ----------------------------------------------------------------- classify
def run_prediction(clf: SpamClassifier, threshold: float) -> None:
    """Button callback: runs before the page redraws so counters are never stale."""
    text = st.session_state.get("email_text", "")
    st.session_state.pop("last_error", None)
    try:
        pred = clf.predict(text, threshold)
    except PredictionError as exc:
        st.session_state.pop("last_result", None)
        st.session_state["last_error"] = str(exc)
        return
    except Exception:  # noqa: BLE001 - never show a traceback to the user
        logger.exception("Unexpected prediction failure")
        st.session_state.pop("last_result", None)
        st.session_state["last_error"] = "Something went wrong while classifying this email. Please try again."
        return
    st.session_state["last_result"] = pred
    history.add_entry(st.session_state, text, pred)


def render_classify_tab(clf: SpamClassifier, threshold: float) -> None:
    left, right = st.columns([3, 2], gap="large")
    with left:
        # st.markdown("**Try a sample**")
        # for row_start in range(0, len(SAMPLE_EMAILS), 4):
        #     cols = st.columns(4)
        #     for col, (key, label, _text) in zip(cols, SAMPLE_EMAILS[row_start:row_start + 4]):
        #         col.button(label, key=f"sample_{key}", on_click=use_sample, args=(key,), width="stretch")

        st.text_area(
            "Email text",
            key="email_text",
            height=240,
            max_chars=config.MAX_EMAIL_CHARS,
            placeholder="Paste the email you want to check…",
        )
        b1, b2, _ = st.columns([1, 1, 2])
        b1.button("Predict", key="act_predict", type="primary", width="stretch",
                  on_click=run_prediction, args=(clf, threshold))
        b2.button("Clear", key="act_clear", on_click=clear_input, width="stretch")

    with right:
        error = st.session_state.get("last_error")
        result = st.session_state.get("last_result")
        if error:
            html(f'<div class="panel">{components.notice("error", error)}</div>')
        elif result:
            html(components.result_panel(result))
        else:
            html(
                '<div class="panel">'
                + components.empty_state(
                    "No result yet",
                    "Paste an email or pick a sample, then press Predict to see the verdict and confidence.",
                )
                + "</div>"
            )


# --------------------------------------------------------------------- bulk
def render_bulk_tab(clf: SpamClassifier, threshold: float) -> None:
    st.markdown("Upload a CSV with one email per row. The first row must be a header.")
    if SAMPLE_CSV_PATH.is_file():
        st.download_button("Download sample CSV", SAMPLE_CSV_PATH.read_bytes(),
                           file_name="sample_emails.csv", mime="text/csv")

    upload = st.file_uploader("CSV file", type=["csv"], label_visibility="collapsed")
    if upload is None:
        st.session_state.pop("batch_result", None)
        return

    try:
        loaded = batch.read_csv_upload(upload.getvalue())
    except batch.BatchError as exc:
        html(components.notice("error", str(exc)))
        return
    except Exception:  # noqa: BLE001
        logger.exception("CSV upload failed")
        html(components.notice("error", "The file could not be processed. Please check it is a valid CSV."))
        return

    frame = loaded.frame
    if loaded.truncated:
        html(components.notice("warn", f"Only the first {config.MAX_BATCH_ROWS:,} rows will be classified."))

    columns = list(frame.columns)
    default_col = batch.detect_text_column(frame)
    c1, c2 = st.columns([2, 1], gap="medium")
    text_col = c1.selectbox("Column with the email text", columns, index=columns.index(default_col))
    c2.markdown("<div style='height:1.9rem'></div>", unsafe_allow_html=True)
    go = c2.button(f"Classify {len(frame):,} emails", type="primary", width="stretch")

    if go:
        try:
            with st.spinner("Classifying…"):
                st.session_state["batch_result"] = (
                    upload.name, text_col, batch.classify_frame(frame, text_col, clf, threshold),
                )
        except batch.BatchError as exc:
            st.session_state.pop("batch_result", None)
            html(components.notice("error", str(exc)))
            return
        except PredictionError as exc:
            st.session_state.pop("batch_result", None)
            html(components.notice("error", str(exc)))
            return
        except Exception:  # noqa: BLE001
            logger.exception("Batch classification failed")
            st.session_state.pop("batch_result", None)
            html(components.notice("error", "Classification failed unexpectedly. Please try again."))
            return

    stored = st.session_state.get("batch_result")
    if not stored or stored[0] != upload.name:
        return
    _name, used_col, result = stored
    stats = batch.summarize(result)

    html(components.kpi_strip({"total": stats["total"], "spam": stats["spam"], "ham": stats["ham"],
                               "spam_rate": stats["spam_rate"]},
                               total_label="Emails in file"))
    html(components.share_bar(stats["spam"], stats["ham"]))
    notes = []
    if stats["skipped"]:
        notes.append(f"{stats['skipped']:,} empty row(s) were skipped.")
    if stats["low_reliability"]:
        notes.append(f"{stats['low_reliability']:,} row(s) have few known words and may be unreliable.")
    if notes:
        html(components.notice("info", " ".join(notes)))

    st.markdown("&nbsp;")
    view = st.radio("Show", ["All", "Spam", "Not spam"], horizontal=True)
    frame_out = result.frame
    if view != "All":
        label = config.LABEL_SPAM if view == "Spam" else config.LABEL_HAM
        frame_out = frame_out[frame_out[result.prediction_col] == label]

    limit = 200
    st.caption(f"Showing {min(limit, len(frame_out)):,} of {len(frame_out):,} rows. The download has every row.")
    html(components.results_table(frame_out.head(limit), used_col, result.prediction_col,
                                  result.probability_col, result.confidence_col))
    st.download_button("Download results (CSV)", batch.to_csv_bytes(result.frame),
                       file_name="spam_classification_results.csv", mime="text/csv", type="primary")


# ------------------------------------------------------------------ history
def render_history_tab() -> None:
    entries = history.get_history(st.session_state)
    if not entries:
        html('<div class="panel">' + components.empty_state(
            "No predictions yet", "Emails you classify on the Classify tab will be listed here.") + "</div>")
        return
    c1, c2, _ = st.columns([1, 1, 3])
    c1.download_button("Download CSV", history.history_to_csv(st.session_state),
                       file_name="prediction_history.csv", mime="text/csv", width="stretch")
    c2.button("Clear history", on_click=history.clear_history, args=(st.session_state,), width="stretch")
    html(components.history_table(entries))


# --------------------------------------------------------------------- main
def main() -> None:
    st.session_state.setdefault("dark_mode", False)
    st.session_state.setdefault("email_text", "")

    clf: SpamClassifier | None = None
    load_error: str | None = None
    try:
        clf = load_classifier()
    except ModelLoadError as exc:
        load_error = str(exc)
    except Exception:  # noqa: BLE001
        logger.exception("Unexpected model load failure")
        load_error = "The models could not be loaded. Check the server logs for details."

    threshold = render_sidebar(clf)
    html(theme.build_css(st.session_state["dark_mode"]))
    html(components.header(
        config.APP_TITLE,
        "Check whether an email is spam, review past results, or classify a whole CSV at once.",
    ))

    if clf is None:
        html(components.notice("error", load_error or "Models unavailable."))
        st.stop()

    html(components.kpi_strip(history.session_stats(st.session_state)))
    n_hist = len(history.get_history(st.session_state))
    tab_classify, tab_bulk, tab_history = st.tabs(["Classify", "Bulk CSV", f"History ({n_hist})"])
    with tab_classify:
        render_classify_tab(clf, threshold)
    with tab_bulk:
        render_bulk_tab(clf, threshold)
    with tab_history:
        render_history_tab()


main()
