# Stage 1: Build Frontend (Next.js)
FROM node:18-alpine AS builder
WORKDIR /app

# Copy generic package.json first to cache deps
# We copy everything inside frontend/ to . because docker context is root
COPY frontend/package.json frontend/package.json
COPY frontend/package-lock.json* frontend/

# Install dependencies
WORKDIR /app/frontend
# If package-lock exists, it will use it. If not, it generates one.
RUN npm install

# Copy source code
COPY frontend/ .

# Build Next.js
# This requires Next.js to be configured with output: 'export' in next.config.js
RUN npm run build


# Stage 2: Production Backend (FastAPI + Static Files)
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

# Copy Built Frontend from builder stage
# We put it in /app/static, which FastAPI mounts
COPY --from=builder /app/frontend/out /app/static

# Expose Port
EXPOSE 8080
ENV PORT=8080

# Run FastAPI with Uvicorn
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
