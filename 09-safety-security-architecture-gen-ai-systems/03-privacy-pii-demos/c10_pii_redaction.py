"""Section 10: local NER + rules, context policy, buffered streams, and safe logs.

Setup: python -m pip install -r requirements-c10.txt
Demo:  python c10_pii_redaction.py
All original text displayed by the demo is synthetic. No network inference.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Callable, Iterable


# ==================== SECTION 10 START ====================
MAX_CHARS = 12_000
MAX_FRAMES = 4_096
CONTEXTS = {"support", "healthcare"}  # Trusted application policy, not prompt instructions.
PATTERNS = (
    ("EMAIL", re.compile(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")),
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("ID", re.compile(r"\b(?:patient|member|customer)[ -]?id\s*[:=]\s*([A-Z0-9-]{3,})", re.I)),
    # Illustrative North American format. Extend and validate for other locales.
    ("PHONE", re.compile(r"(?<!\w)(?:\+?1[ .-]?)?(?:\(\d{3}\)|\d{3})[ .-]?\d{3}[ .-]?\d{4}(?!\w)")),
)


class RedactionError(Exception):
    """Static error codes only: never interpolate untrusted input or engine errors."""


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    label: str
    source: str


@dataclass(frozen=True)
class Redacted:
    text: str = field(repr=False)
    counts: tuple[tuple[str, int], ...]
    sources: tuple[str, ...]


@lru_cache(maxsize=1)
def load_ner():
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm", disable=["parser", "tagger", "lemmatizer", "attribute_ruler"])
        if "ner" not in nlp.pipe_names:
            raise ValueError("Missing NER component")
        return nlp
    except Exception:
        raise RedactionError("ner_unavailable") from None


class PIIRedactor:
    def __init__(self, ner=None):
        # Injection is for unit tests; the demo uses the actual trained spaCy NER.
        self.ner = load_ner() if ner is None else ner

    def redact(self, text: str, *, context: str = "support") -> Redacted:
        if context not in CONTEXTS:
            raise RedactionError("unknown_context")
        if not isinstance(text, str) or not text.strip() or len(text) > MAX_CHARS:
            raise RedactionError("invalid_input")
        text = unicodedata.normalize("NFKC", text)
        if len(text) > MAX_CHARS:
            raise RedactionError("input_too_large")
        # Ambiguous invisible characters may evade simple patterns: withhold for review.
        if any(unicodedata.category(c).startswith("C") and c not in "\r\n\t" for c in text):
            raise RedactionError("unsupported_control_character")
        spans = []
        for label, pattern in PATTERNS:
            for match in pattern.finditer(text):
                start, end = match.span(1 if label == "ID" else 0)
                spans.append(Span(start, end, label, "regex"))
        try:
            entities = self.ner(text).ents
            for entity in entities:
                label = {"PERSON": "PERSON", "GPE": "LOCATION", "LOC": "LOCATION"}.get(entity.label_)
                if context == "healthcare" and entity.label_ in {"DATE", "TIME"}:
                    label = entity.label_
                if label:
                    spans.append(Span(entity.start_char, entity.end_char, label, "ner"))
        except Exception:
            raise RedactionError("ner_failed") from None

        # Union overlapping spans: do not expose an uncovered suffix or shift offsets
        # by editing the text before all detections have been collected.
        merged: list[tuple[int, int, set[str]]] = []
        for span in sorted(spans, key=lambda s: (s.start, s.end)):
            if not 0 <= span.start < span.end <= len(text):
                raise RedactionError("invalid_detection")
            if merged and span.start < merged[-1][1]:
                start, end, labels = merged[-1]
                merged[-1] = (start, max(end, span.end), labels | {span.label})
            else:
                merged.append((span.start, span.end, {span.label}))
        pieces, counts, cursor = [], Counter(), 0
        for start, end, labels in merged:
            label = next(iter(labels)) if len(labels) == 1 else "PII"
            pieces.extend((text[cursor:start], f"[REDACTED_{label}]"))
            counts[label] += 1
            cursor = end
        pieces.append(text[cursor:])
        return Redacted("".join(pieces), tuple(sorted(counts.items())),
                        tuple(sorted({s.source for s in spans})))


def redact_pii(text: str, *, context: str = "support") -> str:
    """Public convenience function; missing/failed NER withholds the input."""
    return PIIRedactor().redact(text, context=context).text


@dataclass(frozen=True)
class Frame:
    text: str = field(default="", repr=False)
    end_of_message: bool = False


def redact_stream(frames: Iterable[Frame], redactor: PIIRedactor, *, context: str = "support") -> Redacted:
    """One bounded logical message; emit nothing until an explicit END and EOF.

    END is supplied by the trusted framing layer, never inferred from newlines or
    user text. Chunk-local NER cannot reliably protect entities split across chunks.
    This intentionally trades token-by-token latency for complete-message context.
    """
    buffer, size, ended = [], 0, False
    try:
        for index, frame in enumerate(frames):
            if index >= MAX_FRAMES:
                raise RedactionError("too_many_frames")
            if not isinstance(frame, Frame) or ended or type(frame.end_of_message) is not bool:
                raise RedactionError("invalid_stream_frame")
            if not isinstance(frame.text, str):
                raise RedactionError("invalid_stream_frame")
            size += len(frame.text)
            if size > MAX_CHARS:
                raise RedactionError("stream_too_large")
            buffer.append(frame.text)
            ended = frame.end_of_message
        if not ended:
            raise RedactionError("incomplete_stream")
        return redactor.redact("".join(buffer), context=context)
    except RedactionError:
        raise
    except Exception:
        raise RedactionError("stream_failed") from None
    finally:
        buffer.clear()  # Releases references; Python strings are not securely zeroized.


class DemoModel:
    """Local downstream spy. Records the actual payload; makes no API call."""
    def __init__(self):
        self.received: list[str] = []

    def send(self, text: str) -> None:
        self.received.append(text)


class RedactionPipeline:
    """Only the redactor's output reaches the application store or model adapter.

    Application storage retains redacted text for the demo's task; audit logging
    stores only counts and static outcomes. Redacted text can still be sensitive.
    """
    def __init__(self, redactor: PIIRedactor, model: DemoModel):
        self.redactor, self.model = redactor, model
        self.db = sqlite3.connect(":memory:")
        self.db.executescript("""
            CREATE TABLE prompts (id INTEGER PRIMARY KEY, redacted_prompt TEXT NOT NULL);
            CREATE TABLE audit (event TEXT NOT NULL, details TEXT NOT NULL);
        """)

    def _process(self, operation: Callable[[], Redacted]) -> dict:
        try:
            result = operation()
        except RedactionError as error:
            event = {"decision": "review", "reason": str(error)}
            with self.db:
                self.db.execute("INSERT INTO audit VALUES (?,?)", ("withheld", json.dumps(event)))
            return event
        self.model.send(result.text)
        with self.db:
            self.db.execute("INSERT INTO prompts(redacted_prompt) VALUES (?)", (result.text,))
            event = {"decision": "redacted", "counts": dict(result.counts), "sources": result.sources}
            self.db.execute("INSERT INTO audit VALUES (?,?)", ("redacted", json.dumps(event)))
        return event

    def process(self, text: str, *, context: str = "support") -> dict:
        return self._process(lambda: self.redactor.redact(text, context=context))

    def process_stream(self, frames: Iterable[Frame], *, context: str = "support") -> dict:
        return self._process(lambda: redact_stream(frames, self.redactor, context=context))

    def close(self):
        self.db.close()


SYNTHETIC_PROMPT = (
    "My name is John Smith. I live in London. "
    "Email john.smith@example.com or call +1 (202) 555-0147. "
    "Patient ID: AB-12345. SSN: 123-45-6789. My appointment is on Tuesday."
)


def demo(scenario: str = "all") -> None:
    redactor = PIIRedactor()
    model = DemoModel()
    pipeline = RedactionPipeline(redactor, model)
    try:
        print("SECTION 10 - PII DETECTION & REDACTION PIPELINES")
        print("Synthetic inputs; real local spaCy NER; simulated model destination.\n")
        if scenario in {"all", "basic"}:
            print("=== ORIGINAL: SYNTHETIC TEACHING FIXTURE ONLY ===")
            print(SYNTHETIC_PROMPT)
            event = pipeline.process(SYNTHETIC_PROMPT, context="healthcare")
            print("\n=== REDACTED: ACTUAL MODEL PAYLOAD ===")
            print(model.received[-1])
            print("\n=== APPLICATION STORE: REDACTED TEXT ONLY ===")
            print(pipeline.db.execute("SELECT redacted_prompt FROM prompts ORDER BY id DESC LIMIT 1").fetchone()[0])
            print("\n=== AUDIT: COUNTS ONLY ===")
            print(json.dumps(event, indent=2))
        if scenario in {"all", "context"}:
            text = "John Smith has an appointment on Tuesday in London."
            print("\n=== TRUSTED CONTEXT POLICY ===")
            for context in ("support", "healthcare"):
                print(context.upper() + ":", redactor.redact(text, context=context).text)
            print("Healthcare policy additionally masks detected dates and times.")
        if scenario in {"all", "stream"}:
            frames = [Frame("Email john.smi"), Frame("th@example."), Frame("com; phone +1 (202) "),
                      Frame("555-0147; patient ID: AB-"), Frame("12345.", True)]
            print("\n=== STREAM: IDENTIFIERS CROSS CHUNK BOUNDARIES ===")
            print("Five frames buffered; no text released before complete-message detection.")
            print(json.dumps(pipeline.process_stream(frames)))
            print("MODEL RECEIVED:", model.received[-1])
            before = len(model.received)
            print("\n=== INTERRUPTED STREAM: WITHHOLD ===")
            print(json.dumps(pipeline.process_stream([Frame("Email john.smi")])))
            print("Additional model calls:", len(model.received) - before)
        print("\nRedaction reduces exposure; it does not prove the absence of sensitive data.")
    finally:
        pipeline.close()


# ===================== SECTION 10 END =====================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=("all", "basic", "context", "stream"), default="all")
    args = parser.parse_args()
    try:
        demo(args.scenario)
    except RedactionError:
        parser.exit(2, "PII detector unavailable. Install requirements-c10.txt; no input was released.\n")
