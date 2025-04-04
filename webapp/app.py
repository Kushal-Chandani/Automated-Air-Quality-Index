import streamlit as st
import hopsworks
import joblib
import pandas as pd
import os
import plotly.express as px
from datetime import datetime
import streamlit.components.v1 as components

# Set page configuration
st.set_page_config(
    page_title="Air Quality Dashboard",
    page_icon="🌬️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
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
        project = hopsworks.login(api_key_value="2EpVtPZvfyir2ZHe.Xq5Zf52NZvrcFMazBANKnavDajjwl759POapcm1FijsZhoDFqhKeY2zu331fo82i")
        mr = project.get_model_registry()
        model_version = 1
        model_obj = mr.get_model("openmeteo_pm2_5_model", version=model_version)
        model_dir = model_obj.download()
        model_path = os.path.join(model_dir, "model.joblib")
        return joblib.load(model_path)
    except Exception as e:
        st.error(f"Error loading model: {str(e)}")
        return None

@st.cache_data(ttl=300)
def get_latest_data(num_records=10):
    try:
        project = hopsworks.login(api_key_value="2EpVtPZvfyir2ZHe.Xq5Zf52NZvrcFMazBANKnavDajjwl759POapcm1FijsZhoDFqhKeY2zu331fo82i")
        fs = project.get_feature_store()
        fg = fs.get_feature_group("openmeteo_aq_feature_group", version=1)
        df = fg.read()
        return df.sort_values("date", ascending=False).head(num_records)
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def get_historical_data():
    """Fetch all historical data to compute averages for forecasting."""
    try:
        project = hopsworks.login(api_key_value="2EpVtPZvfyir2ZHe.Xq5Zf52NZvrcFMazBANKnavDajjwl759POapcm1FijsZhoDFqhKeY2zu331fo82i")
        fs = project.get_feature_store()
        fg = fs.get_feature_group("openmeteo_aq_feature_group", version=1)
        df_hist = fg.read()
        return df_hist
    except Exception as e:
        st.error(f"Error fetching historical data: {str(e)}")
        return pd.DataFrame()

def generate_forecast_data(forecast_period_days=3, freq='H'):
    """
    Generate forecast feature data for the next `forecast_period_days` using historical averages.
    Since we have only historical data, we fill future feature values with averages.
    """
    df_hist = get_historical_data()
    if df_hist.empty:
        st.error("No historical data available for forecasting.")
        return pd.DataFrame()

    # Compute historical averages for pollutant features and change rate
    avg_carbon_monoxide = df_hist['carbon_monoxide'].mean()
    avg_carbon_dioxide = df_hist['carbon_dioxide'].mean()
    avg_nitrogen_dioxide = df_hist['nitrogen_dioxide'].mean()
    avg_sulphur_dioxide = df_hist['sulphur_dioxide'].mean()
    avg_pm2_5_change_rate = df_hist['pm2_5_change_rate'].mean()

    # Determine forecast start time: one hour after the latest timestamp in historical data
    last_date = pd.to_datetime(df_hist['date'].max())
    forecast_start = last_date + pd.Timedelta(hours=1)
    forecast_end = forecast_start + pd.Timedelta(days=forecast_period_days)
    # Create hourly timestamps for the forecast period
    forecast_dates = pd.date_range(start=forecast_start, end=forecast_end - pd.Timedelta(hours=1), freq=freq)

    forecast_df = pd.DataFrame({
        'date': forecast_dates,
        'day': forecast_dates.day,
        'month': forecast_dates.month,
        'carbon_monoxide': avg_carbon_monoxide,
        'carbon_dioxide': avg_carbon_dioxide,
        'nitrogen_dioxide': avg_nitrogen_dioxide,
        'sulphur_dioxide': avg_sulphur_dioxide,
        'pm2_5_change_rate': avg_pm2_5_change_rate
    })
    return forecast_df

def main():
    # Sidebar for settings and information
    with st.sidebar:
        st.title("⚙️ Settings")
        num_records = st.slider("Number of Records", 5, 50, 10, 5)
        theme = st.selectbox("Theme", ["Light", "Dark"])
        refresh_button = st.button("Refresh Data")
        
        st.markdown("---")
        st.subheader("About")
        st.write("Air Quality Prediction Dashboard")
        st.write(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Main content title
    st.title("🌬️ Open-Meteo Air Quality Dashboard")
    
    # Apply theme if selected
    if theme == "Dark":
        st.markdown('<style>body {background-color: #1E1E1E; color: white;}</style>', unsafe_allow_html=True)

    # Load model and latest feature data
    with st.spinner("Loading model and data..."):
        model = load_model()
        df_latest = get_latest_data(num_records)

    if model is None or df_latest.empty:
        st.error("Failed to initialize dashboard. Please check your connection and try again.")
        return

    # Display latest feature data and PM2.5 trend
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("📊 Latest Feature Data")
        st.dataframe(
            df_latest.style.format("{:.2f}", subset=df_latest.select_dtypes(include=['float64']).columns),
            height=300
        )
    with col2:
        st.subheader("📈 PM2.5 Trend")
        if not df_latest.empty:
            fig = px.line(df_latest, x="date", y="pm2_5_change_rate", title="PM2.5 Change Rate")
            st.plotly_chart(fig, use_container_width=True)

    # Predict on latest data
    st.subheader("🔮 Predictions on Latest Data")
    features = [
        'day', 'month', 'pm2_5_change_rate', 'carbon_monoxide',
        'carbon_dioxide', 'nitrogen_dioxide', 'sulphur_dioxide'
    ]
    missing_features = [feat for feat in features if feat not in df_latest.columns]
    if missing_features:
        st.error(f"Missing features: {', '.join(missing_features)}")
        return

    df_predict_latest = df_latest.dropna(subset=features)
    if not df_predict_latest.empty:
        X_latest = df_predict_latest[features]
        predictions_latest = model.predict(X_latest)
        df_predict_latest['pm2_5_prediction'] = predictions_latest

        with st.expander("View Detailed Latest Predictions", expanded=True):
            st.dataframe(
                df_predict_latest[['date', 'pm2_5_prediction'] + features]
                .style.background_gradient(cmap='viridis', subset=['pm2_5_prediction'])
            )

        fig_pred_latest = px.scatter(
            df_predict_latest, 
            x="date", 
            y="pm2_5_prediction", 
            title="PM2.5 Predictions on Latest Data",
            color="pm2_5_prediction",
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig_pred_latest, use_container_width=True)
    else:
        st.warning("No valid latest data available for predictions.")

    # Generate and display forecast predictions for the next 3 days
    st.subheader("🔮 Forecast for Next 3 Days")
    forecast_df = generate_forecast_data(forecast_period_days=3, freq='H')
    if not forecast_df.empty:
        X_forecast = forecast_df[features]
        forecast_predictions = model.predict(X_forecast)
        forecast_df['pm2_5_prediction'] = forecast_predictions

        with st.expander("View Detailed Forecast Predictions", expanded=True):
            st.dataframe(
                forecast_df[['date', 'pm2_5_prediction'] + features]
                .style.background_gradient(cmap='viridis', subset=['pm2_5_prediction'])
            )

        fig_forecast = px.line(
            forecast_df, 
            x='date', 
            y='pm2_5_prediction', 
            title='Forecast PM2.5 for Next 3 Days'
        )
        st.plotly_chart(fig_forecast, use_container_width=True)
    else:
        st.warning("Unable to generate forecast predictions.")

    # Provide a download button for forecast predictions
    csv = forecast_df.to_csv(index=False)
    st.download_button(
        label="Download Forecast Predictions",
        data=csv,
        file_name=f"pm25_forecast_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    main()
