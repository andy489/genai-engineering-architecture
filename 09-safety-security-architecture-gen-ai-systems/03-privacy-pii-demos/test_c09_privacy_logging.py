"""Behavioral checks for the Section 9 demo. No network or third-party packages."""
import json
import unittest
from dataclasses import asdict, replace

from c09_privacy_logging import (
    AuditPolicy, AuditStore, Destination, ProcessingReview, TrainingApproval,
    TrainingGate, assess_processing, build_audit_record, dataset_digest,
    hash_user_id, redact, truncate,
)

KEY = b"test-only-key-do-not-deploy-------"
NOW = 1_700_000_000


class MinimizationTests(unittest.TestCase):
    def test_key_and_tenant_isolation(self):
        token = hash_user_id("user-1", key=KEY, tenant="one")
        self.assertEqual(token, hash_user_id("user-1", key=KEY, tenant="one"))
        self.assertNotEqual(token, hash_user_id("user-1", key=KEY, tenant="two"))
        self.assertNotEqual(token, hash_user_id("user-1", key=b"x" * 32, tenant="one"))
        self.assertNotEqual(token, hash_user_id("user-2", key=KEY, tenant="one"))
        with self.assertRaises(ValueError):
            hash_user_id("user-1", key=b"short", tenant="one")

    def test_redact_before_truncation_and_bound_output(self):
        raw = "Contact " + "a" * 90 + "@example.com; patient ID: H-9912; password=fake-demo"
        preview = truncate(redact(raw), 55)
        self.assertNotIn("a" * 10, preview)
        self.assertNotIn("H-9912", preview)
        self.assertNotIn("fake-demo", preview)
        self.assertLessEqual(len(preview), 55)
        self.assertIn("[EMAIL]", preview)
        self.assertNotIn("\n", redact("first\nsecond\x1b[31m"))
        with self.assertRaises(ValueError):
            redact("x" * 12_001)

    def test_redaction_is_not_anonymization(self):
        self.assertIn("medical appointment", redact("A medical appointment for demo@example.com"))

    def test_invalid_policy_and_decision(self):
        with self.assertRaises(ValueError):
            AuditPolicy("p", "ref", 0)
        with self.assertRaises(ValueError):
            build_audit_record("id", "anything", AuditPolicy("p", "ref", 1),
                               key=KEY, tenant="t", now=NOW)


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.store = AuditStore()
        self.addCleanup(self.store.close)
        self.record = build_audit_record("demo@example.com", "allow", AuditPolicy("p", "ref", 1),
                                         key=KEY, tenant="t", now=NOW)
        self.store.add(self.record, now=NOW)

    def test_closed_schema_and_access(self):
        with self.assertRaises(PermissionError):
            self.store.export_subject(self.record.subject, role="viewer", now=NOW)
        rows = self.store.export_subject(self.record.subject, role="privacy_officer", now=NOW)
        serialized = json.dumps(rows)
        self.assertNotIn("demo@example.com", serialized)
        for field in ("prompt", "response", "message", "email"):
            self.assertNotIn(field, rows[0])
        self.assertEqual(len(rows), 1)
        self.assertEqual(self.store.export_subject("unknown", role="privacy_officer", now=NOW), [])

    def test_delete_all_copies_and_suppress_backup_restore(self):
        result = self.store.delete_subject(self.record.subject, role="privacy_officer")
        self.assertEqual(result["deleted_copies"], {"application": 1, "provider_simulation": 1})
        self.assertFalse(self.store.add(self.record, now=NOW))
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM records").fetchone()[0], 0)
        self.assertEqual(self.store.delete_subject(self.record.subject, role="privacy_officer")
                         ["deleted_copies"]["application"], 0)

    def test_expiry_boundary_hides_then_purges(self):
        expiry = self.record.expires_at
        self.assertEqual(len(self.store.export_subject(self.record.subject, role="privacy_officer", now=expiry - 1)), 1)
        self.assertEqual(self.store.export_subject(self.record.subject, role="privacy_officer", now=expiry), [])
        self.assertEqual(self.store.purge_expired(now=expiry, role="retention_worker")["application"], 1)
        self.assertFalse(self.store.add(replace(self.record, event_id="other"), now=expiry))

    def test_hold_defers_deletion_then_release_enforces_expiry(self):
        self.store.hold(self.record.event_id, "hold-ref", role="privacy_officer")
        expiry = self.record.expires_at
        self.assertEqual(self.store.purge_expired(now=expiry, role="retention_worker")["application"], 0)
        self.assertEqual(self.store.delete_subject(self.record.subject, role="privacy_officer")["status"], "partial_hold")
        self.assertEqual(len(self.store.export_subject(self.record.subject, role="privacy_officer", now=expiry)), 1)
        self.store.release_hold(self.record.event_id, role="privacy_officer")
        self.assertEqual(self.store.purge_expired(now=expiry, role="retention_worker")["application"], 1)

    def test_unauthorized_mutations_and_idempotent_ingestion(self):
        for action in (
            lambda: self.store.delete_subject(self.record.subject, role="viewer"),
            lambda: self.store.purge_expired(now=NOW, role="viewer"),
            lambda: self.store.hold(self.record.event_id, "ref", role="viewer"),
            lambda: self.store.release_hold(self.record.event_id, role="viewer"),
        ):
            with self.assertRaises(PermissionError):
                action()
        self.store.add(self.record, now=NOW)
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM records").fetchone()[0], 2)


