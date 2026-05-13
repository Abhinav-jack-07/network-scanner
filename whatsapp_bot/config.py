from __future__ import annotations

from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


@dataclass(frozen=True)
class Settings:
    business_name: str
    whatsapp_verify_token: str
    whatsapp_access_token: str
    whatsapp_phone_number_id: str
    whatsapp_app_secret: str
    openai_api_key: str
    openai_base_url: str
    openai_model: str
    max_history: int
    rate_limit_max: int
    rate_limit_window_seconds: int
    faq_path: str


def get_settings() -> Settings:
    base_dir = os.path.dirname(__file__)
    return Settings(
        business_name=os.getenv("BUSINESS_NAME", "Your Business"),
        whatsapp_verify_token=_required_env("WHATSAPP_VERIFY_TOKEN"),
        whatsapp_access_token=_required_env("WHATSAPP_ACCESS_TOKEN"),
        whatsapp_phone_number_id=_required_env("WHATSAPP_PHONE_NUMBER_ID"),
        whatsapp_app_secret=_required_env("WHATSAPP_APP_SECRET"),
        openai_api_key=_required_env("OPENAI_API_KEY"),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        max_history=int(os.getenv("MAX_HISTORY", "6")),
        rate_limit_max=int(os.getenv("RATE_LIMIT_MAX", "5")),
        rate_limit_window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")),
        faq_path=os.getenv("FAQ_PATH", os.path.join(base_dir, "faq.json")),
    )
