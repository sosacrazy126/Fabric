import streamlit as st
from utils.errors import ui_error_boundary
from services import patterns
from utils.typing import PatternSpec
from utils.logging import logger

@ui_error_boundary
def render(pattern_name: str) -> None:
    """Render the pattern editor interface for a specific pattern."""
    if not pattern_name:
        st.warning("No pattern selected for editing.")
        return
    
    try:
        # Load the pattern
        pattern_spec = patterns.load_pattern(pattern_name)
        
        # Show pattern info
        st.markdown(f"### Editing Pattern: **{pattern_name}**")
        
        # Pattern validation
        _show_pattern_validation(pattern_spec)
        
        # Edit mode selection
        edit_mode = st.radio(
            "Edit Mode",
            ["Simple Editor", "Advanced (Wizard)"],
            key=f"edit_mode_{pattern_name}",
            horizontal=True,
        )
        
        if edit_mode == "Simple Editor":
            _render_simple_editor(pattern_spec)
        else:
            _render_wizard_editor(pattern_spec)
            
    except FileNotFoundError:
        st.error(f"Pattern '{pattern_name}' not found.")
    except Exception as e:
        st.error(f"Error loading pattern: {e}")
        logger.error(f"Error loading pattern {pattern_name}: {e}", exc_info=True)

def _show_pattern_validation(pattern_spec: PatternSpec) -> None:
    """Show pattern validation status."""
    content = pattern_spec.content.lower()
    required_sections = ["# identity", "# steps", "# output"]
    missing_sections = [section for section in required_sections if section not in content]
    
    if not missing_sections:
        st.success("✅ Pattern structure is valid")
    else:
        st.warning(f"⚠️ Missing sections: {', '.join(missing_sections)}")

@ui_error_boundary
def _render_simple_editor(pattern_spec: PatternSpec) -> None:
    """Render the simple text editor interface."""
    st.subheader("Simple Text Editor")
    
    # Text area for editing
    edited_content = st.text_area(
        "Pattern Content",
        value=pattern_spec.content,
        height=400,
        key=f"simple_editor_{pattern_spec.name}",
        help="Edit the pattern content directly in Markdown format"
    )
    
    # Show changes indicator
    if edited_content != pattern_spec.content:
        st.info("📝 Content has been modified")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("💾 Save Changes", type="primary", key=f"save_simple_{pattern_spec.name}"):
                _save_pattern_changes(pattern_spec.name, edited_content)
        
        with col2:
            if st.button("🔄 Reset", key=f"reset_simple_{pattern_spec.name}"):
                st.rerun()
    else:
        st.success("✅ No changes to save")

@ui_error_boundary
def _render_wizard_editor(pattern_spec: PatternSpec) -> None:
    """Render the wizard-based editor interface."""
    st.subheader("Advanced Wizard Editor")
    
    # Parse existing content into sections
    sections = _parse_pattern_sections(pattern_spec.content)
    
    # Initialize session state for editing
    for section_name, content in sections.items():
        key = f"edit_{pattern_spec.name}_{section_name.lower().replace(' ', '_')}"
        if key not in st.session_state:
            st.session_state[key] = content
    
    # Section selector
    section_names = list(sections.keys())
    if not section_names:
        section_names = ["IDENTITY and PURPOSE", "GOAL", "STEPS", "OUTPUT INSTRUCTIONS"]
    
    current_section = st.radio(
        "Edit Section",
        section_names,
        key=f"wizard_section_{pattern_spec.name}",
        horizontal=True
    )
    
    # Section editor
    section_key = f"edit_{pattern_spec.name}_{current_section.lower().replace(' ', '_')}"
    
    section_content = st.text_area(
        f"Edit {current_section}",
        value=st.session_state.get(section_key, ""),
        height=300,
        key=f"wizard_editor_{pattern_spec.name}_{current_section}",
        help=f"Edit the {current_section} section content"
    )
    
    # Update session state
    st.session_state[section_key] = section_content
    
    # Preview complete pattern
    with st.expander("Preview Complete Pattern", expanded=False):
        rebuilt_content = _rebuild_pattern_content(pattern_spec.name, section_names)
        st.code(rebuilt_content, language="markdown")
    
    # Check for changes
    rebuilt_content = _rebuild_pattern_content(pattern_spec.name, section_names)
    has_changes = rebuilt_content.strip() != pattern_spec.content.strip()
    
    if has_changes:
        st.info("📝 Content has been modified")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("💾 Save Changes", type="primary", key=f"save_wizard_{pattern_spec.name}"):
                _save_pattern_changes(pattern_spec.name, rebuilt_content)
        
        with col2:
            if st.button("🔄 Reset", key=f"reset_wizard_{pattern_spec.name}"):
                # Clear session state for this pattern
                for section_name in section_names:
                    key = f"edit_{pattern_spec.name}_{section_name.lower().replace(' ', '_')}"
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
    else:
        st.success("✅ No changes to save")

def _parse_pattern_sections(content: str) -> dict:
    """Parse pattern content into sections."""
    sections = {}
    current_section = None
    current_content = []
    
    for line in content.split('\n'):
        if line.strip().startswith('# '):
            # Save previous section
            if current_section is not None:
                sections[current_section] = '\n'.join(current_content).strip()
            
            # Start new section
            current_section = line.strip()[2:].strip()
            current_content = []
        else:
            current_content.append(line)
    
    # Save last section
    if current_section is not None:
        sections[current_section] = '\n'.join(current_content).strip()
    
    return sections

def _rebuild_pattern_content(pattern_name: str, section_names: list) -> str:
    """Rebuild pattern content from session state sections."""
    content_parts = []
    
    for section_name in section_names:
        key = f"edit_{pattern_name}_{section_name.lower().replace(' ', '_')}"
        section_content = st.session_state.get(key, "")
        
        content_parts.append(f"# {section_name}")
        if section_content.strip():
            content_parts.append(section_content.strip())
        content_parts.append("")  # Empty line between sections
    
    return '\n'.join(content_parts).strip()

def _save_pattern_changes(pattern_name: str, new_content: str) -> None:
    """Save pattern changes."""
    try:
        spec = PatternSpec(
            name=pattern_name,
            path=None,  # Will be set by save_pattern
            content=new_content
        )
        patterns.save_pattern(spec)
        st.success(f"✅ Pattern '{pattern_name}' saved successfully!")
        
        # Clear any editing session state
        keys_to_remove = [key for key in st.session_state.keys() if f"edit_{pattern_name}_" in key]
        for key in keys_to_remove:
            del st.session_state[key]
        
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error saving pattern: {e}")
        logger.error(f"Error saving pattern {pattern_name}: {e}", exc_info=True)