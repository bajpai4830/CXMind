import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time

API_BASE = "http://127.0.0.1:8000/api/v1"

st.set_page_config(
    page_title="CXMind AI Dashboard",
    page_icon="📊",
    layout="wide"
)

# ---------------------------
# KPI CARD STYLE
# ---------------------------

st.markdown("""
<style>

.kpi-card {
    background-color: #111827;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #1f2937;
    text-align: center;
}

.kpi-title {
    font-size: 16px;
    color: #9ca3af;
}

.kpi-value {
    font-size: 32px;
    font-weight: bold;
    color: #60a5fa;
}

</style>
""", unsafe_allow_html=True)

# ---------------------------
# FORMAT TOPIC
# ---------------------------

def format_topic(topic: str):
    if not topic:
        return ""
    return topic.replace("_", " ").title()

# ---------------------------
# AI INSIGHT
# ---------------------------

def generate_ai_insight(summary, topics):

    total = summary["total_interactions"]
    avg_sentiment = summary["avg_sentiment_compound"]

    if topics:
        top_topic = topics[0]["topic"]
        top_count = topics[0]["count"]
    else:
        top_topic = "unknown"
        top_count = 0

    sentiment_status = "neutral"

    if avg_sentiment > 0.2:
        sentiment_status = "positive"
    elif avg_sentiment < -0.2:
        sentiment_status = "negative"

    insight = f"""
    **AI Insight**

    • Total interactions analyzed: {total}

    • Overall customer sentiment is **{sentiment_status}**

    • The most common issue is **{format_topic(top_topic)}** with **{top_count} complaints**

    • Recommendation: Investigate this issue to improve customer experience.
    """

    return insight

# ---------------------------
# ROOT CAUSE DETECTION
# ---------------------------

def detect_root_cause(topics):

    if not topics:
        return "No complaint pattern detected."

    main_issue = topics[0]["topic"]

    causes = {
        "delivery_issue": "Delivery delays are the main driver of complaints.",
        "support_delay": "Customer support response times are too slow.",
        "refund_request": "Customers frequently request refunds.",
        "product_defect": "Product quality problems are affecting satisfaction.",
        "payment_problem": "Payment processing issues are impacting customers.",
        "technical_bug": "Technical bugs are affecting the user experience."
    }

    return causes.get(
        main_issue,
        "Customer dissatisfaction is caused by multiple operational factors."
    )

# ---------------------------
# SIDEBAR
# ---------------------------

st.sidebar.title("⚙️ Dashboard Controls")

refresh_rate = st.sidebar.slider(
    "Auto Refresh (seconds)",
    5, 60, 10
)

show_feed = st.sidebar.checkbox(
    "Show Live Interaction Feed",
    True
)

st.sidebar.markdown("---")
st.sidebar.caption("CXMind AI Platform")

# ---------------------------
# HEADER
# ---------------------------

st.title("📊 CXMind Customer Experience Intelligence Dashboard")
st.caption("AI-powered monitoring of customer interactions")

placeholder = st.empty()

with placeholder.container():

    try:
        summary = requests.get(f"{API_BASE}/analytics/summary").json()
    except:
        st.error("⚠ Backend not reachable")
        st.stop()

    # ---------------------------
    # NEGATIVE COUNT
    # ---------------------------

    negative = 0
    for s in summary["by_label"]:
        if s["label"] == "negative":
            negative = s["count"]

    # ---------------------------
    # KPI CARDS
    # ---------------------------

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Total Interactions</div>
            <div class="kpi-value">{summary["total_interactions"]}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Average Sentiment</div>
            <div class="kpi-value">{round(summary["avg_sentiment_compound"],3)}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Negative Interactions</div>
            <div class="kpi-value">{negative}</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ---------------------------
    # CX HEALTH SCORE
    # ---------------------------

    st.subheader("📊 CX Health Score")

    cx_score = (1 + summary["avg_sentiment_compound"]) * 50
    cx_score = round(cx_score, 1)

    st.progress(cx_score / 100)
    st.metric("CX Health Score", f"{cx_score}/100")

    if cx_score > 70:
        st.success("Customer experience is healthy")
    elif cx_score > 40:
        st.warning("Customer experience needs attention")
    else:
        st.error("Customer experience is at risk")

    st.divider()

    # ---------------------------
    # SENTIMENT CHART
    # ---------------------------

    col1, col2 = st.columns(2)

    with col1:

        df_label = pd.DataFrame(summary["by_label"])

        fig = px.pie(
            df_label,
            names="label",
            values="count",
            hole=0.45,
            title="Sentiment Distribution"
        )

        st.plotly_chart(fig, width="stretch")

    with col2:

        df_channel = pd.DataFrame(summary["by_channel"])

        fig2 = px.bar(
            df_channel,
            x="channel",
            y="count",
            color="avg_sentiment_compound",
            title="Interactions by Channel",
            text_auto=True
        )

        st.plotly_chart(fig2, width="stretch")

    st.divider()

    # ---------------------------
    # TOP COMPLAINT TOPICS
    # ---------------------------

    st.subheader("📌 Top Complaint Topics")

    topics = requests.get(f"{API_BASE}/analytics/top-topics").json()

    df_topics = pd.DataFrame(topics)
    df_topics["topic"] = df_topics["topic"].apply(format_topic)

    fig3 = px.bar(
        df_topics,
        x="topic",
        y="count",
        text_auto=True,
        color="count"
    )

    st.plotly_chart(fig3, width="stretch")

    st.divider()

    # ---------------------------
    # CUSTOMER JOURNEY VIEWER
    # ---------------------------

    st.subheader("🧭 Customer Journey Viewer")

    customer_id = st.text_input(
        "Enter Customer ID",
        placeholder="Example: C101"
    )

    if customer_id:

        try:

            journey = requests.get(
                f"{API_BASE}/analytics/customer-journey",
                params={"customer_id": customer_id}
            ).json()

            if journey:

                df_journey = pd.DataFrame(journey)

                df_journey["topic"] = df_journey["topic"].apply(format_topic)

                st.dataframe(df_journey, width="stretch")

                fig_journey = px.line(
                    df_journey,
                    x="time",
                    y="channel",
                    markers=True,
                    title="Customer Journey Timeline"
                )

                st.plotly_chart(fig_journey, width="stretch")

            else:

                st.info("No interactions for this customer.")

        except:

            st.error("Journey data not available.")

    st.divider()

# ---------------------------
# LIVE INTERACTION STREAM
# ---------------------------

if show_feed:

    st.subheader("💬 Live Customer Interaction Stream")

    interactions = requests.get(
        f"{API_BASE}/interactions?limit=20"
    ).json()

    if interactions:

        for i in interactions:

            sentiment = i["sentiment_label"]
            topic = format_topic(i["topic"])

            if sentiment == "negative":

                st.error(
                    f"⚠ Customer {i['customer_id']} | {i['channel']} | {topic}\n\n{i['text']}"
                )

            elif sentiment == "positive":

                st.success(
                    f"😊 Customer {i['customer_id']} | {i['channel']} | {topic}\n\n{i['text']}"
                )

            else:

                st.info(
                    f"ℹ Customer {i['customer_id']} | {i['channel']} | {topic}\n\n{i['text']}"
                )

    else:

        st.info("No interactions available yet.")

st.divider()

st.caption(
    "CXMind AI Platform • Sentiment Analysis • Topic Modeling • Customer Risk Prediction"
)

# ---------------------------
# AUTO REFRESH
# ---------------------------

time.sleep(refresh_rate)
st.rerun()