import streamlit as st
from utils.errors import ui_error_boundary
from components import stats_panel, history_table

@ui_error_boundary
def render() -> None:
    st.header("📊 Analysis Dashboard")
    
    # Welcome message and overview
    st.markdown("""
    Welcome to the Analysis Dashboard! Here you can monitor your pattern execution statistics,
    review output history, and manage your starred outputs.
    """)
    
    # Quick overview metrics at the top
    st.markdown("### 📈 Quick Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    # Get basic stats for quick overview
    execution_stats = st.session_state.get("execution_stats", {})
    output_logs = st.session_state.get("output_logs", [])
    starred_outputs = st.session_state.get("starred_outputs", [])
    
    with col1:
        total_runs = execution_stats.get("total_runs", 0)
        st.metric("Total Executions", total_runs)
    
    with col2:
        success_rate = 0
        if total_runs > 0:
            successful = execution_stats.get("successful_runs", 0)
            success_rate = (successful / total_runs) * 100
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    with col3:
        st.metric("Saved Outputs", len(output_logs))
    
    with col4:
        st.metric("Starred Items", len(starred_outputs))
    
    st.markdown("---")
    
    # Main dashboard content with tabs
    tab1, tab2 = st.tabs(["📊 Statistics", "📋 History & Outputs"])
    
    with tab1:
        # Detailed statistics using the stats panel component
        stats_panel.render_stats_overview()
    
    with tab2:
        # History and starred outputs using the history table component
        history_table.render_history_overview()
    
    # Additional dashboard features
    st.markdown("---")
    st.markdown("### ⚙️ Dashboard Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh Data", use_container_width=True):
            # Force refresh by clearing any cached data
            st.cache_data.clear()
            st.success("Dashboard data refreshed!")
            st.rerun()
    
    with col2:
        if st.button("📊 Export Stats", use_container_width=True):
            # Show stats in a format that can be copied
            stats = st.session_state.get("execution_stats", {})
            stats_text = f"""
Fabric Pattern Studio Statistics
================================
Total Executions: {stats.get('total_runs', 0)}
Successful Runs: {stats.get('successful_runs', 0)}
Failed Runs: {stats.get('failed_runs', 0)}
Average Time: {stats.get('avg_execution_time', 0):.2f}s
Saved Outputs: {len(output_logs)}
Starred Items: {len(starred_outputs)}
            """.strip()
            st.code(stats_text, language="text")
            st.info("Copy the statistics above to save or share them.")
    
    with col3:
        if st.button("🗑️ Clear Session Data", use_container_width=True, type="secondary"):
            st.session_state["show_clear_warning"] = True
    
    # Clear data confirmation
    if st.session_state.get("show_clear_warning", False):
        st.warning("⚠️ This will clear all execution statistics and session data (but not saved outputs).")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("⚠️ Confirm Clear", type="primary"):
                # Clear session statistics but preserve saved outputs
                st.session_state.execution_stats = {
                    "total_runs": 0,
                    "successful_runs": 0,
                    "failed_runs": 0,
                    "avg_execution_time": 0
                }
                st.session_state["show_clear_warning"] = False
                st.success("Session statistics cleared!")
                st.rerun()
        
        with col2:
            if st.button("❌ Cancel"):
                st.session_state["show_clear_warning"] = False
                st.rerun()