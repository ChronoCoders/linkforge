import json
import os
from datetime import datetime

import httpx
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="LinkForge", layout="wide", initial_sidebar_state="expanded")

API_BASE = os.environ.get("STREAMLIT_API_BASE", "http://localhost:8000")


def get_api_base():
    return st.session_state.get("api_base", API_BASE)


if "api_base" not in st.session_state:
    st.session_state.api_base = API_BASE

if "linkedin_cookies" not in st.session_state:
    st.session_state.linkedin_cookies = []


def download_csv(df: pd.DataFrame, filename: str):
    csv = df.to_csv(index=False)
    st.download_button("Download CSV", csv, filename, "text/csv", key=filename)


def download_json(data: dict, filename: str):
    json_str = json.dumps(data, indent=2)
    st.download_button("Download JSON", json_str, filename, "application/json", key=filename)


with st.sidebar:
    st.header("LinkForge")
    api_url = st.text_input("API Base URL", value=get_api_base())
    st.session_state.api_base = api_url
    st.divider()
    nav = st.radio(
        "Navigation",
        [
            "Workflow",
            "Post Ingestion",
            "Analysis Results",
            "Performance Insights",
            "Next Post Ideas",
            "Historical Trends",
        ],
        label_visibility="collapsed",
    )

    st.divider()
    with st.expander("LinkedIn Cookie Manager", expanded=False):
        cookie_json = st.text_area(
            "Cookies JSON",
            height=120,
            value=(
                json.dumps(st.session_state.linkedin_cookies)
                if st.session_state.linkedin_cookies
                else "[]"
            ),
        )
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("Save Cookies", use_container_width=True):
                try:
                    cookies = json.loads(cookie_json)
                    st.session_state.linkedin_cookies = cookies
                    st.success("Cookies saved")
                except Exception as e:
                    st.error(f"Invalid JSON: {e}")
        with col_b:
            if st.button("Clear Cookies", use_container_width=True):
                st.session_state.linkedin_cookies = []
                st.success("Cookies cleared")
        with col_c:
            if st.button("Load from File", use_container_width=True):
                st.info("Paste above and Save")
        st.caption("Get cookies from browser devtools > Application > Cookies > linkedin.com")

st.title("LinkForge")

current_cookies = st.session_state.linkedin_cookies

if nav == "Workflow":
    st.header("Complete Workflow")
    st.markdown(
        """
    **1. Post Ingestion** - Authenticate with cookies and scrape profiles/posts.
    **2. Analysis Results** - Run sentiment, themes, performance analysis with exports.
    **3. Performance Insights** - View predictions and confidence charts.
    **4. Next Post Ideas** - Get AI strategy and recommendation.
    **5. Historical Trends** - Charts and downloadable data.
    """
    )
    st.success("Follow left navigation for end-to-end scrape to recommendation flow.")

