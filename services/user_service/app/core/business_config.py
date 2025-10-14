import json
from functools import lru_cache
from pathlib import Path
from app.core.config import settings

class BusinessConfig:
    
    @staticmethod
    @lru_cache(maxsize=1)
    def load() -> dict:

        config_path = Path(settings.BUSINESS_RULES_PATH)
        if not config_path.exists():
            raise FileNotFoundError(f"Business rules file not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
