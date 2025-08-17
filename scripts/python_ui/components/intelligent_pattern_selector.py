"""
Intelligent pattern selector with AI-powered search, recommendations, and workflow building.
"""
import streamlit as st
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
import pandas as pd

from utils.errors import ui_error_boundary
from utils.logging import logger
from services import patterns
from services.pattern_intelligence import pattern_intelligence, PatternRecommendation
from services.workflow_orchestrator import WorkflowStep, Workflow, ExecutionConfig


@ui_error_boundary
def render_intelligent_pattern_selector(key: str = "intelligent_selector") -> Dict[str, Any]:
    """
    Render intelligent pattern selector with AI-powered recommendations and workflow building.
    
    Returns:
        Dict containing selected patterns, workflow config, and metadata
    """
    
    # Initialize session state
    _initialize_selector_state(key)
    
    # Main UI sections
    st.subheader("🧠 Intelligent Pattern Discovery")
    
    # Search and discovery section
    selected_patterns = _render_search_and_discovery_section(key)
    
    # AI Recommendations section
    recommendations = _render_recommendations_section(key, selected_patterns)
    
    # Workflow builder section
    workflow_config = _render_workflow_builder_section(key, selected_patterns)
    
    # Pattern insights section
    if selected_patterns:
        _render_pattern_insights_section(selected_patterns)
    
    return {
        "selected_patterns": selected_patterns,
        "recommendations": recommendations,
        "workflow_config": workflow_config,
        "session_key": key
    }


@ui_error_boundary
def _render_search_and_discovery_section(key: str) -> List[str]:
    """Render the search and pattern discovery section."""
    
    # Search methods tabs
    search_tab, browse_tab, history_tab = st.tabs(["🔍 Smart Search", "📂 Browse", "📚 History"])
    
    selected_patterns = []
    
    with search_tab:
        selected_patterns.extend(_render_smart_search_ui(key))
    
    with browse_tab:
        selected_patterns.extend(_render_browse_patterns_ui(key))
    
    with history_tab:
        selected_patterns.extend(_render_pattern_history_ui(key))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_patterns = []
    for pattern in selected_patterns:
        if pattern not in seen:
            seen.add(pattern)
            unique_patterns.append(pattern)
    
    return unique_patterns


