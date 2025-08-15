"""
Fabric Pattern Studio - Clean Architecture Entry Point (PR-1)
"""
import os, sys
import streamlit as st

# Ensure package imports resolve when running via 'streamlit run app/main.py'
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # scripts/python_ui
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from utils import errors, logging as app_logging  # noqa: E402
from app import routing, state  # noqa: E402
from components import header, sidebar  # noqa: E402
from views import execution, management, dashboard  # noqa: E402

def configure_page() -> None:
    st.set_page_config(
        page_title="Fabric Pattern Studio",
        page_icon="🎭",
        layout="wide",
        initial_sidebar_state="expanded",
    )

@errors.ui_error_boundary
def main() -> None:
    app_logging.init()
    configure_page()
    state.initialize()      # defaults + future persistence hooks
    header.render()
    sidebar.render()

    view = routing.get_current_view()
    if view == "Run Patterns":
        execution.render()
    elif view == "Pattern Management":
        management.render()
    else:
        dashboard.render()

if __name__ == "__main__":
    main()