import unittest
from app.topic_keywords import keyword_topic
from app.topic_normalizer import normalize_topic
from app.topic_cleaner import clean_topic
from app.services.auth_service import hash_password

class TestTopicRefactor(unittest.TestCase):
    def test_keyword_topic(self):
        self.assertEqual(keyword_topic("i need a refund"), "refund_request")
        self.assertEqual(keyword_topic("the app crashed"), "technical_bug")
        self.assertEqual(keyword_topic("where is my delivery"), "delivery_issue")
        self.assertIsNone(keyword_topic("nothing here"))

    def test_normalize_topic(self):
        self.assertEqual(normalize_topic("late delivery"), "delivery_issue")
        self.assertEqual(normalize_topic("payment failed"), "payment_problem")
        self.assertEqual(normalize_topic("unknown topic"), "general_complaint")
        self.assertEqual(normalize_topic(None), "general_complaint")

    def test_clean_topic(self):
        self.assertEqual(clean_topic("general", "great but late delivery", "positive"), "delivery_issue")
        self.assertEqual(clean_topic("general", "excellent product", "positive"), "positive_feedback")
        self.assertEqual(clean_topic("general", "my app freeze", "neutral"), "technical_bug")
        self.assertEqual(clean_topic("general", "delayed package", "negative"), "delivery_issue")
        self.assertEqual(clean_topic("general", "terrible service", "neutral"), "general_complaint")
        self.assertEqual(clean_topic("custom_topic", "no matching words", "neutral"), "custom_topic")

class TestAuthRefactor(unittest.TestCase):
    def test_password_not_stored_plaintext(self):
        password = "plaintextpassword"
        hashed = hash_password(password)
        
        self.assertNotEqual(hashed, password)
        self.assertTrue(hashed.startswith("pbkdf2_sha256$"))
        
        parts = hashed.split("$")
        self.assertEqual(len(parts), 4)
        self.assertEqual(parts[0], "pbkdf2_sha256")
        self.assertEqual(parts[1], "260000")
