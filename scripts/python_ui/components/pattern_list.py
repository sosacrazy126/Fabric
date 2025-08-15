import streamlit as st
from typing import List, Optional
from utils.errors import ui_error_boundary
from services import patterns
from utils.typing import PatternSpec
from utils.logging import logger

@ui_error_boundary
def render_pattern_selector(
    patterns_list: List[PatternSpec],
    key: str = "pattern_selector",
    multi_select: bool = False,
    show_validation: bool = True,
    include_empty_option: bool = True
) -> Optional[str] | List[str]:
    """
    Render a pattern selector with optional validation indicators.
    
    Args:
        patterns_list: List of available patterns
        key: Streamlit widget key
        multi_select: Whether to allow multiple selection
        show_validation: Whether to show validation status
        include_empty_option: Whether to include empty option for single select
        
    Returns:
        Selected pattern name(s) or None
    """
    if not patterns_list:
        st.warning("No patterns available.")
        return [] if multi_select else None
    
    # Prepare pattern options with validation info
    pattern_options = []
    pattern_status = {}
    
    for pattern in patterns_list:
        display_name = pattern.name
        
        if show_validation:
            is_valid, status_icon = _get_validation_status(pattern)
            display_name = f"{status_icon} {pattern.name}"
            pattern_status[pattern.name] = is_valid
        
        pattern_options.append((display_name, pattern.name))
    
    # Create selector widget
    if multi_select:
        selected_display = st.multiselect(
            "Select Patterns",
            options=[display for display, _ in pattern_options],
            key=key
        )
        # Map back to pattern names
        selected_names = []
        for display in selected_display:
            for display_opt, name_opt in pattern_options:
                if display_opt == display:
                    selected_names.append(name_opt)
                    break
        return selected_names
    else:
        options = [display for display, _ in pattern_options]
        if include_empty_option:
            options = [""] + options
        
        selected_display = st.selectbox(
            "Select Pattern",
            options=options,
            key=key
        )
        
        if not selected_display:
            return None
        
        # Map back to pattern name
        for display_opt, name_opt in pattern_options:
            if display_opt == selected_display:
                return name_opt
        return None

@ui_error_boundary
def render_pattern_table(patterns_list: List[PatternSpec], key: str = "pattern_table") -> None:
    """Render a table view of patterns with details."""
    if not patterns_list:
        st.info("No patterns available.")
        return
    
    st.subheader(f"Available Patterns ({len(patterns_list)})")
    
    # Create table data
    table_data = []
    for pattern in patterns_list:
        is_valid, _ = _get_validation_status(pattern)
        status = "✅ Valid" if is_valid else "⚠️ Issues"
        
        # Get content preview
        content_preview = _get_content_preview(pattern.content)
        
        # Get file size
        size_kb = pattern.meta.get("size", 0) / 1024 if pattern.meta.get("size") else 0
        
        table_data.append({
            "Name": pattern.name,
            "Status": status,
            "Size (KB)": f"{size_kb:.1f}",
            "Preview": content_preview
        })
    
    # Display as dataframe
    st.dataframe(
        table_data,
        key=key,
        use_container_width=True,
        hide_index=True
    )

@ui_error_boundary
def render_pattern_cards(patterns_list: List[PatternSpec], key: str = "pattern_cards") -> None:
    """Render patterns as cards with details."""
    if not patterns_list:
        st.info("No patterns available.")
        return
    
    st.subheader(f"Available Patterns ({len(patterns_list)})")
    
    # Calculate number of columns based on pattern count
    num_cols = min(3, len(patterns_list))
    cols = st.columns(num_cols)
    
    for i, pattern in enumerate(patterns_list):
        with cols[i % num_cols]:
            _render_pattern_card(pattern, f"{key}_{i}")

def _render_pattern_card(pattern: PatternSpec, key: str) -> None:
    """Render a single pattern card."""
    is_valid, status_icon = _get_validation_status(pattern)
    status_color = "green" if is_valid else "orange"
    
    with st.container():
        st.markdown(f"### {status_icon} {pattern.name}")
        
        # Status badge
        st.markdown(f"<span style='color: {status_color}'>{'✅ Valid' if is_valid else '⚠️ Has Issues'}</span>", 
                   unsafe_allow_html=True)
        
        # Content preview
        content_preview = _get_content_preview(pattern.content)
        st.text(content_preview)
        
        # File info
        size_kb = pattern.meta.get("size", 0) / 1024 if pattern.meta.get("size") else 0
        st.caption(f"Size: {size_kb:.1f} KB")
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✏️ Edit", key=f"edit_{key}", use_container_width=True):
                st.session_state["edit_pattern_selector"] = pattern.name
                st.session_state["current_view"] = "Pattern Management"
                st.rerun()
        
        with col2:
            if st.button("👁️ View", key=f"view_{key}", use_container_width=True):
                _show_pattern_preview(pattern)

def _show_pattern_preview(pattern: PatternSpec) -> None:
    """Show pattern content in a modal-like expander."""
    with st.expander(f"Preview: {pattern.name}", expanded=True):
        st.code(pattern.content, language="markdown")

def _get_validation_status(pattern: PatternSpec) -> tuple[bool, str]:
    """Get validation status for a pattern."""
    try:
        content = pattern.content.lower()
        required_sections = ["# identity", "# steps", "# output"]
        missing_sections = [section for section in required_sections if section not in content]
        
        if not missing_sections:
            return True, "✅"
        else:
            return False, "⚠️"
    except Exception:
        return False, "❌"

def _get_content_preview(content: str) -> str:
    """Get a preview of pattern content."""
    # Extract first meaningful line that's not a header
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#') and len(line) > 10:
            # Truncate if too long
            if len(line) > 100:
                return line[:97] + "..."
            return line
    
    # Fallback to first non-empty line
    for line in lines:
        line = line.strip()
        if line:
            if len(line) > 100:
                return line[:97] + "..."
            return line
    
    return "No content preview available"

@ui_error_boundary
def render_pattern_search(patterns_list: List[PatternSpec], key: str = "pattern_search") -> List[PatternSpec]:
    """Render a search interface for patterns."""
    st.subheader("Search Patterns")
    
    search_term = st.text_input(
        "Search patterns by name or content",
        key=f"{key}_input",
        placeholder="Enter search term..."
    )
    
    if not search_term:
        return patterns_list
    
    # Filter patterns based on search term
    filtered_patterns = []
    search_lower = search_term.lower()
    
    for pattern in patterns_list:
        # Search in name
        if search_lower in pattern.name.lower():
            filtered_patterns.append(pattern)
            continue
        
        # Search in content
        if search_lower in pattern.content.lower():
            filtered_patterns.append(pattern)
    
    st.info(f"Found {len(filtered_patterns)} pattern(s) matching '{search_term}'")
    return filtered_patterns