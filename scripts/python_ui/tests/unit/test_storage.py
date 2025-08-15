from pathlib import Path
import os
from services import storage

def test_storage_read_write(tmp_path, monkeypatch):
    monkeypatch.setenv("FABRIC_CONFIG_DIR", str(tmp_path))
    logs = [{"id":"1","pattern":"p","input_text":"i","output_text":"o","created_at":"2025-01-01T00:00:00Z"}]
    storage.write_outputs(logs)
    assert storage.read_outputs() == logs

    stars = [{"id":"s1","name":"star","pattern":"p","output_text":"o","created_at":"2025-01-01T00:00:00Z"}]
    storage.write_starred(stars)
    assert storage.read_starred() == stars