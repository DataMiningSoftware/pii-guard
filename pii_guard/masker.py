"""Core masking logic."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .entities import DEFAULT_ENTITIES, EntityDef


@dataclass
class Entity:
    key: str
    label: str
    value: str


@dataclass
class MaskedText:
    text: str
    mapping: dict[str, Entity] = field(default_factory=dict)

    def context(self) -> str:
        """Plain-language description of each placeholder for the LLM."""
        lines = ["The following placeholders have replaced sensitive values:"]
        for ph in sorted(self.mapping):
            lines.append(f"- {ph}: {self.mapping[ph].label}")
        return "\n".join(lines)

    def unmask(self, text: str) -> str:
        """Restore real values in a string that contains placeholders."""
        out = text
        for ph in sorted(self.mapping, key=len, reverse=True):
            out = out.replace(ph, self.mapping[ph].value)
        return out


class Masker:
    def __init__(self, entities: list[EntityDef] | None = None) -> None:
        self._entities = list(entities) if entities is not None else list(DEFAULT_ENTITIES)

    def register(self, key: str, pattern: str, label: str) -> None:
        self._entities.append(EntityDef(key, re.compile(pattern), label))

    def mask(
        self,
        text: str,
        extra_spans: list[tuple[int, int, str, str]] | None = None,
    ) -> MaskedText:
        """Detect sensitive values and replace them with unique placeholders.

        `extra_spans` is an optional list of (start, end, key, label) tuples,
        e.g. from a spaCy NER pass, merged with the regex-detected spans.
        """
        spans: list[tuple[int, int, str, str]] = []
        for ent in self._entities:
            for m in ent.pattern.finditer(text):
                spans.append((m.start(), m.end(), ent.key, ent.label))
        for s, e, key, label in extra_spans or []:
            spans.append((s, e, key, label))

        # Earliest match wins; longer wins ties (avoids overlapping spans).
        spans.sort(key=lambda s: (s[0], -(s[1] - s[0])))
        selected: list[tuple[int, int, str, str]] = []
        last_end = -1
        for s, e, key, label in spans:
            if s >= last_end:
                selected.append((s, e, key, label))
                last_end = e

        counters: dict[str, int] = {}
        value_to_ph: dict[tuple[str, str], str] = {}
        mapping: dict[str, Entity] = {}
        parts: list[str] = []
        pos = 0
        for s, e, key, label in selected:
            value = text[s:e]
            ph = value_to_ph.get((key, value))
            if ph is None:
                idx = counters.get(key, 0)
                ph = f"[{key}_{idx}]"
                counters[key] = idx + 1
                value_to_ph[(key, value)] = ph
                mapping[ph] = Entity(key=key, label=label, value=value)
            parts.append(text[pos:s])
            parts.append(ph)
            pos = e
        parts.append(text[pos:])
        return MaskedText("".join(parts), mapping)
