from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Personalized News Agent"
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: Optional[str] = Field(default=None, alias="OPENAI_BASE_URL")
    openclaw_base_url: Optional[str] = Field(default=None, alias="OPENCLAW_BASE_URL")
    openclaw_gateway_token: Optional[str] = Field(default=None, alias="OPENCLAW_GATEWAY_TOKEN")
    openai_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_MODEL")
    tavily_api_key: Optional[str] = Field(default=None, alias="TAVILY_API_KEY")
    tavily_base_url: str = Field(default="https://api.tavily.com", alias="TAVILY_BASE_URL")
    tg_bot_token: Optional[str] = Field(default=None, alias="TG_BOT_TOKEN")
    tg_api_base: str = Field(default="https://api.telegram.org", alias="TG_API_BASE")
    tg_webhook_base_url: Optional[str] = Field(default=None, alias="TG_BASE_URL")
    rss_data_dir: str = "data/rss"
    recommendation_limit: int = 5

    @property
    def resolved_openai_base_url(self) -> Optional[str]:
        return self.openai_base_url or self.openclaw_base_url

    @property
    def resolved_openai_api_key(self) -> Optional[str]:
        return self.openai_api_key or self.openclaw_gateway_token


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
