from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "sahaj_dev_pw"

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "sahaj"

    redis_url: str = "redis://localhost:6379/0"

    qdrant_url: str = "http://localhost:6333"

    postgres_dsn: str = "postgresql://sahaj:sahaj_dev_pw@localhost:5432/sahaj_cfti"

    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "phi3:mini"


@lru_cache
def get_settings() -> Settings:
    return Settings()
