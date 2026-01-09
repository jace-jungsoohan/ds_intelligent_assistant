#!/bin/bash

# Configuration
KEY_FILE="willog-prod-data-gold-ecbeeb0c9e82.json"
APP_PATH="app/ui/main.py"

# Check if key file exists
if [ ! -f "$KEY_FILE" ]; then
    echo "Error: Key file '$KEY_FILE' not found!"
    echo "Please place the Google Cloud service account JSON key in the project root."
    exit 1
fi

# Set Environment Variable
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/$KEY_FILE"
echo "✅ Credentials set: $GOOGLE_APPLICATION_CREDENTIALS"

# Run Streamlit App
echo "🚀 Starting Willog Intelligent Assistant..."
python3 -m streamlit run "$APP_PATH" --server.headless true --server.address 0.0.0.0 --server.enableCORS false --server.enableXsrfProtection false
