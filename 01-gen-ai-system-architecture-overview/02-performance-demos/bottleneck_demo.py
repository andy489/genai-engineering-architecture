# /// script
# dependencies = [
#   "chromadb==1.5.8",
#   "transformers==5.5.4",
#   "torch==2.11.0",
# ]
# ///
"""GloboAssist Bottleneck Demo — Clip 3.2.  Usage: uv run bottleneck_demo.py"""
import time, warnings
from chromadb import Client
from transformers import pipeline, GenerationConfig, logging as tf_logging

tf_logging.set_verbosity_error()
warnings.filterwarnings("ignore", message=".*generation-related arguments.*")

# ── Globomantics product catalog (20 products) ──────────────────────────
PRODUCTS = [
    ("Globomantics Pro Speaker",   "speakers",    "Premium Bluetooth speaker, 360° sound, IPX7 waterproof, 24h battery, USB-C."),
    ("Globomantics Mini",          "speakers",    "Compact portable speaker, IPX5 water resistance, 12h battery, built-in mic."),
    ("Globomantics Max",           "speakers",    "High-fidelity home speaker, Dolby Atmos, Wi-Fi streaming, voice assistant."),
    ("Globomantics Earbuds",       "speakers",    "ANC wireless earbuds, 30h total battery, multipoint Bluetooth connection."),
    ("Globomantics 4K Monitor",     "monitors",    "32-inch 4K IPS, 99% sRGB, USB-C hub, adjustable ergonomic stand."),
    ("Globomantics UltraWide",      "monitors",    "34-inch curved ultrawide, 144Hz, AMD FreeSync Premium, HDR400."),
    ("Globomantics Portable",       "monitors",    "15.6-inch portable USB-C monitor, 1080p IPS, 1.7 lbs, built-in kickstand."),
    ("Globomantics 65W",          "chargers",    "65W GaN USB-C charger, dual ports, foldable prongs, laptop compatible."),
    ("Globomantics Dock",         "chargers",    "4-port charging station, 100W total, LED per-port wattage display."),
    ("Globomantics Wireless Pad", "chargers",    "15W Qi2 wireless pad, magnetic alignment, foreign object detection."),
    ("Globomantics 20K",            "chargers",    "20,000mAh portable battery, 65W USB-C, passthrough charging, digital display."),
    ("Globomantics Hub Pro",      "accessories", "11-in-1 USB-C hub, dual HDMI, Ethernet, SD reader, 100W passthrough."),
    ("Globomantics Cable Kit",    "accessories", "Braided USB-C cables (0.5/1/2m), 240W rated, 40Gbps data transfer."),
    ("Globomantics Band",            "wearables",   "Fitness tracker, heart rate, SpO2, sleep tracking, 7-day battery, swim-proof."),
    ("Globomantics Watch",           "wearables",   "Smartwatch, AMOLED, GPS, NFC payments, 3-day battery life."),
    ("Globomantics Cam",           "smart-home",  "Indoor 2K security camera, night vision, two-way audio, local storage."),
    ("Globomantics Doorbell",      "smart-home",  "Video doorbell, 180° view, package detection, smart-home integration."),
    ("Globomantics 2TB",           "storage",     "Portable SSD, 2TB, 1050MB/s read, IP55 dust and water resistant."),
    ("Globomantics NAS",           "storage",     "4-bay NAS, RAID support, 2.5GbE, built-in media server."),
    ("Globomantics Router",         "networking",  "Wi-Fi 6E mesh kit (3-pack), 7,500 sq ft coverage, 200+ devices."),
]

MODEL = "distilgpt2"
QUERY = "Is the Globomantics Pro waterproof?"
LONG_SYSTEM = ("You are GloboAssist, the Globomantics customer support assistant. "
    "Answer product questions accurately using only the provided context. "
    "Always cite which product specification you are referencing. "
    "If the answer is not in the context, say you don't know. "
    "Be friendly, professional, and concise in your responses.")
SHORT_SYSTEM = "Answer the product question using only the provided context."

# 1/8-block characters give 8× finer bar resolution than whole blocks alone,
# so sub-character differences (e.g. 0.3 ms vs 5 ms on a 2000 ms scale) stay visible.
_EIGHTHS = ["", "▏", "▎", "▍", "▌", "▋", "▊", "▉"]
def bar(ms, mx):
    if mx <= 0 or ms <= 0: return ""
    eighths = int(round(40 * 8 * ms / mx))
    full, rem = divmod(eighths, 8)
    return "█" * full + _EIGHTHS[rem]

def fmt_ms(v):
    """Show 3 decimals for sub-10 ms values so microsecond-scale differences
    (e.g. prompt construction at ~0.1–0.5 ms) aren't rounded to 0.
    Width is 8 to match the dashed-separator width in the summary table."""
    return f"{v:8.3f}" if v < 10 else f"{v:8.0f}"

