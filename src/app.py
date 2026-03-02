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
CHART_MARGIN      = dict(t=32, b=0, l=0, r=0)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"]                          { font-family: 'Inter', system-ui, sans-serif !important; }
code, pre, .stCode, [data-testid="stCodeBlock"]     { font-family: 'JetBrains Mono', monospace !important; }
section[data-testid="stSidebar"]                    { background-color: #252526 !important; border-right: 1px solid #3e3e42; }
[data-testid="metric-container"]                    { background: #252526; border: 1px solid #3e3e42; border-radius: 6px; padding: 1rem; }
.stDataFrame                                        { border: 1px solid #3e3e42; border-radius: 6px; }
h1, h2, h3                                         { letter-spacing: -0.02em; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ── Init DB ───────────────────────────────────────────────────────────────────
db.init_db()

# ── Cached data loaders ───────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_all_tickets(_version):
    """Load all tickets from DB. _version param busts cache on new data."""
    return db.get_all_tickets()

@st.cache_data(ttl=60)
def load_api_logs(_version, limit=500):
    return db.get_api_logs(limit=limit)

@st.cache_data(ttl=30)
def load_ticket_stats(_version):
    return db.get_ticket_stats()

@st.cache_data(ttl=30)
def load_api_health_stats(_version):
    return db.get_api_health_stats()

if "data_version" not in st.session_state:
    st.session_state.data_version = 0

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("SupportOps AI Monitor")
    st.caption("AI Platform · Support Operations")
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
    st.caption("© 2026 [Archit Konde](https://archit-konde.github.io) · [GitHub](https://github.com/Archit-Konde)")

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
st.title("SupportOps AI Monitor")
st.caption(
    f"Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC  ·  "
    f"Showing {len(filtered_tickets)} of {len(all_tickets)} tickets"
)

# ── Section 1: KPI Metrics ────────────────────────────────────────────────────
st.subheader("Overview")

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
st.subheader("Ticket Analytics")

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
        st.plotly_chart(fig, use_container_width=True)

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
        st.plotly_chart(fig, use_container_width=True)

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
            st.plotly_chart(fig, use_container_width=True)

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
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Section 3: API Health ─────────────────────────────────────────────────────
st.subheader("API Health")

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
            st.plotly_chart(fig, use_container_width=True)

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
            st.plotly_chart(fig, use_container_width=True)
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
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Section 4: Ticket Queue ───────────────────────────────────────────────────
st.subheader("Ticket Queue")

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
with st.expander("Raw API Logs (last 100 calls)"):
    if not api_df.empty:
        st.dataframe(api_df.head(100), use_container_width=True, height=300)
    else:
        st.write("No API logs yet.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    '<div style="text-align:center;padding:1rem 0;font-size:0.78rem;color:#858585;'
    'font-family:\'JetBrains Mono\',monospace;">'
    '&copy; 2026 All rights reserved. Designed &amp; Developed by '
    '<a href="https://archit-konde.github.io/" target="_blank" '
    'style="color:#C9A84C;text-decoration:none;">Archit Konde</a>'
    '</div>',
    unsafe_allow_html=True,
)
