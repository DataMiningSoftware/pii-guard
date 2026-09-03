"""Demo of masking (and optional Groq round-trip)."""

from pii_guard import Masker

SAMPLE = (
    "Hi, I'm Jane Doe. Please reset my account. Email jane.doe@example.com, "
    "phone (555) 123-4567, and my card 4111 1111 1111 1111. "
    "My server IP is 192.168.1.10 and I use https://portal.example.com. "
    "Call me again at jane.doe@example.com to confirm."
)


def main() -> None:
    masker = Masker()
    masked = masker.mask(SAMPLE)

    print("Original:")
    print(SAMPLE)
    print("\nMasked:")
    print(masked.text)
    print("\nContext for the model:")
    print(masked.context())

    print("\nRound-trip unmask of a hypothetical reply:")
    reply = "We reset the account and emailed [EMAIL_0]. We'll call [PHONE_0]."
    print(masked.unmask(reply))


if __name__ == "__main__":
    main()
