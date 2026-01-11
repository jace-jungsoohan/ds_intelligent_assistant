# Stage 1: Build Frontend (Next.js)
FROM node:20-slim AS builder
WORKDIR /app/frontend

# Copy package files
COPY frontend/package.json .
COPY frontend/package-lock.json* .

# Install dependencies (Force to bypass peer-dep issues)
RUN npm install --force --no-audit

# Copy source code
COPY frontend/ .

# Build Next.js
# Ensure NODE_ENV is production
ENV NODE_ENV=production
# Run build (ignoring errors as configured in next.config.js)
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
COPY --from=builder /app/frontend/out /app/static

# Expose Port
EXPOSE 8080
ENV PORT=8080

# Run FastAPI with Uvicorn
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
