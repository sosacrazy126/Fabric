import streamlit as st
from app import routing
from components import provider_selector

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
        
        # Use the provider_selector component
        vendor, model = provider_selector.render()
        
        # Store selected config in session state
        if "config" not in st.session_state:
            st.session_state.config = {}
        
        st.session_state.config["vendor"] = vendor
        st.session_state.config["model"] = model
        
        # Render advanced settings
        advanced_settings = provider_selector.render_advanced_settings()
        st.session_state.config.update(advanced_settings)
        
        # Display status indicator
        if vendor and model:
            provider_selector.render_status_indicator(vendor, model)
            st.caption(f"📡 {vendor} - {model}")