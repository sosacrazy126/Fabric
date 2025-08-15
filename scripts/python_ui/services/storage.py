from __future__ import annotations
import os
from pathlib import Path
from typing import List, Dict, Any
from utils.logging import logger
from utils.io import read_json, write_json
from utils.typing import OutputLog, StarredOutput

def _config_dir() -> Path:
    env = os.environ.get("FABRIC_CONFIG_DIR")
    return Path(env).expanduser() if env else Path.home() / ".config" / "fabric"

def outputs_path() -> Path:
    return _config_dir() / "outputs" / "outputs.json"

def starred_path() -> Path:
    return _config_dir() / "outputs" / "starred_outputs.json"

def read_outputs() -> List[Dict[str, Any]]:
    data = read_json(outputs_path(), default=[])
    if not isinstance(data, list): return []
    return data

def write_outputs(logs: List[Dict[str, Any]]) -> None:
    write_json(outputs_path(), logs)

def read_starred() -> List[Dict[str, Any]]:
    data = read_json(starred_path(), default=[])
    if not isinstance(data, list): return []
    return data

def write_starred(items: List[Dict[str, Any]]) -> None:
    write_json(starred_path(), items)

# Convenience hook used by app.state.initialize()
def load_saved_outputs() -> None:
    try:
        _ = read_starred()
        _ = read_outputs()
        logger.info("storage: loaded persisted outputs")
    except Exception as e:
        logger.warning("storage.load_saved_outputs failed: %s", e)