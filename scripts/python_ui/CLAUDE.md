- \[STATE: execution\_ready] \[PATTERNS: modular\_scaffold] \[VELOCITY: 10x] \[QUALITY: 0.95]

Below is a **copy‑paste PR spec + files** you can hand to Claude/Greptile to open **PR‑1 (Scaffold + Orchestrator)**. It stands alone and runs; no behavior migration yet.

---

## PR‑1 — Scaffold & Tiny Orchestrator

**Title:** chore(ui): scaffold modular Streamlit app + 40‑line main
**Scope:** Add modular structure, tiny `main()`, error boundary, logging. No feature changes.
**Entry command:** `streamlit run scripts/python_ui/app/main.py`

### Directory Layout

```
scripts/python_ui/
  app/            # entry + routing + (later: state)
  views/          # execution | management | dashboard
  components/     # header | sidebar
  services/       # (stubs for PR‑1 only)
  utils/          # errors | logging
  tests/{unit,integration}/
```

---

### Files to Add (copy exactly)

**scripts/python\_ui/app/main.py**

```python
"""
Fabric Pattern Studio - Clean Architecture Entry Point (PR-1)
"""
import os, sys
import streamlit as st
from utils import errors, logging as app_logging

# Ensure package imports resolve when running via 'streamlit run app/main.py'
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # scripts/python_ui
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import routing, state  # noqa: E402
from components import header, sidebar  # noqa: E402
from views import execution, management, dashboard  # noqa: E402

def configure_page() -> None:
    st.set_page_config(
        page_title="Fabric Pattern Studio",
        page_icon="🎭",
        layout="wide",
        initial_sidebar_state="expanded",
    )

@errors.ui_error_boundary
def main() -> None:
    app_logging.init()
    configure_page()
    state.initialize()      # defaults + future persistence hooks
    header.render()
    sidebar.render()

    view = routing.get_current_view()
    if view == "Run Patterns":
        execution.render()
    elif view == "Pattern Management":
        management.render()
    else:
        dashboard.render()

if __name__ == "__main__":
    main()
```

**scripts/python\_ui/app/routing.py**

```python
import streamlit as st

def get_current_view() -> str:
    return st.session_state.get("current_view", "Run Patterns")

def set_view(view_name: str) -> None:
    st.session_state["current_view"] = view_name
```

**scripts/python\_ui/app/state.py**

```python
import streamlit as st
from utils.logging import logger
from services import storage

def initialize() -> None:
    if st.session_state.get("_initialized"):
        return
    logger.info("Initializing session state (PR-1)")

    defaults = {
        "current_view": "Run Patterns",
        "input_content": "",
        "selected_patterns": [],
        "chat_output": [],
        "output_logs": [],
        "starred_outputs": [],
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)

    # placeholder: future persisted reads (PR-2)
    try:
        storage.load_saved_outputs()
    except Exception as e:
        logger.warning("load_saved_outputs failed: %s", e)

    st.session_state["_initialized"] = True
```

**scripts/python\_ui/components/header.py**

```python
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
```

**scripts/python\_ui/components/sidebar.py**

```python
import streamlit as st
from app import routing

VIEWS = ["Run Patterns", "Pattern Management", "Analysis Dashboard"]

def render() -> None:
    with st.sidebar:
        st.header("Navigation")
        current = routing.get_current_view()
        sel = st.radio("View", VIEWS, index=VIEWS.index(current))
        if sel != current:
            routing.set_view(sel)
            st.rerun()

        st.divider()
        st.header("Configuration")
        st.info("Model/Provider config will be added in PR-2/PR-3.")
```

**scripts/python\_ui/views/execution.py**

```python
import streamlit as st
from utils.errors import ui_error_boundary

@ui_error_boundary
def render() -> None:
    st.header("🚀 Run Patterns")
    st.info("Execution UI will be migrated from the legacy file in PR-4.")
```

**scripts/python\_ui/views/management.py**

```python
import streamlit as st
from utils.errors import ui_error_boundary

@ui_error_boundary
def render() -> None:
    st.header("⚙️ Pattern Management")
    st.info("CRUD + editors will be migrated in PR-4.")
```

**scripts/python\_ui/views/dashboard.py**

```python
import streamlit as st
from utils.errors import ui_error_boundary

@ui_error_boundary
def render() -> None:
    st.header("📊 Analysis Dashboard")
    st.info("History/metrics will be migrated in PR-4/PR-5.")
```

**scripts/python\_ui/utils/errors.py**

```python
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
                st.code("".join(traceback.format_exception(e)))
    return _wrap

def handle_fatal(e: Exception) -> None:
    logger.critical("Fatal error: %s", e, exc_info=True)
    st.error("Critical error — application cannot continue.")
    st.stop()
```

**scripts/python\_ui/utils/logging.py**

```python
import logging, os
from datetime import datetime

logger = logging.getLogger("fabric_ui")

def init() -> None:
    if logger.handlers:
        return
    logger.setLevel(logging.INFO)

    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(ch)

    log_dir = os.path.expanduser("~/.config/fabric/logs")
    os.makedirs(log_dir, exist_ok=True)
    fh = logging.FileHandler(os.path.join(log_dir, f"fabric_ui_{datetime.now():%Y%m%d}.log"))
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
    logger.addHandler(fh)

    logger.info("Fabric UI logging initialized")
```

**scripts/python\_ui/services/storage.py**

```python
from utils.logging import logger

def load_saved_outputs() -> None:
    logger.info("load_saved_outputs(): placeholder (PR-2 will implement)")
```

****init**.py placeholders**
Create empty files at:

```
scripts/python_ui/__init__.py
scripts/python_ui/app/__init__.py
scripts/python_ui/views/__init__.py
scripts/python_ui/components/__init__.py
scripts/python_ui/services/__init__.py
scripts/python_ui/utils/__init__.py
scripts/python_ui/tests/__init__.py
scripts/python_ui/tests/unit/__init__.py
scripts/python_ui/tests/integration/__init__.py
```

---

### Reviewer Checklist

* [ ] App launches: `streamlit run scripts/python_ui/app/main.py`
* [ ] Navigation toggles 3 views without errors
* [ ] `main.py` is orchestration only (≈40 LOC), no business logic
* [ ] Errors surface via boundary; logs initialize and write to file
* [ ] No functional regressions introduced

---

## Next PR Specs (paste as tasks after PR‑1)

**PR‑2 — services: patterns/storage + typing**

* Extract pattern CRUD + starred persistence from legacy file.
* Add `utils/typing.py` dataclasses: `PatternSpec`, `RunResult`, `ChainStep`.
* Implement `utils/io.atomic_write(path, data, mode=0o600)` and use it in storage.
* Unit tests for services + io (tmpdir).
* **Acceptance:** typed functions; atomic writes; tests passing.

**PR‑3 — services: runner (safe subprocess)**

* Move all Fabric CLI calls to `services/runner.py` using `subprocess.run([...], shell=False, timeout=90)`.
* Map non‑zero → `ExecutionError`; timeouts → `TimeoutError` (reuse `ExecutionError` subclass if desired).
* Input caps (truncate >50k chars later in PR‑5 UI).
* Unit tests with mocks for subprocess.
* **Acceptance:** no `shell=True`; errors mapped; tests passing.

---

**Next actions:** paste PR‑1 files to Claude/Greptile → open PR; then queue PR‑2/PR‑3 tasks.