@ui_error_boundary
def _render_smart_search_ui(key: str) -> List[str]:
    """Render smart search UI with semantic search capabilities."""
    
    # Search input with suggestions
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input(
            "🔍 Search patterns with natural language",
            placeholder="e.g., 'analyze code quality', 'write documentation', 'extract key insights'",
            key=f"{key}_search_query",
            help="Use natural language to describe what you want to do"
        )
    
    with col2:
        search_mode = st.selectbox(
            "Search Mode",
            ["Semantic", "Keyword", "Hybrid"],
            key=f"{key}_search_mode",
            help="Semantic: AI-powered meaning search, Keyword: exact word matching, Hybrid: both"
        )
    
    selected_patterns = []
    
    if search_query:
        # Apply search filters
        with st.expander("🎛️ Search Filters", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                complexity_filter = st.slider(
                    "Max Complexity",
                    0.0, 1.0, 1.0,
                    key=f"{key}_complexity_filter",
                    help="Filter by pattern complexity (0=simple, 1=complex)"
                )
            
            with col2:
                execution_time_filter = st.slider(
                    "Max Execution Time (s)",
                    0, 300, 300,
                    key=f"{key}_time_filter",
                    help="Filter by estimated execution time"
                )
            
            with col3:
                categories = _get_available_categories()
                category_filter = st.multiselect(
                    "Categories",
                    categories,
                    key=f"{key}_category_filter",
                    help="Filter by pattern categories"
                )
        
        # Perform search
        filters = {
            "max_complexity": complexity_filter,
            "max_execution_time": execution_time_filter,
            "category": category_filter if category_filter else None
        }
        
        try:
            if search_mode == "Semantic":
                search_results = pattern_intelligence.search_patterns_semantic(
                    search_query, limit=10, filters=filters
                )
            else:
                # Fallback to keyword search for now
                search_results = pattern_intelligence.search_patterns_semantic(
                    search_query, limit=10, filters=filters
                )
            
            if search_results:
                st.markdown("### 🎯 Search Results")
                
                # Display search results with enhanced UI
                for i, (pattern_name, relevance_score) in enumerate(search_results):
                    with st.container():
                        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                        
                        with col1:
                            # Pattern info
                            analytics = pattern_intelligence.analyze_pattern_usage(pattern_name)
                            category = pattern_intelligence.categorize_pattern(pattern_name)
                            
                            st.markdown(f"**{pattern_name}**")
                            st.caption(f"📁 {category} • ⭐ {analytics.success_rate:.1%} success • ⏱️ {analytics.avg_execution_time:.1f}s avg")
                        
                        with col2:
                            st.metric("Relevance", f"{relevance_score:.1%}")
                        
                        with col3:
                            st.metric("Complexity", f"{analytics.complexity_score:.1f}")
                        
                        with col4:
                            if st.button(
                                "➕ Add",
                                key=f"{key}_add_{pattern_name}_{i}",
                                use_container_width=True
                            ):
                                if pattern_name not in selected_patterns:
                                    selected_patterns.append(pattern_name)
                                    st.toast(f"Added {pattern_name}", icon="✅")
                                    st.rerun()
                        
                        st.markdown("---")
            else:
                st.info("No patterns found matching your search. Try different keywords or adjust filters.")
                
        except Exception as e:
            logger.error(f"Search failed: {e}")
            st.error(f"Search failed: {e}")
    
    return selected_patterns


@ui_error_boundary
def _render_browse_patterns_ui(key: str) -> List[str]:
    """Render pattern browsing UI with categorization."""
    
    selected_patterns = []
    
    try:
        pattern_specs = patterns.list_patterns()
        if not pattern_specs:
            st.warning("No patterns available")
            return selected_patterns
        
        # Group patterns by category
        categorized_patterns = {}
        for spec in pattern_specs:
            category = pattern_intelligence.categorize_pattern(spec.name)
            if category not in categorized_patterns:
                categorized_patterns[category] = []
            categorized_patterns[category].append(spec.name)
        
        # Display categories
        for category, pattern_list in sorted(categorized_patterns.items()):
            with st.expander(f"📁 {category} ({len(pattern_list)} patterns)", expanded=False):
                
                # Show category patterns in a grid
                cols = st.columns(3)
                for i, pattern_name in enumerate(pattern_list):
                    col = cols[i % 3]
                    
                    with col:
                        analytics = pattern_intelligence.analyze_pattern_usage(pattern_name)
                        
                        # Pattern card
                        with st.container():
                            st.markdown(f"**{pattern_name}**")
                            
                            # Quick stats
                            col_stat1, col_stat2 = st.columns(2)
                            with col_stat1:
                                st.caption(f"⭐ {analytics.success_rate:.1%}")
                            with col_stat2:
                                st.caption(f"⏱️ {analytics.avg_execution_time:.1f}s")
                            
                            # Add button
                            if st.button(
                                "➕ Add",
                                key=f"{key}_browse_add_{pattern_name}",
                                use_container_width=True
                            ):
                                if pattern_name not in selected_patterns:
                                    selected_patterns.append(pattern_name)
                                    st.toast(f"Added {pattern_name}", icon="✅")
                                    st.rerun()
                        
                        st.markdown("---")
        
    except Exception as e:
        logger.error(f"Pattern browsing failed: {e}")
        st.error(f"Failed to load patterns: {e}")
    
    return selected_patterns


@ui_error_boundary
def _render_pattern_history_ui(key: str) -> List[str]:
    """Render pattern usage history UI."""
    
    selected_patterns = []
    
    # Get user's recent patterns
    try:
        # Show trending patterns
        trending = pattern_intelligence.get_trending_patterns(days=7, limit=10)
        
        if trending:
            st.markdown("### 📈 Trending Patterns (Last 7 days)")
            
            for pattern_name, usage_count in trending:
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    analytics = pattern_intelligence.analyze_pattern_usage(pattern_name)
                    category = pattern_intelligence.categorize_pattern(pattern_name)
                    st.markdown(f"**{pattern_name}**")
                    st.caption(f"📁 {category} • {usage_count} uses this week")
                
                with col2:
                    st.metric("Success Rate", f"{analytics.success_rate:.1%}")
                
                with col3:
                    if st.button(
                        "➕ Add",
                        key=f"{key}_trending_{pattern_name}",
                        use_container_width=True
                    ):
                        if pattern_name not in selected_patterns:
                            selected_patterns.append(pattern_name)
                            st.toast(f"Added {pattern_name}", icon="✅")
                            st.rerun()
        else:
            st.info("No usage history available yet. Start using patterns to see trends!")
        
        # Show recently used patterns (if we had user session data)
        st.markdown("### ⏰ Recently Used")
        st.info("Recently used patterns will appear here based on your session history.")
        
    except Exception as e:
        logger.error(f"History loading failed: {e}")
        st.error(f"Failed to load pattern history: {e}")
    
    return selected_patterns


@ui_error_boundary
def _render_recommendations_section(key: str, selected_patterns: List[str]) -> List[PatternRecommendation]:
    """Render AI-powered pattern recommendations."""
    
    st.markdown("---")
    st.subheader("🤖 AI Recommendations")
    
    recommendations = []
    
    try:
        # Get input context for recommendations
        input_content = st.session_state.get("input_content", "")
        
        # Generate recommendations
        if input_content or selected_patterns:
            recommendations = pattern_intelligence.recommend_patterns(
                context=input_content,
                current_patterns=selected_patterns,
                limit=5
            )
        
        if recommendations:
            st.markdown("### 💡 Suggested Patterns")
            
            for i, rec in enumerate(recommendations):
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{rec.pattern_name}**")
                        st.caption(f"📁 {rec.category}")
                        st.caption(f"💭 {rec.reason}")
                    
                    with col2:
                        confidence_color = "green" if rec.confidence_score > 0.7 else "orange" if rec.confidence_score > 0.4 else "red"
                        st.markdown(f":{confidence_color}[{rec.confidence_score:.1%}]")
                        st.caption("Confidence")
                    
                    with col3:
                        st.metric("Est. Time", f"{rec.estimated_execution_time:.1f}s")
                    
                    with col4:
                        if st.button(
                            "➕ Add",
                            key=f"{key}_rec_{rec.pattern_name}_{i}",
                            use_container_width=True
                        ):
                            if rec.pattern_name not in selected_patterns:
                                selected_patterns.append(rec.pattern_name)
                                st.toast(f"Added {rec.pattern_name}", icon="✅")
                                st.rerun()
                    
                    st.markdown("---")
        else:
            st.info("💡 Add some input content or select patterns to get AI recommendations!")
    
    except Exception as e:
        logger.error(f"Recommendations failed: {e}")
        st.error(f"Failed to generate recommendations: {e}")
    
    return recommendations


@ui_error_boundary
def _render_workflow_builder_section(key: str, selected_patterns: List[str]) -> Dict[str, Any]:
    """Render workflow configuration and building section."""
    
    if not selected_patterns:
        return {}
    
    st.markdown("---")
    st.subheader("🔧 Workflow Builder")
    
    # Workflow configuration
    col1, col2 = st.columns(2)
    
    with col1:
        execution_mode = st.selectbox(
            "Execution Mode",
            ["Sequential", "Parallel (where possible)", "Custom Workflow"],
            key=f"{key}_execution_mode",
            help="Choose how patterns should be executed"
        )
    
    with col2:
        auto_optimize = st.toggle(
            "🚀 Auto-optimize workflow",
            key=f"{key}_auto_optimize",
            help="Let AI optimize the pattern order and execution strategy"
        )
    
    # Pattern ordering and configuration
    if execution_mode == "Sequential":
        workflow_config = _render_sequential_workflow_config(key, selected_patterns)
    elif execution_mode == "Parallel (where possible)":
        workflow_config = _render_parallel_workflow_config(key, selected_patterns)
    else:  # Custom Workflow
        workflow_config = _render_custom_workflow_config(key, selected_patterns)
    
    # Workflow optimization suggestions
    if auto_optimize and len(selected_patterns) > 1:
        _render_optimization_suggestions(key, selected_patterns)
    
    return workflow_config


@ui_error_boundary
def _render_sequential_workflow_config(key: str, selected_patterns: List[str]) -> Dict[str, Any]:
    """Render sequential workflow configuration."""
    
    st.markdown("#### 📋 Pattern Execution Order")
    
    # Create reorderable list
    pattern_df = pd.DataFrame({
        "Order": range(1, len(selected_patterns) + 1),
        "Pattern": selected_patterns,
        "Category": [pattern_intelligence.categorize_pattern(p) for p in selected_patterns],
        "Est. Time (s)": [pattern_intelligence.analyze_pattern_usage(p).avg_execution_time for p in selected_patterns],
        "Success Rate": [f"{pattern_intelligence.analyze_pattern_usage(p).success_rate:.1%}" for p in selected_patterns]
    })
    
    edited_df = st.data_editor(
        pattern_df,
        use_container_width=True,
        key=f"{key}_pattern_order",
        hide_index=True,
        column_config={
            "Order": st.column_config.NumberColumn("Order", width="small"),
            "Pattern": st.column_config.TextColumn("Pattern Name"),
            "Category": st.column_config.TextColumn("Category", width="medium"),
            "Est. Time (s)": st.column_config.NumberColumn("Est. Time (s)", width="small"),
            "Success Rate": st.column_config.TextColumn("Success Rate", width="small")
        }
    )
    
    # Update order if changed
    new_order = edited_df["Pattern"].tolist()
    
    return {
        "mode": "sequential",
        "pattern_order": new_order,
        "total_estimated_time": sum(edited_df["Est. Time (s)"]),
        "config": ExecutionConfig()
    }


@ui_error_boundary
def _render_parallel_workflow_config(key: str, selected_patterns: List[str]) -> Dict[str, Any]:
    """Render parallel workflow configuration."""
    
    st.markdown("#### ⚡ Parallel Execution Groups")
    
    # Analyze which patterns can run in parallel
    parallel_groups = []
    sequential_patterns = []
    
    for pattern in selected_patterns:
        relationships = pattern_intelligence.get_pattern_relationships(pattern)
        has_dependencies = any(rel.relationship_type == "sequential" for rel in relationships)
        
        if has_dependencies:
            sequential_patterns.append(pattern)
        else:
            # Group independent patterns
            parallel_groups.append(pattern)
    
    # Display grouping
    if parallel_groups:
        st.success(f"✅ {len(parallel_groups)} patterns can run in parallel:")
        for pattern in parallel_groups:
            st.write(f"  • {pattern}")
    
    if sequential_patterns:
        st.info(f"ℹ️ {len(sequential_patterns)} patterns must run sequentially:")
        for pattern in sequential_patterns:
            st.write(f"  • {pattern}")
    
    # Estimated time savings
    total_sequential_time = sum(
        pattern_intelligence.analyze_pattern_usage(p).avg_execution_time 
        for p in selected_patterns
    )
    
    parallel_time = max(
        [pattern_intelligence.analyze_pattern_usage(p).avg_execution_time for p in parallel_groups] + [0]
    )
    sequential_time = sum(
        pattern_intelligence.analyze_pattern_usage(p).avg_execution_time 
        for p in sequential_patterns
    )
    
    estimated_total_time = parallel_time + sequential_time
    time_savings = total_sequential_time - estimated_total_time
    
    if time_savings > 0:
        st.metric("⏱️ Estimated Time Savings", f"{time_savings:.1f}s")
    
    return {
        "mode": "parallel",
        "parallel_groups": [parallel_groups] if parallel_groups else [],
        "sequential_patterns": sequential_patterns,
        "estimated_time": estimated_total_time,
        "time_savings": time_savings,
        "config": ExecutionConfig()
    }


@ui_error_boundary
def _render_custom_workflow_config(key: str, selected_patterns: List[str]) -> Dict[str, Any]:
    """Render custom workflow configuration with advanced options."""
    
    st.markdown("#### 🎯 Custom Workflow Configuration")
    
    workflow_steps = []
    
    for i, pattern in enumerate(selected_patterns):
        with st.expander(f"🔧 Configure: {pattern}", expanded=i == 0):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Execution conditions
                has_condition = st.checkbox(
                    "Conditional execution",
                    key=f"{key}_condition_{pattern}",
                    help="Only run this pattern if certain conditions are met"
                )
                
                condition_logic = None
                if has_condition:
                    condition_logic = st.text_input(
                        "Condition (Python expression)",
                        placeholder="len(previous_output) > 100",
                        key=f"{key}_condition_logic_{pattern}"
                    )
            
            with col2:
                # Parallel grouping
                parallel_group = st.text_input(
                    "Parallel group (optional)",
                    placeholder="group_1",
                    key=f"{key}_parallel_group_{pattern}",
                    help="Patterns with the same group name will run in parallel"
                )
            
            with col3:
                # Retry configuration
                max_retries = st.number_input(
                    "Max retries",
                    min_value=1,
                    max_value=5,
                    value=3,
                    key=f"{key}_retries_{pattern}"
                )
            
            # Advanced options
            with st.expander("Advanced Options", expanded=False):
                timeout = st.number_input(
                    "Timeout (seconds)",
                    min_value=10,
                    max_value=600,
                    value=90,
                    key=f"{key}_timeout_{pattern}"
                )
                
                depends_on = st.multiselect(
                    "Depends on patterns",
                    [p for p in selected_patterns if p != pattern],
                    key=f"{key}_depends_{pattern}",
                    help="This pattern will only run after the selected patterns complete"
                )
            
            # Create workflow step
            step = WorkflowStep(
                id=f"step_{i}",
                pattern=pattern,
                condition=None,  # Would implement condition parsing
                parallel_group=parallel_group if parallel_group else None,
                timeout=timeout,
                depends_on=depends_on
            )
            workflow_steps.append(step)
    
    return {
        "mode": "custom",
        "steps": workflow_steps,
        "config": ExecutionConfig()
    }


@ui_error_boundary
def _render_optimization_suggestions(key: str, selected_patterns: List[str]) -> None:
    """Render workflow optimization suggestions."""
    
    try:
        suggestions = pattern_intelligence.suggest_workflow_optimizations(
            selected_patterns
        )
        
        if suggestions:
            st.markdown("#### 🚀 Optimization Suggestions")
            
            for i, suggestion in enumerate(suggestions):
                severity_color = {
                    "low": "blue",
                    "medium": "orange", 
                    "high": "red"
                }.get(suggestion["severity"], "gray")
                
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f":{severity_color}[{suggestion['title']}]")
                        st.caption(suggestion["description"])
                    
                    with col2:
                        if st.button(
                            "Apply",
                            key=f"{key}_apply_suggestion_{i}",
                            use_container_width=True
                        ):
                            _apply_optimization_suggestion(suggestion, key)
                            st.rerun()
        
    except Exception as e:
        logger.error(f"Optimization suggestions failed: {e}")


