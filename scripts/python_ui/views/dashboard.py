import streamlit as st
from utils.errors import ui_error_boundary

@ui_error_boundary
def render() -> None:
    st.header("📊 Analysis Dashboard")
    st.info("History/metrics will be migrated in PR-4/PR-5.")