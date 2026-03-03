"""
app.py
SupportOps AI Monitor — Streamlit Dashboard
Run with: streamlit run app.py
"""

import uuid
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timezone

import database as db
import ticket_generator as tg
import ai_triage

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SupportOps AI Monitor",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Design tokens ─────────────────────────────────────────────────────────────
COLORS = {
    "bg":      "#1e1e1e",
    "surface": "#252526",
    "border":  "#3e3e42",
    "text":    "#d4d4d4",
    "muted":   "#6b7280",
    "accent":  "#C9A84C",
    "success": "#4ade80",
    "warning": "#fb923c",
    "danger":  "#f87171",
    "neutral": "#6b7280",
    "indigo":  "#818cf8",
    "yellow":  "#facc15",
}

PRIORITY_COLORS  = {"critical": COLORS["danger"],  "high": COLORS["warning"], "medium": COLORS["yellow"], "low": COLORS["success"]}
SENTIMENT_COLORS = {"positive": COLORS["success"], "neutral": COLORS["neutral"], "negative": COLORS["danger"]}
ERROR_COLORS     = {"rate_limit": COLORS["warning"], "server_error": COLORS["danger"], "timeout": COLORS["yellow"], "unknown": COLORS["neutral"]}
HTTP_COLORS      = {"200": COLORS["success"], "429": COLORS["warning"], "500": COLORS["danger"], "408": COLORS["yellow"], "0": COLORS["neutral"]}

CHART_H_PRIMARY   = 300
CHART_H_SECONDARY = 220
CHART_MARGIN      = dict(t=48, b=0, l=0, r=0)
PLOTLY_CONFIG     = {"displaylogo": False,
                     "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d"]}

