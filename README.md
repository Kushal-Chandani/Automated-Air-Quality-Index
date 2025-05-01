
# Pearls AQI Predictor

The Pearls AQI Predictor is a serverless application that forecasts the Air Quality Index (AQI) for Karachi, Pakistan, over the next 72 hours. It fetches air quality data from the Open-Meteo API, processes it using a feature pipeline, trains machine learning models, and visualizes predictions through an interactive Streamlit dashboard. The project is automated with GitHub Actions for hourly data updates and daily model retraining, and it is containerized using Docker for scalability.

This README provides instructions to run the project either locally or using Docker, including how to set up your Hopsworks API key and execute necessary commands.

---

## Prerequisites

Before running the project, ensure you have the following:

- **Hopsworks Account**: Sign up at Hopsworks.ai and obtain an API key.
- **Python 3.10**: Required for local installation.
- **Docker**: Required for the Docker-based setup.
- **Git**: To clone the repository.
- **A stable internet connection** to fetch data from the Open-Meteo API and interact with Hopsworks.

---

## Repository Structure

- `fetch_features.py`: Fetches and processes air quality data, storing features in Hopsworks.  
- `train_model.py`: Trains machine learning models and saves the best model to Hopsworks.  
- `app.py`: Streamlit application for visualizing AQI forecasts and historical data.  
- `Dockerfile`: Defines the Docker image for the Streamlit app.  
- `docker-compose.yml`: Configures the Docker service.  
- `requirements.txt`: Lists Python dependencies.  
- `.github/workflows/fetch_features.yaml`: GitHub Actions workflow for hourly feature updates.  
- `.github/workflows/train_model.yaml`: GitHub Actions workflow for daily model training.

---

## Setup Instructions

### Option 1: Running Locally

This option installs dependencies directly on your machine and runs the application without Docker.

#### Step 1: Clone the Repository

#### Step 2: Set Up a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 4: Configure Hopsworks API Key

Create a `.env` file in the project root or set the environment variable directly:
```bash
echo "HOPSWORKS_API_KEY=your-hopsworks-api-key" > .env
```

Alternatively, export the key manually:
```bash
export HOPSWORKS_API_KEY=your-hopsworks-api-key
```

Replace `your-hopsworks-api-key` with your actual Hopsworks API key. To obtain it:

- Log in to Hopsworks.
- Navigate to your user settings.
- Generate or copy an API key.

#### Step 5: Fetch and Store Features
```bash
python fetch_features.py
```
This script fetches data from Open-Meteo, processes it (e.g., adds time-based features and PM2.5 change rate), and stores it in the Hopsworks Feature Store.

#### Step 6: Train the Model
```bash
python train_model.py
```
This script evaluates multiple models (e.g., Random Forest, Ridge) and selects the best based on RMSE.

#### Step 7: Run the Streamlit App
```bash
streamlit run app.py
```
Open your browser and navigate to [http://localhost:8501](http://localhost:8501) to view the dashboard. The app displays current AQI, 72-hour forecasts, historical trends, and data exploration tools.

---

### Option 2: Running with Docker

This option uses Docker to containerize the application, ensuring a consistent environment.

#### Step 1: Clone the Repository
```bash
git clone https://github.com/your-username/pearls-aqi-predictor.git
cd pearls-aqi-predictor
```
Replace `your-username` with your GitHub username or the repository URL.

#### Step 2: Configure Hopsworks API Key

Edit the `docker-compose.yml` file to include your Hopsworks API key:
```yaml
version: '3.8'

services:
  streamlit-app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8501:8501"
    environment:
      - HOPSWORKS_API_KEY=your-hopsworks-api-key
    volumes:
      - .:/app
    restart: unless-stopped
```

Replace `your-hopsworks-api-key` with your actual Hopsworks API key (see Step 4 in the local setup for instructions on obtaining it).

Alternatively, create a `.env` file and reference it in `docker-compose.yml`:
```bash
echo "HOPSWORKS_API_KEY=your-hopsworks-api-key" > .env
```

Then modify `docker-compose.yml`:
```yaml
version: '3.8'

services:
  streamlit-app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8501:8501"
    env_file:
      - .env
    volumes:
      - .:/app
    restart: unless-stopped
```

#### Step 3: Build and Run the Docker Container
```bash
docker-compose up --build
```

This command:

- Builds the Docker image using the Dockerfile.
- Starts the Streamlit app, mapping port 8501 to your local machine.

Open your browser and navigate to [http://localhost:8501](http://localhost:8501) to view the dashboard.

#### Step 4: Stopping the Container
```bash
docker-compose down
```

---

## CI/CD Automation

The project includes GitHub Actions workflows for automation:

- **Hourly Feature Updates**: `.github/workflows/fetch_features.yaml` runs `fetch_features.py` every hour.
- **Daily Model Training**: `.github/workflows/train_model.yaml` runs `train_model.py` daily at midnight UTC.

To enable these workflows:

1. Fork or push the repository to GitHub.
2. Add your Hopsworks API key as a GitHub Secret:
   - Go to your repository on GitHub.
   - Navigate to **Settings > Secrets and variables > Actions > New repository secret**.
   - Name the secret `HOPSWORKS_API_KEY` and paste your API key.

The workflows will trigger automatically based on their schedules or can be triggered manually via the GitHub Actions tab.

---

## Troubleshooting

**Hopsworks Connection Issues:**
- Verify your API key is correct and has the necessary permissions.
- Ensure your internet connection is stable.

**Streamlit Not Loading:**
- Check if port 8501 is in use (`lsof -i :8501`) and free it if needed.
- Confirm all dependencies are installed correctly (`pip install -r requirements.txt`).

**Docker Issues:**
- Ensure Docker is running (`docker info`).
- Check logs for errors: `docker-compose logs`.

**Data Fetching Errors:**
- Confirm the Open-Meteo API is accessible and returns valid data.
- Check for missing or invalid data in the Feature Store.

---

## Notes

- The dashboard is optimized for Karachi (latitude: 24.8607, longitude: 67.0011). To adapt it for another city, modify the coordinates in `fetch_features.py`.
- The Hopsworks API key should be kept secure and never hardcoded in the codebase.
- The Docker setup mounts the local directory for development. For production, remove the `volumes` directive in `docker-compose.yml` to use the container's filesystem.