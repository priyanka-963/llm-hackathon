from functools import lru_cache
from pathlib import Path
import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings:
    app_name = os.getenv("APP_NAME", "AI Hotel Revenue Risk Radar")
    app_env = os.getenv("APP_ENV", "local")
    llm_provider = os.getenv("LLM_PROVIDER", "groq").strip().lower()
    groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
    groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    data_path = os.getenv("DATA_PATH", "data/hotel_performance.csv").strip()

    @property
    def resolved_data_path(self) -> Path:
        path = Path(self.data_path)
        return path if path.is_absolute() else PROJECT_ROOT / path


@lru_cache
def get_settings() -> Settings:
    return Settings()
