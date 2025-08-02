from contextlib import contextmanager
from pathlib import Path

class SafeFileHandler:
    @contextmanager
    def create_temp_yaml(self, content: str):
        # Minimal temp file context
        temp_path = Path("temp_stub.yaml")
        temp_path.write_text(content)
        try:
            yield str(temp_path)
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def read_text_file(self, path: str) -> str:
        return Path(path).read_text()

    def write_text_file(self, path: str, content: str):
        Path(path).write_text(content)