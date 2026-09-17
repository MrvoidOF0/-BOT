"""
🌑 VOID Store Bot - Configurações Centralizadas
"""

import os
from dotenv import load_dotenv
from typing import Optional
import json

# Carregar variáveis de ambiente
load_dotenv()

class Config:
    """Configurações centralizadas do bot"""
    
    # ====================================
    # DISCORD
    # ====================================
    DISCORD_TOKEN: str = os.getenv('DISCORD_TOKEN', '')
    GUILD_ID: Optional[int] = int(os.getenv('GUILD_ID', 0)) if os.getenv('GUILD_ID') else None
    PREFIX: str = os.getenv('PREFIX', '!')
    
    # ====================================
    # DATABASE
    # ====================================
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///data/void.db')
    
    # ====================================
    # GOOGLE SHEETS
    # ====================================
    GOOGLE_SHEETS_ENABLED: bool = os.getenv('GOOGLE_SHEETS_ENABLED', 'false').lower() == 'true'
    GOOGLE_SHEET_ID: str = os.getenv('GOOGLE_SHEET_ID', '')
    
    @staticmethod
    def get_google_credentials() -> Optional[dict]:
        """Retorna as credenciais do Google Sheets"""
        creds_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON', '')
        if creds_json:
            try:
                return json.loads(creds_json)
            except json.JSONDecodeError:
                return None
        return None
    
    # ====================================
    # ROLES - ADMIN & STAFF
    # ====================================
    ADMIN_ROLE_ID: Optional[int] = int(os.getenv('ADMIN_ROLE_ID', 0)) if os.getenv('ADMIN_ROLE_ID') else None
    STAFF_ROLE_ID: Optional[int] = int(os.getenv('STAFF_ROLE_ID', 0)) if os.getenv('STAFF_ROLE_ID') else None
    
    # ====================================
    # ROLES - VIP & BOOSTER
    # ====================================
    VIP_ROLE_ID: Optional[int] = int(os.getenv('VIP_ROLE_ID', 0)) if os.getenv('VIP_ROLE_ID') else None
    BOOSTER_ROLE_ID: Optional[int] = int(os.getenv('BOOSTER_ROLE_ID', 0)) if os.getenv('BOOSTER_ROLE_ID') else None
    
    # ====================================
    # ROLES - PROGRESSÃO
    # ====================================
    STARTER_ROLE_ID: Optional[int] = int(os.getenv('STARTER_ROLE_ID', 0)) if os.getenv('STARTER_ROLE_ID') else None
    PLUS_ROLE_ID: Optional[int] = int(os.getenv('PLUS_ROLE_ID', 0)) if os.getenv('PLUS_ROLE_ID') else None
    PREMIUM_ROLE_ID: Optional[int] = int(os.getenv('PREMIUM_ROLE_ID', 0)) if os.getenv('PREMIUM_ROLE_ID') else None
    SUPREME_ROLE_ID: Optional[int] = int(os.getenv('SUPREME_ROLE_ID', 0)) if os.getenv('SUPREME_ROLE_ID') else None
    PRESTIGE_ROLE_ID: Optional[int] = int(os.getenv('PRESTIGE_ROLE_ID', 0)) if os.getenv('PRESTIGE_ROLE_ID') else None
    
    # ====================================
    # TICKETS
    # ====================================
    TICKET_CATEGORY_ID: Optional[int] = int(os.getenv('TICKET_CATEGORY_ID', 0)) if os.getenv('TICKET_CATEGORY_ID') else None
    TICKET_TRANSCRIPT_CHANNEL_ID: Optional[int] = int(os.getenv('TICKET_TRANSCRIPT_CHANNEL_ID', 0)) if os.getenv('TICKET_TRANSCRIPT_CHANNEL_ID') else None
    
    # ====================================
    # LOGS
    # ====================================
    LOG_CHANNEL_ID: Optional[int] = int(os.getenv('LOG_CHANNEL_ID', 0)) if os.getenv('LOG_CHANNEL_ID') else None
    MOD_LOG_CHANNEL_ID: Optional[int] = int(os.getenv('MOD_LOG_CHANNEL_ID', 0)) if os.getenv('MOD_LOG_CHANNEL_ID') else None
    TICKET_LOG_CHANNEL_ID: Optional[int] = int(os.getenv('TICKET_LOG_CHANNEL_ID', 0)) if os.getenv('TICKET_LOG_CHANNEL_ID') else None
    ORDER_LOG_CHANNEL_ID: Optional[int] = int(os.getenv('ORDER_LOG_CHANNEL_ID', 0)) if os.getenv('ORDER_LOG_CHANNEL_ID') else None
    
    # ====================================
    # CONFIGURAÇÕES GERAIS
    # ====================================
    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'production')
    DEBUG: bool = os.getenv('DEBUG', 'false').lower() == 'true'
    LOW_STOCK_THRESHOLD: int = int(os.getenv('LOW_STOCK_THRESHOLD', 5))
    
    # ====================================
    # VALIDAÇÃO
    # ====================================
    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """Valida as configurações obrigatórias"""
        errors = []
        
        if not cls.DISCORD_TOKEN:
            errors.append("❌ DISCORD_TOKEN não configurado")
        
        if not cls.GUILD_ID:
            errors.append("❌ GUILD_ID não configurado")
        
        return len(errors) == 0, errors
    
    @classmethod
    def get_role_tiers(cls) -> dict[str, dict]:
        """Retorna os tiers de cargos por compra"""
        return {
            'STARTER': {
                'role_id': cls.STARTER_ROLE_ID,
                'threshold': 25.00,
                'discount': 3,
                'name': 'Starter',
                'emoji': '🟢'
            },
            'PLUS': {
                'role_id': cls.PLUS_ROLE_ID,
                'threshold': 50.00,
                'discount': 5,
                'name': 'Plus',
                'emoji': '🟣'
            },
            'PREMIUM': {
                'role_id': cls.PREMIUM_ROLE_ID,
                'threshold': 100.00,
                'discount': 7,
                'name': 'Premium',
                'emoji': '🔴'
            },
            'SUPREME': {
                'role_id': cls.SUPREME_ROLE_ID,
                'threshold': 200.00,
                'discount': 10,
                'name': 'Supreme',
                'emoji': '🔵'
            },
            'PRESTIGE': {
                'role_id': cls.PRESTIGE_ROLE_ID,
                'threshold': 350.00,
                'discount': 15,
                'name': 'Prestige',
                'emoji': '🟡'
            }
        }

# Exportar instância única
config = Config()
