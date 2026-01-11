from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.core.config import settings

app = FastAPI(title="Willog AI Assistant API", version="1.0.0")

# CORS Configuration
# In production, replace "*" with specific domain
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routes
app.include_router(api_router, prefix="/api")

# Serve Static Files (Frontend)
from fastapi.staticfiles import StaticFiles
import os

static_dir = os.path.join(os.getcwd(), "static")
if os.path.exists(static_dir):
    # Mount static directory to root, html=True allows serving index.html
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    # Use PORT env var if available, default to 8080 (Cloud Run default)
    import os
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
