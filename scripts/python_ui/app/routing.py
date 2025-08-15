import streamlit as st

def get_current_view() -> str:
    return st.session_state.get("current_view", "Run Patterns")

def set_view(view_name: str) -> None:
    st.session_state["current_view"] = view_name