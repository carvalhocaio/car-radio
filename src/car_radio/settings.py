from enum import StrEnum
from functools import lru_cache
from typing import Self

from pydantic import BaseModel, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from car_radio.domain.pit_wall import BoxCutoffs, EscalationCutoffs

OPENROUTER_BASE_URL = "https://openrouter.ai/api"


class ClassifierBackend(StrEnum):
    TYPESAFE = "typesafe"
    OPENROUTER = "openrouter"
    SELF_HOSTED = "self_hosted"


class ClassifierSettings(BaseModel):
    backend: ClassifierBackend = ClassifierBackend.OPENROUTER
    api_key: SecretStr
    base_url: str | None = None
    model: str = "jev-1.13"
    timeout_seconds: float = Field(default=10.0, gt=0)
    max_retries: int = Field(default=2, ge=0)

    @model_validator(mode="after")
    def _require_base_url_when_self_hosted(self) -> Self:
        if self.backend is ClassifierBackend.SELF_HOSTED and not self.base_url:
            raise ValueError("base_url is required for the self_hosted backend")
        return self

    @property
    def resolved_base_url(self) -> str | None:
        if self.base_url:
            return self.base_url
        if self.backend is ClassifierBackend.OPENROUTER:
            return OPENROUTER_BASE_URL
        return None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CAR_RADIO_",
        env_nested_delimiter="__",
        env_file=".env",
        extra="ignore",
    )

    classifier: ClassifierSettings
    box_cutoffs: BoxCutoffs = BoxCutoffs()
    escalation_cutoffs: EscalationCutoffs = EscalationCutoffs()
    database_url: str = "sqlite+aiosqlite:///./car_radio.sqlite3"
    replay_concurrency: int = Field(default=8, ge=1)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # pyright: ignore[reportCallIssue]
