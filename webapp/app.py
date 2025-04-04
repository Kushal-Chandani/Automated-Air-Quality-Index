# webapp/app.py

import streamlit as st
import hopsworks
import joblib
import pandas as pd
import os

from datetime import datetime

def load_model():
    # Log in to Hopsworks
    project = hopsworks.login(api_key_value= "2EpVtPZvfyir2ZHe.Xq5Zf52NZvrcFMazBANKnavDajjwl759POapcm1FijsZhoDFqhKeY2zu331fo82i")  # <-- Replace
    mr = project.get_model_registry()

    # Get the model named "openmeteo_pm2_5_model"
    model_version = 1  # or fetch the latest version dynamically
    model_obj = mr.get_model("openmeteo_pm2_5_model", version=model_version)
    model_dir = model_obj.download()
    model_path = os.path.join(model_dir, "model.joblib")

    loaded_model = joblib.load(model_path)
    return loaded_model

def get_latest_data(num_records=10):
    # Fetch some recent data from the Feature Store
    project = hopsworks.login(api_key_value= "2EpVtPZvfyir2ZHe.Xq5Zf52NZvrcFMazBANKnavDajjwl759POapcm1FijsZhoDFqhKeY2zu331fo82i")  # <-- Replace
    fs = project.get_feature_store()
    fg = fs.get_feature_group("openmeteo_aq_feature_group", version=1)
    df = fg.read()
    df = df.sort_values("date", ascending=False).head(num_records)
    return df

def main():
    st.title("Open-Meteo Air Quality Dashboard")

    # Load model
    model = load_model()
    st.write("Loaded the best PM2.5 model from Hopsworks Model Registry.")

    # Get latest data
    df = get_latest_data(num_records=10)
    st.subheader("Latest Feature Data (last 10 records):")
    st.dataframe(df)

    # Prepare data for prediction
    features = [
        'day',
        'month',
        'pm2_5_change_rate',
        'carbon_monoxide',
        'carbon_dioxide',
        'nitrogen_dioxide',
        'sulphur_dioxide'
    ]

    # Make sure no missing columns
    for feat in features:
        if feat not in df.columns:
            st.error(f"Feature '{feat}' not found in the DataFrame.")
            return

    # Drop rows with missing data
    df_predict = df.dropna(subset=features)
    if df_predict.empty:
        st.write("No valid rows to predict on.")
        return

    X = df_predict[features]
    predictions = model.predict(X)
    df_predict['pm2_5_prediction'] = predictions

    st.subheader("Predictions on Latest Data:")
    st.dataframe(df_predict[['date', 'pm2_5_prediction'] + features])

if __name__ == "__main__":
    main()