@ui_error_boundary
def _render_pattern_insights_section(selected_patterns: List[str]) -> None:
    """Render insights about selected patterns."""
    
    if not selected_patterns:
        return
    
    st.markdown("---")
    st.subheader("📊 Pattern Insights")
    
    # Overall workflow metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_time = sum(
            pattern_intelligence.analyze_pattern_usage(p).avg_execution_time 
            for p in selected_patterns
        )
        st.metric("Total Est. Time", f"{total_time:.1f}s")
    
    with col2:
        avg_success_rate = sum(
            pattern_intelligence.analyze_pattern_usage(p).success_rate 
            for p in selected_patterns
        ) / len(selected_patterns)
        st.metric("Avg Success Rate", f"{avg_success_rate:.1%}")
    
    with col3:
        categories = set(pattern_intelligence.categorize_pattern(p) for p in selected_patterns)
        st.metric("Categories", len(categories))
    
    with col4:
        avg_complexity = sum(
            pattern_intelligence.analyze_pattern_usage(p).complexity_score 
            for p in selected_patterns
        ) / len(selected_patterns)
        st.metric("Avg Complexity", f"{avg_complexity:.1f}")
    
    # Pattern relationship visualization
    with st.expander("🔗 Pattern Relationships", expanded=False):
        relationships_found = False
        
        for pattern in selected_patterns:
            relationships = pattern_intelligence.get_pattern_relationships(pattern)
            related_in_selection = [
                rel for rel in relationships 
                if (rel.pattern_a in selected_patterns and rel.pattern_b in selected_patterns)
            ]
            
            if related_in_selection:
                relationships_found = True
                st.markdown(f"**{pattern}:**")
                for rel in related_in_selection:
                    other_pattern = rel.pattern_b if rel.pattern_a == pattern else rel.pattern_a
                    rel_icon = {"sequential": "➡️", "complementary": "🤝", "alternative": "🔄"}.get(rel.relationship_type, "🔗")
                    st.write(f"  {rel_icon} {rel.relationship_type.title()} with {other_pattern}")
        
        if not relationships_found:
            st.info("No relationships detected between selected patterns.")


