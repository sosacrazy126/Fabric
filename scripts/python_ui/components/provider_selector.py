"""
Provider and model selection UI component.
Displays vendor dropdown first, then models for that vendor.
"""
import streamlit as st
from typing import Optional, Tuple

from services.config import get_config_manager
from services.providers import ProviderService
from utils.logging import logger
from utils.errors import ui_error_boundary


@ui_error_boundary
def render() -> Tuple[Optional[str], Optional[str]]:
    """
    Render provider and model selection UI.
    
    Returns:
        Tuple of (selected_vendor, selected_model)
    """
    config_manager = get_config_manager()
    provider_service = ProviderService()
    
    # Load current configuration
    config = config_manager.load_config()
    
    # Debug logging
    logger.info(f"Config loaded - default_vendor: {config.default_vendor}, default_model: {config.default_model}")
    
    # Get active vendors
    active_vendors = config_manager.get_active_vendors()
    logger.info(f"Active vendors: {list(active_vendors.keys())}")
    
    if not active_vendors:
        st.warning("No providers configured. Please run 'fabric --setup' first.")
        return None, None
    
    # Provider selection
    vendor_names = list(active_vendors.keys())
    
    # Add "All Providers" option if multiple vendors are configured
    if len(vendor_names) > 1:
        vendor_names.insert(0, "All Providers")
    
    # Determine default vendor selection
    # The config.default_vendor is "openai" (lowercase) from the normalized .env
    default_vendor_idx = 0
    if config.default_vendor:
        # Try exact match first
        if config.default_vendor in vendor_names:
            default_vendor_idx = vendor_names.index(config.default_vendor)
        else:
            # Try case-insensitive match
            for idx, vendor_name in enumerate(vendor_names):
                if vendor_name.lower() == config.default_vendor.lower():
                    default_vendor_idx = idx
                    break
    
    selected_vendor = st.selectbox(
        "🏢 Provider",
        vendor_names,
        index=default_vendor_idx,
        key="provider_selector",
        help="Select your AI provider"
    )
    
    # Handle "All Providers" selection
    if selected_vendor == "All Providers":
        # Get all available models from all vendors
        all_models = []
        for vendor_name in active_vendors.keys():
            models = provider_service.list_available_models(vendor_name)
            for model in models:
                # Add vendor prefix for clarity
                all_models.append({
                    "display": f"{vendor_name}: {model.model}",
                    "vendor": vendor_name,
                    "model": model.model,
                    "full_name": model.full_name
                })
        
        if not all_models:
            st.info("No models available from configured providers.")
            return None, None
        
        # Model selection for all providers
        model_displays = [m["display"] for m in all_models]
        
        # Find default model in list
        default_model_idx = 0
        if config.default_model:
            for idx, model_info in enumerate(all_models):
                if model_info["model"] == config.default_model:
                    default_model_idx = idx
                    break
        
        selected_model_display = st.selectbox(
            "🤖 Model",
            model_displays,
            index=default_model_idx,
            key="model_selector_all",
            help="Select a model from any provider"
        )
        
        # Get actual vendor and model from selection
        selected_idx = model_displays.index(selected_model_display)
        model_info = all_models[selected_idx]
        
        return model_info["vendor"], model_info["model"]
    
    else:
        # Single vendor selected
        vendor_config = active_vendors[selected_vendor]
        
        # Get available models for this vendor
        models = provider_service.list_available_models(selected_vendor)
        
        if not models:
            st.info(f"No models available for {selected_vendor}.")
            
            # Show setup instructions based on vendor
            if selected_vendor == "ollama":
                st.info("Make sure Ollama is running and has models pulled.")
            else:
                st.info(f"Check your {selected_vendor.upper()}_API_KEY configuration.")
            
            return selected_vendor, None
        
        # Extract model names
        model_names = [m.model for m in models]
        
        # Find default model for this vendor
        default_model_idx = 0
        if config.default_model and config.default_model in model_names:
            default_model_idx = model_names.index(config.default_model)
        
        selected_model = st.selectbox(
            "🤖 Model",
            model_names,
            index=default_model_idx,
            key=f"model_selector_{selected_vendor}",
            help=f"Select a {selected_vendor} model"
        )
        
        return selected_vendor, selected_model


@ui_error_boundary
def render_advanced_settings() -> dict:
    """
    Render advanced model settings.
    
    Returns:
        Dictionary of advanced settings
    """
    settings = {}
    
    with st.expander("⚙️ Advanced Settings"):
        temperature = st.slider(
            "Temperature",
            0.0, 1.0,
            st.session_state.get("temperature", 0.7),
            0.1,
            help="Controls randomness (0=focused, 1=creative)"
        )
        settings["temperature"] = temperature
        
        max_tokens = st.number_input(
            "Max Tokens",
            100, 10000,
            st.session_state.get("max_tokens", 2000),
            step=100,
            help="Maximum response length"
        )
        settings["max_tokens"] = max_tokens
        
        timeout = st.number_input(
            "Timeout (seconds)",
            10, 300,
            st.session_state.get("timeout", 90),
            step=10,
            help="Maximum execution time"
        )
        settings["timeout"] = timeout
        
        # Store in session state
        st.session_state.update(settings)
    
    return settings


@ui_error_boundary
def render_status_indicator(vendor: str, model: str) -> None:
    """
    Show connection status for selected vendor/model.
    
    Args:
        vendor: Selected vendor name
        model: Selected model name
    """
    if not vendor:
        return
    
    config_manager = get_config_manager()
    
    # Check if vendor/model is accessible
    is_valid = config_manager.validate_vendor_access(vendor, model)
    
    if is_valid:
        st.success(f"✅ {vendor}/{model if model else 'provider'} is configured")
    else:
        st.warning(f"⚠️ {vendor}/{model if model else 'provider'} may not be accessible")


def get_selected_config() -> dict:
    """
    Get the currently selected configuration.
    
    Returns:
        Dictionary with vendor, model, and advanced settings
    """
    return {
        "vendor": st.session_state.get("provider_selector"),
        "model": st.session_state.get("model_selector"),
        "temperature": st.session_state.get("temperature", 0.7),
        "max_tokens": st.session_state.get("max_tokens", 2000),
        "timeout": st.session_state.get("timeout", 90)
    }