elif nav == "Post Ingestion":
    st.header("Post Ingestion")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Scrape Profile & Posts")
        profile_url = st.text_input("LinkedIn Profile URL")
        force_refresh = st.checkbox("Force refresh", value=False)
        max_posts = st.slider("Max posts", 5, 25, 12)
        use_cookies = st.checkbox("Use saved cookies", value=bool(current_cookies))
        if st.button("Ingest", type="primary"):
            if profile_url:
                with st.spinner("Working..."):
                    try:
                        payload = {"linkedin_url": profile_url, "force_refresh": force_refresh}
                        resp = httpx.post(f"{api_url}/profiles", json=payload, timeout=180)
                        if resp.status_code == 200:
                            profile = resp.json()
                            st.success(f"Saved: {profile.get('full_name')}")
                            scrape_payload = {"url": profile_url, "max_posts": max_posts}
                            if use_cookies and current_cookies:
                                scrape_payload["cookies"] = current_cookies
                            scrape_resp = httpx.post(
                                f"{api_url}/scraping/profile", json=scrape_payload, timeout=180
                            )
                            if scrape_resp.status_code == 200:
                                st.info("Posts done.")
                            st.json(profile)
                        else:
                            st.error(resp.text)
                    except Exception as e:
                        st.error(str(e))
    with col2:
        st.subheader("Recent Profiles")
        if st.button("Refresh"):
            try:
                resp = httpx.get(f"{api_url}/profiles?limit=15", timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("profiles"):
                        df = pd.DataFrame(data["profiles"])
                        st.dataframe(
                            df[["id", "full_name", "headline"]],
                            use_container_width=True,
                            hide_index=True,
                        )
            except Exception as e:
                st.error(str(e))

elif nav == "Analysis Results":
    st.header("Analysis Results")
    profile_id = st.number_input("Profile ID", min_value=1, step=1, value=1)
    if st.button("Run Analysis", type="primary"):
        with st.spinner("Analyzing..."):
            try:
                resp = httpx.post(
                    f"{api_url}/analytics/profile",
                    json={"profile_id": int(profile_id), "include_posts": True},
                    timeout=90,
                )
                if resp.status_code == 200:
                    result = resp.json()
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Sentiment", f"{result.get('overall_sentiment', 0):.3f}")
                    c2.metric("Polarization", f"{result.get('polarization_score', 0):.3f}")
                    c3.metric("Posts", result.get("post_count", 0))
                    c4.metric("Prediction", f"{result.get('performance_prediction', 0):.2%}")
                    if "post_performance_reports" in result:
                        df = pd.DataFrame(result["post_performance_reports"])
                        st.dataframe(df, use_container_width=True)
                        download_csv(df, "analysis.csv")
                        download_json(result, "analysis.json")
                    st.json(result)
                else:
                    st.error(resp.text)
            except Exception as e:
                st.error(str(e))

elif nav == "Performance Insights":
    st.header("Performance Insights")
    profile_id = st.number_input("Profile ID", min_value=1, step=1, value=1, key="perf")
    if st.button("Load"):
        try:
            resp = httpx.post(
                f"{api_url}/analytics/profile", json={"profile_id": int(profile_id)}, timeout=60
            )
            if resp.status_code == 200:
                data = resp.json()
                st.metric("Prediction", f"{data.get('performance_prediction', 0):.2%}")
                if "next_best_posts" in data:
                    df = pd.DataFrame(data["next_best_posts"])
                    fig = px.bar(df, x="tone", y="predicted_engagement", title="Predictions")
                    st.plotly_chart(fig, use_container_width=True)
                st.json(data)
        except Exception as e:
            st.error(str(e))

elif nav == "Next Post Ideas":
    st.header("Next Post Ideas")
    profile_id = st.number_input("Profile ID", min_value=1, step=1, value=1, key="ideas")
    if st.button("Generate", type="primary"):
        try:
            resp = httpx.post(
                f"{api_url}/analytics/recommendations",
                json={"profile_id": int(profile_id)},
                timeout=60,
            )
            if resp.status_code == 200:
                data = resp.json()
                plan = data.get("next_post_plan", {})
                if plan:
                    st.subheader(plan.get("topic", ""))
                    st.write(plan.get("hook", ""))
                    st.write(plan.get("why_it_works", ""))
                    download_json(plan, "recommendation.json")
        except Exception as e:
            st.error(str(e))

elif nav == "Historical Trends":
    st.header("Historical Trends")
    profile_id = st.number_input("Profile ID", min_value=1, step=1, value=1, key="trends")
    if st.button("Load"):
        try:
            resp = httpx.post(
                f"{api_url}/analytics/profile",
                json={"profile_id": int(profile_id), "include_posts": True},
                timeout=60,
            )
            if resp.status_code == 200:
                data = resp.json()
                if "post_performance_reports" in data:
                    df = pd.DataFrame(data["post_performance_reports"])
                    fig = px.line(df, x="posted_at", y="engagement_score", title="Trends")
                    st.plotly_chart(fig, use_container_width=True)
                    download_csv(df, "trends.csv")
        except Exception as e:
            st.error(str(e))

st.caption(f"LinkForge • {datetime.now().year}")
