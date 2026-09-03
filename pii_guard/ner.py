"""Optional spaCy NER spans for names, organizations, and locations."""

from __future__ import annotations

_NER_LABELS = {
    "PERSON": "a person's name",
    "ORG": "an organization",
    "GPE": "a location (city/country)",
    "NORP": "a nationality or group",
    "LOC": "a location",
}


def spacy_spans(
    text: str, model: str = "en_core_web_sm"
) -> list[tuple[int, int, str, str]]:
    """Return (start, end, key, label) spans from spaCy's NER model.

    Raises ImportError if spacy is not installed; returns [] if the model
    is missing.
    """
    import spacy  # noqa: PLC0415

    try:
        nlp = spacy.load(model)
    except OSError:
        return []

    spans: list[tuple[int, int, str, str]] = []
    for ent in nlp(text).ents:
        if ent.label_ in _NER_LABELS:
            spans.append((ent.start_char, ent.end_char, ent.label_, _NER_LABELS[ent.label_]))
    return spans
