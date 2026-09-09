"""Streamlit UI for testing pii-guard."""

import html
import re
import time

import streamlit as st

from pii_guard import Masker

st.set_page_config(page_title="PII Guard", page_icon="🛡️", layout="wide")

SAMPLE = (
    "Hi, I'm Jane Doe. Please reset my account. Email jane.doe@example.com, "
    "phone (555) 123-4567, and my card 4111 1111 1111 1111. "
    "My server IP is 192.168.1.10 and I use https://portal.example.com. "
    "Call me again at jane.doe@example.com to confirm."
)

_PLACEHOLDER_RE = re.compile(r"\[[A-Z_]+\d+\]")


@st.cache_resource
def get_masker() -> Masker:
    return Masker()


def _highlight(text: str) -> str:
    """Escape text and colour the placeholders for display."""
    esc = html.escape(text)
    return _PLACEHOLDER_RE.sub(
        lambda m: (
            "<span style='color:#4ade80;background:#0d2818;padding:1px 6px;"
            "border-radius:4px;font-weight:600'>" + m.group(0) + "</span>"
        ),
        esc,
    )


def animate_mask(text: str, sleep_s: float) -> Masker:
    """Reveal the text character-by-character, masking live as PII completes."""
    masker = get_masker()
    box = st.empty()
    bar = st.progress(0.0)
    status = st.empty()
    n = len(text)
    seen_ph: set[str] = set()
    for i in range(1, n + 1):
        masked = masker.mask(text[:i])
        active = set(masked.mapping) - seen_ph
        seen_ph |= active
        box.markdown(
            "<div style='font-family:monospace;font-size:16px;line-height:1.7;"
            "white-space:pre-wrap;word-break:break-word'>"
            + _highlight(masked.text)
            + "<span style='color:#5b8cff'>▌</span></div>",
            unsafe_allow_html=True,
        )
        if active:
            status.markdown(
                "🔒 Detected: " + ", ".join(sorted(active))
            )
        bar.progress(i / n)
        time.sleep(sleep_s)
    bar.empty()
    status.empty()
    return masker.mask(text)


st.title("🛡️ PII Guard — test the masker")

tab_mask, tab_unmask, tab_llm, tab_custom = st.tabs(
    ["Mask", "Unmask", "LLM round-trip", "Custom entity"]
)

with tab_mask:
    text = st.text_area(
        "Input text",
        value=SAMPLE,
        height=160,
        help="Text to scan for PII / secrets.",
    )
    col_mask, col_anim, col_speed = st.columns([1, 1, 2])
    do_mask = col_mask.button("Mask", type="primary")
    do_anim = col_anim.button("▶ Animate masking", type="primary")
    sleep_s = col_speed.slider("Speed (s/char)", 0.005, 0.15, 0.03, 0.005)

    if do_anim:
        with st.spinner("Animating..."):
            masked = animate_mask(text, sleep_s)
    elif do_mask:
        masked = get_masker().mask(text)
    else:
        masked = None

    if masked is not None:
        st.subheader("Masked text")
        st.code(masked.text)

        st.subheader("Context for the model")
        st.code(masked.context())

        if masked.mapping:
            st.subheader("Mapping")
            rows = [
                {"Placeholder": ph, "Type": e.key, "Label": e.label, "Value": e.value}
                for ph, e in sorted(masked.mapping.items())
            ]
            st.dataframe(rows, width="stretch")
        else:
            st.info("No PII detected.")

with tab_unmask:
    st.write("Paste text containing placeholders to restore the real values.")
    raw = st.text_area(
        "Text to unmask",
        value="Email me at jane@example.com or call (555) 123-4567",
        height=140,
    )
    if st.button("Mask then unmask", type="primary"):
        masker = get_masker()
        masked = masker.mask(raw)
        st.write("Masked:", masked.text)
        st.write("Unmasked:", masked.unmask(masked.text))

    masked_text = st.text_area(
        "Or paste already-masked text (e.g. a reply with [EMAIL_0])",
        value="We reset the account and emailed [EMAIL_0]. We'll call [PHONE_0].",
        height=120,
    )
    source = st.text_area(
        "Source text (used to build the mapping)",
        value=SAMPLE,
        height=120,
    )
    if st.button("Unmask reply", type="primary"):
        masker = get_masker()
        masked = masker.mask(source)
        st.write("Restored:", masked.unmask(masked_text))

with tab_llm:
    st.write("Send a masked prompt to Groq and unmask the reply.")
    st.info("Requires GROQ_API_KEY in a .env file.")
    prompt = st.text_area("Prompt", value="My email is jane@example.com, call (555) 123-4567.", height=120)
    if st.button("Run guarded chat", type="primary"):
        try:
            from pii_guard.llm import chat_guarded

            with st.spinner("Calling Groq..."):
                result = chat_guarded(prompt)
            st.write("Masked prompt sent:")
            st.code(result.masked.text)
            st.write("Unmasked reply:")
            st.write(result.response)
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))

with tab_custom:
    st.write("Register a custom regex entity and test it.")
    col1, col2 = st.columns(2)
    key = col1.text_input("Entity key", value="ACCOUNT")
    label = col2.text_input("Human-readable label", value="an account number")
    pattern = st.text_input("Regex pattern", value=r"\bACCT-\d{6}\b")
    sample = st.text_area("Sample text", value="my account is ACCT-123456", height=100)
    if st.button("Test custom entity", type="primary"):
        masker = Masker()
        try:
            masker.register(key, pattern, label)
            m = masker.mask(sample)
            st.code(m.text)
            st.code(m.context())
        except Exception as exc:  # noqa: BLE001
            st.error(f"Invalid pattern: {exc}")
