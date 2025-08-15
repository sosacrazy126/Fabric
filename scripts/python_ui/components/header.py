import streamlit as st

def render() -> None:
    st.markdown(
        """
        <style>
        .fps-header{background:linear-gradient(90deg,#1f4e79,#2d5a87);padding:12px;border-radius:8px;margin:8px 0 16px}
        .fps-header h1{color:#fff;margin:0;text-align:center;font-weight:700}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="fps-header"><h1>🎭 Fabric Pattern Studio</h1></div>', unsafe_allow_html=True)