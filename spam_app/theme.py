"""Light / dark palettes and the custom CSS injected into Streamlit."""

from __future__ import annotations

LIGHT = {
    "bg": "#EEF1F6", "surface": "#FFFFFF", "surface2": "#F5F7FB", "ink": "#14203A",
    "muted": "#56627A", "line": "#D7DDE8", "accent": "#3B50D8", "accent_ink": "#FFFFFF",
    "spam": "#BE2F25", "spam_bg": "#FBE9E7", "safe": "#17705F", "safe_bg": "#E3F4EF",
    "warn": "#6B4E00", "warn_bg": "#FFF4D6", "shadow": "0 1px 2px rgba(20,32,58,.06)",
}
DARK = {
    "bg": "#0E1320", "surface": "#161D2E", "surface2": "#1C2438", "ink": "#E7ECF5",
    "muted": "#9AA6BD", "line": "#2A3550", "accent": "#8EA2FF", "accent_ink": "#0E1320",
    "spam": "#FF7A6E", "spam_bg": "#3A1E24", "safe": "#5FD9B8", "safe_bg": "#14352F",
    "warn": "#F2D58B", "warn_bg": "#3A311A", "shadow": "none",
}

FONTS_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:"
    "opsz,wght@12..96,500;12..96,700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');"
)

