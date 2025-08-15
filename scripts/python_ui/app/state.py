import streamlit as st
from utils.logging import logger
from services import storage

def initialize() -> None:
    if st.session_state.get("_initialized"):
        return
    logger.info("Initializing session state (PR-1)")

    defaults = {
        "current_view": "Run Patterns",
        "input_content": "",
        "selected_patterns": [],
        "chat_output": [],
        "output_logs": [],
        "starred_outputs": [],
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)

    # placeholder: future persisted reads (PR-2)
    try:
        storage.load_saved_outputs()
    except Exception as e:
        logger.warning("load_saved_outputs failed: %s", e)

    st.session_state["_initialized"] = True