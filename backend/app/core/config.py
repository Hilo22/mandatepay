import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel

# Load .env from workspace root or backend directory
ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")
load_dotenv(BACKEND_DIR / ".env")


class Settings(BaseModel):
    PROJECT_NAME: str = "MandatePay Runtime Core"
    VERSION: str = "1.0.0"
    PORT: int = int(os.getenv("PORT", "8000"))

    # PayPal Developer Sandbox Configuration
    PAYPAL_MODE: str = os.getenv("PAYPAL_MODE", "sandbox")
    PAYPAL_CLIENT_ID: str = os.getenv("PAYPAL_CLIENT_ID", "your_paypal_sandbox_client_id_here")
    PAYPAL_CLIENT_SECRET: str = os.getenv("PAYPAL_CLIENT_SECRET", "your_paypal_sandbox_client_secret_here")
    PAYPAL_WEBHOOK_ID: str = os.getenv("PAYPAL_WEBHOOK_ID", "your_registered_sandbox_webhook_id_here")
    PAYPAL_BASE_URL: str = os.getenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")

    # AI Engine / LLM Configuration (Supports OpenAI & Google Gemini)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "your_openai_or_compatible_api_key_here")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.0"))

    # Database & CORS
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,https://*.render.com")

    @property
    def cors_origin_list(self) -> List[str]:
        origins = [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
        if "*" not in origins:
            origins.append("http://127.0.0.1:3000")
        return origins

    @property
    def sqlalchemy_database_url(self) -> str:
        raw = self.DATABASE_URL
        if raw.startswith("file:"):
            # Convert Prisma-style file:./dev.db to SQLAlchemy sqlite:///./dev.db
            path_part = raw.replace("file:", "", 1)
            return f"sqlite:///{path_part}"
        return raw

    @property
    def has_live_paypal_credentials(self) -> bool:
        return (
            bool(self.PAYPAL_CLIENT_ID)
            and bool(self.PAYPAL_CLIENT_SECRET)
            and "your_paypal_sandbox" not in self.PAYPAL_CLIENT_ID
            and "your_paypal_sandbox" not in self.PAYPAL_CLIENT_SECRET
        )

    @property
    def has_live_openai_key(self) -> bool:
        return self.has_live_llm_key

    @property
    def active_llm_key(self) -> str:
        if self.GEMINI_API_KEY and "your_" not in self.GEMINI_API_KEY:
            return self.GEMINI_API_KEY
        if self.OPENAI_API_KEY and "your_openai" not in self.OPENAI_API_KEY:
            return self.OPENAI_API_KEY
        return ""

    @property
    def is_gemini(self) -> bool:
        key = self.active_llm_key
        return (
            key.startswith("AIzaSy")
            or "gemini" in self.LLM_MODEL.lower()
            or bool(self.GEMINI_API_KEY and "your_" not in self.GEMINI_API_KEY)
        )

    @property
    def llm_endpoint(self) -> str:
        if self.is_gemini:
            # Google Gemini's official OpenAI-compatible endpoint
            return "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
        return "https://api.openai.com/v1/chat/completions"

    @property
    def resolved_model_name(self) -> str:
        if self.is_gemini:
            if "gemini" in self.LLM_MODEL.lower():
                return self.LLM_MODEL
            return "gemini-1.5-flash"
        return self.LLM_MODEL

    @property
    def has_live_llm_key(self) -> bool:
        return bool(self.active_llm_key)



settings = Settings()

