import shutil
import json
import os
import streamlit as st
from subprocess import run, CalledProcessError
from dotenv import load_dotenv
import re
import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from io import StringIO
import uuid

# ... (unchanged helper/util code, OMITTED FOR BREVITY in this artefact to save space, but would be included in a full file overwrite) ...

# --- OMITTING unchanged helpers for brevity, see previous part of file ---

def render_pattern_execution_view():
    """
    Render the UI and logic for the 'Run Patterns' workflow: pattern selection, input, execution, and results.
    """
    try:
        show_welcome_screen()
        patterns = get_patterns()
        logger.debug(f"Available patterns: {patterns}")

        if not patterns:
            logger.warning("No patterns available")
            st.warning("No patterns available. Create a pattern first.")
            return

        tabs = st.tabs(["🚀 Execute", "📊 Analysis"])

        # --- Execute Tab ---
        with tabs[0]:
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            with col1:
                st.header("🎯 Pattern Execution")
            with col2:
                st.metric("Total Runs", st.session_state.execution_stats["total_runs"])
            with col3:
                success_rate = (
                    st.session_state.execution_stats["successful_runs"] /
                    max(st.session_state.execution_stats["total_runs"], 1) * 100
                )
                st.metric("Success Rate", f"{success_rate:.1f}%")
            with col4:
                avg_time = st.session_state.execution_stats["avg_execution_time"]
                st.metric("Avg Time", f"{avg_time:.1f}s")

            st.subheader("🎨 Select Patterns")
            selected_patterns = enhanced_pattern_selector(patterns, "main_patterns")
            st.session_state.selected_patterns = selected_patterns

            with st.expander("📝 Input Content", expanded=True):
                default_input = st.session_state.input_content or ""
                input_text = st.text_area(
                    "Enter input for the selected pattern(s):",
                    value=default_input,
                    height=150,
                    key="pattern_input_main",
                )
                st.session_state.input_content = input_text
                enhance_input_preview()

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📋 Paste from Clipboard", use_container_width=True):
                        success, content, error = get_clipboard_content()
                        if success:
                            st.session_state.input_content = content
                            st.success("Clipboard content pasted!")
                        else:
                            st.error(f"Clipboard error: {error}")

                with col2:
                    if st.button("🧹 Clear Input", use_container_width=True):
                        st.session_state.input_content = ""
                        st.experimental_rerun()

            st.markdown("---")
            chain_mode = st.checkbox(
                "🔗 Chain Mode (Feed output from each pattern into the next)",
                value=False,
                help="Run patterns sequentially, passing the output of each pattern as input to the next.",
            )

            col1, col2, col3 = st.columns(3)
            with col1:
                execute_btn = st.button(
                    "🚀 Execute Patterns",
                    type="primary",
                    use_container_width=True,
                    disabled=not selected_patterns or not st.session_state.input_content.strip(),
                )
            with col2:
                clear_btn = st.button("🧹 Clear Output", use_container_width=True)
            with col3:
                if st.button("📋 Copy All Output", use_container_width=True):
                    content_to_copy = "\n\n".join(st.session_state.chat_output)
                    success, error = set_clipboard_content(content_to_copy)
                    if success:
                        st.success("All output copied to clipboard!", icon="📋")
                    else:
                        st.error(error)

            if execute_btn:
                st.session_state.chat_output = execute_patterns_enhanced(
                    selected_patterns,
                    chain_mode=chain_mode,
                    initial_input=st.session_state.input_content,
                )

            if clear_btn:
                st.session_state.chat_output = []
                st.success("Output cleared.")

            st.markdown("---")
            st.subheader("💬 Pattern Output")

            if st.session_state.chat_output:
                for i, output in enumerate(st.session_state.chat_output):
                    with st.expander(f"Output #{i+1} - {selected_patterns[i] if i < len(selected_patterns) else 'Pattern'}", expanded=False):
                        st.markdown(output)
                        show_pattern_feedback_ui(selected_patterns[i] if i < len(selected_patterns) else "Pattern", output)
            else:
                st.info("No output yet. Run patterns to see results here.")

        # --- Analysis Tab ---
        with tabs[1]:
            st.header("📊 Output Analysis")
            if st.session_state.chat_output:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Outputs", len(st.session_state.chat_output))
                with col2:
                    total_chars = sum(len(output) for output in st.session_state.chat_output)
                    st.metric("Total Characters", f"{total_chars:,}")
                with col3:
                    avg_length = total_chars / len(st.session_state.chat_output)
                    st.metric("Avg Length", f"{avg_length:.0f}")

                search_analysis = st.text_input("🔍 Search in outputs", placeholder="Search content...")
                filtered_outputs = [
                    (i, output) for i, output in enumerate(reversed(st.session_state.chat_output), 1)
                    if not search_analysis or search_analysis.lower() in output.lower()
                ]
                for i, output in filtered_outputs:
                    pattern_name = "Unknown"
                    if output.startswith("### 🎯"):
                        pattern_name = output.split("\n")[0].replace("### 🎯 ", "")
                    elif output.startswith("###"):
                        pattern_name = output.split("\n")[0].replace("### ", "")

                    with st.expander(f"📄 Output #{i} - {pattern_name}", expanded=False):
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            st.markdown(f"**Pattern:** {pattern_name}")
                        with col2:
                            word_count = len(output.split())
                            st.caption(f"Words: {word_count}")
                        with col3:
                            if st.button("📋 Copy", key=f"copy_analysis_{i}"):
                                success, error = set_clipboard_content(output)
                                if success:
                                    st.success("Copied to clipboard!", icon="📋")
                                else:
                                    st.error(error)
                        st.markdown(output)
                        with st.expander("📈 Output Metrics", expanded=False):
                            lines = output.count('\n') + 1
                            chars = len(output)
                            words = len(output.split())
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Lines", lines)
                            with col2:
                                st.metric("Words", words)
                            with col3:
                                st.metric("Characters", chars)
            else:
                st.info("🎯 Run some patterns to see output analysis here.")
    except Exception as e:
        logger.error("Error rendering pattern execution view", exc_info=True)
        st.error(f"Pattern execution view error: {str(e)}")

