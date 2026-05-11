import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="Sarasota Power Demand Forecast", layout="wide", initial_sidebar_state="collapsed")

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
        "&hourly=temperature_2m,precipitation"
        "&temperature_unit=fahrenheit"
        "&forecast_hours=24"
    )

    r = requests.get(url)
    data = r.json()
    current = data["current"]
    hourly = data["hourly"]

    hourly_forecast = {}
    for i, t in enumerate(hourly["time"]):
        h = datetime.fromisoformat(t).hour
        hourly_forecast[h] = {
            "temperature": hourly["temperature_2m"][i],
            "precip_inches": mm_to_inches(hourly["precipitation"][i])
        }

    return {
        "temperature": current["temperature_2m"],
        "precip_mm": current["precipitation"],
        "hourly": hourly_forecast
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

use_system_time = st.sidebar.checkbox("Use current system time", value=True)

hour_labels = ["12 AM", "1 AM", "2 AM", "3 AM", "4 AM", "5 AM", "6 AM", "7 AM",
               "8 AM", "9 AM", "10 AM", "11 AM", "12 PM", "1 PM", "2 PM", "3 PM",
               "4 PM", "5 PM", "6 PM", "7 PM", "8 PM", "9 PM", "10 PM", "11 PM"]
hour = st.sidebar.selectbox("Hour", hour_labels, index=now.hour, disabled=use_system_time)

selected_date = st.sidebar.date_input("Date", value=now.date(), disabled=use_system_time)

if use_system_time:
    hour = now.hour
    day_of_week = now.weekday()
    month = now.month
else:
    hour = hour_labels.index(hour)
    day_of_week = selected_date.weekday()
    month = selected_date.month

st.sidebar.markdown("---")

st.sidebar.markdown("**Historical Load**")
demand_lag_24h = st.sidebar.number_input(
    "Demand Lag 24h (MW)",
    value=0.0
)

st.sidebar.markdown("---")

st.sidebar.markdown("**Weather**")
use_auto_weather = st.sidebar.checkbox("Use real Sarasota weather", value=True)

temperature = st.sidebar.number_input("Temperature (°F)", value=80.0, disabled=use_auto_weather)
precip_inches = st.sidebar.number_input("Precipitation (inches)", value=0.0, disabled=use_auto_weather)

if use_auto_weather:
    try:
        weather = get_sarasota_weather()

        temperature = weather["temperature"]
        precip_inches = mm_to_inches(weather["precip_mm"])

        st.sidebar.success("Using live Sarasota weather")

    except Exception:
        st.sidebar.warning("Weather API failed — using manual input")


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

tab1, tab2 = st.tabs(["Forecast", "Visualization"])

with tab1:
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
    hour_12 = hour % 12
    if hour_12 == 0:
        hour_12 = 12
    ampm = "AM" if hour < 12 else "PM"
    weather_col3.metric(
        "🕒 Hour",
        f"{hour_12}:00 {ampm}"
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
        st.session_state.forecast_result = result

    if "forecast_result" in st.session_state:
        result = st.session_state.forecast_result
        pred = result["predictions"][0]

        st.success("Prediction complete!")

        col1, col2, col3 = st.columns(3)

        yhat = float(pred.get("yhat", 0.0))
        upper = float(pred.get("yhat_upper", yhat))
        lower = float(pred.get("yhat_lower", yhat))

        if yhat < 10000:
            status = "🟢 Low Demand"
            status_color = "#16a34a"
        elif yhat < 20000:
            status = "🟡 Moderate Demand"
            status_color = "#eab308"
        else:
            status = "🔴 Peak Demand"
            status_color = "#dc2626"

        max_demand = 30000.0
        pct = min(max(yhat / max_demand, 0.0), 1.0)

        st.markdown(
            f"""
            <div style="
                padding: 1rem;
                border-radius: 12px;
                background-color: {status_color};
                color: white;
                text-align: center;
                margin-bottom: 1rem;
            ">
                <h2 style="margin: 0;">{status}</h2>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.metric(
            "⚡ Predicted Power Demand",
            f"{yhat:,.0f} MW"
        )

        col1, col2 = st.columns(2)

        col1.metric(
            "⬇ Lower Bound",
            f"{lower:,.0f} MW"
        )

        col2.metric(
            "⬆ Upper Bound",
            f"{upper:,.0f} MW"
        )

        st.progress(pct)

        st.caption(
            f"{pct * 100:.1f}% of assumed peak capacity "
            f"({max_demand:,.0f} MW)"
        )

        st.caption(
            f"Expected demand range: {lower:,.0f} MW – {upper:,.0f} MW"
        )

    # -----------------------------
    # RAW OUTPUT
    # -----------------------------
    with st.expander("Raw Model Response"):
        if "forecast_result" in st.session_state:
            result = st.session_state.forecast_result
            st.json(result)

            json_str = json.dumps(result, indent=2)

            st.download_button(
                label="⬇ Download Prediction JSON",
                data=json_str,
                file_name="power_usage.json",
                mime="application/json"
            )
        else:
            st.caption("Cannot fetch the latest prediction (perhaps you didn't click the button?)")

with tab2:
    st.subheader("Hourly Demand Profile")
    st.caption(
        "Predicts demand for each hour using the actual 24-hour weather forecast. "
        "One batch request — minimal cost."
    )

    hour_labels_short = ["12a", "1a", "2a", "3a", "4a", "5a", "6a", "7a",
                         "8a", "9a", "10a", "11a", "12p", "1p", "2p", "3p",
                         "4p", "5p", "6p", "7p", "8p", "9p", "10p", "11p"]

    if st.button("Generate Profile ⚡", key="profile_btn"):
        with st.spinner("Fetching hourly forecast and querying model..."):
            hourly_forecast = None
            try:
                weather = get_sarasota_weather()
                hourly_forecast = weather.get("hourly")
            except Exception:
                pass

            hourly_rows = []
            for h in range(24):
                if hourly_forecast and h in hourly_forecast:
                    temp = hourly_forecast[h]["temperature"]
                    precip = hourly_forecast[h]["precip_inches"]
                else:
                    temp = temperature
                    precip = precip_inches
                hourly_rows.append({
                    "ds": datetime.now().isoformat(),
                    "month": month,
                    "precipitation": precip,
                    "demand_lag_24h": demand_lag_24h,
                    "temperature": temp,
                    "hour": h,
                    "y": 0.0,
                    "day_of_week": day_of_week,
                })
            hourly_df = pd.DataFrame(hourly_rows)
            result = score_model(hourly_df)

            predictions = result["predictions"]
            yhats = [float(p.get("yhat", 0.0)) for p in predictions]
            uppers = [float(p.get("yhat_upper", y)) for p, y in zip(predictions, yhats)]
            lowers = [float(p.get("yhat_lower", y)) for p, y in zip(predictions, yhats)]

            st.session_state.profile_data = {
                "yhats": yhats,
                "uppers": uppers,
                "lowers": lowers,
            }

    if "profile_data" in st.session_state:
        data = st.session_state.profile_data
        yhats = data["yhats"]
        uppers = data["uppers"]
        lowers = data["lowers"]

        chart_df = pd.DataFrame({
            "Hour": list(range(24)),
            "Demand (MW)": yhats,
            "Upper": uppers,
            "Lower": lowers,
            "Label": hour_labels_short,
        })

        import altair as alt

        band = alt.Chart(chart_df).mark_area(opacity=0.2, color="#FF6B35").encode(
            x=alt.X("Hour:Q", title="Hour of Day"),
            y="Lower:Q",
            y2="Upper:Q",
        )

        line = alt.Chart(chart_df).mark_line(color="#FF6B35", strokeWidth=3).encode(
            x=alt.X("Hour:Q", title="Hour of Day"),
            y=alt.Y("Demand (MW):Q", title="Demand (MW)"),
        )

        chart = (band + line).configure_axis(
            labelExpr="datum.value == 0 ? '12a' : datum.value == 12 ? '12p' : datum.value < 12 ? datum.value + 'a' : (datum.value - 12) + 'p'"
        )

        st.altair_chart(chart, width="stretch")

        peak_hour = yhats.index(max(yhats))
        st.caption(
            f"Peak demand at {hour_labels_short[peak_hour]} "
            f"({max(yhats):,.0f} MW) — trough at {hour_labels_short[yhats.index(min(yhats))]} "
            f"({min(yhats):,.0f} MW)"
        )
