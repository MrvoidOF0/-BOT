"""
🌑 VOID Store Bot - Modelos de Dados
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    """Modelo de usuário"""
    discord_id: int
    username: str
    total_spent: float = 0.0
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

@dataclass
class Order:
    """Modelo de pedido"""
    id: Optional[int] = None
    order_id: str = ""
    client_id: int = 0
    client_name: str = ""
    product: str = ""
    value: float = 0.0
    responsible_id: Optional[int] = None
    responsible_name: Optional[str] = None
    status: str = "pending"
    notes: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

@dataclass
class Ticket:
    """Modelo de ticket"""
    id: Optional[int] = None
    channel_id: int = 0
    creator_id: int = 0
    creator_name: str = ""
    ticket_type: str = ""
    status: str = "open"
    claimed_by: Optional[int] = None
    created_at: datetime = None
    closed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class Task:
    """Modelo de tarefa"""
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    assignee_name: Optional[str] = None
    priority: str = "medium"
    status: str = "pending"
    deadline: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class InventoryItem:
    """Modelo de item de estoque"""
    id: Optional[int] = None
    name: str = ""
    category: str = ""
    quantity: int = 0
    price: float = 0.0
    status: str = "available"
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

@dataclass
class Purchase:
    """Modelo de compra"""
    id: Optional[int] = None
    user_id: int = 0
    order_id: str = ""
    amount: float = 0.0
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class Configuration:
    """Modelo de configuração"""
    key: str = ""
    value: str = ""
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.updated_at is None:
            self.updated_at = datetime.now()
