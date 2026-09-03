import unittest

from pii_guard import Masker


class TestMasker(unittest.TestCase):
    def setUp(self):
        self.masker = Masker()

    def test_masks_email_and_phone(self):
        m = self.masker.mask("Email me at jane@example.com or call (555) 123-4567")
        self.assertNotIn("jane@example.com", m.text)
        self.assertNotIn("(555) 123-4567", m.text)
        self.assertIn("[EMAIL_0]", m.text)
        self.assertIn("[PHONE_0]", m.text)

    def test_same_value_maps_to_same_placeholder(self):
        m = self.masker.mask("a@b.com and again a@b.com")
        self.assertEqual(m.text.count("[EMAIL_0]"), 2)
        self.assertEqual(len(m.mapping), 1)

    def test_unmask_round_trip(self):
        text = "mail jane@example.com now"
        m = self.masker.mask(text)
        self.assertEqual(m.unmask(m.text), text)

    def test_context_describes_placeholders(self):
        m = self.masker.mask("x jane@example.com y")
        self.assertIn("[EMAIL_0]: an email address", m.context())

    def test_credit_card_and_ssn(self):
        m = self.masker.mask("card 4111 1111 1111 1111 and ssn 123-45-6789")
        self.assertIn("[CREDIT_CARD_0]", m.text)
        self.assertIn("[SSN_0]", m.text)

    def test_api_key_masked(self):
        m = self.masker.mask("key gsk_abcdefghijklmnop123456")
        self.assertIn("[API_KEY_0]", m.text)

    def test_no_pii_returns_unchanged(self):
        m = self.masker.mask("just a normal sentence here")
        self.assertEqual(m.text, "just a normal sentence here")
        self.assertEqual(m.mapping, {})

    def test_custom_entity(self):
        masker = Masker()
        masker.register("ACCOUNT", r"\bACCT-\d{6}\b", "an account number")
        m = masker.mask("my account is ACCT-123456")
        self.assertIn("[ACCOUNT_0]", m.text)


if __name__ == "__main__":
    unittest.main()
