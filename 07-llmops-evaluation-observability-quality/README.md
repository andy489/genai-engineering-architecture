# LLMOps: Evaluation, Observability, and Quality

A practical course on operating large language model systems in production — covering evaluation metrics, structured logging, automated testing, drift detection, and experiment tracking.

All four modules are consolidated into a single notebook: [`llmops-evaluation-observability-quality.ipynb`](llmops-evaluation-observability-quality.ipynb).

## Modules

| Module | Topic |
|--------|-------|
| 01 | LLM Evaluation Metrics and Frameworks |
| 02 | Observability, Logging, and Evaluation |
| 03 | Automated Testing Strategies |
| 04 | Drift Detection and Model Monitoring |

## Demo Notebooks

Each module includes a hands-on demo notebook:

- [`01/demos.ipynb`](01/demos.ipynb) — Multimodal evaluation dataset: vision-QA prompts, accuracy metrics by modality
- [`02/demos.ipynb`](02/demos.ipynb) — Observability: structured LLM call logging, real-time dashboard, latency alerting
- [`03/demos.ipynb`](03/demos.ipynb) — GenAI tests: unit, integration, and CI gate for a summarization function
- [`04/demos.ipynb`](04/demos.ipynb) — Experiment tracking with MLflow: compare LLM configurations, identify best run

## Assets

The [`assets/`](assets/) directory contains educational diagrams extracted from the course slides:

- `01-testing-pyramid.png` — GenAI testing pyramid showing the three test layers by speed and realism
- `02-canary-testing.png` — Canary deployment flow illustrating traffic splitting and parallel version comparison

## Setup

The demo notebooks use the OpenAI Python SDK and expect an API key in `../api_key.txt` (one level above this directory).

```bash
pip install openai pandas matplotlib ipywidgets mlflow pillow
```
