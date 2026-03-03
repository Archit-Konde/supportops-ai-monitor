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
}

PRIORITY_COLORS  = {"critical": COLORS["danger"],  "high": COLORS["warning"], "medium": "#facc15", "low": COLORS["success"]}
SENTIMENT_COLORS = {"positive": COLORS["success"], "neutral": COLORS["neutral"], "negative": COLORS["danger"]}
ERROR_COLORS     = {"rate_limit": COLORS["warning"], "server_error": COLORS["danger"], "timeout": "#facc15", "unknown": COLORS["neutral"]}
HTTP_COLORS      = {"200": COLORS["success"], "429": COLORS["warning"], "500": COLORS["danger"], "408": "#facc15", "0": COLORS["neutral"]}

CHART_H_PRIMARY   = 300
CHART_H_SECONDARY = 220
CHART_MARGIN      = dict(t=48, b=0, l=0, r=0)
PLOTLY_CONFIG     = {"displaylogo": False,
                     "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d"]}

# ── Global CSS — VS Code Dark+ terminal aesthetic ─────────────────────────────
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
/* Expander arrow — CSS hides what it can, JS below removes the rest */
[data-testid="stExpanderToggleIcon"],
[data-testid="stSidebarCollapseButton"] span { display: none !important; }
details summary::before {
  content: "›";
  display: inline-block;
  color: #C9A84C;
  font-size: 1.1rem;
  font-weight: 700;
  margin-right: 0.4rem;
  transition: transform 0.2s ease;
  font-family: 'JetBrains Mono', monospace;
}
details[open] summary::before { transform: rotate(90deg); }
/* Hide Streamlit top bar (Rerun / Settings / Made with Streamlit) */
header[data-testid="stHeader"] { display: none !important; }
#MainMenu { display: none !important; }
/* Fix upload widget text clipping in narrow sidebar */
[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] span
  { word-wrap: break-word !important; overflow-wrap: break-word !important;
    font-size: 0.78rem !important; }
