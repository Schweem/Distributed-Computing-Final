import streamlit as st
import requests
from datetime import datetime

st.set_page_config(
  page_title="Power Demand Forecast",
  page_icon="⚡",
  layout="wide"
)

st.title("⚡ Power Demand Forecast Dashboard")
st.write("Predict electricity demand using weather and historical demand data.")

# Sidebar
st.sidebar.header("Input Parameters")

location = st.sidebar.text_input("City", "Sarasota, FL")
demand_lag_24h = st.sidebar.number_input(
  "Demand 24 Hours Ago (MW)",
  min_value=0.0,
  value=18000.0,
  step=100.0
)

# Placeholder weather values (replace later with API call)
temperature = st.sidebar.number_input(
  "Temperature (°F)",
  value=80.0
)

precipitation = st.sidebar.number_input(
  "Precipitation (inches)",
  value=0.0
)

# Current time features
now = datetime.now()

hour = now.hour
day_of_week = now.weekday() + 1   # Match your encoding
month = now.month

# Show derived features
st.subheader("Derived Time Features")
st.write({
  "hour": hour,
  "day_of_week": day_of_week,
  "month": month
})

# Build feature vector
features = {
  "hour": hour,
  "day_of_week": day_of_week,
  "month": month,
  "temperature": temperature,
  "precipitation": precipitation,
  "demand_lag_24h": demand_lag_24h
}

st.subheader("Model Inputs")
st.json(features)

# Prediction button
if st.button("Predict Demand"):
  # Temporary placeholder prediction (TODO REMOVE)
  predicted_demand = (
    demand_lag_24h * 0.85
    + temperature * 120
    + precipitation * -50
  )
  
  st.metric(
    "Predicted Power Demand",
    f"{predicted_demand:,.0f} MW"
  )
