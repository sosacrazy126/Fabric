import streamlit as st
from fabric_ui.core.fabric_client import FabricClient
from fabric_ui.core.pattern_manager import PatternManager
from fabric_ui.ui.components.pattern_selector import render_pattern_selector

class PromptHubView:
    def __init__(self, fabric_client=None, pattern_manager=None, *_, **__):
        self.fabric_client = fabric_client or FabricClient()
        self.pattern_manager = pattern_manager or PatternManager(self.fabric_client)

    def render(self):
        st.title("🧵 Fabric Prompt Hub")
        st.markdown("Transform your ideas with AI-powered patterns.")

        status = self.fabric_client.get_status()
        if not status.get("fabric_installed"):
            self._render_setup_instructions()
            return

        self._render_status_summary(status)
        st.divider()
        col1, col2 = st.columns([1, 1])
        with col1:
            self._render_input_section()
        with col2:
            self._render_pattern_section()

    def _render_setup_instructions(self):
        st.error("❌ Fabric CLI not available or not configured.")
        with st.expander("Setup Instructions"):
            st.markdown("""
            **To use Fabric Prompt Hub:**
            1. Install Fabric CLI: `go install github.com/danielmiessler/fabric@latest`
            2. Run setup: `fabric --setup`
            3. Configure your API keys and patterns
            4. Refresh this page
            """)

    def _render_status_summary(self, status):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Fabric Version", status.get('version') or "Unknown")
        with col2:
            st.metric("Vendors", status.get('vendor_count', 0))
        with col3:
            st.metric("Patterns", status.get('pattern_count', 0))
        with col4:
            st.metric("Status", "🟢 Ready" if status.get("fabric_installed") else "🔴 Error")

    def _render_input_section(self):
        st.subheader("📝 Input")
        st.text_area("Enter your text:", height=200, placeholder="Paste or type your content here...")

    def _render_pattern_section(self):
        st.subheader("🎯 Patterns")
        patterns = self.pattern_manager.discover()
        selected = render_pattern_selector(patterns)
        if not selected:
            st.info("Select a pattern to continue.")
            return
        # Placeholder for execution/actions in next phase