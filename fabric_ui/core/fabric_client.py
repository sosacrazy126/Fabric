import subprocess
import time

class FabricClient:
    def __init__(self):
        self._model_cache = {}
        self._model_cache_time = 0
        self._model_cache_ttl = 300 # seconds

    def _run_cmd(self, cmd: list[str], timeout: int = 10):
        max_retries = 3
        retry_delay = 1
        for attempt in range(max_retries):
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                return result.returncode == 0, result.stdout, result.stderr
            except subprocess.TimeoutExpired:
                if attempt == max_retries - 1:
                    return False, "", "Timeout"
                time.sleep(retry_delay)
            except FileNotFoundError:
                return False, "", "fabric CLI not found"
            except Exception as e:
                if attempt == max_retries - 1:
                    return False, "", f"{e}"
                time.sleep(retry_delay)
        return False, "", "Max retries exceeded"

    def get_providers(self) -> dict:
        now = time.time()
        if self._model_cache and (now - self._model_cache_time < self._model_cache_ttl):
            return self._model_cache
        ok, output, err = self._run_cmd(["fabric", "--listmodels"])
        if not ok:
            self._model_cache = {}
            self._model_cache_time = now
            return {}
        parsed = self._parse_models_output(output)
        self._model_cache = parsed
        self._model_cache_time = now
        return parsed

    def get_status(self) -> dict:
        status = {"fabric_installed": False, "version": None, "pattern_count": 0, "vendor_count": 0, "errors": []}
        ok, output, err = self._run_cmd(["fabric", "--version"])
        if ok:
            status["fabric_installed"] = True
            status["version"] = output.strip().splitlines()[0] if output else None
        else:
            status["errors"].append(f"fabric CLI not found or not working: {err}")
        providers = self.get_providers()
        status["vendor_count"] = len(providers)
        # For pattern count, scan ~/.config/fabric/patterns
        from pathlib import Path
        pattern_dir = Path.home() / ".config" / "fabric" / "patterns"
        if pattern_dir.exists():
            status["pattern_count"] = len([p for p in pattern_dir.iterdir() if p.is_dir() and (p / "system.md").exists()])
        else:
            status["pattern_count"] = 0
        return status

    def _parse_models_output(self, output: str) -> dict:
        providers = {}
        current = None
        for line in output.splitlines():
            l = line.strip()
            if not l:
                continue
            if l.endswith(":"):
                current = l.rstrip(":")
                providers[current] = []
            elif current is not None:
                providers[current].append(l)
        return providers

    def execute_pattern(self, pattern: str, input_text: str):
        # Placeholder, does not actually run fabric
        return {"success": True, "output": f"Pattern: {pattern}\nInput: {input_text}"}