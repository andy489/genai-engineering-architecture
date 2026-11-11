# Safety and Security Architecture for GenAI Systems

This course covers the architectural patterns and controls needed to build GenAI systems that are safe, secure, and private. It progresses from adversarial prompt defense and multi-modal content moderation through PII protection and regulatory compliance, to secure deployment, authentication, threat modeling, and production hardening.

All four modules are consolidated into a single Jupyter Notebook.

## Contents

| File / Directory | Description |
|---|---|
| [`safety-security-architecture-gen-ai-systems.ipynb`](safety-security-architecture-gen-ai-systems.ipynb) | Complete course notebook (all 4 modules) |
| [`assets/`](assets/) | Extracted architecture and flow diagrams (16 PNGs) |
| [`01-adversarial-prompting-demos/`](01-adversarial-prompting-demos/) | GenAI safety gateway — adversarial defense pipeline |
| [`02-content-moderation-demos/`](02-content-moderation-demos/) | Multi-layer moderation architecture demos and test inputs |
| [`03-privacy-pii-demos/`](03-privacy-pii-demos/) | PII detection, redaction, and data minimisation demos |
| [`04-secure-deployment-demos/`](04-secure-deployment-demos/) | Secure deployment, access controls, and checkpoint recovery |

## Modules

| Module | Topic |
|---|---|
| 01 | Adversarial Prompting and Jailbreak Defense Architecture |
| 02 | Content Moderation and Multi-Modal Safety Systems |
| 03 | Privacy Architecture and PII Protection |
| 04 | Secure Deployment and Production Hardening |

## Assets

The `assets/` directory contains 16 architecture and flow diagrams extracted from the course slides, covering topics including the privacy data flow, PII detection pipeline, federated learning, TEE inference, tool execution gate, production trust boundaries, and threat modeling workflow.

## Setup

Each demo directory has its own `requirements.txt`. Install per-demo dependencies in a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\Activate.ps1 on Windows
pip install -r <demo-dir>/requirements.txt
```

Module 01 and 03 demos require no external API key for local-gate and redaction demonstrations. Module 01's provider-moderation and generation steps require a valid OpenAI API key.
