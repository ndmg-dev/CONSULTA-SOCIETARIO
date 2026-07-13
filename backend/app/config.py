"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration using pydantic-settings.

    Values are loaded from environment variables first, then from a .env file.
    """

    DATABASE_URL: str = (
        "postgresql+asyncpg://mguser:mgpass2024@localhost:5432/consulta_societario"
    )
    DATABASE_URL_SYNC: str = (
        "postgresql://mguser:mgpass2024@localhost:5432/consulta_societario"
    )
    CNPJ_API_BASE_URL: str = "https://brasilapi.com.br/api/cnpj/v1"
    MAX_RECURSION_DEPTH: int = 3
    CACHE_TTL_HOURS: int = 24

    model_config = {"env_file": ".env"}


settings = Settings()
