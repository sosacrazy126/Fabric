from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

@dataclass
class PatternSpec:
    name: str
    path: Path
    content: str
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    meta: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OutputLog:
    id: str
    pattern: str
    input_text: str
    output_text: str
    created_at: str  # ISO8601

@dataclass
class StarredOutput:
    id: str
    name: str
    pattern: str
    output_text: str
    created_at: str  # ISO8601

@dataclass
class RunResult:
    success: bool
    output: str
    error: Optional[str]
    duration_ms: int
    exit_code: int
    meta: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ChainStep:
    pattern: str
    input: str
    output: Optional[str] = None
    error: Optional[str] = None
    duration_ms: int = 0