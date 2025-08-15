import re

_NAME_RE = re.compile(r"^[a-zA-Z0-9._\-]{1,100}$")

def validate_pattern_name(name: str) -> None:
    if not _NAME_RE.fullmatch(name or ""):
        raise ValueError("Invalid pattern name. Allowed: letters, digits, ., _, -, length ≤100.")

def sanitize_input(text: str, max_length: int = 50_000) -> str:
    if text is None:
        return ""
    t = str(text)
    if len(t) > max_length:
        return t[:max_length]
    return t