import base64
import re
from typing import Tuple, List

# 15+ Pre-compiled deterministic prompt injection and privilege escalation signatures
INJECTION_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("system_override", re.compile(r"\bsystem\s+override\b", re.IGNORECASE)),
    ("critical_override", re.compile(r"\bcritical\s+override\b", re.IGNORECASE)),
    ("ignore_previous_instructions", re.compile(r"\bignore\s+(all\s+)?previous\s+(instructions|prompts|rules|constraints|budget|limits)\b", re.IGNORECASE)),
    ("disregard_limits", re.compile(r"\bdisregard\s+(all\s+|previous\s+)?(max\s+charge|budget|limits|instructions|policy|rules)\b", re.IGNORECASE)),
    ("bypass_policy", re.compile(r"\bbypass\s+(policy|guardrails|security|filters|assertions|limits)\b", re.IGNORECASE)),
    ("emergency_payout", re.compile(r"\bemergency\s+(payout|transfer|wire|release)\b", re.IGNORECASE)),
    ("elevate_privilege", re.compile(r"\belevate\s+privilege(s)?\b", re.IGNORECASE)),
    ("admin_release", re.compile(r"\badmin(istrative)?\s+(release|override|maintenance\s+fee|bypass)\b", re.IGNORECASE)),
    ("grant_admin", re.compile(r"\bgrant\s+(admin|root|superuser)\b", re.IGNORECASE)),
    ("format_drive", re.compile(r"\b(format\s+drive|rm\s+-rf|drop\s+table)\b", re.IGNORECASE)),
    ("ignore_budget", re.compile(r"\bignore\s+(budget|spending\s+cap|limit)\b", re.IGNORECASE)),
    ("unlimited_spend", re.compile(r"\bunlimited\s+(spend|budget|credit|payout)\b", re.IGNORECASE)),
    ("sudo_mode", re.compile(r"\b(sudo\s+mode|developer\s+mode|jailbreak|dan\s+mode)\b", re.IGNORECASE)),
    ("root_access", re.compile(r"\broot\s+access\b", re.IGNORECASE)),
    ("arbitrary_code_exec", re.compile(r"(\beval\s*\(|\bexec\s*\(|__import__\s*\(|os\.system\s*\()", re.IGNORECASE)),
]

# Hexadecimal or Base64 encoded exploit detector
HEX_ESCAPE_PATTERN = re.compile(r"(?:\\x[0-9a-fA-F]{2}){4,}|0x[0-9a-fA-F]{16,}")
BASE64_CANDIDATE_PATTERN = re.compile(r"\b(?:[A-Za-z0-9+/]{4}){6,}(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?\b")
SUSPICIOUS_DECODED_KEYWORDS = (
    b"override",
    b"ignore",
    b"bypass",
    b"eval(",
    b"exec(",
    b"system(",
    b"admin",
    b"payout",
    b"/bin/sh",
)


def inspect_prompt_injection(text: str) -> Tuple[bool, str]:
    """
    Deterministic, sub-millisecond prompt injection scanner.
    Returns (is_injected: bool, matched_reason: str).
    """
    if not text:
        return False, ""

    # 1. Direct signature regex matching
    for label, pattern in INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            matched_token = match.group(0)
            return (
                True,
                f"Prompt injection signature [{label}] matched token: '{matched_token}'",
            )

    # 2. Hexadecimal encoded exploit check
    if HEX_ESCAPE_PATTERN.search(text):
        return (
            True,
            "Encoded hexadecimal payload detected attempting to bypass guardrail filters",
        )

    # 3. Base64 encoded instruction check
    for candidate in BASE64_CANDIDATE_PATTERN.findall(text):
        try:
            decoded = base64.b64decode(candidate, validate=True).lower()
            for kw in SUSPICIOUS_DECODED_KEYWORDS:
                if kw in decoded:
                    return (
                        True,
                        f"Base64-encoded exploit payload detected containing '{kw.decode('ascii', errors='ignore')}'",
                    )
        except Exception:
            continue

    return False, ""

