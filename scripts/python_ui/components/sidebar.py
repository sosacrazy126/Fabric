import streamlit as st
from app import routing

VIEWS = ["Run Patterns", "Pattern Management", "Analysis Dashboard"]

def render() -> None:
    with st.sidebar:
        st.header("Navigation")
        current = routing.get_current_view()
        sel = st.radio("View", VIEWS, index=VIEWS.index(current))
        if sel != current:
            routing.set_view(sel)
            st.rerun()

        st.divider()
        st.header("Configuration")
        st.info("Model/Provider config will be added in PR-2/PR-3.")