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
    whatsapp_api_version: str
    openai_api_key: str
    openai_base_url: str
    openai_model: str
    max_history: int
    rate_limit_max: int
    rate_limit_window_seconds: int
    faq_path: str
    whatsapp_request_timeout_seconds: int
    openai_request_timeout_seconds: int
    log_redaction_chars: int


def get_settings() -> Settings:
    base_dir = os.path.dirname(__file__)
    return Settings(
        business_name=os.getenv("BUSINESS_NAME", "Your Business"),
        whatsapp_verify_token=_required_env("WHATSAPP_VERIFY_TOKEN"),
        whatsapp_access_token=_required_env("WHATSAPP_ACCESS_TOKEN"),
        whatsapp_phone_number_id=_required_env("WHATSAPP_PHONE_NUMBER_ID"),
        whatsapp_app_secret=_required_env("WHATSAPP_APP_SECRET"),
        whatsapp_api_version=os.getenv("WHATSAPP_API_VERSION", "v19.0"),
        openai_api_key=_required_env("OPENAI_API_KEY"),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        max_history=int(os.getenv("MAX_HISTORY", "6")),
        rate_limit_max=int(os.getenv("RATE_LIMIT_MAX", "5")),
        rate_limit_window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")),
        faq_path=os.getenv("FAQ_PATH", os.path.join(base_dir, "faq.json")),
        whatsapp_request_timeout_seconds=int(
            os.getenv("WHATSAPP_REQUEST_TIMEOUT_SECONDS", "10")
        ),
        openai_request_timeout_seconds=int(
            os.getenv("OPENAI_REQUEST_TIMEOUT_SECONDS", "15")
        ),
        log_redaction_chars=int(os.getenv("LOG_REDACTION_CHARS", "40")),
    )
