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


class OpenAISettings(BaseSettings):
    """OpenAI API settings for embeddings (`OPENAI_*` env vars)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="OPENAI_",
        extra="ignore",
    )

    api_key: str = ""
    embedding_model: str = "text-embedding-3-small"


class QdrantSettings(BaseSettings):
    """Local Qdrant settings for the embedding experiment (`QDRANT_*` env vars)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="QDRANT_",
        extra="ignore",
    )

    path: str = ".qdrant"
    collection: str = "atomic_notes"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    deepseek: DeepSeekSettings = Field(default_factory=DeepSeekSettings)
    notion: NotionSettings = Field(default_factory=NotionSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    qdrant: QdrantSettings = Field(default_factory=QdrantSettings)


def load_settings() -> Settings:
    return Settings()
