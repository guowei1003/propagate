from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/propagate"
    llm_provider: str = "demo"
    llm_api_base: str = ""
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    docker_network: str = "propagate-net"
    worker_concurrency: int = 3
    worker_poll_sec: float = 1.0
    runner_image: str = "propagate-runner:latest"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
