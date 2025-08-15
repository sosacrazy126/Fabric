from __future__ import annotations
import json, os, tempfile
from pathlib import Path
from typing import Any

def atomic_write_text(path: Path, data: str, mode: int = 0o600) -> None:
    def atomic_write_text(path: Path, data: str, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent) as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)
    try:
        try:
            os.chmod(tmp_path, mode)
        except Exception:
            pass  # Windows may not support POSIX perms; acceptable fallback
        tmp_path.replace(path)
    finally:
        if tmp_path.exists():
            try: tmp_path.unlink()
            except Exception: pass

def read_json(path: Path, default: Any) -> Any:
    if not Path(path).exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json(path: Path, obj: Any, mode: int = 0o600) -> None:
    atomic_write_text(Path(path), json.dumps(obj, ensure_ascii=False, indent=2), mode=mode)