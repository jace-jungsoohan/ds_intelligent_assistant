# Backend Only Deployment (Frontend Build Skipped)
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Application Code (Backend)
COPY . .

# Copy Dummy Static Files instead of building frontend
RUN mkdir -p /app/static
COPY static/ /app/static/

# Expose Port
EXPOSE 8080
ENV PORT=8080

# Run FastAPI with Uvicorn
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
