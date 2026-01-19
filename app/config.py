from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Topcell Weighbridge"
    data_dir: str = str(Path(__file__).resolve().parent / "data")
    db_path: str = str(Path(__file__).resolve().parent / "data" / "weighbridge.db")
    attachments_dir: str = str(Path(__file__).resolve().parent / "data" / "attachments")

    # Odoo connectivity
    odoo_base_url: str | None = None
    odoo_api_key: str | None = None
    odoo_db: str | None = None
    odoo_username: str | None = None

    # Sync cadence and serial behavior
    sync_interval_seconds: int = 20
    serial_read_timeout: float = 0.2
    allow_weight_simulation: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.attachments_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    return settings