# Helper functions

def _initialize_selector_state(key: str) -> None:
    """Initialize session state for the selector."""
    if f"{key}_initialized" not in st.session_state:
        st.session_state[f"{key}_initialized"] = True
        st.session_state[f"{key}_selected_patterns"] = []


def _get_available_categories() -> List[str]:
    """Get list of available pattern categories."""
    try:
        pattern_specs = patterns.list_patterns()
        categories = set()
        for spec in pattern_specs:
            category = pattern_intelligence.categorize_pattern(spec.name)
            categories.add(category)
        return sorted(list(categories))
    except Exception:
        return ["ANALYSIS", "WRITING", "CODING", "SUMMARY", "EXTRACTION", "TRANSFORMATION"]


def _apply_optimization_suggestion(suggestion: Dict[str, Any], key: str) -> None:
    """Apply an optimization suggestion."""
    suggestion_type = suggestion.get("type")
    
    if suggestion_type == "reorder_patterns":
        # Update session state with new order
        new_order = suggestion.get("suggested_order", [])
        st.session_state[f"{key}_optimized_order"] = new_order
        st.toast("Pattern order optimized!", icon="🚀")
    
    elif suggestion_type == "parallel_execution":
        # Enable parallel execution for suggested patterns
        parallel_patterns = suggestion.get("parallel_patterns", [])
        st.session_state[f"{key}_parallel_patterns"] = parallel_patterns
        st.toast("Parallel execution enabled!", icon="⚡")
    
    elif suggestion_type == "consolidate_patterns":
        # Suggest pattern consolidation
        st.toast("Pattern consolidation suggestion noted!", icon="💡")
    
    else:
        st.toast("Optimization applied!", icon="✅")