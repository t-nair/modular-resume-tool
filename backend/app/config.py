from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://resume_user:resume_pass@db:5432/resume_db"

    # OpenAI
    openai_api_key: str = ""

    # App
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
