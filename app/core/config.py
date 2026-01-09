
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):




    PROJECT_ID: str = "willog-prod-data-gold"
    DATASET_ID: str = "rag"
    LOCATION: str = "asia-northeast3"  # For Vertex AI LLM (Seoul)
    BQ_LOCATION: str = "asia-northeast3"  # For BigQuery (Seoul)
    
    # Optional: LLM settings
    # OPENAI_API_KEY: str = ...

    class Config:
        env_file = ".env"

settings = Settings()
