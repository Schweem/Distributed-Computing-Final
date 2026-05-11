# Distributed Computing Final: FPL Demand Prediction

**Team:** Seamus, Tre

**Live URL:** https://sarasota-power-predictatron.streamlit.app/

## Overview

End-to-end pipeline for predicting hourly electricity demand for Florida Power & Light (FPL) in the Sarasota region.

- **Ingestion:** AWS Lambda pulls power (EIA API) and weather (OpenWeather) data every hour → S3 Bronze
- **Transformation:** Databricks Medallion Architecture (Bronze → Silver → Gold)
- **Model:** Prophet with engineered features (hour, day_of_week, temperature), served via Databricks MLflow
- **Dashboard:** Streamlit app consuming the model serving endpoint

## Run the Test Script

```bash
pip install -r requirements.txt
python test_script.py
```

Requires `DATABRICKS_TOKEN` environment variable.
