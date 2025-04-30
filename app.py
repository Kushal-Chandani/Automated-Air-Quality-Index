#app.py

import streamlit as st
import hopsworks
import joblib
import pandas as pd
import os
import plotly.express as px
import numpy as np
from datetime import datetime

st.set_page_config(
    page_title="Air Quality Dashboard",
    page_icon="🌬️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main {
        background-color: #f0f2f6;
        padding: 20px;
    }
    .sidebar .sidebar-content {
        background-color: #ffffff;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_model():
    try:
        project = hopsworks.login(api_key_value="2EpVtPZvfyir2ZHe.Xq5Zf52NZvrcFMazBANKnavDajjwl759POapcm1FijsZhoDFqhKeY2zu331fo82i"
)
        mr = project.get_model_registry()
        model_obj = mr.get_model("openmeteo_pm2_5_model", version=1)
        model_dir = model_obj.download()
        model_path = os.path.join(model_dir, "model.joblib")
        return joblib.load(model_path)
    except Exception as e:
        st.error(f"Error loading model: {str(e)}")
        return None

@st.cache_data(ttl=600)
def get_historical_data():
    try:
        project = hopsworks.login(api_key_value="2EpVtPZvfyir2ZHe.Xq5Zf52NZvrcFMazBANKnavDajjwl759POapcm1FijsZhoDFqhKeY2zu331fo82i"
)
        fs = project.get_feature_store()
        fg = fs.get_feature_group("openmeteo_aq_feature_group", version=1)
        return fg.read()
    except Exception as e:
        st.error(f"Error fetching historical data: {str(e)}")
        return pd.DataFrame()

def generate_forecast_data(forecast_period_days=3, freq='H', df_hist=None):
    if df_hist is None or df_hist.empty:
        return pd.DataFrame()

    avg_vals = {
        'carbon_monoxide': df_hist['carbon_monoxide'].mean(),
        'carbon_dioxide': df_hist['carbon_dioxide'].mean(),
        'nitrogen_dioxide': df_hist['nitrogen_dioxide'].mean(),
        'sulphur_dioxide': df_hist['sulphur_dioxide'].mean(),
        'pm2_5_change_rate': df_hist['pm2_5_change_rate'].mean(),
    }
    std_vals = {
        k: df_hist[k].std() * 0.2 for k in avg_vals
    }

    forecast_start = pd.Timestamp.utcnow().replace(minute=0, second=0, microsecond=0) + pd.Timedelta(hours=1)
    forecast_end = forecast_start + pd.Timedelta(days=forecast_period_days)
    forecast_dates = pd.date_range(start=forecast_start, end=forecast_end - pd.Timedelta(hours=1), freq=freq)
    n = len(forecast_dates)

    forecast_df = pd.DataFrame({
        'date': forecast_dates,
        'day': forecast_dates.day,
        'month': forecast_dates.month,
        'carbon_monoxide': np.random.normal(avg_vals['carbon_monoxide'], std_vals['carbon_monoxide'], n),
        'carbon_dioxide': np.random.normal(avg_vals['carbon_dioxide'], std_vals['carbon_dioxide'], n),
        'nitrogen_dioxide': np.random.normal(avg_vals['nitrogen_dioxide'], std_vals['nitrogen_dioxide'], n),
        'sulphur_dioxide': np.random.normal(avg_vals['sulphur_dioxide'], std_vals['sulphur_dioxide'], n),
        'pm2_5_change_rate': np.random.normal(avg_vals['pm2_5_change_rate'], std_vals['pm2_5_change_rate'], n),
    })
    return forecast_df.round(6)

def main():
    with st.sidebar:
        st.title("⚙️ Settings")
        theme = st.selectbox("Theme", ["Light", "Dark"])
        st.markdown("---")
        st.subheader("About")
        st.write("Air Quality Prediction Dashboard")
        st.write(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    st.title("🌬️ Open-Meteo Air Quality Dashboard")
    if theme == "Dark":
        st.markdown('<style>body {background-color: #1E1E1E; color: white;}</style>', unsafe_allow_html=True)

    with st.spinner("Loading model and data..."):
        model = load_model()
        df_hist = get_historical_data()

    if model is None or df_hist.empty:
        st.error("Failed to load model or data.")
        return

    features = ['day', 'month', 'pm2_5_change_rate', 'carbon_monoxide', 'carbon_dioxide', 'nitrogen_dioxide', 'sulphur_dioxide']

    # 🔮 Next 24 hours prediction
    st.subheader("🔮 Predictions for the Next 24 Hours")
    df_24h = generate_forecast_data(forecast_period_days=1, freq='H', df_hist=df_hist)
    X_24h = df_24h[features]
    df_24h['pm2_5_prediction'] = model.predict(X_24h)

    with st.expander("View Detailed Latest Predictions", expanded=True):
        st.dataframe(df_24h[['date', 'pm2_5_prediction'] + features]
                     .style.background_gradient(cmap='viridis', subset=['pm2_5_prediction']))

    fig_24h = px.scatter(df_24h, x="date", y="pm2_5_prediction", title="Predicted PM2.5 for Next 24 Hours",
                         color="pm2_5_prediction", color_continuous_scale="Viridis")
    st.plotly_chart(fig_24h, use_container_width=True)

    # 📈 Forecast 3 days
    st.subheader("🔮 Forecast for Next 3 Days")
    df_forecast = generate_forecast_data(forecast_period_days=3, freq='H', df_hist=df_hist)
    df_forecast['pm2_5_prediction'] = model.predict(df_forecast[features])

    with st.expander("View Detailed Forecast Predictions", expanded=True):
        st.dataframe(df_forecast[['date', 'pm2_5_prediction'] + features]
                     .style.background_gradient(cmap='viridis', subset=['pm2_5_prediction']))

    fig_forecast = px.line(df_forecast, x='date', y='pm2_5_prediction', title='Forecast PM2.5 for Next 3 Days')
    st.plotly_chart(fig_forecast, use_container_width=True)

    csv = df_forecast.to_csv(index=False)
    st.download_button("Download Forecast Predictions", data=csv,
                       file_name=f"pm25_forecast_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")

if __name__ == "__main__":
    main()
