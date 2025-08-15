import streamlit as st

def render_sidebar(status: dict = None) -> str:
    st.sidebar.title("Fabric Studio")
    if status:
        st.sidebar.markdown(f"**Fabric:** {'✅' if status.get('fabric_installed') else '❌'}  {status.get('version','–')}")
        st.sidebar.caption(f"{status.get('vendor_count',0)} vendors • {status.get('pattern_count',0)} patterns")
    view = st.sidebar.radio(
        "View", ["Prompt Hub", "Pattern Management", "Analysis", "Settings"]
    )
    return view