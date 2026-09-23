# Container configuration for Project FORESIGHT
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Run data pipeline to populate production artifacts
RUN python -m src.pipeline && python -m src.generate_predictions_and_risk

EXPOSE 8501 8000

# Default to Streamlit dashboard (can be overridden to run uvicorn service.main:app)
CMD ["streamlit", "run", "app/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
