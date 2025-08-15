import streamlit as st
from typing import Dict, Any, List
from services import storage
from utils.errors import ui_error_boundary

@ui_error_boundary
def render_execution_stats() -> None:
    """Render execution statistics panel."""
    st.subheader("📊 Execution Statistics")
    
    # Get execution stats from session state (legacy support)
    stats = st.session_state.get("execution_stats", {
        "total_runs": 0,
        "successful_runs": 0,
        "failed_runs": 0,
        "avg_execution_time": 0
    })
    
    # Create metrics columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Runs", stats["total_runs"])
    
    with col2:
        if stats["total_runs"] > 0:
            success_rate = (stats["successful_runs"] / stats["total_runs"]) * 100
            st.metric("Success Rate", f"{success_rate:.1f}%")
        else:
            st.metric("Success Rate", "0.0%")
    
    with col3:
        st.metric("Failed Runs", stats["failed_runs"])
    
    with col4:
        st.metric("Avg Time", f"{stats['avg_execution_time']:.1f}s")

@ui_error_boundary
def render_storage_stats() -> None:
    """Render storage statistics panel."""
    st.subheader("💾 Storage Statistics")
    
    try:
        # Get data from storage
        outputs = storage.read_outputs()
        starred = storage.read_starred()
        
        # Also check session state for current session data
        session_outputs = st.session_state.get("output_logs", [])
        session_starred = st.session_state.get("starred_outputs", [])
        
        # Use session state if available (more current), otherwise use storage
        total_outputs = len(session_outputs) if session_outputs else len(outputs)
        total_starred = len(session_starred) if session_starred else len(starred)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Saved Outputs", total_outputs)
        
        with col2:
            st.metric("Starred Items", total_starred)
        
        with col3:
            # Calculate total characters in outputs
            if session_outputs:
                total_chars = sum(len(log.get("output", "")) for log in session_outputs)
            else:
                total_chars = sum(len(log.get("output", "")) for log in outputs)
            st.metric("Total Characters", f"{total_chars:,}")
        
        with col4:
            # Calculate average output length
            if total_outputs > 0:
                avg_length = total_chars / total_outputs
                st.metric("Avg Length", f"{avg_length:.0f}")
            else:
                st.metric("Avg Length", "0")
                
    except Exception as e:
        st.error(f"Error loading storage statistics: {str(e)}")

@ui_error_boundary
def render_pattern_stats() -> None:
    """Render pattern usage statistics."""
    st.subheader("🎨 Pattern Statistics")
    
    try:
        # Get data from storage and session
        outputs = storage.read_outputs()
        session_outputs = st.session_state.get("output_logs", [])
        
        # Use session state if available, otherwise storage
        all_outputs = session_outputs if session_outputs else outputs
        
        if not all_outputs:
            st.info("No pattern execution data available yet.")
            return
        
        # Count pattern usage
        pattern_counts: Dict[str, int] = {}
        for log in all_outputs:
            pattern = log.get("pattern", "Unknown")
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        # Sort patterns by usage
        sorted_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write("**Most Used Patterns:**")
            for i, (pattern, count) in enumerate(sorted_patterns[:5]):
                st.write(f"{i+1}. **{pattern}**: {count} uses")
        
        with col2:
            st.metric("Unique Patterns", len(pattern_counts))
            if sorted_patterns:
                most_used = sorted_patterns[0]
                st.metric("Top Pattern", f"{most_used[0][:15]}..." if len(most_used[0]) > 15 else most_used[0])
                
    except Exception as e:
        st.error(f"Error loading pattern statistics: {str(e)}")

@ui_error_boundary
def render_stats_overview() -> None:
    """Render complete statistics overview."""
    # Create tabs for different stat categories
    tab1, tab2, tab3 = st.tabs(["📊 Execution", "💾 Storage", "🎨 Patterns"])
    
    with tab1:
        render_execution_stats()
    
    with tab2:
        render_storage_stats()
    
    with tab3:
        render_pattern_stats()