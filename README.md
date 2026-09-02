# Clabsi Cauti Surveillance Agent

> **Domain:** Infectious Disease Surveillance & Microbiology  
> **Reference Guidelines & Standards:** `CLSI M100, EUCAST & CDC NHSN Clinical Standards`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Clabsi Cauti Surveillance Agent** is an advanced analytical and computational platform implementing Central Line & Catheter Dwell-Time HAI Classifier.

DeviceHAI Sentinel: Autonomous Central Line & Catheter-Associated Infection Arbiter
Automates CDC NHSN device-day denominators, line dwell-time tracking, and CLABSI/CAUTI case classification to eliminate subjective manual surveillance.

Domain: Infection Control
Author: Dr. Abu Suraih Sakhri
License: MIT

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Core Algorithmic & Evaluation Engines

- **`DeviceType`** — dedicated module for device type evaluation and state verification.
- **`OrganismType`** — dedicated module for organism type evaluation and state verification.
- **`SurveillanceVerdict`** — dedicated module for surveillance verdict evaluation and state verification.
- **`CLABSIAssessment`** — dedicated module for c l a b s i assessment evaluation and state verification.
- **`CAUTIAssessment`** — dedicated module for c a u t i assessment evaluation and state verification.
- **`EpidemiologicalMetrics`** — dedicated module for epidemiological metrics evaluation and state verification.

---

## 📐 Mathematical Formulation & Logic

```text
  Calculates Standardized Infection Ratio (SIR) with Poisson exact 95% CI
  interp = "Predicted events zero or missing; SIR cannot be calculated."
  return calculate_sir_and_dur(**kwargs)
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --organism <value> --cultures <value> --days <value> --fever <value>
```

### Parameter Reference
- `--organism`: Specifies input measurement or parameter value.
- `--cultures`: Specifies input measurement or parameter value.
- `--days`: Specifies input measurement or parameter value.
- `--fever`: Specifies input measurement or parameter value.
- `--anc`: Specifies input measurement or parameter value.
- `--cfu`: Specifies input measurement or parameter value.
- `--observed`: Specifies input measurement or parameter value.
- `--predicted`: Specifies input measurement or parameter value.
- `--device-days`: Specifies input measurement or parameter value.
- `--patient-days`: Specifies input measurement or parameter value.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `case_id` | Parameter / observation metric | Required |
| `patient_id` | Parameter / observation metric | Required |
| `surveillance_type` | Parameter / observation metric | Required |
| `organism` | Parameter / observation metric | Required |
| `device_days` | Parameter / observation metric | Required |
| `fever` | Parameter / observation metric | Required |
| `hypotension` | Parameter / observation metric | Required |
| `anc` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t clabsi-cauti-surveillance-agent .
docker run -p 8000:8000 clabsi-cauti-surveillance-agent
```
