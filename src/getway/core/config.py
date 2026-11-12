from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GETWAY_", env_file=".env", extra="ignore")

    download_dir: Path = Path("./downloads")
    max_concurrent_downloads: int = 3
    ffmpeg_path: str | None = None


settings = Settings()