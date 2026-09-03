"""Entity definitions (regex patterns + human-readable labels)."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class EntityDef:
    key: str
    pattern: "re.Pattern[str]"
    label: str


def _p(pattern: str, flags: int = 0) -> "re.Pattern[str]":
    return re.compile(pattern, flags)


DEFAULT_ENTITIES: list[EntityDef] = [
    EntityDef("EMAIL", _p(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "an email address"),
    EntityDef(
        "API_KEY",
        _p(r"\b(?:sk-|gsk_|pk-|AKIA|ghp_|xox[bap]-)[A-Za-z0-9_-]{10,}\b"),
        "an API key or secret token",
    ),
    EntityDef("CREDIT_CARD", _p(r"\b(?:\d[ -]?){13,16}\b"), "a credit card number"),
    EntityDef("SSN", _p(r"\b\d{3}-\d{2}-\d{4}\b"), "a social security number"),
    EntityDef("IBAN", _p(r"\b[A-Z]{2}\d{2}[A-Z0-9]{1,30}\b"), "a bank account number (IBAN)"),
    EntityDef("IP_ADDRESS", _p(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "an IP address"),
    EntityDef("URL", _p(r"https?://[^\s]+[^\s.,;:!?]"), "a URL"),
    EntityDef(
        "PHONE",
        _p(r"(?:\+\d[\d\s.-]{7,}\d|\(\d{3}\)\s?\d{3}[- ]\d{4}|\d{3}-\d{3}-\d{4})"),
        "a phone number",
    ),
]
