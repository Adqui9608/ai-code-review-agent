"""Streamlit dashboard for the AI Code Review Agent."""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="AI Code Review Agent",
    layout="wide",
)

st.title("AI Code Review Agent")
st.markdown("Enter a GitHub PR URL below to run an AI-powered code review.")

pr_url = st.text_input(
    "GitHub PR URL",
    placeholder="https://github.com/owner/repo/pull/123",
)

if st.button("Run Review", disabled=not pr_url):
    st.info("Review pipeline not yet connected. This is a placeholder.")
