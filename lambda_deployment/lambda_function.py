import json
import os
import boto3
import requests
from datetime import datetime

s3 = boto3.client('s3')
BUCKET_NAME = os.environ['BRONZE_BUCKET']
EIA_KEY = os.environ['EIA_API_KEY']
OWM_KEY = os.environ['OWM_API_KEY']

def lambda_handler(event, context):
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    
    # 1. Fetch Power Data (FPL - Sarasota Region)
    eia_url = f"https://api.eia.gov/v2/electricity/rto/region-data/data/?api_key={EIA_KEY}&facets[respondent][]=FPL&frequency=hourly&data[]=value"
    power_res = requests.get(eia_url).json()
    
    # 2. Fetch Weather Data (Sarasota, FL)
    owm_url = f"http://api.openweathermap.org/data/2.5/weather?q=Sarasota,us&appid={OWM_KEY}&units=imperial"
    weather_res = requests.get(owm_url).json()
    
    # 3. Write to S3 (Bronze Layer)
    # We save these as separate files for clean distributed processing later
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=f"power/fpl_{timestamp}.json",
        Body=json.dumps(power_res)
    )
    
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=f"weather/sarasota_{timestamp}.json",
        Body=json.dumps(weather_res)
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps(f'Successfully ingested data for {timestamp}')
    }
