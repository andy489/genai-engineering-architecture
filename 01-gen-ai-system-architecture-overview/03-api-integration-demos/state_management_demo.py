import time
from typing import List, Dict, Optional

class SessionStore:
    def __init__(self):
        # Mocks a fast external key-value store (like Redis)
        self.store: Dict[str, Dict] = {}

    def save(self, session_id: str, history: List[Dict], last_active: float):
        self.store[session_id] = {
            "history": history.copy(),
            "last_active": last_active
        }

    def get(self, session_id: str) -> Optional[Dict]:
        return self.store.get(session_id)

    def delete(self, session_id: str):
        if session_id in self.store:
            del self.store[session_id]

# Token estimation (rough estimate just for demonstration)
def estimate_tokens(text: str) -> int:
    return len(text.split()) * 2 + 10

class GloboAssistChat:
    def __init__(self, store: SessionStore):
        self.store = store
        self.max_tokens = 4000
    
    def format_progress(self, current: int, maximum: int) -> str:
        pct = (current / maximum) * 100
        filled = min(int(pct / 5), 20)
        bar = "█" * filled + "░" * max(0, 20 - filled)
        return f"[{bar}] {int(pct)}%"

    def phase_1_build_state(self):
        print("\n═══ PHASE 1: Building conversation state ═══")
        print("Session: sess_a1b2 | User: user_7391")
        
        # Simulating conversation
        conversation = [
            {"role": "Customer", "text": "Hi, I'm looking for wireless speakers"},
            {"role": "GloboAssist", "text": "I'd recommend the Globomantics Pro, they have excellent bass."},
            {"role": "Customer", "text": "Do they come in black?"},
            {"role": "GloboAssist", "text": "Yes, they do. Would you like to ship them?"},
            {"role": "Customer", "text": "Yes, ship to 123 Oak St."},
            {"role": "GloboAssist", "text": "Got it. Anything else I can help you with today?"},
            {"role": "Customer", "text": "What's your return policy?"},
            {"role": "GloboAssist", "text": "You can return most items within 30 days of purchase..."},
            {"role": "Customer", "text": "Actually, show me headphones instead"},
        ]
        
        cumulative_tokens = 0
        history = []
        for i, turn in enumerate(conversation, 1):
            history.append(turn)
            # Simulating token growth artificially for the sake of the demo threshold
            cumulative_tokens += estimate_tokens(turn['text']) * 35
            
            # Save to external store so state survives between requests
            self.store.save("sess_a1b2", history, time.time())
            
            print(f"Turn {i:2d} │ {turn['role']}: \"{turn['text'][:35]}...\"".ljust(58) + 
                  f"│ Tokens: {cumulative_tokens:4d} / {self.max_tokens} {self.format_progress(cumulative_tokens, self.max_tokens)}")
            
            if cumulative_tokens > self.max_tokens:
                print("CONTEXT BUDGET EXCEEDED — triggering truncation strategies")
                break
        
        return history

    def phase_2_compare_strategies(self, history):
        print("\n═══ PHASE 2: Truncation strategies comparison ═══")
        print("┌─────────────────┬────────┬──────────────────────────────────────┐")
        print("│ Strategy        │ Tokens │ What's preserved / lost              │")
        print("├─────────────────┼────────┼──────────────────────────────────────┤")
        
        # 1. Sliding Window (K=4)
        sw_tokens = sum(estimate_tokens(t['text']) * 35 for t in history[-3:])
        print(f"│ Sliding window  │ {sw_tokens:6d} │ ✓ Turns 3-5                          │")
        print("│   (K=3)         │        │ ✗ Lost: \"Globomantics Pro\" preference│")
        print("│                 │        │ ✗ Lost: shipping address from T5     │")
        print("├─────────────────┼────────┼──────────────────────────────────────┤")
        
        # 2. Extractive Summary (Condensing history down to core entities)
        summary = "User interested in Globomantics Pro. Shipping to 123 Oak St. Asked about return policy."
        ext_tokens = 320
        print(f"│ Extractive      │ {ext_tokens:6d} │ ✓ \"User interested in Globomantics   │")
        print("│   summary       │        │   Pro. Shipping to 123 Oak St.       │")
        print("│                 │        │   Asked about return policy.\"        │")
        print("│                 │        │ ✗ Lost: conversation flow details    │")
        print("├─────────────────┼────────┼──────────────────────────────────────┤")
        
        # 3. Selective retention
        sel_tokens = 900
        print(f"│ Selective       │ {sel_tokens:6d} │ ✓ Turn 2 (product preference)        │")
        print("│   retention     │        │ ✓ Turn 5 (shipping address)          │")
        print("│                 │        │ ✗ Lost: return policy turns (info)   │")
        print("└─────────────────┴────────┴──────────────────────────────────────┘")
        
        compression = (1-ext_tokens/4200) * 100
        print(f"Recommendation: Extractive summary, best compression ({compression:.2f}%) and preserves key entities")
        
        # Save summary back to session store for Phase 3
        self.store.save("sess_a1b2", [{"role": "system", "text": f"PREVIOUS CONTEXT: {summary}"}, history[-1]], time.time())

    def phase_3_session_recovery(self):
        print("\n═══ PHASE 3: Session recovery ═══")
        print("[Simulating disconnect...]")
        time.sleep(2)  # Short pause simulates user switching devices
        print("A few seconds later, user reconnects from a different device...")
        print("Looking up session sess_a1b2 for user_7391...")
        
        session = self.store.get("sess_a1b2")
        if session:
            elapsed = int(time.time() - session['last_active'])
            print(f"✓ Session found! Last activity: {elapsed} seconds ago.")
            summary = session['history'][0]['text'].replace("PREVIOUS CONTEXT: ", "")
            print(f"Context summary: \"{summary}\"")
            print("→ GloboAssist: \"Welcome back! We were looking at headphones. Would you like to continue?\"")

    def phase_4_expired_recovery(self):
        print("\n═══ PHASE 4: Session recovery (expired) ═══")
        print("Looking up session sess_expired for user_7391...")
        
        session = self.store.get("sess_expired")
        if not session:
            print("✗ Session not found (TTL expired or never existed).")
            print("→ GloboAssist: \"Hi there! How can I help you today?\"")
            print("Privacy note: Authenticated sessions retained 30 days, then PII redacted. Guest sessions purged at TTL (30 min).")

if __name__ == "__main__":
    store = SessionStore()
    app = GloboAssistChat(store)
    
    # Run the 4 demonstration phases
    history = app.phase_1_build_state()
    app.phase_2_compare_strategies(history)
    app.phase_3_session_recovery()
    app.phase_4_expired_recovery()
