# GenAI Inference and Serving Architecture

This module covers the full spectrum of GenAI inference and serving — from model selection and the transformer inference pipeline, through batching and GPU scaling strategies, to cost engineering and advanced techniques such as speculative decoding, quantization, and attention optimization.

All modules are consolidated into a single notebook:
[`gen-ai-inference-serving-architecture.ipynb`](gen-ai-inference-serving-architecture.ipynb)

## Modules

| Module | Topic |
|---|---|
| 01 | Model Inference and Efficient Model Selection |
| 02 | Batching and Throughput Optimization |
| 03 | GPU Scaling and Infrastructure Considerations |
| 04 | Cost Engineering and Optimization Strategies |
| 05 | Advanced Inference Techniques for Speed and Quality |

## Demos

Each module includes a Jupyter notebook with hands-on code examples:

- [`01/demos.ipynb`](01/demos.ipynb) — Context length impact on latency, sampling parameters, KV-cache reuse
- [`02/demos.ipynb`](02/demos.ipynb) — Single vs. batched requests benchmarking
- [`03/demos.ipynb`](03/demos.ipynb) — FP32 vs FP16 inference timing and GPU memory utilization
- [`04/demos.ipynb`](04/demos.ipynb) — Prompt compression, response caching, batching, quantization cost comparison
- [`05/demos.ipynb`](05/demos.ipynb) — Full-context inference, retrieval-based approach, smart inference router

## Assets

The [`assets/`](assets/) directory contains educational diagrams extracted from the course slides:

- `03-pipeline-parallelism.png` — Pipeline parallelism: layers split across GPUs with micro-batch streaming

## Setup

The demo notebooks use the following Python packages:

```
torch
transformers
numpy
pandas
psutil
```

Install with:

```bash
pip install torch transformers numpy pandas psutil
```
