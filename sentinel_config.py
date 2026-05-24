import os
import json
from pydantic import BaseModel, Field

CONFIG_FILE = os.path.expanduser("~/.gemini/antigravity/sentinel_config.json")

class SentinelConfig(BaseModel):
    sandbox_dir: str = Field(
        default="/Users/sadeep/Projects/Proactive System Sentinel/sandbox",
        description="The sandbox directory monitored by the smart organizer"
    )
    audit_interval: int = Field(
        default=60,
        description="Interval in seconds for periodic audits"
    )
    cpu_alert_threshold: float = Field(
        default=80.0,
        description="CPU percentage above which alerts are generated"
    )
    ram_alert_threshold: float = Field(
        default=85.0,
        description="RAM memory usage percentage above which alerts are generated"
    )
    disk_alert_threshold: float = Field(
        default=90.0,
        description="Disk space usage percentage above which alerts are generated"
    )
    dir_growth_threshold_mb: float = Field(
        default=10.0,
        description="Directory growth (in MB) within one audit interval that triggers alerts"
    )

def load_config() -> SentinelConfig:
    """Loads config from local JSON storage or returns defaults."""
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
            return SentinelConfig(**data)
        except Exception:
            # Fallback to default if there is a parsing error
            return SentinelConfig()
    return SentinelConfig()

def save_config(config: SentinelConfig):
    """Saves config to local JSON storage."""
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config.model_dump(), f, indent=2)
