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

    opensearch_url: str = "http://localhost:9200"

    kafka_bootstrap_servers: str = "localhost:9092"

    # Setu Account Aggregator sandbox - see docs/ROADMAP.md for how to get
    # real values (Setu, unlike DigiLocker/Aadhaar, offers a free developer
    # sandbox signup).
    setu_base_url: str = "https://fiu-sandbox.setu.co"
    setu_client_id: str = ""
    setu_client_secret: str = ""
    setu_product_instance_id: str = ""

    postgres_dsn: str = "postgresql://sahaj:sahaj_dev_pw@localhost:5432/sahaj_cfti"

    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "phi3:mini"

    # WhatsApp Cloud API - see docs/ARCHITECTURE.md ("What changed from the
    # original design") for why Cloud API replaced the on-prem Business API
    # spec, and docs/ROADMAP.md for the manual setup steps these can't
    # automate (a Meta developer account and business verification).
    whatsapp_api_version: str = "v20.0"
    whatsapp_verify_token: str = ""
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