def render_pattern_management_view():
    """
    Render the UI for pattern creation, editing, deletion, and descriptions management.
    """
    try:
        create_tab, edit_tab, delete_tab, descriptions_tab = st.tabs(["Create", "Edit", "Delete", "📋 Descriptions"])

        with create_tab:
            st.header("Create New Pattern")
            creation_mode = st.radio(
                "Creation Mode",
                ["Simple Editor", "Advanced (Wizard)"],
                key="creation_mode_main",
                horizontal=True,
            )
            if creation_mode == "Simple Editor":
                pattern_creation_ui()
            else:
                pattern_creation_wizard()

        with edit_tab:
            st.header("Edit Patterns")
            patterns = get_patterns()
            if not patterns:
                st.warning("No patterns available. Create a pattern first.")
            else:
                selected_pattern = st.selectbox(
                    "Select Pattern to Edit", [""] + patterns
                )
                if selected_pattern:
                    pattern_editor(selected_pattern)

        with delete_tab:
            st.header("Delete Patterns")
            patterns = get_patterns()
            if not patterns:
                st.warning("No patterns available.")
            else:
                patterns_to_delete = st.multiselect(
                    "Select Patterns to Delete",
                    patterns,
                    key="delete_patterns_selector",
                )
                if patterns_to_delete:
                    st.warning(
                        f"You are about to delete {len(patterns_to_delete)} pattern(s):"
                    )
                    for pattern in patterns_to_delete:
                        st.markdown(f"- {pattern}")
                    confirm_delete = st.checkbox(
                        "I understand that this action cannot be undone"
                    )
                    if st.button(
                        "🗑️ Delete Selected Patterns",
                        type="primary",
                        disabled=not confirm_delete,
                    ):
                        if confirm_delete:
                            for pattern in patterns_to_delete:
                                success, message = delete_pattern(pattern)
                                if success:
                                    st.success(f"✓ {pattern}: {message}")
                                else:
                                    st.error(f"✗ {pattern}: {message}")
                            st.experimental_rerun()
                        else:
                            st.error(
                                "Please confirm deletion by checking the box above."
                            )
                else:
                    st.info("Select one or more patterns to delete.")

        with descriptions_tab:
            show_pattern_management_ui()
    except Exception as e:
        logger.error("Error rendering pattern management view", exc_info=True)
        st.error(f"Pattern management view error: {str(e)}")

