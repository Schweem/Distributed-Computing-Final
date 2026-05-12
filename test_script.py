import os
import requests
import pandas as pd
import json
from dotenv import load_dotenv

load_dotenv()
DATABRICKS_TOKEN = os.environ.get('DATABRICKS_TOKEN')

def score_model(dataset: pd.DataFrame):
    url = 'https://dbc-724c7636-740c.cloud.databricks.com/serving-endpoints/sarasota-power-api/invocations'
    
    headers = {
        'Authorization': f'Bearer {DATABRICKS_TOKEN}', 
        'Content-Type': 'application/json'
    }
    
    ds_dict = {
        "dataframe_split": {
            "columns": list(dataset.columns),
            "data": dataset.values.tolist()
        }
    }
    
    data_json = json.dumps(ds_dict, allow_nan=True)
    
    response = requests.post(url, headers=headers, data=data_json)
    
    if response.status_code != 200:
        raise Exception(f'Request failed with status {response.status_code}, {response.text}')
        
    return response.json()

future_data = pd.DataFrame({
    "ds": ["2026-05-10T12:00:00"],
    "month": [5],
    "precipitation": [0.0],
    "demand_lag_24h": [0.0],
    "temperature": [85.2],
    "hour": [12],
    "y": [0.0],
    "day_of_week": [6] # e.g., Sunday
})

forecast = score_model(future_data)

power_demand = forecast['predictions'][0].get('yhat', "N/A")
upper = forecast['predictions'][0].get('yhat_upper', "N/A")
lower = forecast['predictions'][0].get('yhat_lower', "N/A")

print(f"Prediction for power demand (mw): {power_demand}")
print(f"Upper bound: {upper}")
print(f"Lower bound: {lower}")
