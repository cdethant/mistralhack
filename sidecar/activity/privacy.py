"""
Privacy anonymization: hash window titles and redact sensitive keywords
when privacy_mode is enabled.
"""
import hashlib
import re

# Keywords whose titles will be fully replaced
SENSITIVE_PATTERNS = [
    r"\bbank(ing)?\b",
    r"\bcredit\b",
    r"\bpassword\b",
    r"\bmedical\b",
    r"\btherapy\b",
    r"\bdoctor\b",
    r"\btinder\b",
    r"\bbumble\b",
    r"\bhinge\b",
    r"\bdating\b",
    r"\bpaypal\b",
    r"\bvenmo\b",
    r"\btax(es)?\b",
    r"\bporn\b",
    r"\badult\b",
    r"\bcasino\b",
    r"\bgambling\b",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in SENSITIVE_PATTERNS]


def anonymize_title(title: str) -> str:
    """
    If the title contains sensitive content, return a hashed placeholder.
    Otherwise truncate to 40 chars for minimal exposure.
    """
    for pattern in _COMPILED:
        if pattern.search(title):
            h = hashlib.sha256(title.encode()).hexdigest()[:8]
            return f"Doc-{h}"
    # Non-sensitive: return a short version
    words = title.split()[:4]
    return " ".join(words) + ("…" if len(title.split()) > 4 else "")


def anonymize_app(app_name: str, whitelist: list[str] | None = None) -> str:
    """
    Return the real app name if it's on the user's whitelist or not sensitive.
    Apps on the whitelist are always reported as 'Private-<app>'.
    """
    whitelist = whitelist or []
    if app_name in whitelist:
        return "PrivateApp"
    for pattern in _COMPILED:
        if pattern.search(app_name):
            return "PrivateApp"
    return app_name
