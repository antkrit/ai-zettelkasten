from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DeepSeekSettings(BaseSettings):
    """DeepSeek API credentials and model selection (`DEEPSEEK_*` env vars)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="DEEPSEEK_",
        extra="ignore",
    )

    api_key: str = ""
    api_url: str = "https://api.deepseek.com"
    api_model: str = "deepseek-chat"


class NotionSettings(BaseSettings):
    """Notion integration settings (`NOTION_*` env vars)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="NOTION_",
        extra="ignore",
    )

    api_key: str = ""
    database_id: str = ""
    title_property: str = "Name"
    tags_property: str = "Tags"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    deepseek: DeepSeekSettings = Field(default_factory=DeepSeekSettings)
    notion: NotionSettings = Field(default_factory=NotionSettings)


def load_settings() -> Settings:
    return Settings()