class ProcessingTests(unittest.TestCase):
    def setUp(self):
        self.dest = Destination("provider", "EU", "terms", "safeguards")
        self.review = ProcessingReview(("GDPR",), "scope", "purpose", True, (self.dest,))

    def test_region_does_not_authorize_onward_transfer(self):
        sub = Destination("subprocessor", "US", "terms", "safeguards", True)
        review = replace(self.review, destinations=(self.dest, sub))
        self.assertIn("transfer_assessment_missing", assess_processing(review)["reasons"])
        reviewed = replace(review, destinations=(self.dest, replace(sub, transfer_ref="reviewed-transfer")))
        self.assertEqual(assess_processing(reviewed)["decision"], "allow")

    def test_unknown_or_incomplete_assessments_fail_closed(self):
        for changes in ({"assessment_ref": ""}, {"purpose_authority_ref": ""},
                        {"inventory_complete": False}, {"destinations": ()},
                        {"regulations": ("additional-law",)}):
            self.assertEqual(assess_processing(replace(self.review, **changes))["decision"], "review")

    def test_ccpa_choice_is_activity_specific(self):
        review = replace(self.review, regulations=("CCPA",), sale_sharing_opt_out=True)
        self.assertEqual(assess_processing(review)["decision"], "allow")
        self.assertEqual(assess_processing(replace(review, sale_or_sharing=True))["decision"], "block")
        sensitive = replace(review, restricted_sensitive_use=True, sensitive_use_limit=True)
        self.assertEqual(assess_processing(sensitive)["reasons"], ["sensitive_use_limit"])

    def test_hipaa_baa_is_not_a_substitute_for_safeguards(self):
        review = replace(self.review, regulations=("HIPAA",), contains_phi=True)
        self.assertEqual(assess_processing(review)["decision"], "review")
        with_baa = replace(review, destinations=(replace(self.dest, baa_ref="baa"),))
        self.assertEqual(assess_processing(with_baa)["decision"], "allow")
        missing_safeguards = replace(with_baa, destinations=(replace(with_baa.destinations[0], safeguards_ref=""),))
        self.assertEqual(assess_processing(missing_safeguards)["decision"], "review")


class TrainingTests(unittest.TestCase):
    def setUp(self):
        self.gate = TrainingGate()
        self.data = [{"text": "Synthetic refund question", "label": "safe"}]
        self.approval = TrainingApproval("a", dataset_digest(self.data), "classifier",
                                         "authority", "rights", "provenance", NOW + 100)

    def release(self, data=None, now=NOW, purpose="classifier"):
        return self.gate.release(self.data if data is None else data,
                                 approval_id="a", purpose=purpose, now=now)

    def test_missing_approval_and_incomplete_evidence(self):
        with self.assertRaises(PermissionError):
            self.release()
        with self.assertRaises(ValueError):
            self.gate.register(replace(self.approval, rights_review_ref=""), role="privacy_officer")
        with self.assertRaises(PermissionError):
            self.gate.register(self.approval, role="viewer")

    def test_only_exact_dataset_purpose_and_time_are_approved(self):
        self.gate.register(self.approval, role="privacy_officer")
        released = self.release()
        self.assertEqual(released, self.data)
        released[0]["text"] = "modified copy"
        self.assertNotEqual(released, self.data)
        for kwargs in ({"data": [{"text": "changed"}]}, {"now": NOW + 100}, {"purpose": "other"}):
            with self.assertRaises(PermissionError):
                self.release(**kwargs)
        with self.assertRaises(ValueError):
            self.gate.register(self.approval, role="privacy_officer")

    def test_revocation_blocks_next_release(self):
        self.gate.register(self.approval, role="privacy_officer")
        self.gate.revoke("a", role="privacy_officer")
        with self.assertRaises(PermissionError):
            self.release()


if __name__ == "__main__":
    unittest.main()
