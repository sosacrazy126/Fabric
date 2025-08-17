"""
Enhanced pattern selector component with search, filtering, and descriptions.
"""
import streamlit as st
from typing import List, Dict, Any, Optional
from utils.errors import ui_error_boundary
from utils.logging import logger
from services import patterns

# Cache for pattern data to prevent repeated loading
_pattern_cache = {
    "specs": None,
    "descriptions": None,
    "search_index": None,
    "last_refresh": 0
}

CACHE_REFRESH_INTERVAL = 60  # Refresh cache every 60 seconds

def _get_cached_patterns():
    """Get cached pattern data, refreshing if needed."""
    import time
    current_time = time.time()
    
    # Check if cache needs refresh
    if (_pattern_cache["specs"] is None or 
        current_time - _pattern_cache["last_refresh"] > CACHE_REFRESH_INTERVAL):
        
        try:
            # Load pattern specs
            pattern_specs = patterns.list_patterns()
            _pattern_cache["specs"] = pattern_specs
            
            # Build search index for fast searching
            search_index = {}
            for spec in pattern_specs:
                if hasattr(spec, 'name') and hasattr(spec, 'content'):
                    # Create searchable text combining name and content
                    searchable_text = f"{spec.name} {spec.content or ''}".lower()
                    search_index[spec.name] = searchable_text
            
            _pattern_cache["search_index"] = search_index
            _pattern_cache["descriptions"] = _load_pattern_descriptions()
            _pattern_cache["last_refresh"] = current_time
            
            logger.info(f"Refreshed pattern cache with {len(pattern_specs)} patterns")
            
        except Exception as e:
            logger.error(f"Failed to refresh pattern cache: {e}")
            # Return existing cache if available
            if _pattern_cache["specs"] is None:
                raise e
    
    return _pattern_cache

@ui_error_boundary
def render_pattern_selector(key: str = "pattern_selector") -> List[str]:
    """
    Render enhanced pattern selector with descriptions, tags, and search functionality.
    
    Args:
        key: Unique key for the selector component
        
    Returns:
        List of selected pattern names
    """
    # Load patterns from cache
    try:
        cache = _get_cached_patterns()
        pattern_specs = cache["specs"]
        pattern_names = [spec.name for spec in pattern_specs]
    except Exception as e:
        logger.error(f"Failed to load patterns: {e}")
        st.error(f"Failed to load patterns: {e}")
        return []
    
    if not pattern_names:
        st.warning("No patterns available. Create a pattern first.")
        return []

    # Load pattern descriptions from cache
    descriptions_data = cache["descriptions"]
    all_tags = _get_all_tags(descriptions_data)

    # Search and filter controls
    st.subheader("🔍 Find Patterns")
    
    # Search bar
    search_col, filter_col = st.columns([2, 1])
    
    with search_col:
        search_query = st.text_input(
            "Search patterns",
            value=st.session_state.get(f"{key}_search", ""),
            placeholder="Search by name, description, or content...",
            key=f"{key}_search_input",
            help="Search through pattern names, descriptions, and content"
        )
        st.session_state[f"{key}_search"] = search_query
    
    with filter_col:
        show_filters = st.toggle(
            "🏷️ Filters", 
            value=st.session_state.get(f"{key}_show_filters", False),
            key=f"{key}_filter_toggle"
        )
        st.session_state[f"{key}_show_filters"] = show_filters

    # Filter controls
    selected_tags = []
    if show_filters:
        with st.expander("Filter by Category", expanded=True):
            if all_tags:
                try:
                    selected_tags = st.pills(
                        "Select tags to filter patterns",
                        all_tags,
                        selection_mode="multi",
                        key=f"{key}_tag_pills",
                        label_visibility="collapsed"
                    )
                except (AttributeError, TypeError):
                    # Fall back to multiselect if pills is not available
                    selected_tags = st.multiselect(
                        "Select tags to filter patterns",
                        all_tags,
                        key=f"{key}_tag_multiselect",
                        label_visibility="collapsed"
                    )

    # Apply filters
    filtered_patterns = pattern_names

    # Apply search filter first using cached search index
    if search_query:
        filtered_patterns = _filter_patterns_by_search_cached(
            filtered_patterns, search_query, cache["search_index"], descriptions_data
        )

    # Filter by tags
    if selected_tags:
        filtered_patterns = _filter_patterns_by_tags(
            filtered_patterns, selected_tags, descriptions_data
        )

    if not filtered_patterns:
        if search_query and selected_tags:
            st.info(f"No patterns match search '{search_query}' and tags: {', '.join(selected_tags)}")
        elif search_query:
            st.info(f"No patterns match search: '{search_query}'")
        elif selected_tags:
            st.info(f"No patterns match tags: {', '.join(selected_tags)}")
        else:
            st.info("No patterns match your filters.")
        return []

    # Show filter results summary
    summary_parts = []
    if search_query:
        summary_parts.append(f"search: '{search_query}'")
    if selected_tags:
        summary_parts.append(f"tags: {', '.join(selected_tags)}")
    
    if summary_parts:
        st.caption(f"📊 Showing {len(filtered_patterns)} of {len(pattern_names)} patterns matching {' and '.join(summary_parts)}")

    # Enhanced pattern display with variable indicators
    pattern_display_options = []
    for pattern in filtered_patterns:
        variables = _detect_pattern_variables(pattern)
        if variables:
            display_name = f"{pattern} 🔧 ({len(variables)} vars)"
        else:
            display_name = pattern
        pattern_display_options.append(display_name)

    # Pattern selection
    selected_display_patterns = []
    try:
        if len(filtered_patterns) <= 10:
            selected_display_patterns = st.pills(
                "Select Patterns",
                pattern_display_options,
                selection_mode="multi",
                key=f"{key}_pills"
            )
        else:
            raise AttributeError("Too many patterns for pills")
    except (AttributeError, TypeError):
        # Fall back to multiselect if pills is not available
        selected_display_patterns = st.multiselect(
            "Select Patterns",
            pattern_display_options,
            key=f"{key}_multiselect"
        )

    # Convert display names back to actual pattern names
    selected_patterns = []
    if selected_display_patterns:
        for display_pattern in selected_display_patterns:
            actual_pattern = display_pattern.split(' 🔧')[0]
            selected_patterns.append(actual_pattern)

    return selected_patterns


