import functools, traceback
import streamlit as st
from utils.logging import logger

class FabricUIError(Exception): ...
class ValidationError(FabricUIError): ...
class ExecutionError(FabricUIError): ...

def ui_error_boundary(fn):
    @functools.wraps(fn)
    def _wrap(*a, **k):
        try:
            return fn(*a, **k)
        except Exception as e:
            logger.error("UI error in %s: %s", fn.__name__, e, exc_info=True)
            st.error("Unexpected error. See details below.")
            with st.expander("Error details"):
                st.code("".join(traceback.format_exception(type(e), e, e.__traceback__)))
    return _wrap

def handle_fatal(e: Exception) -> None:
    logger.critical("Fatal error: %s", e, exc_info=True)
    st.error("Critical error — application cannot continue.")
    st.stop()