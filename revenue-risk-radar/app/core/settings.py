from functools import lru_cache
from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parents[2]

try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass


def _clean_env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


class Settings:
    def __init__(self) -> None:
        self.app_name = _clean_env("APP_NAME", "AI Hotel Revenue Risk Radar")
        self.app_env = _clean_env("APP_ENV", "local")
        self.groq_api_key = _clean_env("GROQ_API_KEY")
        self.groq_model = _clean_env("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.gemini_api_key = _clean_env("GEMINI_API_KEY")
        self.gemini_model = _clean_env("GEMINI_MODEL", "gemini-2.5-flash")
        self.data_path = _clean_env("DATA_PATH", "data/hotel_performance.csv")
        self.llm_provider = self._resolve_llm_provider()

    def _resolve_llm_provider(self) -> str:
        configured_provider = _clean_env("LLM_PROVIDER").lower()
        if configured_provider:
            return configured_provider
        if self.groq_api_key:
            return "groq"
        if self.gemini_api_key:
            return "gemini"
        return "groq"

    @property
    def resolved_data_path(self) -> Path:
        path = Path(self.data_path)
        return path if path.is_absolute() else PROJECT_ROOT / path


@lru_cache
def get_settings() -> Settings:
    return Settings()
