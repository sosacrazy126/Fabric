from contextlib import contextmanager
from pathlib import Path
import tempfile
import yaml
import os

class SafeFileHandler:
    def __init__(self, max_file_size: int = 10 * 1024 * 1024):
        self.max_file_size = max_file_size

    def read_text_file(self, path: Path, encoding: str = "utf-8") -> str | None:
        if not path.exists():
            return None
        if path.stat().st_size > self.max_file_size:
            return None
        return path.read_text(encoding=encoding)

    def write_text_file(self, path: Path, content: str, encoding: str = "utf-8"):
        if len(content.encode(encoding)) > self.max_file_size:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding=encoding)

    @contextmanager
    def create_temp_yaml(self, data: dict):
        # Create a temp yaml file, yield Path, delete after
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="w") as tf:
            yaml.dump(data, tf)
            tf.flush()
            temp_path = Path(tf.name)
        try:
            yield temp_path
        finally:
            if temp_path.exists():
                temp_path.unlink()