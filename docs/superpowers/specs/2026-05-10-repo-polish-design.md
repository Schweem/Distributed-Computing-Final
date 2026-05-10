# Repo Polish Design

## Goal
Bring the repo into compliance with project requirements (README.md, write-up PDF, clean directory structure) with minimal effort (K.I.S.S.).

## Deliverables

### 1. README.md (repo root)
- Project title: "Distributed Computing Final: FPL Demand Prediction"
- Team members: Seamus, Tre
- Live URL: placeholder ("TBD — deployed on Databricks + Streamlit")
- Instructions: `python test_script.py`

### 2. One-Page Write-Up (PDF, repo root)
Complete rewrite covering the full pipeline:
- **Data Ingestion:** AWS Lambda (EventBridge trigger every hour) → EIA + OpenWeather APIs → raw JSON to S3 Bronze bucket
- **Bronze → Silver (Databricks):** Auto Loader reads S3 JSON → parse/clean/timestamp-align → Delta tables (`silver_power`, `silver_weather`)
- **Silver → Gold (Databricks):** Inner join on timestamp → feature engineering (hour, day_of_week, month, demand_lag_24h) → `gold_power_demand` table
- **Model Training (Databricks):** Prophet model with temperature/hour/day_of_week regressors → logged to MLflow with Unity Catalog → registered as `sarasota_live_forecaster`
- **Dashboard:** Streamlit app → live weather from Open-Meteo → build feature vector → Databricks Serving endpoint → display forecast
- **Cost analysis:** AWS Free Tier operation
- Rename `bronze_writeup.md` → `writeup.md`, then convert to PDF

### 3. Directory Cleanup
- `LambdaWorker/lambda_deployment/`: remove vendored deps (certifi, requests, urllib3, charset_normalizer, idna, bin/) — keep only `lambda_function.py`
- `LambdaWorker/lambda_deployment/`: add `requirements.txt` listing `requests`, `boto3`
- `LambdaWorker/deployment.zip`: remove (build artifact)
- Keep everything else flat and unchanged

## Non-Goals
- No restructuring or renaming of directories beyond what's listed
- No code changes to notebooks, app.py, or lambda_function.py
- No CI/CD setup
- No deployment
