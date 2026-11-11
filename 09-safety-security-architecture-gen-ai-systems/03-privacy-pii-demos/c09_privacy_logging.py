"""Section 9: privacy decisions made executable, using synthetic data only.

Run: python c09_privacy_logging.py
Standard library only; no API calls, real users, or model training.
Governance evidence is supplied by trusted operators, not inferred by this code.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import sqlite3
import textwrap
import unicodedata
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from itertools import zip_longest


# ==================== SECTION 9 START ====================
# 1. Minimize before logging. Pseudonymization is not anonymization.

def hash_user_id(user_id: str, *, key: bytes, tenant: str, key_id: str = "demo-v1") -> str:
    """Tenant-scoped HMAC; unlike a plain hash, guessing IDs requires the key.

    Use stable, canonical internal IDs. Never store the key beside audit records.
    This demo generates an ephemeral key; real deployments need managed keys and
    a rotation/subject-lookup plan that covers historical key versions.
    """
    if len(key) < 32 or not user_id or not tenant or not key_id:
        raise ValueError("A 32-byte key, user ID, tenant, and key ID are required")
    material = json.dumps(["security-audit", tenant, user_id], ensure_ascii=True).encode()
    # Keep 128 bits of the HMAC for a compact pseudonym, never just a short hash prefix.
    return f"{key_id}:" + hmac.new(key, material, hashlib.sha256).hexdigest()[:32]


def redact(message: str) -> str:
    """Illustrative patterns, NOT comprehensive PII detection or HIPAA de-identification."""
    if len(message) > 12_000:
        raise ValueError("Demo input limit exceeded")
    message = unicodedata.normalize("NFKC", message)
    patterns = (
        (r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[EMAIL]"),
        (r"\b(?:patient|member)[ -]?id\s*[:=]?\s*[A-Z0-9-]+", "[HEALTH_ID]"),
        (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]"),
        (r"\b(?:password|api[_ -]?key)\s*[:=]\s*[^\s;,]+", "[SECRET]"),
    )
    for pattern, replacement in patterns:
        message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)
    # Strip control/format characters; JSON encoding handles quotes and backslashes.
    return " ".join("".join(
        " " if unicodedata.category(char).startswith("C") else char for char in message
    ).split())


def truncate(message: str, length: int = 100) -> str:
    """Bound displayed characters, including the suffix. Redact BEFORE calling this."""
    if type(length) is not int or length < 3:
        raise ValueError("length must be an integer of at least 3")
    return message if len(message) <= length else message[:length - 3] + "..."


@dataclass(frozen=True)
class AuditPolicy:
    policy_id: str
    authority_ref: str
    retention_days: int
    purpose: str = "security_audit"

    def __post_init__(self) -> None:
        if (not self.policy_id or not self.authority_ref or self.purpose != "security_audit"
                or type(self.retention_days) is not int or self.retention_days < 1):
            raise ValueError("A reviewed audit policy and positive retention period are required")


@dataclass(frozen=True)
class AuditRecord:
    event_id: str
    subject: str
    decision: str
    purpose: str
    policy_id: str
    authority_ref: str
    created_at: int
    expires_at: int
    # Closed schema: there is deliberately no prompt, response, email, or preview.


def build_audit_record(user_id: str, decision: str, policy: AuditPolicy, *,
                       key: bytes, tenant: str, now: int) -> AuditRecord:
    if decision not in {"allow", "block", "review"}:
        raise ValueError("Unknown safety decision")
    return AuditRecord(
        secrets.token_hex(16), hash_user_id(user_id, key=key, tenant=tenant),
        decision, policy.purpose, policy.policy_id, policy.authority_ref,
        now, now + policy.retention_days * 86_400,
    )


# 2. Store only that schema; enforce access, expiry, holds, and deletion.
class AuditStore:
    """Real in-memory SQLite operations on two explicitly LOCAL copies.

    Roles are trusted application context in this example, not authentication.
    A real service must derive them from verified identity, never request fields.
    """
    COPIES = ("application", "provider_simulation")

    def __init__(self) -> None:
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            CREATE TABLE records (
                copy TEXT NOT NULL, event_id TEXT NOT NULL, subject TEXT NOT NULL,
                decision TEXT NOT NULL CHECK(decision IN ('allow','block','review')),
                purpose TEXT NOT NULL CHECK(purpose = 'security_audit'),
                policy_id TEXT NOT NULL, authority_ref TEXT NOT NULL,
                created_at INTEGER NOT NULL, expires_at INTEGER NOT NULL,
                PRIMARY KEY(copy, event_id), CHECK(expires_at > created_at)
            );
            CREATE INDEX subject_lookup ON records(subject);
            CREATE TABLE holds (event_id TEXT PRIMARY KEY, authority_ref TEXT NOT NULL);
            CREATE TABLE tombstones (event_id TEXT PRIMARY KEY);
        """)

    @staticmethod
    def require(role: str, *allowed: str) -> None:
        if role not in allowed:
            raise PermissionError("Operation not permitted")

    def add(self, record: AuditRecord, *, now: int) -> bool:
        """Used for ingestion and restore: deleted/expired records cannot return."""
        if record.expires_at <= now or self.db.execute(
            "SELECT 1 FROM tombstones WHERE event_id = ?", (record.event_id,)
        ).fetchone():
            return False
        inserted = 0
        with self.db:
            for copy in self.COPIES:
                inserted += self.db.execute(
                    "INSERT INTO records VALUES (?,?,?,?,?,?,?,?,?) "
                    "ON CONFLICT(copy, event_id) DO NOTHING",
                    (copy, *asdict(record).values()),
                ).rowcount
        return inserted > 0

    def export_subject(self, subject: str, *, role: str, now: int) -> list[dict]:
        self.require(role, "privacy_officer")
        return [dict(row) for row in self.db.execute("""
            SELECT * FROM records WHERE subject = ? AND copy = 'application'
            AND (expires_at > ? OR event_id IN (SELECT event_id FROM holds))
            ORDER BY created_at, event_id
        """, (subject, now))]

    def hold(self, event_id: str, authority_ref: str, *, role: str) -> None:
        self.require(role, "privacy_officer")
        if not authority_ref or not self.db.execute(
            "SELECT 1 FROM records WHERE event_id = ?", (event_id,)
        ).fetchone():
            raise ValueError("Hold needs an existing event and a documented authority")
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO holds VALUES (?,?)", (event_id, authority_ref))

    def release_hold(self, event_id: str, *, role: str) -> None:
        self.require(role, "privacy_officer")
        with self.db:
            self.db.execute("DELETE FROM holds WHERE event_id = ?", (event_id,))

    def _delete(self, event_ids: list[str]) -> dict:
        counts = {copy: 0 for copy in self.COPIES}
        with self.db:
            for event_id in event_ids:
                self.db.execute("INSERT OR IGNORE INTO tombstones VALUES (?)", (event_id,))
                for copy in self.COPIES:
                    counts[copy] += self.db.execute(
                        "DELETE FROM records WHERE copy = ? AND event_id = ?", (copy, event_id)
                    ).rowcount
        return counts

    def delete_subject(self, subject: str, *, role: str) -> dict:
        """Run AFTER identity verification and an authorized rights assessment."""
        self.require(role, "privacy_officer")
        rows = self.db.execute("""
            SELECT DISTINCT r.event_id, h.authority_ref FROM records r
            LEFT JOIN holds h ON r.event_id = h.event_id WHERE subject = ?
        """, (subject,)).fetchall()
        held = sum(row["authority_ref"] is not None for row in rows)
        counts = self._delete([row["event_id"] for row in rows if row["authority_ref"] is None])
        return {"deleted_copies": counts, "held_events": held,
                "status": "partial_hold" if held else "local_copies_complete"}

    def purge_expired(self, *, now: int, role: str) -> dict:
        self.require(role, "retention_worker")
        rows = self.db.execute("""
            SELECT DISTINCT event_id FROM records WHERE expires_at <= ?
            AND event_id NOT IN (SELECT event_id FROM holds)
        """, (now,)).fetchall()
        return self._delete([row["event_id"] for row in rows])

    def close(self) -> None:
        self.db.close()


