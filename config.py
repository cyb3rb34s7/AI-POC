from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    # LLM
    llm_adapter: Literal["custom", "bedrock", "groq"] = "groq"

    # Custom LLM
    custom_llm_url: str = ""
    custom_llm_api_key: str = ""

    # Bedrock
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"

    # Groq
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # Java backend
    java_backend_url: str = "http://localhost:8080"
    java_filter_endpoint: str = "/api/v1/assets/filter"

    # App
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