@ui_error_boundary
def render_pattern_details(selected_patterns: List[str]) -> None:
    """
    Render detailed pattern information for selected patterns.
    
    Args:
        selected_patterns: List of selected pattern names
    """
    if not selected_patterns:
        return
        
    descriptions_data = _load_pattern_descriptions()
    
    with st.expander("📋 Pattern Details", expanded=False):
        for pattern in selected_patterns:
            pattern_info = _get_pattern_description_and_tags(pattern, descriptions_data)
            
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"### 🎯 {pattern}")
                    
                    # Show description
                    description = pattern_info["description"]
                    if description and description != "No description available":
                        st.markdown(f"**Description:** {description}")
                    else:
                        # Fallback to pattern content preview
                        try:
                            pattern_spec = patterns.load_pattern(pattern)
                            if pattern_spec.content:
                                preview = pattern_spec.content[:200] + "..." if len(pattern_spec.content) > 200 else pattern_spec.content
                                st.markdown(f"**Preview:** {preview}")
                            else:
                                st.info("No description available")
                        except Exception as e:
                            logger.warning(f"Failed to load pattern {pattern}: {e}")
                            st.info("No description available")
                    
                    # Show tags
                    tags = pattern_info["tags"]
                    if tags and len(tags) > 0:
                        if st.session_state.get("show_pattern_categories", False):
                            tag_display = " • ".join(tags)
                            st.caption(f"Categories: {tag_display}")
                        else:
                            st.caption(f"📂 {len(tags)} categories available")
                
                with col2:
                    # Pattern feedback display
                    if pattern in st.session_state.get("pattern_feedback", {}):
                        feedback = st.session_state.pattern_feedback[pattern]
                        if feedback == 1:
                            st.success("👍 Liked")
                        else:
                            st.error("👎 Disliked")
                    
                    # Quick action buttons
                    if st.button("ℹ️ Full Details", key=f"details_{pattern}"):
                        try:
                            pattern_spec = patterns.load_pattern(pattern)
                            with st.expander(f"Full details for {pattern}", expanded=True):
                                st.code(pattern_spec.content, language="markdown")
                        except Exception as e:
                            st.error(f"Failed to load pattern details: {e}")
                
                st.markdown("---")


def _detect_pattern_variables(pattern_name: str) -> List[str]:
    """Detect variables in a pattern by analyzing its content."""
    try:
        pattern_spec = patterns.load_pattern(pattern_name)
        # Simple variable detection - look for {{variable}} patterns
        import re
        variables = re.findall(r'\{\{(\w+)\}\}', pattern_spec.content)
        return list(set(variables))
    except Exception:
        return []


