import subprocess
from services import runner
from utils.typing import RunResult

class Dummy:
    def __init__(self, rc=0, out=b"ok", err=b""):
        self.returncode = rc
        self.stdout = out
        self.stderr = err

def test_run_fabric_success(monkeypatch):
    def fake_run(args, input, stdout, stderr, check, timeout):
        assert args[0] == "fabric"
        assert check is False
        assert isinstance(timeout, (int, float))
        assert stdout == subprocess.PIPE and stderr == subprocess.PIPE
        return Dummy(0, b"hello", b"")
    monkeypatch.setattr(subprocess, "run", fake_run)
    res: RunResult = runner.run_fabric("valid_name", "hi")
    assert res.success and res.output == "hello" and res.exit_code == 0

def test_run_fabric_failure(monkeypatch):
    def fake_run(*a, **k): return Dummy(1, b"", b"boom")
    monkeypatch.setattr(subprocess, "run", fake_run)
    res = runner.run_fabric("valid_name", "x")
    assert not res.success and "boom" in (res.error or "")

def test_run_fabric_timeout(monkeypatch):
    def fake_run(*a, **k): raise subprocess.TimeoutExpired(cmd="fabric", timeout=1)
    monkeypatch.setattr(subprocess, "run", fake_run)
    res = runner.run_fabric("valid_name", "x", timeout_s=1)
    assert not res.success and res.meta.get("timeout") == "true"

def test_run_chain_propagates_output(monkeypatch):
    calls = {"n": 0}
    def fake_run(args, input, stdout, stderr, check, timeout):
        calls["n"] += 1
        return Dummy(0, f"out{calls['n']}".encode(), b"")
    monkeypatch.setattr(subprocess, "run", fake_run)
    steps = runner.run_chain(["a","b"], "seed")
    assert len(steps) == 2
    assert steps[0].output == "out1"
    assert steps[1].input == "out1"