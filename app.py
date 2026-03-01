"""
app.py
SupportOps AI Monitor — Streamlit Dashboard
Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

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

# ── Init DB ───────────────────────────────────────────────────────────────────
db.init_db()

# ── Cached data loaders ──────────────────────────────────────────────────────
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
    st.title("🎫 SupportOps AI Monitor")
    st.caption("Enterprise AI Platform · Support Dashboard")
    st.divider()

    st.subheader("⚙️ Data Controls")

    n_tickets = st.slider("Tickets to generate", min_value=10, max_value=200, value=50, step=10)
    days_back = st.slider("Days back", min_value=7, max_value=90, value=30)

    if st.button("🔄 Generate & Triage Tickets", use_container_width=True, type="primary"):
        try:
            with st.spinner("Generating tickets..."):
                tickets = tg.generate_batch(n=n_tickets, days_back=days_back)
                for t in tickets:
                    db.insert_ticket(t)

            progress_bar = st.progress(0)
            status_text = st.empty()

            def update_progress(i, total):
                progress_bar.progress(i / total)
                status_text.text(f"Triaging ticket {i}/{total}...")

            with st.spinner("Running AI triage..."):
                stats = ai_triage.triage_batch(tickets, progress_callback=update_progress)

            progress_bar.empty()
            status_text.empty()
            st.success(f"✅ {stats['success']} triaged · {stats['failed']} failed")
            st.session_state.data_version += 1
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error during ticket generation/triage: {e}")

    st.divider()

    st.subheader("🔍 Filters")
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
    st.caption("Built by Archit Konde · [GitHub](https://github.com/Archit-Konde)")

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
st.title("🎫 SupportOps AI Monitor")
st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC  ·  Showing {len(filtered_tickets)} of {len(all_tickets)} tickets")

# ── Section 1: KPI Metrics ────────────────────────────────────────────────────
st.subheader("📊 Overview")

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
    st.info("👈 Use the sidebar to generate and triage tickets to populate the dashboard.")
    st.stop()

st.divider()

# ── Section 2: Ticket Analytics ───────────────────────────────────────────────
st.subheader("🎫 Ticket Analytics")

col1, col2, col3 = st.columns(3)

with col1:
    # Category breakdown
    if not ticket_df.empty and "category" in ticket_df.columns:
        cat_counts = ticket_df["category"].value_counts().reset_index()
        cat_counts.columns = ["category", "count"]
        fig = px.pie(
            cat_counts,
            names="category",
            values="count",
            title="Tickets by Category",
            color_discrete_sequence=px.colors.qualitative.Set3,
            hole=0.4,
        )
        fig.update_layout(height=300, margin=dict(t=40, b=0))
        st.plotly_chart(fig, use_container_width=True)

with col2:
    # Priority breakdown
    if not ticket_df.empty and "priority" in ticket_df.columns:
        priority_order = ["critical", "high", "medium", "low"]
        priority_colors = {
            "critical": "#ef4444",
            "high": "#f97316",
            "medium": "#eab308",
            "low": "#22c55e",
        }
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
            color_discrete_map=priority_colors,
        )
        fig.update_layout(
            height=300,
            margin=dict(t=40, b=0),
            showlegend=False,
            xaxis_title="",
            yaxis_title="Count",
        )
        st.plotly_chart(fig, use_container_width=True)

with col3:
    # Sentiment breakdown
    if not ticket_df.empty and "sentiment" in ticket_df.columns:
        sent_df = ticket_df[ticket_df["sentiment"].notna()]
        if not sent_df.empty:
            sent_counts = sent_df["sentiment"].value_counts().reset_index()
            sent_counts.columns = ["sentiment", "count"]
            sentiment_colors = {
                "positive": "#22c55e",
                "neutral": "#94a3b8",
                "negative": "#ef4444",
            }
            fig = px.bar(
                sent_counts,
                x="sentiment",
                y="count",
                title="Customer Sentiment",
                color="sentiment",
                color_discrete_map=sentiment_colors,
            )
            fig.update_layout(
                height=300,
                margin=dict(t=40, b=0),
                showlegend=False,
                xaxis_title="",
                yaxis_title="Count",
            )
            st.plotly_chart(fig, use_container_width=True)

# Ticket volume over time
if not ticket_df.empty and "created_at" in ticket_df.columns:
    ticket_df["created_date"] = pd.to_datetime(ticket_df["created_at"]).dt.date
    volume_df = ticket_df.groupby("created_date").size().reset_index(name="count")
    fig = px.line(
        volume_df,
        x="created_date",
        y="count",
        title="Ticket Volume Over Time",
        markers=True,
        color_discrete_sequence=["#6366f1"],
    )
    fig.update_layout(
        height=250,
        margin=dict(t=40, b=0),
        xaxis_title="",
        yaxis_title="Tickets",
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Section 3: API Health Monitor ─────────────────────────────────────────────
st.subheader("🔬 API Health Monitor")

if not api_df.empty:
    col1, col2 = st.columns(2)

    with col1:
        # Latency over time (successful calls only)
        success_df = api_df[api_df["success"] == 1].copy()
        if not success_df.empty:
            success_df["timestamp"] = pd.to_datetime(success_df["timestamp"])
            success_df = success_df.sort_values("timestamp")
            fig = px.scatter(
                success_df,
                x="timestamp",
                y="latency_ms",
                title="API Latency Over Time (successful calls)",
                color_discrete_sequence=["#6366f1"],
                opacity=0.6,
            )
            fig.add_hline(
                y=success_df["latency_ms"].mean(),
                line_dash="dash",
                line_color="#f97316",
                annotation_text=f"Mean: {success_df['latency_ms'].mean():.0f}ms",
            )
            fig.update_layout(height=300, margin=dict(t=40, b=0))
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Error type breakdown
        error_df = api_df[api_df["success"] == 0]
        if not error_df.empty:
            err_counts = error_df["error_type"].value_counts().reset_index()
            err_counts.columns = ["error_type", "count"]
            error_colors = {
                "rate_limit": "#f97316",
                "server_error": "#ef4444",
                "timeout": "#eab308",
                "unknown": "#94a3b8",
            }
            fig = px.bar(
                err_counts,
                x="error_type",
                y="count",
                title="API Errors by Type",
                color="error_type",
                color_discrete_map=error_colors,
            )
            fig.update_layout(
                height=300,
                margin=dict(t=40, b=0),
                showlegend=False,
                xaxis_title="",
                yaxis_title="Error Count",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("✅ No API errors recorded.")

    # Status code distribution
    code_counts = api_df["status_code"].value_counts().reset_index()
    code_counts.columns = ["status_code", "count"]
    code_counts["status_code"] = code_counts["status_code"].astype(str)
    code_colors = {
        "200": "#22c55e",
        "429": "#f97316",
        "500": "#ef4444",
        "408": "#eab308",
        "0": "#94a3b8",
    }
    fig = px.bar(
        code_counts,
        x="status_code",
        y="count",
        title="HTTP Status Code Distribution",
        color="status_code",
        color_discrete_map=code_colors,
    )
    fig.update_layout(
        height=250,
        margin=dict(t=40, b=0),
        showlegend=False,
        xaxis_title="HTTP Status Code",
        yaxis_title="Count",
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Section 4: Live Ticket Queue ──────────────────────────────────────────────
st.subheader("📋 Ticket Queue")

if not ticket_df.empty:
    display_cols = ["ticket_id", "created_at", "customer", "subject", "priority", "status", "category", "sentiment", "ai_summary"]
    display_cols = [c for c in display_cols if c in ticket_df.columns]
    display_df = ticket_df[display_cols].copy()

    # Colour-code priority
    def priority_badge(val):
        colors = {
            "critical": "background-color: #fee2e2; color: #991b1b; font-weight: bold",
            "high": "background-color: #ffedd5; color: #9a3412",
            "medium": "background-color: #fef9c3; color: #854d0e",
            "low": "background-color: #dcfce7; color: #166534",
        }
        return colors.get(val, "")

    styled = display_df.style.map(priority_badge, subset=["priority"])

    st.dataframe(styled, use_container_width=True, height=400)

    # Ticket detail viewer
    with st.expander("🔍 View ticket details"):
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
                    st.info(f"🤖 **AI Summary:** {ticket['ai_summary']}")
                st.text_area("Ticket Body", value=ticket["body"], height=200, disabled=True)

                if ticket["status"] != "resolved":
                    if st.button("✅ Mark as Resolved", type="primary"):
                        db.resolve_ticket(selected_id)
                        st.success("Ticket resolved!")
                        st.session_state.data_version += 1
                        st.rerun()

st.divider()

# ── Section 5: Raw API Logs ───────────────────────────────────────────────────
with st.expander("📜 Raw API Logs (last 100 calls)"):
    if not api_df.empty:
        st.dataframe(api_df.head(100), use_container_width=True, height=300)
    else:
        st.write("No API logs yet.")
