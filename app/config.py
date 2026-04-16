"""Application configuration loaded from environment variables.

All config lives here. Other modules import the module-level ``settings``
instance rather than reading environment variables directly.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed, validated application settings.

    Values are read from (in order of precedence):
        1. Environment variables
        2. A local ``.env`` file in the project root
        3. Defaults defined on the fields below

    Attributes:
        openai_api_key: Secret key for the OpenAI API. Required.
        model_name: OpenAI chat model used for both extraction and
            interpretation stages.
    """

    openai_api_key: str = Field(..., description="OpenAI API key.")
    model_name: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model used for LLM calls.",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        protected_namespaces=(),
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance.

    Using ``lru_cache`` ensures the ``.env`` file is parsed exactly once
    per process, and every caller sees the same object.

    Returns:
        The singleton ``Settings`` instance for this process.
    """
    return Settings()