# 3. Gate processing using a reviewed purpose and the COMPLETE provider inventory.
@dataclass(frozen=True)
class Destination:
    name: str
    region: str
    terms_ref: str = ""
    safeguards_ref: str = ""
    transfer_required: bool = False  # Determined by a prior jurisdiction assessment.
    transfer_ref: str = ""
    baa_ref: str = ""


@dataclass(frozen=True)
class ProcessingReview:
    regulations: tuple[str, ...]
    assessment_ref: str
    purpose_authority_ref: str
    inventory_complete: bool
    destinations: tuple[Destination, ...]
    contains_phi: bool = False
    sale_or_sharing: bool = False
    sale_sharing_opt_out: bool = False
    restricted_sensitive_use: bool = False
    sensitive_use_limit: bool = False


def assess_processing(review: ProcessingReview) -> dict:
    """Checks documented prerequisites, not legal applicability or document validity.

    References must come from a protected, reviewed policy registry in deployment.
    CCPA choices here are scoped to the relevant activity, not all processing.
    """
    reasons = []
    if not review.assessment_ref or not review.purpose_authority_ref:
        reasons.append("purpose_or_applicability_unreviewed")
    if not review.inventory_complete or not review.destinations:
        reasons.append("provider_inventory_incomplete")
    if set(review.regulations) - {"GDPR", "CCPA", "HIPAA"}:
        reasons.append("additional_jurisdiction_review_required")
    for dest in review.destinations:
        if not all((dest.name, dest.region, dest.terms_ref, dest.safeguards_ref)):
            reasons.append("provider_terms_or_safeguards_missing")
        if dest.transfer_required and not dest.transfer_ref:
            reasons.append("transfer_assessment_missing")
        if "HIPAA" in review.regulations and review.contains_phi and not dest.baa_ref:
            reasons.append("business_associate_agreement_missing")
    if "CCPA" in review.regulations:
        if review.sale_or_sharing and review.sale_sharing_opt_out:
            return {"decision": "block", "reasons": ["sale_sharing_opt_out"]}
        if review.restricted_sensitive_use and review.sensitive_use_limit:
            return {"decision": "block", "reasons": ["sensitive_use_limit"]}
    return {"decision": "review" if reasons else "allow", "reasons": sorted(set(reasons))}


