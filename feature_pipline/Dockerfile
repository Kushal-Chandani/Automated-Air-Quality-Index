# feature_pipeline/Dockerfile
FROM python:3.8-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY fetch_features.py .
CMD ["python", "fetch_features.py"]
