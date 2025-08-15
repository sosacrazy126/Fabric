from pathlib import Path
import os
import shutil
import tempfile
from services import patterns
from utils.typing import PatternSpec

def test_patterns_crud(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("FABRIC_PATTERNS_DIR", str(tmp_path))
    # create
    patterns.save_pattern(PatternSpec(name="hello", path=tmp_path/"hello.md", content="# test"))
    # list
    lst = patterns.list_patterns()
    assert any(p.name == "hello" for p in lst)
    # load
    spec = patterns.load_pattern("hello")
    assert "test" in spec.content
    # delete
    removed = patterns.delete_patterns(["hello"])
    assert removed == 1