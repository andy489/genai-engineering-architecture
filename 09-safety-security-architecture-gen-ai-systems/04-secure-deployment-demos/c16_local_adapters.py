"""Adapters: local fixtures, real SQLite delivery deduplication.

No API calls or real users. CLI identity/fault switches are test fixtures only.
"""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
from contextlib import closing


class LocalServices:
    def __init__(self, root, fault=None, revoked=False):
        self.root, self.fault, self.revoked = Path(root), fault, revoked
        self.calls = 0

    def authorize(self, request):
        # Production: verify current server-side identity, tenant, scope and policy.
        if self.revoked or request["subject"] != "demo-user" or request["tenant"] != "tenant-a":
            raise PermissionError("Current authorization denied; recovery halted")

    def retrieve(self, request):
        print("RETRIEVAL: local policy-v1, scoped to tenant-a")
        return {"source": "policy-v1", "trust": "untrusted", "text": "Refunds are available within 30 days."}

    def generate(self, request, context):
        # Production: use a provider timeout, separate policy from untrusted context,
        # and normalize only transient provider failures to TimeoutError.
        self.calls += 1
        if self.fault == "crash":
            print("INJECTED CRASH: generation interrupted before completion.", flush=True)
            os._exit(3)
        if self.fault == "always-timeout" or (self.fault == "timeout" and self.calls == 1):
            raise TimeoutError("Synthetic provider timeout")
        print("GENERATION: local deterministic adapter")
        return {"text": "DEMO_SECRET" if self.fault == "unsafe-output" else context["text"]}

    def validate_output(self, response):
        # Minimal local contract/canary check, not comprehensive moderation or DLP.
        if (not isinstance(response, dict) or not isinstance(response.get("text"), str)
                or not 1 <= len(response["text"]) <= 2000 or "DEMO_SECRET" in response["text"]):
            raise ValueError("Output policy rejected response; release blocked")
        print("OUTPUT CHECK: passed local contract and canary rule")
        return {"approved": True, "policy_version": "demo-v1"}

    def deliver(self, request, response, key):
        # This is a real local receiving service contract: unique key + payload binding.
        self.root.mkdir(parents=True, exist_ok=True)
        payload = json.dumps({"recipient": request["subject"], "tenant": request["tenant"],
                              "response": response}, sort_keys=True)
        fingerprint = hashlib.sha256(payload.encode()).hexdigest()
        with closing(sqlite3.connect(self.root / "deliveries.sqlite3")) as db, db:
            db.execute("CREATE TABLE IF NOT EXISTS deliveries (key TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, payload TEXT NOT NULL)")
            inserted = db.execute("INSERT OR IGNORE INTO deliveries VALUES (?, ?, ?)",
                                  (key, fingerprint, payload)).rowcount
            if db.execute("SELECT fingerprint FROM deliveries WHERE key=?", (key,)).fetchone()[0] != fingerprint:
                raise ValueError("Idempotency key reused with a different payload")
        print("DELIVERY: " + ("inserted once" if inserted else "duplicate suppressed"), flush=True)
        if self.fault == "crash-after-delivery":
            print("INJECTED CRASH: delivery committed, checkpoint still at 4.", flush=True)
            os._exit(3)
        return {"receipt": key}
