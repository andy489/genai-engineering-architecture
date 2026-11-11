import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from c10_pii_redaction import (
    MAX_CHARS, DemoModel, Frame, PIIRedactor, RedactionError, RedactionPipeline,
    SYNTHETIC_PROMPT, load_ner, redact_stream,
)


def no_entities(text):
    """Test double isolates rule/transport behavior; this is not an NER model."""
    return SimpleNamespace(ents=[])


class RulesAndStreamTests(unittest.TestCase):
    def setUp(self):
        self.redactor = PIIRedactor(no_entities)
        self.model = DemoModel()
        self.pipeline = RedactionPipeline(self.redactor, self.model)
        self.addCleanup(self.pipeline.close)

    def test_rules_and_safe_downstream_storage(self):
        raw = "Email demo@example.com; call +1 (202) 555-0147; patient ID: AB-12345; SSN 123-45-6789."
        event = self.pipeline.process(raw)
        stored = self.pipeline.db.execute("SELECT redacted_prompt FROM prompts").fetchone()[0]
        self.assertEqual(self.model.received, [stored])
        for secret in ("demo@example.com", "555-0147", "AB-12345", "123-45-6789"):
            self.assertNotIn(secret, stored)
            self.assertNotIn(secret, str(self.pipeline.db.execute("SELECT * FROM audit").fetchall()))
        self.assertEqual(sum(event["counts"].values()), 4)
        self.assertNotIn("text", event)

    def test_every_split_position_matches_whole_message(self):
        raw = "demo@example.com +1 (202) 555-0147 patient ID: AB-12345"
        expected = self.redactor.redact(raw).text
        for cut in range(len(raw) + 1):
            with self.subTest(cut=cut):
                actual = redact_stream([Frame(raw[:cut]), Frame(raw[cut:], True)], self.redactor)
                self.assertEqual(actual.text, expected)

    def test_no_downstream_call_before_end(self):
        def source():
            yield Frame("demo@")
            self.assertEqual(self.model.received, [])
            self.assertEqual(self.pipeline.db.execute("SELECT count(*) FROM prompts").fetchone()[0], 0)
            yield Frame("example.com", True)
        self.pipeline.process_stream(source())
        self.assertEqual(self.model.received, ["[REDACTED_EMAIL]"])

    def test_incomplete_oversized_and_trailing_frames_withheld(self):
        for frames in ([Frame("demo@")], [Frame("x" * (MAX_CHARS + 1), True)],
                       [Frame("ok", True), Frame("extra")], []):
            with self.subTest(frames=len(frames)):
                self.assertEqual(self.pipeline.process_stream(frames)["decision"], "review")
        self.assertEqual(self.model.received, [])
        self.assertEqual(self.pipeline.db.execute("SELECT count(*) FROM prompts").fetchone()[0], 0)

    def test_source_failure_does_not_log_exception_text(self):
        def source():
            yield Frame("demo@")
            raise RuntimeError("secret@example.com")
        self.assertEqual(self.pipeline.process_stream(source())["reason"], "stream_failed")
        self.assertNotIn("secret@example.com", str(self.pipeline.db.execute("SELECT * FROM audit").fetchall()))
        self.assertEqual(self.model.received, [])

    def test_ner_failure_withholds_even_after_regex_matches(self):
        def broken(text):
            raise RuntimeError(text)
        self.pipeline.redactor = PIIRedactor(broken)
        self.assertEqual(self.pipeline.process("secret@example.com")["reason"], "ner_failed")
        self.assertEqual(self.model.received, [])
        self.assertNotIn("secret@example.com", str(self.pipeline.db.execute("SELECT * FROM audit").fetchall()))

    def test_overlap_union_leaves_no_suffix(self):
        def overlaps(text):
            return SimpleNamespace(ents=[SimpleNamespace(label_="PERSON", start_char=2, end_char=len(text))])
        result = PIIRedactor(overlaps).redact("demo@example.com")
        self.assertEqual(result.text, "[REDACTED_PII]")

    def test_unicode_and_context_validation(self):
        self.assertEqual(self.redactor.redact("ｄｅｍｏ＠ｅｘａｍｐｌｅ．ｃｏｍ").text, "[REDACTED_EMAIL]")
        for text in ("demo\u200b@example.com", "", "x" * (MAX_CHARS + 1)):
            with self.assertRaises(RedactionError):
                self.redactor.redact(text)
        with self.assertRaises(RedactionError):
            self.redactor.redact("hello", context="unknown")


class ActualNERTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.redactor = PIIRedactor()  # Required real model, deliberately not skipped.

    def test_actual_trained_ner_and_context_policy(self):
        text = "John Smith has an appointment on Tuesday in London."
        support = self.redactor.redact(text, context="support")
        healthcare = self.redactor.redact(text, context="healthcare")
        self.assertIn("ner", support.sources)
        for value in ("John Smith", "London"):
            self.assertNotIn(value, support.text)
        self.assertIn("Tuesday", support.text)
        self.assertNotIn("Tuesday", healthcare.text)

    def test_full_demo_fixture_contains_no_seeded_identifiers(self):
        result = self.redactor.redact(SYNTHETIC_PROMPT, context="healthcare")
        for value in ("John Smith", "London", "john.smith@example.com", "555-0147", "AB-12345", "123-45-6789", "Tuesday"):
            self.assertNotIn(value, result.text)
        self.assertEqual(result.sources, ("ner", "regex"))

    def test_name_split_across_stream_frames(self):
        result = redact_stream([Frame("John "), Frame("Smith lives in Lon"), Frame("don.", True)], self.redactor)
        self.assertNotIn("John", result.text)
        self.assertNotIn("Smith", result.text)
        self.assertNotIn("London", result.text)

    def test_unavailable_model_fails_closed(self):
        load_ner.cache_clear()
        with patch("spacy.load", side_effect=OSError("synthetic model failure")):
            with self.assertRaisesRegex(RedactionError, "^ner_unavailable$"):
                load_ner()
        load_ner.cache_clear()


if __name__ == "__main__":
    unittest.main()
