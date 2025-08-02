import streamlit as st
import logging
from pathlib import Path

from fabric_ui.config.settings import APP_NAME
from fabric_ui.config.logging_config import setup_logging
from fabric_ui.ui.layout.header import render_header
from fabric_ui.ui.layout.sidebar import render_sidebar
from fabric_ui.ui.views.prompt_hub import PromptHubView

class FabricStudioApp:
    """Main Streamlit controller for Fabric UI."""

    def __init__(self):
        setup_logging()
        self.app_name = APP_NAME

    def inject_custom_css(self):
        # Look for a static CSS file and inject if it exists
        css_path = Path(__file__).parent / "static" / "styles.css"
        if css_path.exists():
            with open(css_path) as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    def main(self):
        st.set_page_config(
            page_title=self.app_name,
            page_icon="🧵",
            layout="wide"
        )
        self.inject_custom_css()
        render_header()
        view = render_sidebar()

        # Routing logic (minimal for now)
        if view == "Prompt Hub":
            PromptHubView().render()
        # TODO: Add more views ("Pattern Management", etc.) as they are migrated

def main():
    FabricStudioApp().main()