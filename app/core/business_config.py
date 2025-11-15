import json
from functools import lru_cache
from pathlib import Path
from app.core.config import settings

class BusinessConfig:

    """Class to load and cache business configuration rules from a JSON file."""
    
    @staticmethod
    @lru_cache(maxsize=1)

    def load() -> dict:

        """Load and cache the business configuration from a JSON file."""

        # Load configuration file
        config_path = Path(settings.BUSINESS_RULES_PATH)
        if not config_path.exists():
            raise FileNotFoundError(f"Business rules file not found: {config_path}")

        # Read configuration file
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
