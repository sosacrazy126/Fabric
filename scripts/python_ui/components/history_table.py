import streamlit as st
from typing import List, Dict, Any
from services import storage
from utils.errors import ui_error_boundary
from datetime import datetime

@ui_error_boundary
def render_output_history() -> None:
    """Render output history table with search and filtering."""
    st.subheader("📋 Output History")
    
    try:
        # Get data from storage and session
        stored_outputs = storage.read_outputs()
        session_outputs = st.session_state.get("output_logs", [])
        
        # Use session state if available (more current), otherwise use storage
        all_outputs = session_outputs if session_outputs else stored_outputs
        
        if not all_outputs:
            st.info("No output history available yet. Run some patterns to see history here!")
            return
        
        # Search and filter controls
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_term = st.text_input(
                "🔍 Search outputs",
                placeholder="Search in patterns, inputs, or outputs...",
                key="history_search"
            )
        
        with col2:
            # Get unique patterns for filter
            unique_patterns = list(set(log.get("pattern", "Unknown") for log in all_outputs))
            selected_pattern = st.selectbox(
                "Filter by pattern",
                ["All"] + sorted(unique_patterns),
                key="history_pattern_filter"
            )
        
        with col3:
            show_count = st.selectbox(
                "Show entries",
                [10, 25, 50, 100, "All"],
                index=1,
                key="history_count"
            )
        
        # Filter outputs based on search and pattern filter
        filtered_outputs = all_outputs.copy()
        
        if search_term:
            search_lower = search_term.lower()
            filtered_outputs = [
                log for log in filtered_outputs
                if (search_lower in log.get("pattern", "").lower() or
                    search_lower in log.get("input", "").lower() or
                    search_lower in log.get("output", "").lower())
            ]
        
        if selected_pattern != "All":
            filtered_outputs = [
                log for log in filtered_outputs
                if log.get("pattern") == selected_pattern
            ]
        
        # Sort by timestamp (newest first) if timestamp available
        try:
            filtered_outputs.sort(
                key=lambda x: datetime.fromisoformat(x.get("timestamp", "1970-01-01T00:00:00")),
                reverse=True
            )
        except (ValueError, TypeError):
            # Fallback to original order if timestamp parsing fails
            pass
        
        # Limit results
        if show_count != "All":
            filtered_outputs = filtered_outputs[:show_count]
        
        # Display summary
        st.write(f"Showing {len(filtered_outputs)} of {len(all_outputs)} total outputs")
        
        # Display outputs
        for i, log in enumerate(filtered_outputs):
            with st.expander(
                f"🎯 {log.get('pattern', 'Unknown')} - {log.get('timestamp', 'Unknown time')}",
                expanded=False
            ):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown("**Pattern:**")
                    st.code(log.get("pattern", "Unknown"), language="text")
                    
                    st.markdown("**Input:**")
                    input_text = log.get("input", "")
                    if len(input_text) > 200:
                        st.text_area("", value=input_text, height=100, key=f"input_{i}", disabled=True)
                    else:
                        st.code(input_text, language="text")
                    
                    st.markdown("**Output:**")
                    output_text = log.get("output", "")
                    if len(output_text) > 500:
                        st.text_area("", value=output_text, height=200, key=f"output_{i}", disabled=True)
                    else:
                        st.markdown(output_text)
                
                with col2:
                    # Action buttons
                    if st.button("📋 Copy Output", key=f"copy_{i}"):
                        try:
                            # Try to copy to clipboard (platform dependent)
                            st.code(output_text, language="text")
                            st.success("Output displayed for copying!")
                        except Exception as e:
                            st.error(f"Copy failed: {str(e)}")
                    
                    # Star/unstar functionality
                    starred_outputs = st.session_state.get("starred_outputs", [])
                    is_starred = any(
                        starred.get("output") == log.get("output") and
                        starred.get("pattern") == log.get("pattern")
                        for starred in starred_outputs
                    )
                    
                    if is_starred:
                        if st.button("⭐ Starred", key=f"unstar_{i}"):
                            # Remove from starred
                            st.session_state.starred_outputs = [
                                starred for starred in starred_outputs
                                if not (starred.get("output") == log.get("output") and
                                       starred.get("pattern") == log.get("pattern"))
                            ]
                            st.success("Removed from starred!")
                            st.rerun()
                    else:
                        if st.button("☆ Star", key=f"star_{i}"):
                            # Add to starred
                            starred_item = {
                                "pattern": log.get("pattern", "Unknown"),
                                "input": log.get("input", ""),
                                "output": log.get("output", ""),
                                "timestamp": log.get("timestamp", datetime.now().isoformat()),
                                "custom_name": f"Starred {log.get('pattern', 'Output')}"
                            }
                            st.session_state.starred_outputs.append(starred_item)
                            st.success("Added to starred!")
                            st.rerun()
                    
                    # Output metrics
                    with st.expander("📈 Metrics", expanded=False):
                        output_text = log.get("output", "")
                        lines = output_text.count('\n') + 1
                        words = len(output_text.split())
                        chars = len(output_text)
                        
                        st.metric("Lines", lines)
                        st.metric("Words", words)
                        st.metric("Characters", chars)
        
    except Exception as e:
        st.error(f"Error loading output history: {str(e)}")

