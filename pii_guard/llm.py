"""Guarded LLM round-trip: mask → chat → unmask (Groq via OpenAI-compatible API)."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from .masker import Masker, MaskedText

load_dotenv()

GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")


def _client():
    from openai import OpenAI

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set. Add it to .env")
    return OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key)


@dataclass
class GuardedResult:
    response: str  # unmasked
    masked: MaskedText


def chat_guarded(
    prompt: str,
    system: str | None = None,
    model: str | None = None,
    use_ner: bool = False,
) -> GuardedResult:
    """Send a privacy-masked prompt to the LLM and unmask the reply."""
    masker = Masker()
    extra = None
    if use_ner:
        from .ner import spacy_spans

        extra = spacy_spans(prompt)
    masked = masker.mask(prompt, extra_spans=extra)

    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    user_content = masked.text
    if masked.mapping:
        user_content += "\n\n[Context for placeholders]\n" + masked.context()
    messages.append({"role": "user", "content": user_content})

    resp = _client().chat.completions.create(
        model=model or GROQ_MODEL, messages=messages
    )
    out = resp.choices[0].message.content or ""
    return GuardedResult(masked.unmask(out), masked)
