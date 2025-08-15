import streamlit as st
from utils.errors import ui_error_boundary

@ui_error_boundary
def render() -> None:
    st.header("⚙️ Pattern Management")
    st.info("CRUD + editors will be migrated in PR-4.")