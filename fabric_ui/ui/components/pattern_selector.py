import streamlit as st
from typing import List, Optional
from fabric_ui.core.pattern_manager import PatternInfo

def render_pattern_selector(patterns: List[PatternInfo]) -> Optional[PatternInfo]:
    if not patterns:
        st.warning("No patterns found.")
        return None

    search = st.text_input("🔍 Search patterns", "")
    filtered = patterns
    if search:
        search_l = search.lower()
        filtered = [p for p in patterns if search_l in p.name.lower() or search_l in p.display_name.lower() or search_l in p.description.lower() or any(search_l in tag.lower() for tag in p.tags)]

    categories = sorted(set(p.category for p in filtered))
    if len(categories) > 1:
        cat = st.selectbox("Category", options=["All"] + categories)
        if cat != "All":
            filtered = [p for p in filtered if p.category == cat]
    else:
        cat = None

    if not filtered:
        st.info("No patterns match.")
        return None

    options = [f"{p.display_name}" for p in filtered]
    idx = st.selectbox("Select a pattern", options=list(range(len(options))), format_func=lambda i: options[i])
    selected = filtered[idx]

    with st.expander("Pattern details", expanded=False):
        st.markdown(f"**Name:** {selected.name}")
        st.markdown(f"**Description:** {selected.description}")
        st.markdown(f"**Category:** {selected.category}")
        st.markdown(f"**Tags:** {', '.join(selected.tags)}")
        st.markdown(f"**Has user.md:** {'✅' if selected.has_user else '❌'}")
        st.markdown(f"**Estimated tokens:** {selected.est_tokens}")

    return selected