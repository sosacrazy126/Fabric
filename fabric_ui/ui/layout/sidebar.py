import streamlit as st

def render_sidebar(status=None):
    """Sidebar navigation, referencing status (if provided)."""
    st.sidebar.title("Navigation")
    if status:
        st.sidebar.markdown(f"**Fabric status:** {'✅' if status.get('fabric_installed') else '❌'}")
    # TODO: Add actual sidebar navigation and config widgets.
    return "Prompt Hub"