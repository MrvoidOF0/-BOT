"""
🌑 VOID Store Bot - Configurações Centralizadas
Versão defensiva: aceita variáveis ausentes sem quebrar.
"""

import os
from dotenv import load_dotenv
from typing import Optional
import json

load_dotenv()

def _get_int(key: str) -> Optional[int]:
    """Lê variável de ambiente como inteiro, retorna None se ausente ou inválida"""
    value = os.getenv(key, "").strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None

def _get_bool(key: str, default: bool = False) -> bool:
    """Lê variável de ambiente como booleano"""
    value = os.getenv(key, "").strip().lower()
    if not value:
        return default
    return value in ("true", "1", "yes")

def _get_str(key: str, default: str = "") -> str:
    """Lê variável de ambiente como string"""
    return os.getenv(key, default).strip()


class Config:
    """Configurações centralizadas do bot"""

    # ====================================
    # DISCORD
    # ====================================
    DISCORD_TOKEN: str = _get_str("DISCORD_TOKEN")
    GUILD_ID: Optional[int] = _get_int("GUILD_ID")
    PREFIX: str = _get_str("PREFIX", "!")

    # ====================================
    # DATABASE
    # ====================================
    DATABASE_URL: str = _get_str("DATABASE_URL", "sqlite:///data/void.db")

    # ====================================
    # GOOGLE SHEETS
    # ====================================
    GOOGLE_SHEETS_ENABLED: bool = _get_bool("GOOGLE_SHEETS_ENABLED", False)
    GOOGLE_SHEET_ID: str = _get_str("GOOGLE_SHEET_ID")

    @staticmethod
    def get_google_credentials() -> Optional[dict]:
        """Retorna credenciais do Google Sheets de forma segura"""
        creds_json = _get_str("GOOGLE_SERVICE_ACCOUNT_JSON")
        if not creds_json:
            return None
        try:
            return json.loads(creds_json)
        except json.JSONDecodeError:
            return None

    # ====================================
    # ROLES — ADMIN & STAFF
    # ====================================
    ADMIN_ROLE_ID: Optional[int] = _get_int("ADMIN_ROLE_ID")
    STAFF_ROLE_ID: Optional[int] = _get_int("STAFF_ROLE_ID")

    # ====================================
    # ROLES — VIP & BOOSTER
    # ====================================
    VIP_ROLE_ID: Optional[int] = _get_int("VIP_ROLE_ID")
    BOOSTER_ROLE_ID: Optional[int] = _get_int("BOOSTER_ROLE_ID")

    # ====================================
    # ROLES — PROGRESSÃO
    # ====================================
    STARTER_ROLE_ID: Optional[int] = _get_int("STARTER_ROLE_ID")
    PLUS_ROLE_ID: Optional[int] = _get_int("PLUS_ROLE_ID")
    PREMIUM_ROLE_ID: Optional[int] = _get_int("PREMIUM_ROLE_ID")
    SUPREME_ROLE_ID: Optional[int] = _get_int("SUPREME_ROLE_ID")
    PRESTIGE_ROLE_ID: Optional[int] = _get_int("PRESTIGE_ROLE_ID")

    # ====================================
    # TICKETS
    # ====================================
    TICKET_CATEGORY_ID: Optional[int] = _get_int("TICKET_CATEGORY_ID")
    TICKET_TRANSCRIPT_CHANNEL_ID: Optional[int] = _get_int("TICKET_TRANSCRIPT_CHANNEL_ID")

    # ====================================
    # LOGS
    # ====================================
    LOG_CHANNEL_ID: Optional[int] = _get_int("LOG_CHANNEL_ID")
    MOD_LOG_CHANNEL_ID: Optional[int] = _get_int("MOD_LOG_CHANNEL_ID")
    TICKET_LOG_CHANNEL_ID: Optional[int] = _get_int("TICKET_LOG_CHANNEL_ID")
    ORDER_LOG_CHANNEL_ID: Optional[int] = _get_int("ORDER_LOG_CHANNEL_ID")

    # ====================================
    # GERAL
    # ====================================
    ENVIRONMENT: str = _get_str("ENVIRONMENT", "production")
    DEBUG: bool = _get_bool("DEBUG", False)
    LOW_STOCK_THRESHOLD: int = int(_get_str("LOW_STOCK_THRESHOLD", "5") or "5")

    # ====================================
    # VALIDAÇÃO
    # ====================================
    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """Valida apenas as configurações realmente obrigatórias"""
        errors = []

        if not cls.DISCORD_TOKEN:
            errors.append("❌ DISCORD_TOKEN não configurado")

        if not cls.GUILD_ID:
            errors.append("❌ GUILD_ID não configurado")

        return len(errors) == 0, errors

    @classmethod
    def get_role_tiers(cls) -> dict:
        """Retorna os tiers de cargos por compra"""
        return {
            "STARTER": {
                "role_id": cls.STARTER_ROLE_ID,
                "threshold": 25.00,
                "discount": 3,
                "name": "Starter",
                "emoji": "🟢"
            },
            "PLUS": {
                "role_id": cls.PLUS_ROLE_ID,
                "threshold": 50.00,
                "discount": 5,
                "name": "Plus",
                "emoji": "🟣"
            },
            "PREMIUM": {
                "role_id": cls.PREMIUM_ROLE_ID,
                "threshold": 100.00,
                "discount": 7,
                "name": "Premium",
                "emoji": "🔴"
            },
            "SUPREME": {
                "role_id": cls.SUPREME_ROLE_ID,
                "threshold": 200.00,
                "discount": 10,
                "name": "Supreme",
                "emoji": "🔵"
            },
            "PRESTIGE": {
                "role_id": cls.PRESTIGE_ROLE_ID,
                "threshold": 350.00,
                "discount": 15,
                "name": "Prestige",
                "emoji": "🟡"
            }
        }


config = Config()
