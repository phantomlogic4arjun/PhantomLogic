import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL


PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")


class DatabaseConfig:

    @staticmethod
    def get_database_url() -> URL:

        required_settings = [
            "PHANTOM_LOGIC_DB_HOST",
            "PHANTOM_LOGIC_DB_PORT",
            "PHANTOM_LOGIC_DB_NAME",
            "PHANTOM_LOGIC_DB_USER",
            "PHANTOM_LOGIC_DB_PASSWORD",
        ]

        missing_settings = [
            setting
            for setting in required_settings
            if not os.getenv(setting)
        ]

        if missing_settings:
            raise ValueError(
                f"Missing database configuration: {', '.join(missing_settings)}"
            )

        return URL.create(
            drivername="postgresql+psycopg",
            username=os.getenv("PHANTOM_LOGIC_DB_USER"),
            password=os.getenv("PHANTOM_LOGIC_DB_PASSWORD"),
            host=os.getenv("PHANTOM_LOGIC_DB_HOST"),
            port=int(os.getenv("PHANTOM_LOGIC_DB_PORT")),
            database=os.getenv("PHANTOM_LOGIC_DB_NAME"),
        )