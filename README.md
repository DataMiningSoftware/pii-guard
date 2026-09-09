# pii-guard

A privacy layer for LLM prompts: detects sensitive information (PII, secrets) in
user text, replaces it with **unique typed placeholders**, tells the model what
each placeholder represents (without leaking the value), and restores the real
values in the model's reply.

## Why

Sending raw user text to an LLM can leak emails, phone numbers, credit cards,
API keys, IP addresses, and more — to the model provider and into logs. This
library sits in front of the LLM call:

```
raw text ──► Masker.mask() ──► "[EMAIL_0] lives in [LOCATION_0]"  ──► LLM
                                    │
                              context: "[EMAIL_0] = an email address, ..."
                                    │
LLM reply (with placeholders) ──► MaskedText.unmask() ──► reply with real values
```

## Features

- **Regex entities** out of the box: email, phone, credit card, SSN, IBAN, IP
  address, URL, and API keys/secrets (`sk-`, `gsk_`, `pk-`, `AKIA`, `ghp_`).
- **Unique, deterministic placeholders** — the same value always maps to the same
  `[TYPE_N]`, and each distinct value gets its own id.
- **Context block** — a plain-language description of each placeholder (e.g.
  `[EMAIL_0]: an email address`) so the model reasons about the *type* without
  ever seeing the *value*.
- **Unmask** — restore real values in the reply.
- **Extensible** — register custom regex entities, or add spaCy NER for names,
  organizations, and locations.

## Layout

```
pii-guard/
├── pii_guard/
│   ├── entities.py  # EntityDef + built-in patterns
│   ├── masker.py    # Masker, MaskedText
│   ├── ner.py       # optional spaCy NER spans
│   ├── llm.py       # Groq round-trip (mask → chat → unmask)
│   └── cli.py       # demo
├── tests/test_masker.py
├── .env.example
└── README.md
```

## Usage

```python
from pii_guard import Masker

masker = Masker()
masked = masker.mask("Email me at jane@example.com or call (555) 123-4567")

print(masked.text)       # "Email me at [EMAIL_0] or call [PHONE_0]"
print(masked.context())  # "- [EMAIL_0]: an email address\n- [PHONE_0]: a phone number"

reply = "We'll reach out to [EMAIL_0] shortly."
print(masked.unmask(reply))  # "We'll reach out to jane@example.com shortly."
```

Full LLM round-trip (Groq):

```python
from pii_guard.llm import chat_guarded

result = chat_guarded("My name is Jane, email jane@example.com, card 4111 1111 1111 1111")
print(result.response)   # model's reply with real values restored
```

## Setup

```powershell
pip install -r requirements.txt
Copy-Item .env.example .env   # add GROQ_API_KEY
```

## Tests

```powershell
python -m pytest tests
```

8 tests cover entity detection, deterministic placeholder assignment, the context
block, and the mask → unmask round-trip (no external services required).

## Test UI

A Streamlit UI (`app.py`) lets you test masking interactively:

```powershell
streamlit run app.py
```

- **Mask** — paste text and see the masked output, model context, and mapping table.
- **▶ Animate masking** — reveal text character-by-character, watching each PII value
  flip to a placeholder live (with a speed slider).
- **Unmask**, **LLM round-trip**, and **Custom entity** tabs cover the rest.

Optional NER (names/orgs/locations) requires spaCy:

```powershell
pip install spacy
python -m spacy download en_core_web_sm
```

## Caveats

- Regex detection is heuristic — it can miss or over-match. For a hard privacy
  guarantee, combine with a dedicated NER/PII service and **do not send secrets
  to third-party models at all** where possible.
- Always treat the masked text as still potentially sensitive; masking reduces
  exposure, it does not make data safe to ship anywhere.