/* Print styles for PDF export */
@media print {
  section[data-testid="stSidebar"], header[data-testid="stHeader"],
  .custom-footer, .back-to-top, .stButton { display: none !important; }
  .stApp { background: white !important; }
  [data-testid="stMetricValue"] { color: #1e1e1e !important; }
  h1,h2,h3,p,span,div { color: #1e1e1e !important; }
  [data-testid="metric-container"] { border: 1px solid #ccc !important; background: white !important; }
}
</style>
""", unsafe_allow_html=True)

# ── Fix expander "arrow_right" ligature text ─────────────────────────────────
# Streamlit strips <script> from st.markdown, so we must use components.v1.html
# which creates a real iframe. From there, window.parent.document reaches the
# Streamlit DOM. MutationObserver re-runs on every change to catch late renders.
# ── All JS fixes — must use components.v1.html (Streamlit strips <script> from st.markdown) ─
st.components.v1.html("""
<script>
(function(){
  var doc = window.parent.document;

  /* 1. Strip "arrow_right" / "arrow_drop_down" ligature text from expanders */
  function fixExpanders(){
    doc.querySelectorAll('details summary').forEach(function(s){
      var tw = doc.createTreeWalker(s, NodeFilter.SHOW_TEXT, null, false);
      var n;
      while(n = tw.nextNode()){
        if(n.textContent.indexOf('arrow_right') !== -1)
          n.textContent = n.textContent.replace(/arrow_right/g, '');
        if(n.textContent.indexOf('arrow_drop_down') !== -1)
          n.textContent = n.textContent.replace(/arrow_drop_down/g, '');
      }
    });
  }
  fixExpanders();
  new MutationObserver(fixExpanders).observe(doc.body, {childList:true, subtree:true});

  /* 2. Back-to-top button — scroll listener on Streamlit's inner container */
  var btn = doc.getElementById('backToTop');
  if(btn){
    function getContainer(){
      return doc.querySelector('[data-testid="stMainBlockContainer"]')
          || doc.querySelector('[data-testid="stAppViewContainer"]')
          || doc.querySelector('.main')
          || null;
    }
    function onScroll(){
      var c = getContainer();
      var top = c ? c.scrollTop : window.parent.scrollY;
      btn.classList.toggle('visible', top > 400);
    }
    /* Capture-phase listener catches scroll events from any target */
    doc.addEventListener('scroll', onScroll, true);
    /* Also poll for container and attach directly */
    var poll = setInterval(function(){
      var c = getContainer();
      if(c){ c.addEventListener('scroll', onScroll); clearInterval(poll); }
    }, 300);
    btn.addEventListener('click', function(e){
      e.preventDefault();
      var c = getContainer();
      if(c) c.scrollTo({top:0, behavior:'smooth'});
      else  window.parent.scrollTo({top:0, behavior:'smooth'});
    });
  }
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
        f'<p style="font-family:\'JetBrains Mono\',monospace;font-size:0.95rem;'
        f'color:#d4d4d4;margin:1rem 0 0.5rem;">'
        f'<span style="color:#C9A84C;font-weight:600;">$</span> {cmd}</p>',
        unsafe_allow_html=True,
    )

# ── HTML Report generator ─────────────────────────────────────────────────────
def _build_html_report(all_tix: list, t_stats: dict, a_stats: dict) -> str:
    """Return a self-contained HTML string. Open in browser → Ctrl+P → Save as PDF."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # KPI block
    kpis_html = "".join(
        f'<div class="kpi"><div class="kv">{v}</div><div class="kl">{lbl}</div></div>'
        for v, lbl in [
            (t_stats.get("total", 0),              "Total Tickets"),
            (t_stats.get("open", 0),               "Open"),
            (t_stats.get("resolved", 0),           "Resolved"),
            (f"{a_stats.get('success_rate', 0)}%", "API Success Rate"),
            (f"{a_stats.get('avg_latency_ms', 0)} ms", "Avg Latency"),
        ]
    )

    # Category / priority breakdown rows
    def _rows(d):
        return "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in d.items())

    # Recent tickets table (top 50)
    ticket_rows = "".join(
        f"<tr>"
        f"<td>{t.get('ticket_id','')}</td>"
        f"<td>{t.get('customer','')}</td>"
        f"<td>{str(t.get('subject',''))[:70]}</td>"
        f"<td>{t.get('priority','')}</td>"
        f"<td>{t.get('status','')}</td>"
        f"<td>{t.get('category') or '—'}</td>"
        f"<td>{t.get('sentiment') or '—'}</td>"
        f"<td>{str(t.get('ai_summary') or '—')[:80]}</td>"
        f"</tr>"
        for t in all_tix[:50]
    )

    error_rows = _rows(a_stats.get("errors_by_type", {})) or "<tr><td colspan='2'>None</td></tr>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>SupportOps AI Monitor — {now}</title>
<style>
  body{{font-family:'Courier New',monospace;background:#fff;color:#1e1e1e;
       max-width:1200px;margin:0 auto;padding:2rem;font-size:13px;}}
  h1{{border-bottom:3px solid #C9A84C;padding-bottom:.4rem;font-size:1.4rem;}}
  h2{{font-size:.9rem;color:#555;margin:1.8rem 0 .4rem;text-transform:uppercase;letter-spacing:.05em;}}
  .meta{{color:#888;font-size:.75rem;margin-bottom:1.5rem;}}
  .kpis{{display:flex;flex-wrap:wrap;gap:.75rem;margin:1rem 0 1.5rem;}}
  .kpi{{border:1px solid #ddd;padding:.8rem 1.2rem;min-width:110px;}}
  .kv{{font-size:1.6rem;font-weight:700;color:#C9A84C;}}
  .kl{{font-size:.7rem;color:#888;margin-top:.1rem;}}
  table{{border-collapse:collapse;width:100%;margin-top:.5rem;}}
  th{{background:#f4f4f4;padding:.35rem .55rem;text-align:left;border:1px solid #ddd;font-size:.75rem;}}
  td{{padding:.3rem .55rem;border:1px solid #eee;font-size:.75rem;vertical-align:top;}}
  tr:nth-child(even){{background:#fafafa;}}
  @media print{{body{{padding:.5rem;}}}}
</style>
</head>
<body>
<h1>&gt; SupportOps AI Monitor</h1>
<p class="meta">Generated: {now} &nbsp;·&nbsp; Tickets shown: {min(len(all_tix),50)} of {len(all_tix)}</p>

<h2>Key Metrics</h2>
<div class="kpis">{kpis_html}</div>

<h2>Tickets by Category</h2>
<table><tr><th>Category</th><th>Count</th></tr>{_rows(t_stats.get('by_category', {}))}</table>

<h2>Tickets by Priority</h2>
<table><tr><th>Priority</th><th>Count</th></tr>{_rows(t_stats.get('by_priority', {}))}</table>

<h2>Tickets by Sentiment</h2>
<table><tr><th>Sentiment</th><th>Count</th></tr>{_rows(t_stats.get('by_sentiment', {}))}</table>

<h2>API Health</h2>
<table>
  <tr><th>Metric</th><th>Value</th></tr>
  <tr><td>Total API Calls</td><td>{a_stats.get('total_calls', 0)}</td></tr>
  <tr><td>Success Rate</td><td>{a_stats.get('success_rate', 0)}%</td></tr>
  <tr><td>Avg Latency</td><td>{a_stats.get('avg_latency_ms', 0)} ms</td></tr>
</table>

<h2>API Errors by Type</h2>
<table><tr><th>Error Type</th><th>Count</th></tr>{error_rows}</table>

<h2>Recent Tickets (Top 50)</h2>
<table>
  <tr><th>ID</th><th>Customer</th><th>Subject</th><th>Priority</th>
      <th>Status</th><th>Category</th><th>Sentiment</th><th>AI Summary</th></tr>
  {ticket_rows}
</table>
</body>
</html>"""


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
    st.caption("// HTML report download available below the dashboard")

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
all_tickets = load_all_tickets(st.session_state.data_version)
api_logs = load_api_logs(st.session_state.data_version, limit=500)

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

    def priority_badge(val):
        base = "border-radius: 3px; padding: 1px 6px; font-size: 0.75rem; font-weight: 600; font-family: 'JetBrains Mono', monospace;"
        badge = {
            "critical": f"color: {COLORS['danger']}; border: 1px solid {COLORS['danger']}; {base}",
            "high":     f"color: {COLORS['warning']}; border: 1px solid {COLORS['warning']}; {base}",
            "medium":   f"color: #facc15; border: 1px solid #facc15; {base}",
            "low":      f"color: {COLORS['success']}; border: 1px solid {COLORS['success']}; {base}",
        }
        return badge.get(val, "")

    styled = display_df.style.map(priority_badge, subset=["priority"])
    st.dataframe(styled, use_container_width=True, height=400)

    with st.expander("View ticket details"):
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
with st.expander("$ tail -f api.log (last 100 calls)"):
    if not api_df.empty:
        st.dataframe(api_df.head(100), use_container_width=True, height=300)
    else:
        st.write("No API logs yet.")

st.divider()

# ── Section 6: Export ─────────────────────────────────────────────────────────
_term("export --format html")
if all_tickets:
    _report_stats  = load_ticket_stats(st.session_state.data_version)
    _report_api    = load_api_health_stats(st.session_state.data_version) if api_logs else {}
    _report_html   = _build_html_report(all_tickets, _report_stats, _report_api)
    st.download_button(
        label="⬇ Download Report (HTML)",
        data=_report_html,
        file_name=f"supportops-report-{datetime.now().strftime('%Y%m%d-%H%M')}.html",
        mime="text/html",
        use_container_width=True,
        help="Open the downloaded file in your browser, then Ctrl+P → Save as PDF.",
    )
    st.caption("// open in browser → Ctrl+P → Save as PDF for a clean printout")
else:
    st.caption("// generate tickets first to enable report download")
