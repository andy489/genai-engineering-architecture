"""Section 11: minimal records, scoped memory, retention, and user deletion.
Run: python c11_data_minimization.py (standard library; synthetic data only).
"""
import hashlib
import hmac
import json
import secrets
import time
from copy import deepcopy

# ==================== SECTION 11 START ====================
class MinimalMemory:
    """One trusted tenant context; session IDs come from the application.
    Demo boundary, not authentication. Pseudonyms are not anonymous data.
    """
    def __init__(self, tenant, key, retention_seconds=60, clock=time.time):
        if not tenant or len(key) < 32 or retention_seconds <= 0:
            raise ValueError("Tenant, strong key, and positive retention required")
        self.tenant, self.key, self.ttl, self.clock = tenant, key, retention_seconds, clock
        self._records = {}  # (session, random record ID) -> four-field record

    def hash_user_id(self, user_id):
        material = json.dumps([self.tenant, user_id]).encode()
        return hmac.new(self.key, material, hashlib.sha256).hexdigest()

    def purge_expired(self):
        cutoff = self.clock() - self.ttl
        expired = [k for k, r in self._records.items() if r["timestamp"] <= cutoff]
        for key in expired:
            del self._records[key]
        return len(expired)

    def store(self, user_id, session, decision, flags=()):
        if not user_id or not session or decision not in {"allow", "block", "review"}:
            raise ValueError("Invalid decision or scope")
        if set(flags) - {"pii", "injection", "borderline"}:
            raise ValueError("Flags must use the controlled vocabulary")
        self.purge_expired()
        self._records[session, secrets.token_hex(8)] = {
            "user_hash": self.hash_user_id(user_id), "timestamp": self.clock(),
            "decision": decision, "flags": sorted(set(flags)),
        }

    def read(self, user_hash, session):
        self.purge_expired()  # Expired memory cannot be returned to a caller.
        return deepcopy([r for (s, _), r in self._records.items()
                         if s == session and r["user_hash"] == user_hash])

    def delete_user(self, user_hash):
        matches = [k for k, r in self._records.items() if r["user_hash"] == user_hash]
        for key in matches:
            del self._records[key]  # All sessions for this user in this tenant.
        return len(matches)


def demo():
    now = [1_800_000_000]  # Injectable clock: demonstrate expiry without waiting.
    key = secrets.token_bytes(32)  # Ephemeral; never printed. Production: managed key.
    memory = MinimalMemory("tenant-a", key, clock=lambda: now[0])
    memory.store("alice", "chat-1", "review", ("pii",))
    alice, bob = memory.hash_user_id("alice"), memory.hash_user_id("bob")
    print("MINIMAL RECORD:", json.dumps(memory.read(alice, "chat-1")[0], indent=2))
    print("Other session sees:", len(memory.read(alice, "chat-2")))
    other = MinimalMemory("tenant-b", key)
    print("Same user, different tenant token:", other.hash_user_id("alice") != alice)
    now[0] += 60
    print("Expired records removed:", memory.purge_expired())
    memory.store("alice", "chat-1", "review", ("borderline",))
    memory.store("alice", "chat-2", "allow")
    memory.store("bob", "chat-1", "block", ("injection",))
    print("Before deletion:", len(memory._records))
    print("Alice records deleted:", memory.delete_user(alice))
    print("After deletion:", len(memory._records))
    print("Bob records remaining:", len(memory.read(bob, "chat-1")))

# ===================== SECTION 11 END =====================
if __name__ == "__main__":
    demo()
