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
    # Check environment variable first
    env = os.environ.get("FABRIC_PATTERNS_DIR")
    if env:
        return Path(env).expanduser()
    
    # Check standard Fabric config locations
    fabric_config_dir = Path.home() / ".config" / "fabric"
    
    # Try patterns subdirectory first
    patterns_dir = fabric_config_dir / "patterns"
    if patterns_dir.exists():
        return patterns_dir
    
    # Fallback to config directory itself (some setups store patterns directly there)
    if fabric_config_dir.exists():
        return fabric_config_dir
    
    # Create default if nothing exists
    patterns_dir.mkdir(parents=True, exist_ok=True)
    return patterns_dir

_NAME_RE = re.compile(r"^[a-zA-Z0-9._\-]+$")

def _assert_valid_name(name: str) -> None:
    if not _NAME_RE.match(name):
        raise ValueError("Invalid pattern name. Allowed: letters, digits, ., _, -")

def _safe_path_for(name: str) -> Path:
    _assert_valid_name(name)
    root = _patterns_root().resolve()
    
    # Check if pattern exists as directory with system.md
    dir_path = (root / name / "system.md").resolve()
    if dir_path.exists() and str(dir_path).startswith(str(root)):
        return dir_path
    
    # Default to .md file format
    path = (root / f"{name}.md").resolve()
    if not str(path).startswith(str(root)):
        raise ValueError("Unsafe pattern path")
    return path

def list_patterns() -> List[PatternSpec]:
    root = _patterns_root()
    root.mkdir(parents=True, exist_ok=True)
    specs: List[PatternSpec] = []
    
    # Look for patterns in multiple formats and locations
    pattern_files = []
    
    # Check for .md files (standard format)
    pattern_files.extend(root.glob("*.md"))
    
    # Check for directories with system.md files (Fabric pattern format)
    for item in root.iterdir():
        if item.is_dir():
            system_file = item / "system.md"
            if system_file.exists():
                pattern_files.append(system_file)
    
    # Also check for patterns directly in the config directory
    if root.name != "patterns":
        config_patterns = root.glob("*.md")
        pattern_files.extend(config_patterns)
    
    for p in sorted(pattern_files):
        try:
            stat = p.stat()
            # For system.md files, use the parent directory name as pattern name
            if p.name == "system.md":
                pattern_name = p.parent.name
            else:
                pattern_name = p.stem
            
            content = p.read_text(encoding="utf-8")
            
            specs.append(PatternSpec(
                name=pattern_name,
                path=p,
                content=content,
                created_at=stat.st_ctime,
                modified_at=stat.st_mtime,
                meta={"size": stat.st_size, "format": "system.md" if p.name == "system.md" else "md"}
            ))
        except Exception as e:
            logger.warning(f"Failed to load pattern {p}: {e}")
            continue
    
    logger.info("patterns.list: %d found in %s", len(specs), root)
    return specs

def load_pattern(name: str) -> PatternSpec:
    root = _patterns_root()
    
    # Try different pattern file locations and formats
    possible_paths = [
        root / f"{name}.md",  # Standard .md file
        root / name / "system.md",  # Fabric directory format
        root.parent / f"{name}.md",  # Direct in config dir
    ]
    
    for path in possible_paths:
        if path.exists():
            try:
                stat = path.stat()
                content = path.read_text(encoding="utf-8")
                return PatternSpec(
                    name=name,
                    path=path,
                    content=content,
                    created_at=stat.st_ctime,
                    modified_at=stat.st_mtime,
                    meta={"size": stat.st_size, "format": "system.md" if path.name == "system.md" else "md"},
                )
            except Exception as e:
                logger.warning(f"Failed to load pattern from {path}: {e}")
                continue
    
    raise FileNotFoundError(f"Pattern not found: {name}")

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