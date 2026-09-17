"""
🌑 VOID Store Bot - Constantes
"""

# ====================================
# CORES
# ====================================
class Colors:
    """Cores padrão do bot"""
    BLACK = 0x000000
    DARK_GRAY = 0x2b2d31
    GRAY = 0x5865f2
    WHITE = 0xffffff
    
    # Status
    SUCCESS = 0x00ff00
    ERROR = 0xff0000
    WARNING = 0xffff00
    INFO = 0x5865f2
    
    # VOID Colors
    VOID_PRIMARY = 0x000000
    VOID_SECONDARY = 0x2b2d31

# ====================================
# EMOJIS
# ====================================
class Emojis:
    """Emojis padrão do bot"""
    
    # Status
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    LOADING = "⏳"
    
    # Tickets
    TICKET = "🎫"
    PURCHASE = "🛒"
    SERVICE = "⚙️"
    SUPPORT = "💬"
    REPORT = "🚨"
    CLOSE = "🔒"
    OPEN = "🔓"
    
    # Pedidos
    ORDER = "📦"
    PENDING = "⚪"
    IN_PROGRESS = "🟡"
    COMPLETED = "🟢"
    CANCELLED = "🔴"
    
    # Cargos
    CROWN = "👑"
    STARTER = "🟢"
    PLUS = "🟣"
    PREMIUM = "🔴"
    SUPREME = "🔵"
    PRESTIGE = "🟡"
    VIP = "💎"
    BOOSTER = "🚀"
    
    # Tarefas
    TASK = "📋"
    HIGH_PRIORITY = "🔴"
    MEDIUM_PRIORITY = "🟡"
    LOW_PRIORITY = "🟢"
    
    # Estoque
    INVENTORY = "📦"
    IN_STOCK = "🟢"
    LOW_STOCK = "🟡"
    OUT_OF_STOCK = "🔴"
    
    # Moderação
    BAN = "🔨"
    KICK = "👢"
    TIMEOUT = "⏰"
    WARN = "⚠️"
    CLEAR = "🧹"
    
    # Diversos
    MONEY = "💰"
    CALENDAR = "📅"
    CLOCK = "🕐"
    USER = "👤"
    SETTINGS = "⚙️"
    HELP = "❓"
    VOID = "🌑"

# ====================================
# STATUS
# ====================================
class TicketStatus:
    """Status de tickets"""
    OPEN = "open"
    CLOSED = "closed"
    ARCHIVED = "archived"

class OrderStatus:
    """Status de pedidos"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskStatus:
    """Status de tarefas"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskPriority:
    """Prioridades de tarefas"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class StockStatus:
    """Status de estoque"""
    AVAILABLE = "available"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"

# ====================================
# TIPOS DE TICKET
# ====================================
class TicketType:
    """Tipos de ticket"""
    PURCHASE = "purchase"
    SERVICE = "service"
    SUPPORT = "support"
    REPORT = "report"
    
    @classmethod
    def get_emoji(cls, ticket_type: str) -> str:
        """Retorna o emoji do tipo de ticket"""
        emojis = {
            cls.PURCHASE: Emojis.PURCHASE,
            cls.SERVICE: Emojis.SERVICE,
            cls.SUPPORT: Emojis.SUPPORT,
            cls.REPORT: Emojis.REPORT
        }
        return emojis.get(ticket_type, Emojis.TICKET)
    
    @classmethod
    def get_name(cls, ticket_type: str) -> str:
        """Retorna o nome do tipo de ticket"""
        names = {
            cls.PURCHASE: "Compra",
            cls.SERVICE: "Serviço",
            cls.SUPPORT: "Suporte",
            cls.REPORT: "Denúncia"
        }
        return names.get(ticket_type, "Ticket")

# ====================================
# LIMITES
# ====================================
class Limits:
    """Limites do sistema"""
    MAX_TICKET_NAME_LENGTH = 50
    MAX_ORDER_ID_LENGTH = 20
    MAX_TASK_NAME_LENGTH = 100
    MAX_PRODUCT_NAME_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 1000
    EMBED_FIELD_LIMIT = 25
    EMBED_DESCRIPTION_LIMIT = 4096
    BUTTON_LABEL_LIMIT = 80