def render_analysis_dashboard_view():
    """
    Render the output history and starred outputs dashboard view.
    """
    try:
        st.header("Pattern Output History")
        all_tab, starred_tab = st.tabs(["All Outputs", "⭐ Starred"])
        with all_tab:
            if not st.session_state.output_logs:
                st.info(
                    "No pattern outputs recorded yet. Run some patterns to see their logs here."
                )
            else:
                for i, log in enumerate(reversed(st.session_state.output_logs)):
                    with st.expander(
                        f"Output #{len(st.session_state.output_logs)-i} - {log['pattern_name']} ({log['timestamp']})",
                        expanded=False,
                    ):
                        st.markdown("### Input")
                        st.code(log["input"], language="text")
                        st.markdown("### Output")
                        st.markdown(log["output"])

                        is_starred = any(
                            s["timestamp"] == log["timestamp"]
                            for s in st.session_state.starred_outputs
                        )

                        col1, col2 = st.columns([1, 4])
                        with col1:
                            if not is_starred:
                                if st.button(
                                    "⭐ Star",
                                    key=f"star_{i}",
                                    use_container_width=True,
                                ):
                                    st.session_state.starring_output = (
                                        len(st.session_state.output_logs) - i - 1
                                    )
                                    st.session_state.temp_star_name = ""
                            else:
                                st.write("⭐ Starred")

                        with col2:
                            if st.button("📋 Copy Output", key=f"copy_{i}"):
                                success, error = set_clipboard_content(
                                    log["output"]
                                )
                                if success:
                                    st.success("Output copied to clipboard!")
                                else:
                                    st.error(error)

                        if (
                            st.session_state.starring_output
                            == len(st.session_state.output_logs) - i - 1
                        ):
                            st.markdown("---")
                            with st.form(key=f"star_name_form_{i}"):
                                name_input = st.text_input(
                                    "Enter a name for this output (optional):",
                                    key=f"star_name_input_{i}",
                                )
                                col1, col2 = st.columns(2)
                                with col1:
                                    submit = st.form_submit_button(
                                        "Save", use_container_width=True
                                    )
                                with col2:
                                    cancel = st.form_submit_button(
                                        "Cancel", use_container_width=True
                                    )

                                if submit:
                                    handle_star_name_input(
                                        st.session_state.starring_output, name_input
                                    )
                                    st.session_state.starring_output = None
                                    st.experimental_rerun()
                                elif cancel:
                                    st.session_state.starring_output = None
                                    st.experimental_rerun()
                st.markdown("---")
        with starred_tab:
            if not st.session_state.starred_outputs:
                st.info(
                    "No starred outputs yet. Star some outputs to see them here!"
                )
            else:
                for i, starred in enumerate(st.session_state.starred_outputs):
                    with st.expander(
                        f"⭐ {starred.get('custom_name', f'Starred Output #{i+1}')} ({starred['timestamp']})",
                        expanded=False,
                    ):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(
                                f"### {starred.get('custom_name', f'Starred Output #{i+1}')}"
                            )
                        with col2:
                            if st.button("✏️ Edit Name", key=f"edit_name_{i}"):
                                st.session_state[f"editing_name_{i}"] = True

                        if st.session_state.get(f"editing_name_{i}", False):
                            new_name = st.text_input(
                                "Enter new name:",
                                value=starred.get("custom_name", ""),
                                key=f"new_name_{i}",
                            )
                            col1, col2 = st.columns([1, 1])
                            with col1:
                                if st.button("Save", key=f"save_name_{i}"):
                                    st.session_state.starred_outputs[i][
                                        "custom_name"
                                    ] = new_name
                                    del st.session_state[f"editing_name_{i}"]
                                    st.success("Name updated!")
                                    st.experimental_rerun()
                            with col2:
                                if st.button("Cancel", key=f"cancel_name_{i}"):
                                    del st.session_state[f"editing_name_{i}"]
                                    st.experimental_rerun()

                        st.markdown("### Pattern")
                        st.code(starred["pattern_name"], language="text")
                        st.markdown("### Input")
                        st.code(
                            starred["input"], language="text"
                        )
                        st.markdown("### Output")
                        st.markdown(starred["output"])

                        col1, col2 = st.columns([1, 4])
                        with col1:
                            if st.button("❌ Remove Star", key=f"unstar_{i}"):
                                unstar_output(i)
                                st.success("Output unstarred!")
                                st.experimental_rerun()

                        with col2:
                            if st.button("📋 Copy Output", key=f"copy_starred_{i}"):
                                try:
                                    run(
                                        ["xclip", "-selection", "clipboard"],
                                        input=starred["output"].encode(),
                                        check=True,
                                    )
                                    st.success("Output copied to clipboard!")
                                except Exception as e:
                                    st.error(f"Error copying to clipboard: {e}")

                if st.button("Clear All Starred"):
                    if st.checkbox("Confirm clearing all starred outputs"):
                        st.session_state.starred_outputs = []
                        save_outputs()
                        st.success("All starred outputs cleared!")
                        st.experimental_rerun()
    except Exception as e:
        logger.error("Error rendering analysis dashboard view", exc_info=True)
        st.error(f"Analysis dashboard view error: {str(e)}")

def handle_application_error(e):
    """
    Centralized error logging and Streamlit error presentation.
    """
    logger.error("Unexpected error in application", exc_info=True)
    st.error(f"An unexpected error occurred: {str(e)}")

def main():
    """Main function to run the Streamlit app."""
    logger.info("Starting Fabric Pattern Studio")
    try:
        initialize_app()
        render_header()
        view = setup_sidebar()

        if view == "Run Patterns":
            render_pattern_execution_view()
        elif view == "Pattern Management":
            render_pattern_management_view()
        else:
            render_analysis_dashboard_view()

    except Exception as e:
        handle_application_error(e)
    finally:
        logger.info("Application shutdown")


if __name__ == "__main__":
    logger.info("Application startup")
    main()