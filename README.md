# Automated-Air-Quality-Index

## Overview
This project automates fetching air-quality features (hourly), training a model (daily), and serving predictions on a Streamlit dashboard.

## Directory Structure
- `.github/workflows`: GitHub Actions workflows for CI/CD
- `feature_pipeline`: Code to fetch & store features in Hopsworks
- `train_pipeline`: Code to train & register the best model
- `webapp`: Streamlit app to visualize predictions

## Requirements
- Python 3.9+
- Hopsworks API key configured as `HOPSWORKS_API_KEY` in GitHub secrets
- Dependencies listed in `requirements.txt` files

## How to Run Locally
1. Clone the repo
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate

3. Install dependencies for each folder (or combine them in a single environment).

4. Run the feature pipeline:

cd feature_pipeline
python fetch_features.py

5. Run the train pipeline:

cd train_pipeline
python train_model.py

6. Run the webapp:

cd webapp
streamlit run app.py

7. Open the Streamlit app in your browser at http://localhost:8501.

# Done!

With this structure and code, you have:
- **Automated feature ingestion** every hour,  
- **Automated training** every day,  
- A **Streamlit** web app that pulls the **best model** and **latest features** from Hopsworks and displays predictions in a dashboard,  
- **CI/CD** with GitHub Actions.  