_BASE_CSS = """
:root {
  --bg:%(bg)s; --surface:%(surface)s; --surface2:%(surface2)s; --ink:%(ink)s;
  --muted:%(muted)s; --line:%(line)s; --accent:%(accent)s; --accent-ink:%(accent_ink)s;
  --spam:%(spam)s; --spam-bg:%(spam_bg)s; --safe:%(safe)s; --safe-bg:%(safe_bg)s;
  --warn:%(warn)s; --warn-bg:%(warn_bg)s; --shadow:%(shadow)s;
  --display:'Bricolage Grotesque','Segoe UI',system-ui,sans-serif;
  --body:'IBM Plex Sans','Segoe UI',system-ui,-apple-system,sans-serif;
}
html, body, .stApp, [data-testid="stAppViewContainer"] { background:var(--bg) !important; }
.stApp { font-family:var(--body); }
.stApp p, .stApp li, .stApp label { font-family:var(--body); }
[data-testid="stIconMaterial"], .material-symbols-rounded { font-family:'Material Symbols Rounded' !important; }
.stApp, .stApp p, .stApp li, .stApp label, [data-testid="stMarkdownContainer"],
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] *,
[data-testid="stRadio"] label, [data-testid="stCaptionContainer"] { color:var(--ink) !important; }
[data-testid="stCaptionContainer"], .muted { color:var(--muted) !important; }
h1, h2, h3 { font-family:var(--display) !important; color:var(--ink) !important; letter-spacing:-.01em; }

/* Chrome */
#MainMenu, footer, [data-testid="stDeployButton"], [data-testid="stAppDeployButton"], .stDeployButton { display:none !important; visibility:hidden; }
[data-testid="stHeader"] { background:transparent !important; }
[data-testid="stHeader"] * { color:var(--ink) !important; }
.block-container { max-width:1180px; padding-top:2.2rem; padding-bottom:4rem; }
[data-testid="stSidebar"] { background:var(--surface) !important; border-right:1px solid var(--line); }
[data-testid="stSidebar"] * { color:var(--ink); }

/* Header */
.app-head { display:flex; flex-wrap:wrap; align-items:flex-end; justify-content:space-between; gap:1rem; margin-bottom:1.1rem; }
.app-title { font-family:var(--display); font-weight:700; font-size:2rem; line-height:1.1; margin:0; color:var(--ink); }
.app-sub { margin:.35rem 0 0; color:var(--muted); font-size:.98rem; max-width:56ch; }
.kpis { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:.75rem; margin:0 0 1.4rem; }
.kpi { background:var(--surface); border:1px solid var(--line); border-radius:10px; padding:.8rem 1rem; box-shadow:var(--shadow); }
.kpi b { display:block; font-family:var(--display); font-size:1.6rem; line-height:1.15; color:var(--ink); }
.kpi span { font-size:.85rem; color:var(--muted); }
.kpi.spam b { color:var(--spam); } .kpi.safe b { color:var(--safe); }

/* Panels */
.panel { background:var(--surface); border:1px solid var(--line); border-radius:12px; padding:1.2rem 1.3rem; box-shadow:var(--shadow); }
.panel h3 { margin:0 0 .6rem; font-size:1.1rem; }
.empty { color:var(--muted); text-align:center; padding:2.2rem 1rem; line-height:1.55; }
.empty b { display:block; color:var(--ink); font-family:var(--display); font-size:1.1rem; margin-bottom:.3rem; }

/* Verdict (the stamp) */
.verdict { display:flex; flex-wrap:wrap; align-items:center; gap:1.4rem; }
.stamp { font-family:var(--display); font-weight:700; font-size:2.1rem; line-height:1; padding:.55rem 1.1rem;
  border:3px solid currentColor; border-radius:10px; outline:2px solid currentColor; outline-offset:3px;
  transform:rotate(-4deg); display:inline-block; animation:stampIn .35s ease-out both; }
.verdict.spam .stamp { color:var(--spam); } .verdict.safe .stamp { color:var(--safe); }
.conf b { display:block; font-family:var(--display); font-size:2.3rem; line-height:1; color:var(--ink); }
.conf span { color:var(--muted); font-size:.9rem; }
@keyframes stampIn { from { transform:rotate(-4deg) scale(1.35); opacity:0; } to { transform:rotate(-4deg) scale(1); opacity:1; } }
@media (prefers-reduced-motion: reduce) { .stamp { animation:none; } }

.split { display:flex; height:14px; border-radius:7px; overflow:hidden; background:var(--line); margin:1.2rem 0 .45rem; }
.split i { display:block; height:100%%; }
.split .s-safe { background:var(--safe); } .split .s-spam { background:var(--spam); }
.split-legend { display:flex; justify-content:space-between; font-size:.88rem; color:var(--muted); }
.split-legend .a { color:var(--safe); font-weight:600; } .split-legend .b { color:var(--spam); font-weight:600; }
.facts { display:grid; grid-template-columns:repeat(auto-fit,minmax(68px,1fr)); gap:.7rem; margin-top:1.1rem; }
.fact { background:var(--surface2); border-radius:8px; padding:.6rem .65rem; }
.fact b { display:block; font-size:1.2rem; color:var(--ink); } .fact span { font-size:.8rem; color:var(--muted); }

/* Notices & chips */
.notice { border-radius:8px; padding:.7rem .9rem; font-size:.93rem; margin:.8rem 0 0; line-height:1.45; }
.notice.warn { background:var(--warn-bg); color:var(--warn); }
.notice.error { background:var(--spam-bg); color:var(--spam); }
.notice.info { background:var(--surface2); color:var(--muted); border:1px solid var(--line); }
.chip { display:inline-block; padding:.12rem .55rem; border-radius:999px; font-size:.82rem; font-weight:600; white-space:nowrap; }
.chip.spam { background:var(--spam-bg); color:var(--spam); } .chip.safe { background:var(--safe-bg); color:var(--safe); }
.chip.skip { background:var(--surface2); color:var(--muted); }

/* Tables */
.tbl-wrap { overflow-x:auto; border:1px solid var(--line); border-radius:10px; background:var(--surface); }
table.tbl { border-collapse:collapse; width:100%%; font-size:.9rem; }
.tbl th { text-align:left; padding:.6rem .8rem; background:var(--surface2); color:var(--muted); font-weight:600; border-bottom:1px solid var(--line); white-space:nowrap; }
.tbl td { padding:.6rem .8rem; border-bottom:1px solid var(--line); color:var(--ink); vertical-align:top; }
.tbl tr:last-child td { border-bottom:0; } .tbl td.num { text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }
.tbl td.txt { min-width:260px; max-width:520px; }

/* Streamlit widgets */
[data-testid="stTextArea"] textarea, [data-baseweb="textarea"], [data-baseweb="base-input"],
[data-testid="stSelectbox"] [data-baseweb="select"] > div {
  background:var(--surface) !important; color:var(--ink) !important; border-color:var(--line) !important; }
[data-testid="stTextArea"] textarea { font-family:var(--body); font-size:1rem; line-height:1.55; }
[data-testid="stTextArea"] textarea::placeholder { color:var(--muted) !important; opacity:1; }
[data-baseweb="popover"] > div, [data-baseweb="menu"], ul[role="listbox"] { background:var(--surface) !important; }
[data-baseweb="popover"] li, [data-baseweb="popover"] li * { color:var(--ink) !important; }
div[data-testid="stTextArea"] div[data-baseweb="textarea"]:focus-within { border-color:var(--accent) !important; }

.stButton > button, [data-testid="stDownloadButton"] > button, [data-testid^="stBaseButton"] {
  border-radius:8px; font-family:var(--body); font-weight:600; border:1px solid var(--line);
  background:var(--surface); color:var(--ink); transition:border-color .15s, background .15s; }
.stButton > button:hover, [data-testid="stDownloadButton"] > button:hover { border-color:var(--accent); color:var(--accent); }
.stButton > button p, [data-testid="stDownloadButton"] > button p { color:inherit !important; }
.stButton > button[kind="primary"], button[data-testid="stBaseButton-primary"] {
  background:var(--accent) !important; color:var(--accent-ink) !important; border-color:var(--accent) !important; }
.stButton > button[kind="primary"] p, button[data-testid="stBaseButton-primary"] p { color:var(--accent-ink) !important; }
.stButton > button:focus-visible, [data-testid="stDownloadButton"] > button:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }

button[data-baseweb="tab"] { font-family:var(--body); font-weight:600; background:transparent !important; }
button[data-baseweb="tab"] p { color:var(--muted) !important; }
button[data-baseweb="tab"][aria-selected="true"] p { color:var(--ink) !important; }
[data-baseweb="tab-highlight"] { background:var(--accent) !important; }
[data-baseweb="tab-border"] { background:var(--line) !important; }

[data-testid="stFileUploaderDropzone"] { background:var(--surface) !important; border:1.5px dashed var(--line) !important; border-radius:10px; }
[data-testid="stFileUploaderDropzone"] * { color:var(--muted) !important; }
[data-testid="stFileUploaderDropzone"] button { color:var(--ink) !important; }
[data-testid="stFileUploader"] small { color:var(--muted) !important; }
[data-testid="stFileUploaderFile"], [data-testid="stFileChip"] { background:var(--surface2) !important; border-radius:8px; }
[data-testid="stFileUploaderFile"] *, [data-testid="stFileChip"] * { color:var(--ink) !important; }
[data-testid="stSelectbox"] div, [data-testid="stSelectbox"] input { background-color:var(--surface) !important; color:var(--ink) !important; border-color:var(--line) !important; }
[data-testid="stSelectboxVirtualDropdown"], [data-testid="stSelectboxVirtualDropdown"] *, [role="listbox"], [role="listbox"] *, [role="option"] { background-color:var(--surface) !important; color:var(--ink) !important; }
[role="option"][aria-selected="true"], [role="option"]:hover { background-color:var(--surface2) !important; }
[data-testid="stSelectbox"] svg { fill:var(--muted) !important; }
[data-testid="stRadio"] [role="radiogroup"] label p { color:var(--ink) !important; }

[class*="st-key-sample_"] button { height:auto; min-height:2.5rem; padding:.35rem .5rem; }
[class*="st-key-sample_"] button p { white-space:normal; line-height:1.2; font-size:.86rem; text-align:center; }
[data-testid="stTextArea"] textarea { border:0 !important; outline:none !important; }
[data-testid="stTextArea"] div { border-color:var(--line) !important; background-color:var(--surface) !important; }
[data-testid="stTextArea"] div:focus-within { border-color:var(--accent) !important; }
.verdict { padding-top:.5rem; }

/* Responsive */
@media (max-width: 760px) {
  .block-container { padding-left:1rem; padding-right:1rem; padding-top:1.2rem; }
  .app-title { font-size:1.55rem; }
  .kpis { grid-template-columns:repeat(2,minmax(0,1fr)); }
  .stamp { font-size:1.7rem; } .conf b { font-size:1.9rem; }
  /* keep sample buttons and Predict/Clear two-per-row instead of one tall stack */
  [data-testid="stHorizontalBlock"]:has([class*="st-key-sample_"]):not(:has([data-testid="stHorizontalBlock"])),
  [data-testid="stHorizontalBlock"]:has([class*="st-key-act_"]):not(:has([data-testid="stHorizontalBlock"])) { flex-direction:row !important; flex-wrap:wrap !important; gap:.5rem !important; }
  [data-testid="stHorizontalBlock"]:has([class*="st-key-sample_"]):not(:has([data-testid="stHorizontalBlock"])) > [data-testid="stColumn"],
  [data-testid="stHorizontalBlock"]:has([class*="st-key-act_"]):not(:has([data-testid="stHorizontalBlock"])) > [data-testid="stColumn"] { flex:1 1 calc(50% - .5rem) !important; min-width:calc(50% - .5rem) !important; width:auto !important; }
  [data-testid="stHorizontalBlock"]:has([class*="st-key-act_"]):not(:has([data-testid="stHorizontalBlock"])) > [data-testid="stColumn"]:last-child:empty { display:none; }
}
"""


def build_css(dark: bool) -> str:
    """Return a <style> block for the chosen theme.

    Colours are injected by plain placeholder replacement (``%(name)s``), so CSS
    percent signs such as ``calc(50% - 1rem)`` need no escaping.
    """
    palette = DARK if dark else LIGHT
    css = _BASE_CSS
    for key, value in palette.items():
        css = css.replace(f"%({key})s", value)
    css = css.replace("%%", "%")  # legacy escaped percent signs
    return f"<style>{FONTS_IMPORT}{css}</style>"
