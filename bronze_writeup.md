# Distributed Computing Final Project: FPL Demand Prediction

## 1. Project Overview
This project focuses on predicting hourly electricity demand for the **Florida Power and Light (FPL)** grid in the Sarasota, Florida region. To satisfy the requirements of the distributed computing final, the project avoids static, pre-packaged datasets (like those from Kaggle) in favor of building a live telemetry pipeline. This "Mission Control" approach demonstrates real-world data engineering and distributed processing principles.

## 2. Architectural Choices
The project utilizes a **Medallion Architecture** (Bronze, Silver, Gold) to manage data flow and transformations. 

### Why Medallion Architecture?
* **Decoupling:** Separates raw ingestion from complex processing.
* **Resilience:** Raw data is never lost or modified, allowing reprocessing if errors occur downstream.
* **Scalability:** Fits perfectly with distributed storage (S3) and compute (Spark) paradigms.

## 3. Progress: Phase 1 - Data Ingestion (Bronze Layer)
We have successfully completed the end-to-end setup of the Bronze layer. This phase acts as the "Harvester," pulling raw JSON data from external APIs and storing it in a data lake.

### Components Deployed:
1.  **Data Sources:**
    * **U.S. Energy Information Administration (EIA) API:** Pulls hourly load data for the FPL grid region.
    * **OpenWeather API:** Pulls current temperature and weather conditions for Sarasota, FL.
2.  **Compute - AWS Lambda:** * A Python 3.x serverless function executes the API calls.
    * A custom deployment package was created to include the external `requests` library.
    * API keys and configuration details are securely passed via Lambda Environment Variables.
3.  **Storage - Amazon S3:**
    * Bucket: `sarasota-power-data-bronze`
    * Raw JSON responses are dumped into separate `power/` and `weather/` directories.
    * Files are timestamped (e.g., `fpl_YYYY-MM-DD_HH-MM.json`) to prevent overwriting and create an immutable time-series log.
4.  **Automation - Amazon EventBridge:**
    * A recurring schedule triggers the Lambda function every 1 hour.
    * This automates the ingestion process, creating a continuous, distributed stream of telemetry data.
5.  **Security & Identity - AWS IAM:**
    * The Lambda function runs under a least-privilege IAM Execution Role, granting it basic logging permissions and explicit `s3:PutObject` access to the Bronze bucket.

## 4. Cost Analysis
The entire ingestion pipeline was designed to operate efficiently within the **AWS Free Tier**:
* **Lambda:** ~730 invocations/month (Free Tier allows 1M). Cost: $0.00
* **S3:** ~15MB storage and 1,460 PUT requests/month (Free Tier allows 5GB / 2,000 PUTs). Cost: $0.00
* **EventBridge:** Standard scheduling. Cost: $0.00
* **APIs:** Operating well within daily free limits. Cost: $0.00

## 5. Next Steps: Phase 2 - Transformation (Silver Layer)
With the Bronze layer successfully harvesting hourly data, the next phase will focus on distributed data processing. 

**Upcoming Tasks:**
* Connect **Databricks** to the S3 Bronze bucket.
* Write an **Apache Spark** script to clean the raw JSON data, extract relevant fields (timestamp, load value, temperature, humidity), and handle any missing or malformed records.
* Join the disparate power and weather datasets into a unified tabular format.
* Write the cleaned, joined data back to S3 as Parquet files (the Silver Layer).