def _load_pattern_descriptions() -> List[Dict[str, Any]]:
    """Load pattern descriptions from JSON file. This should be moved to a service."""
    import json
    import os
    
    try:
        descriptions_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "..", "pattern_descriptions", "pattern_descriptions.json"
        )
        if os.path.exists(descriptions_file):
            with open(descriptions_file, 'r') as f:
                data = json.load(f)
                # Handle different JSON structures
                if isinstance(data, dict) and "patterns" in data:
                    return data["patterns"]
                elif isinstance(data, list):
                    return data
                else:
                    logger.warning("Unknown pattern descriptions format")
                    return []
    except Exception as e:
        logger.warning(f"Failed to load pattern descriptions: {e}")
    
    return []


def _get_all_tags(descriptions_data: List[Dict[str, Any]]) -> List[str]:
    """Get all unique tags from pattern descriptions."""
    all_tags = set()
    for pattern in descriptions_data:
        # Safety check to ensure we're dealing with dictionaries
        if isinstance(pattern, dict):
            tags = pattern.get("tags", [])
            all_tags.update(tags)
    return sorted(list(all_tags))


def _filter_patterns_by_tags(patterns: List[str], selected_tags: List[str], descriptions_data: List[Dict[str, Any]]) -> List[str]:
    """Filter patterns by selected tags."""
    if not selected_tags:
        return patterns

    # Create a mapping of pattern names to their tags
    pattern_tags = {}
    for pattern_data in descriptions_data:
        # Safety check to ensure we're dealing with dictionaries
        if isinstance(pattern_data, dict):
            pattern_name = pattern_data.get("patternName")
            tags = pattern_data.get("tags", [])
            if pattern_name:
                pattern_tags[pattern_name] = tags

    filtered_patterns = []
    for pattern in patterns:
        pattern_tags_list = pattern_tags.get(pattern, [])
        # Check if any of the selected tags match the pattern's tags
        if any(tag in pattern_tags_list for tag in selected_tags):
            filtered_patterns.append(pattern)

    return filtered_patterns


def _get_pattern_description_and_tags(pattern_name: str, descriptions_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Get pattern description and tags from the descriptions data."""
    if descriptions_data is None:
        descriptions_data = _load_pattern_descriptions()

    for pattern in descriptions_data:
        # Safety check to ensure we're dealing with dictionaries
        if isinstance(pattern, dict) and pattern.get("patternName") == pattern_name:
            return {
                "description": pattern.get("description", "No description available"),
                "tags": pattern.get("tags", [])
            }

    # Fallback: try to extract from pattern content
    try:
        pattern_spec = patterns.load_pattern(pattern_name)
        if pattern_spec.content:
            lines = pattern_spec.content.split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and len(line) > 20:
                    return {
                        "description": line[:200] + "..." if len(line) > 200 else line,
                        "tags": ["UNCATEGORIZED"]
                    }
    except Exception:
        pass

    return {
        "description": "No description available",
        "tags": []
    }


def _filter_patterns_by_search_cached(patterns: List[str], search_query: str, search_index: Dict[str, str], descriptions_data: List[Dict[str, Any]]) -> List[str]:
    """Filter patterns by search query using cached search index for better performance."""
    if not search_query:
        return patterns
    
    search_lower = search_query.lower().strip()
    if not search_lower:
        return patterns
    
    # Create description lookup once
    pattern_descriptions = {}
    for pattern_data in descriptions_data:
        if isinstance(pattern_data, dict):
            pattern_name = pattern_data.get("patternName")
            description = pattern_data.get("description", "")
            if pattern_name:
                pattern_descriptions[pattern_name] = description.lower()
    
    filtered_patterns = []
    for pattern in patterns:
        # Check in cached search index (includes name + content)
        searchable_text = search_index.get(pattern, "")
        if search_lower in searchable_text:
            filtered_patterns.append(pattern)
            continue
        
        # Also check description
        description = pattern_descriptions.get(pattern, "")
        if search_lower in description:
            filtered_patterns.append(pattern)
            continue
    
    return filtered_patterns

# Legacy function kept for compatibility
def _filter_patterns_by_search(patterns: List[str], search_query: str, pattern_specs: List[Any], descriptions_data: List[Dict[str, Any]]) -> List[str]:
    """Legacy search function - use _filter_patterns_by_search_cached for better performance."""
    # Get current cache to use the fast method
    try:
        cache = _get_cached_patterns()
        return _filter_patterns_by_search_cached(patterns, search_query, cache["search_index"], descriptions_data)
    except:
        # Fallback to old implementation if cache fails
        return patterns