# ── Global CSS — VS Code Dark+ terminal aesthetic ─────────────────────────────
# Load Material Symbols font so Streamlit's icon ligatures render as icons
# instead of literal text like "keyboard_double_arrow_right".
# <link> tags are NOT stripped by st.markdown (unlike <script>).
st.markdown(
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family='
    'Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family='
    'Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/icon?family='
    'Material+Icons|Material+Icons+Round|Material+Icons+Outlined" />',
    unsafe_allow_html=True,
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stMarkdown, .stText,
[data-testid="stMetricValue"], [data-testid="stMetricLabel"],
.stSelectbox, .stMultiSelect, .stSlider, .stButton button,
h1,h2,h3,h4,h5,h6, p, span, div, label, input, textarea,
code, pre, .stCode, [data-testid="stCodeBlock"],
.streamlit-expanderHeader
  { font-family: 'JetBrains Mono', monospace !important; }
/* Restore Material icon fonts — the global monospace override above
   clobbers Streamlit's icon font on span/div elements. */
.material-icons,
.material-icons-round,
.material-icons-outlined,
.material-symbols-rounded,
.material-symbols-outlined,
[class*="material-symbols"],
[class*="material-icons"],
[data-testid="stSidebarCollapseButton"] span,
[data-testid="stSidebarCollapseButton"] button span,
[data-testid="collapsedControl"] span,
[data-testid="collapsedControl"] button span,
header[data-testid="stHeader"] span,
header[data-testid="stHeader"] button span {
  font-family: 'Material Symbols Rounded', 'Material Symbols Outlined',
               'Material Icons', 'Material Icons Round', 'Material Icons Outlined' !important;
  font-weight: normal !important;
  font-style: normal !important;
  letter-spacing: normal !important;
  text-transform: none !important;
  white-space: nowrap !important;
}
.stApp { background-color: #1e1e1e !important; }
section[data-testid="stSidebar"]
  { background-color: #252526 !important; border-right: 1px solid #3e3e42 !important; }
.stButton button[kind="primary"], .stButton button[data-testid="baseButton-primary"], button[kind="primary"]
  { background-color: #C9A84C !important; color: #1e1e1e !important;
    border: 1px solid #C9A84C !important; font-weight: 600 !important; }
.stButton button[kind="primary"]:hover, button[kind="primary"]:hover
  { background-color: #b8972e !important; border-color: #b8972e !important; }
[data-testid="metric-container"]
  { background: #252526 !important; border: 1px solid #3e3e42 !important;
    border-radius: 4px !important; padding: 1rem !important; }
[data-testid="stMetricValue"] { color: #C9A84C !important; font-weight: 700 !important; }
.stDataFrame { border: 1px solid #3e3e42 !important; border-radius: 4px !important; }
.streamlit-expanderHeader { background-color: #252526 !important; border-radius: 4px !important; }
.stTextInput input, .stTextArea textarea
  { background-color: #252526 !important; border: 1px solid #3e3e42 !important; color: #d4d4d4 !important; }
hr { border-color: #3e3e42 !important; }
h1,h2,h3 { letter-spacing: -0.02em; font-weight: 600; color: #d4d4d4 !important; }
::selection { background: #C9A84C; color: #1e1e1e; }
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: #1e1e1e; }
::-webkit-scrollbar-thumb { background: #3e3e42; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #5a5a5e; }
footer { visibility: hidden !important; }
.custom-footer { position: fixed; left: 0; bottom: 0; width: 100%;
  background: rgba(30,30,30,0.95); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
  border-top: 1px solid #3e3e42; text-align: center; padding: 0.6rem 1rem;
  font-size: 0.72rem; color: #858585; z-index: 999; font-family: 'JetBrains Mono', monospace; }
.custom-footer a { color: #C9A84C; text-decoration: none; }
.main .block-container { padding-bottom: 4rem !important; }
/* Terminal-style multiselect tags — outline, not filled */
[data-testid="stMultiSelect"] [data-baseweb="tag"]
  { background-color: transparent !important; border: 1px solid #C9A84C !important;
    color: #C9A84C !important; border-radius: 2px !important; }
[data-testid="stMultiSelect"] [data-baseweb="tag"] span,
[data-testid="stMultiSelect"] [data-baseweb="tag"] [role="presentation"]
  { color: #C9A84C !important; }
/* Hide Streamlit header anchor icon */
[data-testid="StyledLinkIconContainer"] { display: none !important; }
/* Streamlit top bar — keep it functional (sidebar toggle lives here)
   but make it invisible so it doesn't clash with our design */
header[data-testid="stHeader"] {
  background: transparent !important;
  border: none !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
}
#MainMenu { display: none !important; }
/* Sidebar collapse/expand — theme the icon color */
[data-testid="stSidebarCollapseButton"] button,
[data-testid="collapsedControl"] button { color: #858585 !important; }
/* Fix upload widget text clipping in narrow sidebar */
[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] span
  { word-wrap: break-word !important; overflow-wrap: break-word !important;
    font-size: 0.78rem !important; }
/* Minimal print fallback — hides chrome if user hits Ctrl+P on dashboard.
   For a proper PDF, use the Download PDF Report button instead. */
@media print {
  /* 1. Hide UI elements */
  section[data-testid="stSidebar"],
  header[data-testid="stHeader"],
  .custom-footer, .back-to-top, iframe,
  [data-testid="stSidebarCollapseButton"],
  [data-testid="stBottomBlockContainer"],
  [data-testid="stFileUploader"],
  .stButton, .stCheckbox, .stToggle, .stDownloadButton,
  #MainMenu, footer, .stSpinner, .stMetricDelta { display: none !important; }

  /* 2. Base Page Reset */
  html, body, .stApp, .main, .stAppViewContainer, .stAppMain, 
  [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"] {
    background-color: white !important;
    color: black !important;
  }
  
  [data-testid="stMainBlockContainer"] { 
    max-width: 100% !important; 
    padding: 0 !important; 
    margin: 0 !important;
  }

  /* 3. Headers and Terminal Cmds */
  h1, h2, h3, h4, h5, h6, p, span, div, label, .term-cmd { 
    color: black !important; 
    background-color: transparent !important;
    text-shadow: none !important;
  }
  
  .term-cmd {
    border-bottom: 2px solid #C9A84C !important;
    padding-bottom: 4px !important;
    margin: 2rem 0 0.5rem 0 !important;
    font-weight: 700 !important;
  }
  .term-cmd span { color: #C9A84C !important; }

  /* 4. KPI Metrics - Keep them simple and bold */
  [data-testid="metric-container"] {
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    margin-bottom: 10px;
  }
  [data-testid="stMetricValue"] { color: #C9A84C !important; font-weight: 800 !important; }
  [data-testid="stMetricLabel"] { color: #333333 !important; }

  /* 5. Charts & DataFrames - THE FIX */
  /* We use invert(1) hue-rotate(180deg) to flip the dark theme to light theme
     for these specific complex components while preserving colors. */
  [data-testid="stPlotlyChart"], [data-testid="stDataFrame"] {
    filter: invert(1) hue-rotate(180deg) contrast(0.9) brightness(1.1) !important;
    background-color: transparent !important;
    margin-bottom: 2rem !important;
    page-break-inside: avoid !important;
    display: block !important;
  }
  
  /* Ensure the surrounding container doesn't have a dark background */
  .element-container, .stPlotlyChart, .stDataFrame {
    background-color: white !important;
  }

  /* 6. General Cleanup */
  * { 
    -webkit-print-color-adjust: exact !important; 
    print-color-adjust: exact !important;
  }
  
  hr { display: none !important; }
}
</style>





""", unsafe_allow_html=True)

# ── JS fixes — st.markdown strips <script>, so use components.v1.html ────────
# NOTE: window.parent.document may be blocked by cross-origin policy on
# HuggingFace Spaces. The try/catch ensures silent failure, not a crash.
st.components.v1.html("""
<script>
(function(){
  try {
    const pc = window.parent.console;
    setTimeout(() => {
      pc.clear();
      pc.log(
        "%c %c > SupportOps AI Monitor %c\\n" +
        "%c—————————————————————————————————————————————————————————————————————\\n" +
        "%cDesigned & Developed by Archit Konde\\n" +
        "Portfolio: https://archit-konde.github.io/\\n" +
        "GitHub:    https://github.com/Archit-Konde/supportops-ai-monitor\\n\\n" +
        "%c[ PROJECT PHILOSOPHY ]%c\\n" +
        "At the intersection of support operations and predictive intelligence lies \\n" +
        "the future of customer success. This monitor is engineered to transform \\n" +
        "raw ticket data into coherent operational narratives, ensuring that \\n" +
        "efficiency never comes at the cost of the human experience.\\n\\n" +
        "%c[ DEV TIP ]%c\\n" +
        "Seniority in engineering isn't about complexity; it's about clarity. \\n" +
        "Always optimize for the next developer who will read your code.\\n" +
        "—————————————————————————————————————————————————————————————————————%c",
        "background:#C9A84C; padding:5px 0;",
        "background:#C9A84C; color:#1e1e1e; font-weight:bold; font-size:16px; padding:5px 10px; font-family:monospace;",
        "background:#C9A84C; padding:5px 0;",
        "color:#666; font-size:12px; font-family:monospace;",
        "color:#C9A84C; font-size:14px; font-weight:bold; font-family:monospace;",
        "color:#C9A84C; font-weight:bold; font-size:12px; font-family:monospace;",
        "color:#858585; font-size:12px; font-style:italic; font-family:monospace;",
        "color:#C9A84C; font-weight:bold; font-size:12px; font-family:monospace;",
        "color:#858585; font-size:12px; font-family:monospace;",
        "color:#666; font-size:12px; font-family:monospace;"
      );

    }, 1000);


    // ——— Easter Egg: Type 'archit' for a surprise ———
    // Strategy: Don't fight Streamlit's 'C' shortcut. Instead,
    // auto-dismiss the "Clear caches" dialog if it appears mid-sequence,
    // and show a clean popup when the full word is typed.
    try {
      var pdoc = window.parent.document;
      if (!pdoc._archit_egg_v2) {
        pdoc._archit_egg_v2 = true;
        var buf = '';
        var tmr = null;
        var midSequence = false;

        // MutationObserver: auto-dismiss cache dialog during 'archit' typing
        var obs = new MutationObserver(function() {
          if (!midSequence) return;
          var btns = pdoc.querySelectorAll('[data-testid="stBaseButton-secondary"]');
          btns.forEach(function(b) {
            if (b.textContent.trim() === 'Cancel') b.click();
          });
        });
        obs.observe(pdoc.body, { childList: true, subtree: true });

        pdoc.addEventListener('keydown', function(e) {
          var k = (e.key || '').toLowerCase();
          if (!k || k.length > 1) return;

          buf = (buf + k).slice(-6);
          midSequence = (buf.length > 0 && 'archit'.startsWith(buf));
          clearTimeout(tmr);
          tmr = setTimeout(function() { buf = ''; midSequence = false; }, 2000);

          if (buf === 'archit') {
            buf = '';
            midSequence = false;
            if (pdoc.getElementById('archit_popup')) return;

            var overlay = pdoc.createElement('div');
            overlay.id = 'archit_popup';
            overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);z-index:2147483647;display:flex;align-items:center;justify-content:center;backdrop-filter:blur(6px);cursor:pointer;opacity:0;transition:opacity 0.3s ease;';
            overlay.innerHTML =
              '<div style="background:#1e1e1e;border:1px solid #333;border-radius:12px;padding:48px 56px;max-width:440px;width:90%;text-align:center;box-shadow:0 24px 64px rgba(0,0,0,0.6);font-family:sans-serif;" onclick="event.stopPropagation();">'
              + '<div style="width:80px;height:80px;border-radius:50%;background:linear-gradient(135deg,#C9A84C,#8B7332);margin:0 auto 24px;display:flex;align-items:center;justify-content:center;font-size:32px;font-weight:bold;color:#1e1e1e;">AK</div>'
              + '<h2 style="margin:0 0 6px;color:#e0e0e0;font-size:1.5rem;font-weight:700;">Archit Konde</h2>'
              + '<p style="margin:0 0 20px;color:#C9A84C;font-size:0.85rem;letter-spacing:1px;text-transform:uppercase;">Developer &bull; Engineer &bull; Builder</p>'
              + '<p style="margin:0 0 28px;color:#999;font-size:0.9rem;line-height:1.7;">Designed and built this SupportOps AI Monitor to bridge the gap between raw support data and actionable intelligence. Passionate about clean code, thoughtful design, and tools that make teams more effective.</p>'
              + '<div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">'
              + '<a href="https://archit-konde.github.io/" target="_blank" style="display:inline-block;padding:10px 22px;background:#C9A84C;color:#1e1e1e;text-decoration:none;border-radius:6px;font-size:0.85rem;font-weight:600;">Portfolio</a>'
              + '<a href="https://github.com/Archit-Konde/supportops-ai-monitor" target="_blank" style="display:inline-block;padding:10px 22px;background:#333;color:#e0e0e0;text-decoration:none;border-radius:6px;font-size:0.85rem;font-weight:600;border:1px solid #555;">GitHub</a>'
              + '</div>'
              + '<p style="margin:28px 0 0;color:#555;font-size:0.7rem;">Press Escape or click outside to close</p>'
              + '</div>';

            pdoc.body.appendChild(overlay);
            requestAnimationFrame(function() { overlay.style.opacity = '1'; });

            var closeFn = function() {
              overlay.style.opacity = '0';
              setTimeout(function() { overlay.remove(); }, 300);
            };
            overlay.addEventListener('click', closeFn);
            pdoc.addEventListener('keydown', function esc(ev) {
              if (ev.key === 'Escape') { closeFn(); pdoc.removeEventListener('keydown', esc, true); }
            }, true);
            setTimeout(closeFn, 12000);
          }
        }, true);
      }
    } catch(e) {}




    var doc = window.parent.document;
    var btn = doc.getElementById('backToTop');
    if(!btn) return;
    function getC(){
      return doc.querySelector('[data-testid="stMainBlockContainer"]')
          || doc.querySelector('[data-testid="stAppViewContainer"]')

          || doc.querySelector('.main') || null;
    }
    function onScroll(){
      var c = getC();
      var top = c ? c.scrollTop : window.parent.scrollY;
      btn.classList.toggle('visible', top > 400);
    }
    doc.addEventListener('scroll', onScroll, true);
    var poll = setInterval(function(){
      var c = getC();
      if(c){ c.addEventListener('scroll', onScroll); clearInterval(poll); }
    }, 300);
    btn.addEventListener('click', function(e){
      e.preventDefault();
      var c = getC();
      if(c) c.scrollTo({top:0, behavior:'smooth'});
      else  window.parent.scrollTo({top:0, behavior:'smooth'});
    });
  } catch(e) { /* cross-origin — scroll-to-top won't work on this host */ }
})();
</script>
""", height=0)

# ── Fixed footer + scroll-to-top (rendered early so st.stop() can't hide them) ─
st.markdown(
    '<div class="custom-footer">'
    '&copy; 2026 All rights reserved. Designed &amp; Developed by '
    '<a href="https://archit-konde.github.io/" target="_blank">Archit Konde</a>'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown("""
<style>
.back-to-top {
  position: fixed; bottom: 3.5rem; right: 2rem; z-index: 998;
  width: 38px; height: 38px; background: #252526; border: 1px solid #3e3e42;
  color: #C9A84C; font-family: 'JetBrains Mono', monospace; font-size: 1rem;
  cursor: pointer; opacity: 0; visibility: hidden; transform: translateY(8px);
  transition: opacity 0.2s, visibility 0.2s, border-color 0.2s, background 0.2s,
              color 0.2s, transform 0.2s;
  display: flex; align-items: center; justify-content: center;
  text-decoration: none; border-radius: 4px;
}
.back-to-top.visible { opacity: 1; visibility: visible; transform: translateY(0); }
.back-to-top:hover { background: #C9A84C; border-color: #C9A84C; color: #1e1e1e; }
</style>
<a href="#" class="back-to-top" id="backToTop" title="Back to top">&#8593;</a>
""", unsafe_allow_html=True)


# ── Terminal-style section headers ────────────────────────────────────────────
def _term(cmd):
    """Render a terminal-style section header: $ cmd."""
    st.markdown(
        f'<p class="term-cmd" style="font-family:\'JetBrains Mono\',monospace;font-size:0.95rem;'
        f'color:#d4d4d4;margin:1rem 0 0.5rem;">'
        f'<span style="color:#C9A84C;font-weight:600;">$</span> {cmd}</p>',
        unsafe_allow_html=True,
    )

# ── HTML Report generator ─────────────────────────────────────────────────────
# Dark-themed, chart-embedded, print-ready HTML report.
# Open in browser → Ctrl+P → Save as PDF to get a proper dark-themed PDF.
_REPORT_CHART_LAYOUT = dict(
    paper_bgcolor="#1e1e1e",
    plot_bgcolor="#252526",
    font=dict(color="#d4d4d4", family="'Courier New', monospace", size=11),
    title=dict(font=dict(color="#d4d4d4", size=12)),
    xaxis=dict(gridcolor="#3e3e42", linecolor="#3e3e42", zerolinecolor="#3e3e42"),
    yaxis=dict(gridcolor="#3e3e42", linecolor="#3e3e42", zerolinecolor="#3e3e42"),
    legend=dict(bgcolor="#1e1e1e", bordercolor="#3e3e42", font=dict(color="#d4d4d4")),
    margin=dict(t=44, b=20, l=20, r=20),
    height=280,
)

_PDF_CHART_LAYOUT = dict(
    paper_bgcolor="white",
    plot_bgcolor="#fdfdfd",
    font=dict(color="#212529", family="Arial, sans-serif", size=10),
    title=dict(font=dict(color="#111111", size=12)),
    xaxis=dict(gridcolor="#eeeeee", linecolor="#cccccc", zerolinecolor="#cccccc"),
    yaxis=dict(gridcolor="#eeeeee", linecolor="#cccccc", zerolinecolor="#cccccc"),
    margin=dict(t=50, b=30, l=30, r=30),
    height=300,
)

def _build_pdf_report(all_tix: list, api_logs_raw: list, t_stats: dict, a_stats: dict):
    """Generate a beautiful, spacious light-themed PDF report."""
    import io
    import base64
    from xhtml2pdf import pisa
    import plotly.io as _pio
    import plotly.express as _px

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    tix_df  = pd.DataFrame(all_tix)    if all_tix    else pd.DataFrame()
    api_df  = pd.DataFrame(api_logs_raw) if api_logs_raw else pd.DataFrame()

    def _fig_to_base64(fig, layout=None):
        if layout:
            fig.update_layout(**layout)
        else:
            fig.update_layout(**_PDF_CHART_LAYOUT)
        img_bytes = fig.to_image(format="png", width=700, height=350, scale=2)
        return f"data:image/png;base64,{base64.b64encode(img_bytes).decode('utf-8')}"

    # -- Charts --
    img_cat = img_pri = img_sent = img_vol = img_lat = img_err = img_http = ""

    if not tix_df.empty:
        try:
            if "category" in tix_df.columns:
                cat_c = tix_df["category"].value_counts().reset_index()
                cat_c.columns = ["category", "count"]
                img_cat = _fig_to_base64(_px.pie(cat_c, names="category", values="count", title="Tickets by Category", color_discrete_sequence=list(PRIORITY_COLORS.values()), hole=0.4))
            
            if "priority" in tix_df.columns:
                pri_c = (tix_df["priority"].value_counts().reindex(["critical","high","medium","low"]).dropna().reset_index())
                pri_c.columns = ["priority", "count"]
                img_pri = _fig_to_base64(_px.bar(pri_c, x="priority", y="count", title="Tickets by Priority", color="priority", color_discrete_map=PRIORITY_COLORS))

            if "sentiment" in tix_df.columns:
                s_c = tix_df[tix_df["sentiment"].notna()]["sentiment"].value_counts().reset_index()
                s_c.columns = ["sentiment", "count"]
                if not s_c.empty:
                    img_sent = _fig_to_base64(_px.bar(s_c, x="sentiment", y="count", title="Customer Sentiment", color="sentiment", color_discrete_map=SENTIMENT_COLORS))

            if "created_at" in tix_df.columns:
                tix_df["_date"] = pd.to_datetime(tix_df["created_at"]).dt.date
                vol_df = tix_df.groupby("_date").size().reset_index(name="count")
                img_vol = _fig_to_base64(_px.line(vol_df, x="_date", y="count", title="Ticket Volume Over Time", markers=True, color_discrete_sequence=[COLORS["indigo"]]))
        except Exception as e:
            st.error(f"Error generating support charts: {e}")

    if not api_df.empty:
        try:
            suc = api_df[api_df["success"] == 1].copy()
            if not suc.empty:
                suc["timestamp"] = pd.to_datetime(suc["timestamp"])
                fig_lat = _px.scatter(suc.sort_values("timestamp"), x="timestamp", y="latency_ms", title="API Latency Over Time", color_discrete_sequence=[COLORS["indigo"]], opacity=0.6)
                img_lat = _fig_to_base64(fig_lat)

            err_df = api_df[api_df["success"] == 0]
            if not err_df.empty:
                e_c = err_df["error_type"].value_counts().reset_index()
                e_c.columns = ["error_type", "count"]
                img_err = _fig_to_base64(_px.bar(e_c, x="error_type", y="count", title="API Errors by Type", color="error_type", color_discrete_map=ERROR_COLORS))

            hc = api_df["status_code"].value_counts().reset_index()
            hc.columns = ["status_code", "count"]
            hc["status_code"] = hc["status_code"].astype(str)
            img_http = _fig_to_base64(_px.bar(hc, x="status_code", y="count", title="HTTP Status Code Distribution", color="status_code", color_discrete_map=HTTP_COLORS))
        except Exception as e:
            st.error(f"Error generating API charts: {e}")

    # -- KPI Table (xhtml2pdf fallback for flex) --
    kpi_items = [
        (str(t_stats.get("total", 0)), "Total Tickets"),
        (str(t_stats.get("open", 0)), "Open"),
        (str(t_stats.get("resolved", 0)), "Resolved"),
        (f"{a_stats.get('success_rate', 0)}%", "API Success Rate"),
        (f"{a_stats.get('avg_latency_ms', 0)} ms", "Avg Latency"),
    ]
    
    kpis_html = "<table style='width: 100%;'><tr>"
    for v, lbl in kpi_items:
        kpis_html += f"""
        <td style='width: 20%; padding: 5px;'>
            <div style='background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 15px; border-radius: 5px; text-align: center;'>
                <div style='font-size: 18px; font-weight: bold; color: #C9A84C;'>{v}</div>
                <div style='font-size: 10px; color: #666;'>{lbl}</div>
            </div>
        </td>"""
    kpis_html += "</tr></table>"

    # -- Ticket Table --
    ticket_rows = ""
    for i, t in enumerate(all_tix[:60]):
        bg = "#ffffff" if i % 2 == 0 else "#f9f9f9"
        priority = str(t.get('priority','')).upper()
        p_color = PRIORITY_COLORS.get(t.get('priority',''), '#333')
        ticket_rows += f"""
        <tr style='background-color: {bg}'>
            <td>{str(t.get('ticket_id',''))}</td>
            <td>{str(t.get('customer',''))}</td>
            <td>{str(t.get('subject',''))[:60]}</td>
            <td style='color:{p_color}'><b>{priority}</b></td>
            <td>{str(t.get('status',''))}</td>
            <td>{str(t.get('category','') or '—')}</td>
            <td>{str(t.get('sentiment','') or '—')}</td>
        </tr>"""

    html = f"""
    <html>
    <head>
        <style>
            @page {{ size: A4 landscape; margin: 1cm; }}
            body {{ font-family: Helvetica, Arial, sans-serif; color: #333; line-height: 1.4; background-color: white; }}
            .header {{ border-bottom: 2px solid #C9A84C; padding-bottom: 10px; margin-bottom: 20px; }}
            .title {{ font-size: 22px; font-weight: bold; color: #111; }}
            .title span {{ color: #C9A84C; }}
            .meta {{ font-size: 9px; color: #666; margin-top: 5px; }}
            .section-title {{ font-size: 13px; font-weight: bold; color: #C9A84C; margin-top: 20px; margin-bottom: 10px; text-transform: uppercase; border-left: 4px solid #C9A84C; padding-left: 10px; }}
            .chart-table {{ width: 100%; }}
            .chart-cell {{ width: 50%; padding: 10px; text-align: center; }}
            .chart-img {{ width: 100%; border: 1px solid #f0f0f0; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 9px; }}
            th {{ background-color: #f1f3f5; color: #111; text-align: left; padding: 8px; border: 1px solid #dee2e6; }}
            td {{ padding: 6px 8px; border: 1px solid #dee2e6; vertical-align: top; }}
            .footer {{ position: fixed; bottom: 0; width: 100%; text-align: center; font-size: 8px; color: #999; border-top: 1px solid #eee; padding-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="title"><span>&gt;</span> SupportOps AI Monitor Report</div>
            <div class="meta">Generated: {now} | Total Tickets: {t_stats.get('total', 0)} | System Status: Optimal</div>
        </div>


        <div class="section-title">Operational Overview</div>
        {kpis_html}

        <div class="section-title">Support Analytics</div>
        <table class="chart-table">
            <tr>
                <td class="chart-cell">{f'<img class="chart-img" src="{img_cat}">' if img_cat else ''}</td>
                <td class="chart-cell">{f'<img class="chart-img" src="{img_pri}">' if img_pri else ''}</td>
            </tr>
            <tr>
                <td class="chart-cell">{f'<img class="chart-img" src="{img_sent}">' if img_sent else ''}</td>
                <td class="chart-cell">{f'<img class="chart-img" src="{img_vol}">' if img_vol else ''}</td>
            </tr>
        </table>

        <pdf:nextpage />

        <div class="section-title">API Health & Performance</div>
        <table class="chart-table">
            <tr>
                <td class="chart-cell">{f'<img class="chart-img" src="{img_lat}">' if img_lat else ''}</td>
                <td class="chart-cell">{f'<img class="chart-img" src="{img_err}">' if img_err else ''}</td>
            </tr>
        </table>
        <div style="text-align: center; padding: 10px;">
            {f'<img style="width: 80%; border: 1px solid #f0f0f0;" src="{img_http}">' if img_http else ''}
        </div>

        <pdf:nextpage />

        <div class="section-title">Ticket Registry - Recent Activity</div>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Customer</th>
                    <th>Subject</th>
                    <th>Priority</th>
                    <th>Status</th>
                    <th>Category</th>
                    <th>Sentiment</th>
                </tr>
            </thead>
            <tbody>
                {ticket_rows}
            </tbody>
        </table>

        <div class="footer">
            &copy; 2026 All rights reserved. Designed & Developed by <a href="https://archit-konde.github.io/">Archit Konde</a>
        </div>
    </body>
    </html>
    """


    
    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf_buffer)
    
    if pisa_status.err:
        return None
        
    return pdf_buffer.getvalue()



# ── Init DB ───────────────────────────────────────────────────────────────────
db.init_db()

# ── Cached data loaders ───────────────────────────────────────────────────────
# NOTE: parameter MUST NOT start with underscore — Streamlit excludes _-prefixed
# params from the cache key, so _version would never bust the cache.
@st.cache_data(ttl=60)
def load_all_tickets(version):
    """Load all tickets from DB. version param busts cache on new data."""
    return db.get_all_tickets()

@st.cache_data(ttl=60)
def load_api_logs(version, limit=500):
    return db.get_api_logs(limit=limit)

@st.cache_data(ttl=30)
def load_ticket_stats(version):
    return db.get_ticket_stats()

@st.cache_data(ttl=30)
def load_api_health_stats(version):
    return db.get_api_health_stats()

if "data_version" not in st.session_state:
    st.session_state.data_version = 0

# ── Load data (Move up to use in sidebar) ─────────────────────────────────────
all_tickets = load_all_tickets(st.session_state.data_version)
api_logs = load_api_logs(st.session_state.data_version, limit=500)

_report_stats  = load_ticket_stats(st.session_state.data_version) if all_tickets else {}
_report_api    = load_api_health_stats(st.session_state.data_version) if api_logs else {}

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("**> SupportOps AI Monitor**")
    st.caption("// AI Platform · Support Operations")
    st.divider()


    st.subheader("Data Controls")

    n_tickets = st.slider("Tickets to generate", min_value=10, max_value=200, value=50, step=10)
    days_back = st.slider("Days back", min_value=7, max_value=90, value=30)

    if st.button("Generate & Triage Tickets", use_container_width=True, type="primary"):
        try:
            with st.spinner("Generating tickets..."):
                tickets = tg.generate_batch(n=n_tickets, days_back=days_back)
                for t in tickets:
                    db.insert_ticket(t)

            progress_bar = st.progress(0)
            status_text = st.empty()

            def update_progress(i, total):
                progress_bar.progress(i / total)
                status_text.text(f"Triaging {i} of {total}...")

            with st.spinner("Running AI triage..."):
                stats = ai_triage.triage_batch(tickets, progress_callback=update_progress)


            progress_bar.empty()
            status_text.empty()
            st.success(f"{stats['success']} triaged · {stats['failed']} failed")
            st.session_state.data_version += 1
            st.rerun()
        except Exception as e:
            st.error(f"Error during ticket generation/triage: {e}")

    st.divider()

    # ── CSV/Excel Upload ──────────────────────────────────────────────────────
    st.subheader("Upload Tickets")

    uploaded_file = st.file_uploader(
        "Upload CSV or Excel file",
        type=["csv", "xlsx"],
        help="Required columns: subject, body. Optional: customer, priority, status.",
    )

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".xlsx"):
                upload_df = pd.read_excel(uploaded_file)
            else:
                upload_df = pd.read_csv(uploaded_file)

            required = {"subject", "body"}
            missing = required - set(upload_df.columns)
            if missing:
                st.error(f"Missing required columns: {', '.join(missing)}")
            else:
                st.write(f"Found **{len(upload_df)}** tickets in upload.")
                st.dataframe(upload_df.head(5), use_container_width=True, height=150)

                if st.button("Import & Triage Uploaded Tickets", use_container_width=True):
                    uploaded_tickets = []
                    for _, row in upload_df.iterrows():
                        ticket = {
                            "ticket_id": f"TKT-{uuid.uuid4().hex[:8].upper()}",
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "customer": str(row.get("customer", "Uploaded")).strip() or "Uploaded",
                            "subject": str(row["subject"]).strip(),
                            "body": str(row["body"]).strip(),
                            "priority": str(row.get("priority", "medium")).strip().lower(),
                            "status": str(row.get("status", "open")).strip().lower(),
                        }
                        if ticket["priority"] not in {"low", "medium", "high", "critical"}:
                            ticket["priority"] = "medium"
                        if ticket["status"] not in {"open", "in_progress", "resolved"}:
                            ticket["status"] = "open"
                        uploaded_tickets.append(ticket)

                    with st.spinner("Inserting tickets..."):
                        for t in uploaded_tickets:
                            db.insert_ticket(t)

                    upload_progress = st.progress(0)
                    upload_status = st.empty()

                    def upload_update(i, total):
                        upload_progress.progress(i / total)
                        upload_status.text(f"Triaging {i} of {total}...")

                    with st.spinner("Running AI triage on uploaded tickets..."):
                        upload_stats = ai_triage.triage_batch(
                            uploaded_tickets, progress_callback=upload_update
                        )


                    upload_progress.empty()
                    upload_status.empty()
                    st.success(
                        f"Imported {len(uploaded_tickets)} tickets. "
                        f"{upload_stats['success']} triaged, {upload_stats['failed']} failed."
                    )
                    st.session_state.data_version += 1
                    st.rerun()
        except Exception as e:
            st.error(f"Error processing file: {e}")

    st.divider()

    st.subheader("Filters")
    status_filter = st.multiselect(
        "Ticket Status",
        options=["open", "in_progress", "resolved"],
        default=["open", "in_progress", "resolved"],
    )
    priority_filter = st.multiselect(
        "Priority",
        options=["critical", "high", "medium", "low"],
        default=["critical", "high", "medium", "low"],
    )

    st.divider()

    # ── Export + Reset ─────────────────────────────────────────────────────────
    st.subheader("Export")
    
    if all_tickets:
        with st.spinner("Preparing..."):
            _sidebar_pdf = _build_pdf_report(all_tickets, api_logs, _report_stats, _report_api)
        
        if _sidebar_pdf:
            st.download_button(
                label="⬇ Download PDF Report",
                data=_sidebar_pdf,
                file_name=f"supportops-report-{datetime.now().strftime('%Y%m%d-%H%M')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="sidebar_download_pdf"
            )

    else:
        st.caption("Generate tickets to export")



    st.divider()

    if st.button("Reset All Data", use_container_width=True):
        st.session_state.confirm_reset = True

    if st.session_state.get("confirm_reset"):
        st.warning("This will permanently delete all tickets and API logs.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Confirm", type="primary", use_container_width=True):
                db.clear_all_data()
                st.cache_data.clear()
                st.session_state.data_version = 0
                st.session_state.pop("confirm_reset", None)
                st.rerun()
        with c2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.pop("confirm_reset", None)
                st.rerun()

# ── Load data ─────────────────────────────────────────────────────────────────
# Apply filters

filtered_tickets = [
    t for t in all_tickets
    if t["status"] in status_filter and t["priority"] in priority_filter
]

ticket_df = pd.DataFrame(filtered_tickets) if filtered_tickets else pd.DataFrame()
api_df = pd.DataFrame(api_logs) if api_logs else pd.DataFrame()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    '<h1 style="font-family:\'JetBrains Mono\',monospace;color:#d4d4d4;'
    'font-size:1.6rem;font-weight:700;letter-spacing:-0.03em;">'
    '<span style="color:#C9A84C;">&gt;</span> SupportOps AI Monitor</h1>',
    unsafe_allow_html=True,
)

st.caption(
    f"Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC  ·  "
    f"Showing {len(filtered_tickets)} of {len(all_tickets)} tickets"
)

# ── Section 1: KPI Metrics ────────────────────────────────────────────────────
_term("cat overview")

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

if all_tickets:
    ticket_stats = load_ticket_stats(st.session_state.data_version)
    api_stats = load_api_health_stats(st.session_state.data_version) if api_logs else {}

    with kpi1:
        st.metric("Total Tickets", ticket_stats["total"])
    with kpi2:
        open_count = ticket_stats["open"]
        st.metric("Open", open_count, delta=f"{open_count} need action", delta_color="inverse")
    with kpi3:
        st.metric("Resolved", ticket_stats["resolved"])
    with kpi4:
        rate = api_stats.get("success_rate", 0)
        delta_color = "normal" if rate >= 95 else "inverse"
        st.metric("API Success Rate", f"{rate}%", delta_color=delta_color)
    with kpi5:
        latency = api_stats.get("avg_latency_ms", 0)
        st.metric("Avg API Latency", f"{latency} ms")
else:
    st.info("Use the sidebar to generate and triage tickets to populate the dashboard.")
    st.stop()

st.divider()

# ── Section 2: Ticket Analytics ───────────────────────────────────────────────
_term("./analytics --tickets")

col1, col2, col3 = st.columns(3)

with col1:
    if not ticket_df.empty and "category" in ticket_df.columns:
        cat_counts = ticket_df["category"].value_counts().reset_index()
        cat_counts.columns = ["category", "count"]
        fig = px.pie(
            cat_counts,
            names="category",
            values="count",
            title="Tickets by Category",
            color_discrete_sequence=list(PRIORITY_COLORS.values()),
            hole=0.4,
        )
        fig.update_layout(height=CHART_H_PRIMARY, margin=CHART_MARGIN)
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

with col2:
    if not ticket_df.empty and "priority" in ticket_df.columns:
        priority_order = ["critical", "high", "medium", "low"]
        pri_counts = (
            ticket_df["priority"]
            .value_counts()
            .reindex(priority_order)
            .dropna()
            .reset_index()
        )
        pri_counts.columns = ["priority", "count"]
        fig = px.bar(
            pri_counts,
            x="priority",
            y="count",
            title="Tickets by Priority",
            color="priority",
            color_discrete_map=PRIORITY_COLORS,
        )
        fig.update_layout(
            height=CHART_H_PRIMARY,
            margin=CHART_MARGIN,
            showlegend=False,
            xaxis_title="",
            yaxis_title="Count",
        )
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

with col3:
    if not ticket_df.empty and "sentiment" in ticket_df.columns:
        sent_df = ticket_df[ticket_df["sentiment"].notna()]
        if not sent_df.empty:
            sent_counts = sent_df["sentiment"].value_counts().reset_index()
            sent_counts.columns = ["sentiment", "count"]
            fig = px.bar(
                sent_counts,
                x="sentiment",
                y="count",
                title="Customer Sentiment",
                color="sentiment",
                color_discrete_map=SENTIMENT_COLORS,
            )
            fig.update_layout(
                height=CHART_H_PRIMARY,
                margin=CHART_MARGIN,
                showlegend=False,
                xaxis_title="",
                yaxis_title="Count",
            )
            st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

if not ticket_df.empty and "created_at" in ticket_df.columns:
    ticket_df["created_date"] = pd.to_datetime(ticket_df["created_at"]).dt.date
    volume_df = ticket_df.groupby("created_date").size().reset_index(name="count")
    fig = px.line(
        volume_df,
        x="created_date",
        y="count",
        title="Ticket Volume Over Time",
        markers=True,
        color_discrete_sequence=[COLORS["indigo"]],
    )
    fig.update_layout(
        height=CHART_H_SECONDARY,
        margin=CHART_MARGIN,
        xaxis_title="",
        yaxis_title="Tickets",
    )
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

st.divider()

# ── Section 3: API Health ─────────────────────────────────────────────────────
_term("./health --api")

if not api_df.empty:
    col1, col2 = st.columns(2)

    with col1:
        success_df = api_df[api_df["success"] == 1].copy()
        if not success_df.empty:
            success_df["timestamp"] = pd.to_datetime(success_df["timestamp"])
            success_df = success_df.sort_values("timestamp")
            fig = px.scatter(
                success_df,
                x="timestamp",
                y="latency_ms",
                title="API Latency Over Time",
                color_discrete_sequence=[COLORS["indigo"]],
                opacity=0.6,
            )
            fig.add_hline(
                y=success_df["latency_ms"].mean(),
                line_dash="dash",
                line_color=COLORS["warning"],
                annotation_text=f"Mean: {success_df['latency_ms'].mean():.0f}ms",
            )
            fig.update_layout(height=CHART_H_PRIMARY, margin=CHART_MARGIN)
            st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

    with col2:
        error_df = api_df[api_df["success"] == 0]
        if not error_df.empty:
            err_counts = error_df["error_type"].value_counts().reset_index()
            err_counts.columns = ["error_type", "count"]
            fig = px.bar(
                err_counts,
                x="error_type",
                y="count",
                title="API Errors by Type",
                color="error_type",
                color_discrete_map=ERROR_COLORS,
            )
            fig.update_layout(
                height=CHART_H_PRIMARY,
                margin=CHART_MARGIN,
                showlegend=False,
                xaxis_title="",
                yaxis_title="Error Count",
            )
            st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        else:
            st.success("No API errors recorded.")

    code_counts = api_df["status_code"].value_counts().reset_index()
    code_counts.columns = ["status_code", "count"]
    code_counts["status_code"] = code_counts["status_code"].astype(str)
    fig = px.bar(
        code_counts,
        x="status_code",
        y="count",
        title="HTTP Status Code Distribution",
        color="status_code",
        color_discrete_map=HTTP_COLORS,
    )
    fig.update_layout(
        height=CHART_H_SECONDARY,
        margin=CHART_MARGIN,
        showlegend=False,
        xaxis_title="HTTP Status Code",
        yaxis_title="Count",
    )
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

st.divider()

# ── Section 4: Ticket Queue ───────────────────────────────────────────────────
_term("ls tickets/")

if not ticket_df.empty:
    display_cols = ["ticket_id", "created_at", "customer", "subject", "priority", "status", "category", "sentiment", "ai_summary"]
    display_cols = [c for c in display_cols if c in ticket_df.columns]
    display_df = ticket_df[display_cols].copy()
    if "ai_summary" in display_df.columns:
        display_df = display_df.rename(columns={"ai_summary": "Ops Insight"})


    def priority_badge(val):
        base = "border-radius: 3px; padding: 1px 6px; font-size: 0.75rem; font-weight: 600; font-family: 'JetBrains Mono', monospace;"
        badge = {
            "critical": f"color: {COLORS['danger']}; border: 1px solid {COLORS['danger']}; {base}",
            "high":     f"color: {COLORS['warning']}; border: 1px solid {COLORS['warning']}; {base}",
            "medium":   f"color: {COLORS['yellow']}; border: 1px solid {COLORS['yellow']}; {base}",
            "low":      f"color: {COLORS['success']}; border: 1px solid {COLORS['success']}; {base}",
        }
        return badge.get(val, "")

    styled = display_df.style.map(priority_badge, subset=["priority"])
    st.dataframe(styled, use_container_width=True, height=400)

    if st.toggle("› View ticket details", key="toggle_ticket_details"):
        with st.container(border=True):
            ticket_ids = [t["ticket_id"] for t in filtered_tickets]
            selected_id = st.selectbox("Select ticket ID", options=ticket_ids)
            if selected_id:
                ticket = next((t for t in filtered_tickets if t["ticket_id"] == selected_id), None)
                if ticket:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Priority", ticket["priority"].upper())
                    with col2:
                        st.metric("Status", ticket["status"])
                    with col3:
                        st.metric("Category", ticket.get("category", "—"))

                    st.write(f"**Customer:** {ticket['customer']}")
                    st.write(f"**Subject:** {ticket['subject']}")
                    st.write(f"**Created:** {ticket['created_at']}")
                    if ticket.get("ai_summary"):
                        st.info(f"→ AI: {ticket['ai_summary']}")
                    st.text_area("Ticket Body", value=ticket["body"], height=200, disabled=True)

                    if ticket["status"] != "resolved":
                        if st.button("Mark as Resolved", type="primary"):
                            db.resolve_ticket(selected_id)
                            st.success("Ticket resolved.")
                            st.session_state.data_version += 1
                            st.rerun()

st.divider()

# ── Section 5: Raw API Logs ───────────────────────────────────────────────────
_term("tail -f api.log")
if st.toggle("› Show last 100 API calls", key="toggle_api_logs"):
    with st.container(border=True):
        if not api_df.empty:
            st.dataframe(api_df.head(100), use_container_width=True, height=300)
        else:
            st.write("No API logs yet.")

st.divider()

# ── Section 6: Export ─────────────────────────────────────────────────────────
_term("export --format pdf")
if all_tickets:
    _report_stats  = load_ticket_stats(st.session_state.data_version)
    _report_api    = load_api_health_stats(st.session_state.data_version) if api_logs else {}
    
    with st.spinner("Finalizing report..."):
        _report_pdf = _build_pdf_report(all_tickets, api_logs, _report_stats, _report_api)

    if _report_pdf:
        st.download_button(
            label="⬇ Download PDF Report",
            data=_report_pdf,
            file_name=f"supportops-report-{datetime.now().strftime('%Y%m%d-%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    else:
        st.error("Failed to generate report. Please verify system dependencies.")
else:
    st.caption("Population of system data required for report generation.")


