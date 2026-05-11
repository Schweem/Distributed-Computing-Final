import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="Sarasota Power Demand Forecast", layout="wide")

DATABRICKS_TOKEN = st.secrets["DATABRICKS_TOKEN"]

URL = "https://dbc-724c7636-740c.cloud.databricks.com/serving-endpoints/sarasota-power-api/invocations"

# -----------------------------
# HELPERS
# -----------------------------
def mm_to_inches(mm):
    return mm * 0.0393701


def get_sarasota_weather():
    """
    Fixed location: Sarasota, Florida
    Open-Meteo uses lat/lon internally
    """
    lat = 27.3364
    lon = -82.5307

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,precipitation"
        "&temperature_unit=fahrenheit"
    )

    r = requests.get(url)
    data = r.json()["current"]

    return {
        "temperature": data["temperature_2m"],
        "precip_mm": data["precipitation"]
    }


def score_model(dataset: pd.DataFrame):
    headers = {
        "Authorization": f"Bearer {DATABRICKS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "dataframe_split": {
            "columns": list(dataset.columns),
            "data": dataset.values.tolist()
        }
    }

    response = requests.post(URL, headers=headers, data=json.dumps(payload))

    if response.status_code != 200:
        st.error(response.text)
        raise Exception("Databricks request failed")

    return response.json()


# -----------------------------
# UI
# -----------------------------
st.title("⚡ Sarasota Power Demand Forecast")
st.caption(
    "This dashboard forecasts Sarasota electricity demand using a Databricks-hosted ML model. "
    "Adjust time, weather, and historical load in the sidebar, then click predict."
)

st.divider()

# -----------------------------
# SIDEBAR
# -----------------------------
st.sidebar.header("Inputs")

st.sidebar.markdown("**Time**")
now = datetime.now()

hour = st.sidebar.slider("Hour", 0, 23, now.hour)
day_of_week = st.sidebar.slider("Day of Week (0=Mon)", 0, 6, now.weekday())
month = st.sidebar.slider("Month", 1, 12, now.month)

st.sidebar.markdown("---")

st.sidebar.markdown("**Historical Load**")
demand_lag_24h = st.sidebar.number_input(
    "Demand Lag 24h (MW)",
    value=0.0
)

st.sidebar.markdown("---")

st.sidebar.markdown("**Weather**")
use_auto_weather = st.sidebar.checkbox("Use real Sarasota weather", value=True)

if use_auto_weather:
    try:
        weather = get_sarasota_weather()

        temperature = weather["temperature"]
        precip_inches = mm_to_inches(weather["precip_mm"])

        st.sidebar.success("Using live Sarasota weather")

    except Exception:
        st.sidebar.warning("Weather API failed — using manual input")

        temperature = st.sidebar.number_input("Temperature (°F)", value=80.0)
        precip_inches = st.sidebar.number_input("Precipitation (inches)", value=0.0)

else:
    temperature = st.sidebar.number_input("Temperature (°F)", value=80.0)
    precip_inches = st.sidebar.number_input("Precipitation (inches)", value=0.0)


# -----------------------------
# BUILD MODEL INPUT
# -----------------------------
features = pd.DataFrame([{
    "ds": datetime.now().isoformat(),
    "month": month,
    "precipitation": precip_inches,
    "demand_lag_24h": demand_lag_24h,
    "temperature": temperature,
    "hour": hour,
    "y": 0.0,
    "day_of_week": day_of_week
}])

# with st.container():
#     st.subheader("Model Input Features")
#     st.dataframe(features)
#     st.caption(
#         "`hour` (0–23) · `day_of_week` (0=Mon) · `month` (1–12) · "
#         "`temperature` (°F) · `precipitation` (in) · "
#         "`demand_lag_24h` (MW, previous day) · `ds` (timestamp)"
#     )

# displaying the current weather conditions that the API fetched
# in a prettier way
st.subheader("Current Conditions")
weather_col1, weather_col2, weather_col3, weather_col4 = st.columns(4)
weather_col1.metric(
    "🌡 Temperature",
    f"{temperature:.1f} °F"
)
weather_col2.metric(
    "🌧 Precipitation",
    f"{precip_inches:.2f} in"
)
weather_col3.metric(
    "🕒 Hour",
    f"{hour:02d}:00"
)
weather_col4.metric(
    "📍 Location",
    "Sarasota, FL"
)
st.caption(
    "Live weather data from Sarasota is used by default, but all values can be "
    "manually overridden in the sidebar."
)

st.divider()

# -----------------------------
# PREDICTION
# -----------------------------
if st.button("Predict Power Demand ⚡"):

    with st.spinner("Querying Databricks model..."):
        result = score_model(features)

    pred = result["predictions"][0]

    st.success("Prediction complete!")

    col1, col2, col3 = st.columns(3)

    col1.metric("Predicted Demand (MW)", f"{pred.get('yhat', 'N/A')}")
    col2.metric("Upper Bound", f"{pred.get('yhat_upper', 'N/A')}")
    col3.metric("Lower Bound", f"{pred.get('yhat_lower', 'N/A')}")

# -----------------------------
# RAW OUTPUT
# -----------------------------
with st.expander("Raw Model Response"):
    if "result" in locals():
        st.json(result)
    else:
        st.caption("Cannot fetch the latest prediction (perhaps you didn't click the button?)")
