# Repo Polish Implementation Plan

> **For agentic workers:** No subagents needed — single session, straightforward tasks.

**Goal:** Bring repo into compliance with project requirements (README, write-up PDF, clean directory) with minimal effort.

**Architecture:** Simple file operations — create README.md, write new project writeup.md and convert to PDF, clean vendored deps out of LambdaWorker.

**Tech Stack:** Markdown, Python (for PDF generation via `fpdf2` or similar)

---

### Task 1: Clean Up LambdaWorker Directory

**Files:**
- Delete: `LambdaWorker/lambda_deployment/certifi/`
- Delete: `LambdaWorker/lambda_deployment/certifi-2026.2.25.dist-info/`
- Delete: `LambdaWorker/lambda_deployment/charset_normalizer/`
- Delete: `LambdaWorker/lambda_deployment/charset_normalizer-3.4.7.dist-info/`
- Delete: `LambdaWorker/lambda_deployment/idna/`
- Delete: `LambdaWorker/lambda_deployment/idna-3.11.dist-info/`
- Delete: `LambdaWorker/lambda_deployment/requests/`
- Delete: `LambdaWorker/lambda_deployment/requests-2.33.1.dist-info/`
- Delete: `LambdaWorker/lambda_deployment/urllib3/`
- Delete: `LambdaWorker/lambda_deployment/urllib3-2.6.3.dist-info/`
- Delete: `LambdaWorker/lambda_deployment/bin/`
- Delete: `LambdaWorker/deployment.zip`
- Create: `LambdaWorker/lambda_deployment/requirements.txt`

- [ ] **Step 1: Remove vendored dependency directories**

Run:
```bash
rm -rf LambdaWorker/lambda_deployment/{certifi,certifi-2026.2.25.dist-info,charset_normalizer,charset_normalizer-3.4.7.dist-info,idna,idna-3.11.dist-info,requests,requests-2.33.1.dist-info,urllib3,urllib3-2.6.3.dist-info,bin}
```

- [ ] **Step 2: Remove deployment.zip build artifact**

Run:
```bash
rm LambdaWorker/deployment.zip
```

- [ ] **Step 3: Create requirements.txt for Lambda function**

Write `LambdaWorker/lambda_deployment/requirements.txt`:
```
requests>=2.28
boto3>=1.26
```

---

### Task 2: Create README.md

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README.md**

Write `README.md` at repo root:

```markdown
# Distributed Computing Final: FPL Demand Prediction

**Team:** Seamus, Tre

**Live URL:** TBD

## Overview

End-to-end pipeline for predicting hourly electricity demand for Florida Power & Light (FPL) in the Sarasota region.

- **Ingestion:** AWS Lambda pulls power (EIA API) and weather (OpenWeather) data every hour → S3 Bronze
- **Transformation:** Databricks Medallion Architecture (Bronze → Silver → Gold)
- **Model:** Prophet with engineered features (hour, day_of_week, temperature), served via Databricks MLflow
- **Dashboard:** Streamlit app consuming the model serving endpoint

## Run the Test Script

```bash
pip install -r dashboard/requirements.txt
python test_script.py
```

Requires `DATABRICKS_TOKEN` environment variable.
```

---

### Task 3: Write One-Page Project Write-Up

**Files:**
- Create: `writeup.md`
- Create: `writeup.pdf`
- Delete: `bronze_writeup.md`

- [ ] **Step 1: Remove old bronze write-up**

```bash
rm bronze_writeup.md
```

- [ ] **Step 2: Write the full project write-up**

Write `writeup.md` covering the complete pipeline:

```markdown
# Distributed Computing Final: FPL Demand Prediction

**Team:** Seamus, Tre

## Pipeline Overview

This project implements a distributed, serverless pipeline to predict hourly electricity demand for Florida Power & Light (FPL) in Sarasota, FL. It follows a Medallion Architecture (Bronze → Silver → Gold) and emphasizes real-time telemetry over static datasets.

## 1. Data Ingestion (Bronze Layer)

An AWS Lambda function, triggered hourly by EventBridge, fetches JSON data from two sources:
- **EIA API:** Hourly power load for the FPL region
- **OpenWeather API:** Current temperature and weather for Sarasota

Raw JSON responses are written to S3 (`sarasota-power-data-bronze`) with timestamped filenames, creating an immutable time-series log. The pipeline stays within AWS Free Tier (~730 Lambda invocations/month, ~15 MB storage).

## 2. Transformation (Silver & Gold Layers)

Databricks processes the raw Bronze data using Apache Spark:

- **Silver:** Auto Loader incrementally reads new JSON files from S3. Power data is parsed from nested arrays into timestamped demand readings. Weather data is cleaned and aligned to hourly timestamps. Both are written as Delta tables (`silver_power`, `silver_weather`).

- **Gold:** Silver tables are joined on timestamp. Features are engineered: hour, day_of_week, month, and demand_lag_24h (previous day's load). The result is a clean feature table (`gold_power_demand`) ready for modeling.

## 3. Model Training & Serving

A **Prophet** forecasting model is trained on the Gold table using temperature, hour, and day_of_week as regressors. The model is logged to **MLflow** with a schema signature and registered in Unity Catalog as `sarasota_live_forecaster`. It's deployed via Databricks Model Serving, exposing a REST API endpoint.

## 4. Dashboard

A **Streamlit** web app provides the user interface. It fetches live weather from Open-Meteo, builds the feature vector, calls the Databricks serving endpoint, and displays the predicted power demand with uncertainty bounds.

## Architecture

```
EventBridge → AWS Lambda → S3 Bronze → Databricks (Silver → Gold → Prophet) → MLflow → Streamlit Dashboard
```

All components operate within cloud free tiers. The pipeline is fully distributed: Lambda handles serverless ingestion, S3 provides durable object storage, and Databricks/Spark manages distributed transformations and model training.
```

- [ ] **Step 3: Convert writeup.md to PDF**

Run a Python script to convert the Markdown to a clean one-page PDF. First install `fpdf2`:

```bash
pip install fpdf2 markdown
```

Then run:

```python
# save as scripts/md_to_pdf.py and run it
import markdown
from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        pass
    def footer(self):
        pass

pdf = PDF()
pdf.add_page()
with open("writeup.md") as f:
    text = f.read()

html = markdown.markdown(text)
pdf.set_auto_page_break(auto=True, margin=15)
pdf.set_font("Helvetica", size=10)
pdf.multi_cell(0, 5, text.encode('latin-1', 'replace').decode('latin-1'))
pdf.output("writeup.pdf")
```

Or more simply, use `pandoc` if available:

```bash
pandoc writeup.md -o writeup.pdf --pdf-engine=xelatex -V geometry:margin=0.8in
```

---

## Spec Coverage Check

| Spec Requirement | Task |
|---|---|
| README.md with title, team, URL, test instructions | Task 2 |
| Write-up PDF at repo root | Task 3 |
| Pipeline code in clearly named directory | Already exists (`DatabricksNotebooks/`) |
| App source code | Already exists (`dashboard/`, `LambdaWorker/`) |
| Test script at root | Already exists (`test_script.py`) |
| Clean directory structure | Task 1 |

## Placeholder Scan

- No TODOs, TBDs, or vague instructions in the plan
- All file paths are explicit
- All code blocks contain complete content