# 4. Training is a different purpose: bind approval to exact data and enforce it.
def dataset_digest(records: list[dict]) -> str:
    canonical = json.dumps(records, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


@dataclass(frozen=True)
class TrainingApproval:
    approval_id: str
    dataset_digest: str
    purpose: str
    authority_ref: str
    rights_review_ref: str
    provenance_ref: str
    expires_at: int


class TrainingGate:
    """Local trusted approval registry; no model is trained by this example."""
    def __init__(self) -> None:
        self.approvals: dict[str, TrainingApproval] = {}
        self.revoked: set[str] = set()

    def register(self, approval: TrainingApproval, *, role: str) -> None:
        AuditStore.require(role, "privacy_officer")
        if not all((approval.approval_id, approval.dataset_digest, approval.purpose,
                    approval.authority_ref, approval.rights_review_ref, approval.provenance_ref)):
            raise ValueError("Approval evidence is incomplete")
        if approval.approval_id in self.approvals:
            raise ValueError("Approval IDs are immutable; issue a new version")
        self.approvals[approval.approval_id] = approval

    def revoke(self, approval_id: str, *, role: str) -> None:
        AuditStore.require(role, "privacy_officer")
        self.revoked.add(approval_id)

    def release(self, records: list[dict], *, approval_id: str, purpose: str, now: int) -> list[dict]:
        approval = self.approvals.get(approval_id)
        if (approval is None or approval_id in self.revoked or approval.expires_at <= now
                or approval.purpose != purpose or approval.dataset_digest != dataset_digest(records)):
            raise PermissionError("Excluded from training: missing, expired, revoked, or mismatched approval")
        # Defensive deep copy: subsequent edits cannot silently change this release.
        return json.loads(json.dumps(records, allow_nan=False))


# 5. Presentation helpers and deterministic scenarios; only identifiers vary.
def side_by_side(before: dict, after: dict) -> None:
    def lines(value: dict) -> list[str]:
        return [part for line in json.dumps(value, indent=2, ensure_ascii=True).splitlines()
                for part in textwrap.wrap(line, width=58, replace_whitespace=False,
                                          drop_whitespace=False) or [""]]
    print(f"{'BEFORE: synthetic raw log':58} | AFTER: necessary metadata")
    print("-" * 119)
    for left, right in zip_longest(lines(before), lines(after), fillvalue=""):
        print(f"{left:58} | {right}")


def emit(title: str, value: object) -> None:
    print(f"\n=== {title} ===")
    print(json.dumps(value, indent=2))


def demo() -> None:
    print("SECTION 9 - REGULATORY LANDSCAPE FOR GENAI SYSTEMS")
    print("Synthetic local demonstration; controls are not compliance certification.\n")
    now = int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp())
    key = secrets.token_bytes(32)  # Ephemeral, never printed or persisted.
    policy = AuditPolicy("audit-demo-v1", "reviewed-purpose-demo", retention_days=7)
    user = "demo@example.com"
    message = "Contact demo@example.com; patient ID: H-9912 about a medical appointment next Tuesday."
    record = build_audit_record(user, "allow", policy, key=key, tenant="course", now=now)
    side_by_side(
        {"email": user, "prompt": message, "response": "Private medical details (synthetic).",
         "decision": "allow", "retain_forever": True, "training_eligible": True},
        asdict(record),
    )
    emit("REDACT, THEN TRUNCATE: DISPLAY ONLY, NOT STORED", {
        "preview": truncate(redact(message), 55),
        "lesson": "Medical context survives redaction. The audit schema excludes all message content.",
        "pseudonym": "A keyed token can still be personal data.",
    })
    store = AuditStore()
    try:
        store.add(record, now=now)
        try:
            store.export_subject(record.subject, role="viewer", now=now)
        except PermissionError:
            emit("RESTRICTED ACCESS", {"viewer": "denied"})
        emit("VERIFIED RIGHTS WORKFLOW: ACCESS", {
            "records_found": len(store.export_subject(record.subject, role="privacy_officer", now=now))
        })
        # This tuple is a local backup snapshot, intentionally not modified by deletion.
        backup = (record,)
        emit("DELETE ACROSS LOCAL COPIES", store.delete_subject(record.subject, role="privacy_officer"))
        restored = sum(store.add(item, now=now) for item in backup)
        emit("RESTORE WITH DELETION LEDGER", {"restored": restored, "suppressed": len(backup) - restored})

        expiring = build_audit_record("demo-2", "review", policy, key=key, tenant="course", now=now)
        held = build_audit_record("demo-3", "block", policy, key=key, tenant="course", now=now)
        store.add(expiring, now=now)
        store.add(held, now=now)
        store.hold(held.event_id, "documented-hold-demo", role="privacy_officer")
        later = now + 8 * 86_400
        emit("ADVANCE CLOCK: RETENTION ENFORCEMENT", store.purge_expired(now=later, role="retention_worker"))
        emit("DOCUMENTED HOLD: PARTIAL DELETION", store.delete_subject(held.subject, role="privacy_officer"))
        store.release_hold(held.event_id, role="privacy_officer")
        emit("RELEASE HOLD AND PURGE", store.purge_expired(now=later, role="retention_worker"))
    finally:
        store.close()

    provider = Destination("model-provider", "EU", "terms-demo", "safeguards-demo")
    subprocessor = Destination("support-subprocessor", "US", "terms-demo", "safeguards-demo", True)
    review = ProcessingReview(("GDPR",), "scope-demo", "purpose-demo", True, (provider, subprocessor))
    emit("EU STORAGE + UNREVIEWED ONWARD TRANSFER", assess_processing(review))
    reviewed = replace(review, destinations=(provider, replace(subprocessor, transfer_ref="transfer-review-demo")))
    emit("COMPLETE REVIEWED ROUTE", assess_processing(reviewed))
    emit("CCPA: HONOR THE APPLICABLE OPT-OUT", assess_processing(replace(
        reviewed, regulations=("CCPA",), sale_or_sharing=True, sale_sharing_opt_out=True)))
    emit("CCPA: HONOR A SENSITIVE-USE LIMIT", assess_processing(replace(
        reviewed, regulations=("CCPA",), restricted_sensitive_use=True, sensitive_use_limit=True)))
    emit("HIPAA: PHI ROUTE WITHOUT BUSINESS AGREEMENTS", assess_processing(replace(
        reviewed, regulations=("HIPAA",), contains_phi=True)))

    gate = TrainingGate()
    candidate = [asdict(record)]  # Deliberately try the audit-to-training shortcut.
    try:
        gate.release(candidate, approval_id="none", purpose="safety_evaluation", now=now)
    except PermissionError:
        emit("AUDIT DATA: NO AUTOMATIC TRAINING REUSE", {"decision": "exclude"})
    # A separate, wholly synthetic dataset; no deleted audit record is reused.
    dataset = [{"text": "Explain the fictional refund policy.", "label": "safe"}]
    approval = TrainingApproval("approval-demo", dataset_digest(dataset), "safety_classifier",
                                "training-authority-demo", "rights-review-demo", "synthetic-v1", later)
    gate.register(approval, role="privacy_officer")
    released = gate.release(dataset, approval_id=approval.approval_id, purpose="safety_classifier", now=now)
    emit("SEPARATELY APPROVED DATASET", {"released_rows": len(released), "approval": approval.approval_id})
    try:
        gate.release(dataset + [{"text": "Unapproved extra row"}],
                     approval_id=approval.approval_id, purpose="safety_classifier", now=now)
    except PermissionError:
        emit("CHANGED DATASET: APPROVAL NO LONGER MATCHES", {"decision": "exclude"})
    gate.revoke(approval.approval_id, role="privacy_officer")
    try:
        gate.release(dataset, approval_id=approval.approval_id, purpose="safety_classifier", now=now)
    except PermissionError:
        emit("REVOKED APPROVAL", {"next_release": "denied"})
    print("\nDeleting a log does not untrain a model. No model was trained here.")
    print("Retention is policy-specific; 7 days is a demo choice, not a legal deadline.")
    print("Provider copies are local simulations; real remote deletion requires acknowledgement.")
    print("\nDemo complete. Run: python -m unittest -v test_c09_privacy_logging")


# ===================== SECTION 9 END =====================

if __name__ == "__main__":
    demo()
