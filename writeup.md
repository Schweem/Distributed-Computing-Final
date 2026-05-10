# Distributed Computing Final: FPL Demand Prediction

**Team:** Seamus, Tre

## Pipeline Overview

This project implements a distributed, serverless pipeline to predict hourly
electricity demand for Florida Power & Light (FPL) in Sarasota, FL. It follows
a Medallion Architecture (Bronze -> Silver -> Gold) and emphasizes real-time
telemetry over static datasets.

## 1. Data Ingestion (Bronze Layer)

An AWS Lambda function, triggered hourly by EventBridge, fetches JSON data from
two sources: the **EIA API** (hourly power load for the FPL region) and the
**OpenWeather API** (current temperature and weather for Sarasota). Raw JSON
responses are written to S3 (`sarasota-power-data-bronze`) with timestamped
filenames, creating an immutable time-series log. The pipeline stays within
AWS Free Tier (~730 Lambda invocations/month, ~15 MB storage).

## 2. Transformation (Silver & Gold Layers)

Databricks processes the raw Bronze data using Apache Spark:

- **Silver:** Auto Loader incrementally reads new JSON files from S3. Power
  data is parsed from nested arrays into timestamped demand readings. Weather
  data is cleaned and aligned to hourly timestamps. Both are written as Delta
  tables (`silver_power`, `silver_weather`).

- **Gold:** Silver tables are joined on timestamp. Features are engineered:
  hour, day_of_week, month, and demand_lag_24h (previous day's load). The
  result is a feature table (`gold_power_demand`) ready for modeling.

## 3. Model Training & Serving

A **Prophet** forecasting model is trained on the Gold table using temperature,
hour, and day_of_week as regressors. The model is logged to **MLflow** with a
schema signature and registered in Unity Catalog as
`sarasota_live_forecaster`. It is deployed via Databricks Model Serving,
exposing a REST API for inference.

## 4. Dashboard

A **Streamlit** web app provides the user interface. It fetches live weather
from Open-Meteo, builds the feature vector, calls the Databricks serving
endpoint, and displays the predicted power demand with upper/lower uncertainty
bounds.

## Architecture

```
EventBridge -> AWS Lambda -> S3 Bronze
                                |
                     Databricks (Silver -> Gold -> Prophet)
                                |
                     MLflow -> Databricks Serving -> Streamlit Dashboard
```

All components operate within cloud free tiers. The pipeline is fully
distributed: Lambda handles serverless ingestion, S3 provides durable object
storage, and Databricks/Spark manages distributed transformations and model
training.
