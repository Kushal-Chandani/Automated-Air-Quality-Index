# train_pipeline/Dockerfile
FROM python:3.8-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY train_model.py .
CMD ["python", "train_model.py"]
