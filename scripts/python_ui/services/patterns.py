from __future__ import annotations
import os
import re
from pathlib import Path
from typing import List
from utils.logging import logger
from utils.typing import PatternSpec
from utils.io import atomic_write_text

# Default patterns directory — can be overridden via FABRIC_PATTERNS_DIR
def _patterns_root() -> Path:
    env = os.environ.get("FABRIC_PATTERNS_DIR")
    return Path(env).expanduser() if env else Path.home() / ".config" / "fabric" / "patterns"

_NAME_RE = re.compile(r"^[a-zA-Z0-9._\-]+$")

def _assert_valid_name(name: str) -> None:
    if not _NAME_RE.match(name):
        raise ValueError("Invalid pattern name. Allowed: letters, digits, ., _, -")

def _safe_path_for(name: str) -> Path:
    _assert_valid_name(name)
    root = _patterns_root().resolve()
    path = (root / f"{name}.md").resolve()
    if not str(path).startswith(str(root)):
        raise ValueError("Unsafe pattern path")
    return path

def list_patterns() -> List[PatternSpec]:
    root = _patterns_root()
    root.mkdir(parents=True, exist_ok=True)
    specs: List[PatternSpec] = []
    for p in sorted(root.glob("*.md")):
        stat = p.stat()
        specs.append(PatternSpec(
            name=p.stem,
            path=p,
            content=p.read_text(encoding="utf-8"),
            created_at=stat.st_ctime,
            modified_at=stat.st_mtime,
            meta={"size": stat.st_size}
        ))
    logger.info("patterns.list: %d found in %s", len(specs), root)
    return specs

def load_pattern(name: str) -> PatternSpec:
    path = _safe_path_for(name)
    if not path.exists():
        raise FileNotFoundError(f"Pattern not found: {name}")
    stat = path.stat()
    return PatternSpec(
        name=name,
        path=path,
        content=path.read_text(encoding="utf-8"),
        created_at=None,
        modified_at=None,
        meta={"size": stat.st_size},
    )

def save_pattern(spec: PatternSpec) -> None:
    path = _safe_path_for(spec.name)
    atomic_write_text(path, spec.content)
    logger.info("patterns.save: %s", path)

def delete_patterns(names: List[str]) -> int:
    count = 0
    for n in names:
        p = _safe_path_for(n)
        if p.exists():
            p.unlink()
            count += 1
    logger.info("patterns.delete: %d removed", count)
    return count