def fmt_delta(new, old):
    """Inline delta for the waterfall rows; shows ↓ for improvements, ↑ for regressions."""
    if old <= 0 or new <= 0: return ""
    pct = (1 - new/old) * 100
    if abs(pct) < 0.5: return ""
    return f"  {'↓' if pct > 0 else '↑'} {abs(pct):.0f}%"

def pct_cell(old, new):
    """Change cell for the summary table; returns a fixed-width 5-char string."""
    if old <= 0 or new <= 0: return "   — "
    return f"{(1 - new/old) * 100:>+4.0f}%"

def run_pipeline(col, gen, gen_cfg, top_k, system, where=None):
    t0 = time.perf_counter()
    q = {"query_texts": [QUERY], "n_results": top_k}
    if where: q["where"] = where
    res = col.query(**q)
    t1 = time.perf_counter()
    chunks = "\n".join(res["documents"][0])
    prompt = f"{system}\n\nContext:\n{chunks}\n\nQ: {QUERY}\nA:"
    t2 = time.perf_counter()
    gen(prompt, generation_config=gen_cfg, truncation=True)
    t3 = time.perf_counter()
    return [(t1-t0)*1000, (t2-t1)*1000, (t3-t2)*1000]

def show(title, subtitle, labels, ms, prev=None, scale_max=None):
    total = sum(ms)
    mx = scale_max if scale_max else max(ms)
    print(f"\n{'═'*58}\n  {title}\n  Query: \"{QUERY}\"")
    if subtitle: print(f"  Changes: {subtitle}")
    print(f"{'─'*58}")
    for i, (lbl, v) in enumerate(zip(labels, ms)):
        d = fmt_delta(v, prev[i]) if prev else ""
        print(f"  {lbl:<30} {bar(v,mx)} {fmt_ms(v)}ms{d}")
    print(f"{'─'*58}")
    d = fmt_delta(total, sum(prev)) if prev else ""
    print(f"  {'TOTAL':<30} {fmt_ms(total)}ms{d}\n{'═'*58}")
    return total

# ── Setup ────────────────────────────────────────────────────────────────
print("Loading model and building product index...")
gen = pipeline("text-generation", model=MODEL, device=-1)
gen_cfg = GenerationConfig(
    max_new_tokens=200, do_sample=False,
    pad_token_id=gen.tokenizer.eos_token_id,
)
db = Client()
col = db.create_collection("products", metadata={"hnsw:space": "cosine"})
col.add(
    ids=[f"p{i}" for i in range(len(PRODUCTS))],
    documents=[f"{n}: {d}" for n, _, d in PRODUCTS],
    metadatas=[{"name": n, "category": c} for n, c, _ in PRODUCTS],
)
print(f"Indexed {len(PRODUCTS)} products.\n")

L1 = ["Retrieval (top_k=15)",         "Prompt construction", "Model inference"]
L2 = ["Retrieval (top_k=3, filtered)","Prompt construction", "Model inference"]

ms1 = run_pipeline(col, gen, gen_cfg, top_k=15, system=LONG_SYSTEM)
t1  = show("UNOPTIMIZED PIPELINE", None, L1, ms1)
print(f"  Bottlenecks: Retrieval ({ms1[0]/t1*100:.0f}%), Inference ({ms1[2]/t1*100:.0f}%)")

ms2 = run_pipeline(col, gen, gen_cfg, top_k=3, system=SHORT_SYSTEM, where={"category": "speakers"})
show("OPTIMIZED PIPELINE", "top_k=3, category filter, shorter prompt", L2, ms2, ms1, scale_max=max(ms1))
print(f"  Main bottleneck reduced")

print(f"""
┌─────────────────────────────┬──────────────┬──────────────┬─────────┐
│ Step                        │ Unoptimized  │  Optimized   │ Change  │
├─────────────────────────────┼──────────────┼──────────────┼─────────┤
│ Retrieval                   │ {fmt_ms(ms1[0])} ms  │ {fmt_ms(ms2[0])} ms  │  {pct_cell(ms1[0], ms2[0])}  │
│ Prompt construction         │ {fmt_ms(ms1[1])} ms  │ {fmt_ms(ms2[1])} ms  │  {pct_cell(ms1[1], ms2[1])}  │
│ Model inference             │ {fmt_ms(ms1[2])} ms  │ {fmt_ms(ms2[2])} ms  │  {pct_cell(ms1[2], ms2[2])}  │
├─────────────────────────────┼──────────────┼──────────────┼─────────┤
│ TOTAL                       │ {fmt_ms(sum(ms1))} ms  │ {fmt_ms(sum(ms2))} ms  │  {pct_cell(sum(ms1), sum(ms2))}  │
└─────────────────────────────┴──────────────┴──────────────┴─────────┘""")