@ui_error_boundary
def render_starred_outputs() -> None:
    """Render starred outputs table."""
    st.subheader("⭐ Starred Outputs")
    
    try:
        # Get starred outputs from session state and storage
        session_starred = st.session_state.get("starred_outputs", [])
        stored_starred = storage.read_starred()
        
        # Use session state if available, otherwise storage
        all_starred = session_starred if session_starred else stored_starred
        
        if not all_starred:
            st.info("No starred outputs yet. Star some outputs from the history to see them here!")
            return
        
        # Sort by timestamp (newest first)
        try:
            all_starred.sort(
                key=lambda x: datetime.fromisoformat(x.get("timestamp", "1970-01-01T00:00:00")),
                reverse=True
            )
        except (ValueError, TypeError):
            pass
        
        st.write(f"Total starred outputs: {len(all_starred)}")
        
        for i, starred in enumerate(all_starred):
            with st.expander(
                f"⭐ {starred.get('custom_name', f'Starred Output #{i+1}')}",
                expanded=False
            ):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Edit name functionality
                    current_name = starred.get('custom_name', f'Starred Output #{i+1}')
                    new_name = st.text_input(
                        "Name:",
                        value=current_name,
                        key=f"starred_name_{i}"
                    )
                    
                    if new_name != current_name:
                        if st.button("💾 Update Name", key=f"update_name_{i}"):
                            starred["custom_name"] = new_name
                            st.success("Name updated!")
                            st.rerun()
                    
                    st.markdown("**Pattern:**")
                    st.code(starred.get("pattern", "Unknown"), language="text")
                    
                    st.markdown("**Input:**")
                    input_text = starred.get("input", "")
                    if len(input_text) > 200:
                        st.text_area("", value=input_text, height=100, key=f"starred_input_{i}", disabled=True)
                    else:
                        st.code(input_text, language="text")
                    
                    st.markdown("**Output:**")
                    output_text = starred.get("output", "")
                    if len(output_text) > 500:
                        st.text_area("", value=output_text, height=200, key=f"starred_output_{i}", disabled=True)
                    else:
                        st.markdown(output_text)
                
                with col2:
                    # Action buttons
                    if st.button("📋 Copy Output", key=f"copy_starred_{i}"):
                        st.code(output_text, language="text")
                        st.success("Output displayed for copying!")
                    
                    if st.button("❌ Remove Star", key=f"remove_star_{i}"):
                        st.session_state.starred_outputs.remove(starred)
                        st.success("Removed from starred!")
                        st.rerun()
                    
                    # Show timestamp
                    st.caption(f"Starred: {starred.get('timestamp', 'Unknown')}")
        
        # Bulk actions
        if len(all_starred) > 1:
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🗑️ Clear All Starred", type="secondary"):
                    st.session_state["confirm_clear_starred"] = True
            
            if st.session_state.get("confirm_clear_starred", False):
                with col2:
                    if st.button("⚠️ Confirm Clear All", type="primary"):
                        st.session_state.starred_outputs = []
                        st.session_state["confirm_clear_starred"] = False
                        st.success("All starred outputs cleared!")
                        st.rerun()
        
    except Exception as e:
        st.error(f"Error loading starred outputs: {str(e)}")

@ui_error_boundary
def render_history_overview() -> None:
    """Render complete history overview with tabs."""
    # Create tabs for different history views
    tab1, tab2 = st.tabs(["📋 All History", "⭐ Starred"])
    
    with tab1:
        render_output_history()
    
    with tab2:
        render_starred_outputs()