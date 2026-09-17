"""
🌑 VOID Store Bot - Gerenciador de Banco de Dados
"""

import aiosqlite
import asyncpg
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pathlib import Path
from config import config
from utils.logger import logger
from .models import User, Order, Ticket, Task, InventoryItem, Purchase, Configuration

class Database:
    """Gerenciador de banco de dados com suporte a SQLite e PostgreSQL"""
    
    def __init__(self):
        self.db_type = "postgresql" if config.DATABASE_URL.startswith("postgres") else "sqlite"
        self.connection: Optional[Union[aiosqlite.Connection, asyncpg.Pool]] = None
        logger.info(f"Database type: {self.db_type}")
    
    async def connect(self):
        """Conecta ao banco de dados"""
        try:
            if self.db_type == "sqlite":
                # Criar diretório data se não existir
                Path("data").mkdir(exist_ok=True)
                
                # Conectar ao SQLite
                db_path = config.DATABASE_URL.replace("sqlite:///", "")
                self.connection = await aiosqlite.connect(db_path)
                self.connection.row_factory = aiosqlite.Row
                logger.info(f"Connected to SQLite database: {db_path}")
                
            else:
                # Conectar ao PostgreSQL
                self.connection = await asyncpg.create_pool(config.DATABASE_URL)
                logger.info("Connected to PostgreSQL database")
            
            # Inicializar schema
            await self.initialize_schema()
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def disconnect(self):
        """Desconecta do banco de dados"""
        try:
            if self.connection:
                if self.db_type == "sqlite":
                    await self.connection.close()
                else:
                    await self.connection.close()
                logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")
    
    async def initialize_schema(self):
        """Inicializa o schema do banco de dados"""
        try:
            schema_path = Path(__file__).parent / "schema.sql"
            
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = f.read()
            
            if self.db_type == "sqlite":
                await self.connection.executescript(schema)
                await self.connection.commit()
            else:
                async with self.connection.acquire() as conn:
                    # PostgreSQL usa sintaxe ligeiramente diferente
                    # Adaptar schema se necessário
                    await conn.execute(schema)
            
            logger.info("Database schema initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            raise
    
    # ====================================
    # USERS
    # ====================================
    
    async def get_user(self, discord_id: int) -> Optional[User]:
        """Busca um usuário pelo Discord ID"""
        try:
            if self.db_type == "sqlite":
                async with self.connection.execute(
                    "SELECT * FROM users WHERE discord_id = ?",
                    (discord_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return User(**dict(row))
            else:
                async with self.connection.acquire() as conn:
                    row = await conn.fetchrow(
                        "SELECT * FROM users WHERE discord_id = $1",
                        discord_id
                    )
                    if row:
                        return User(**dict(row))
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user {discord_id}: {e}")
            return None
    
    async def create_user(self, discord_id: int, username: str) -> Optional[User]:
        """Cria um novo usuário"""
        try:
            user = User(discord_id=discord_id, username=username)
            
            if self.db_type == "sqlite":
                await self.connection.execute(
                    """
                    INSERT OR IGNORE INTO users (discord_id, username, total_spent, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (user.discord_id, user.username, user.total_spent, user.created_at, user.updated_at)
                )
                await self.connection.commit()
            else:
                async with self.connection.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO users (discord_id, username, total_spent, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (discord_id) DO NOTHING
                        """,
                        user.discord_id, user.username, user.total_spent, user.created_at, user.updated_at
                    )
            
            logger.info(f"User created: {username} ({discord_id})")
            return user
            
        except Exception as e:
            logger.error(f"Error creating user {discord_id}: {e}")
            return None
    
    async def update_user_spent(self, discord_id: int, amount: float) -> bool:
        """Atualiza o valor gasto por um usuário"""
        try:
            if self.db_type == "sqlite":
                await self.connection.execute(
                    """
                    UPDATE users 
                    SET total_spent = total_spent + ?, updated_at = ?
                    WHERE discord_id = ?
                    """,
                    (amount, datetime.now(), discord_id)
                )
                await self.connection.commit()
            else:
                async with self.connection.acquire() as conn:
                    await conn.execute(
                        """
                        UPDATE users 
                        SET total_spent = total_spent + $1, updated_at = $2
                        WHERE discord_id = $3
                        """,
                        amount, datetime.now(), discord_id
                    )
            
            logger.info(f"Updated spent for user {discord_id}: +{amount}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user spent {discord_id}: {e}")
            return False
    
    async def reset_user_spent(self, discord_id: int) -> bool:
        """Reseta o valor gasto por um usuário"""
        try:
            if self.db_type == "sqlite":
                await self.connection.execute(
                    "UPDATE users SET total_spent = 0, updated_at = ? WHERE discord_id = ?",
                    (datetime.now(), discord_id)
                )
                await self.connection.commit()
            else:
                async with self.connection.acquire() as conn:
                    await conn.execute(
                        "UPDATE users SET total_spent = 0, updated_at = $1 WHERE discord_id = $2",
                        datetime.now(), discord_id
                    )
            
            logger.info(f"Reset spent for user {discord_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting user spent {discord_id}: {e}")
            return False
    
    # ====================================
    # ORDERS
    # ====================================
    
    async def get_next_order_number(self) -> int:
        """Retorna o próximo número de pedido"""
        try:
            if self.db_type == "sqlite":
                async with self.connection.execute("SELECT COUNT(*) FROM orders") as cursor:
                    row = await cursor.fetchone()
                    return row[0] if row else 0
            else:
                async with self.connection.acquire() as conn:
                    count = await conn.fetchval("SELECT COUNT(*) FROM orders")
                    return count if count else 0
        except Exception as e:
            logger.error(f"Error getting next order number: {e}")
            return 0
    
    async def create_order(self, order: Order) -> Optional[Order]:
        """Cria um novo pedido"""
        try:
            if self.db_type == "sqlite":
                cursor = await self.connection.execute(
                    """
                    INSERT INTO orders 
                    (order_id, client_id, client_name, product, value, responsible_id, 
                     responsible_name, status, notes, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (order.order_id, order.client_id, order.client_name, order.product,
                     order.value, order.responsible_id, order.responsible_name, order.status,
                     order.notes, order.created_at, order.updated_at)
                )
                await self.connection.commit()
                order.id = cursor.lastrowid
            else:
                async with self.connection.acquire() as conn:
                    row = await conn.fetchrow(
                        """
                        INSERT INTO orders 
                        (order_id, client_id, client_name, product, value, responsible_id,
                         responsible_name, status, notes, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                        RETURNING id
                        """,
                        order.order_id, order.client_id, order.client_name, order.product,
                        order.value, order.responsible_id, order.responsible_name, order.status,
                        order.notes, order.created_at, order.updated_at
                    )
                    order.id = row['id']
            
            logger.info(f"Order created: {order.order_id}")
            return order
            
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return None
    
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Busca um pedido pelo ID"""
        try:
            if self.db_type == "sqlite":
                async with self.connection.execute(
                    "SELECT * FROM orders WHERE order_id = ?",
                    (order_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return Order(**dict(row))
            else:
                async with self.connection.acquire() as conn:
                    row = await conn.fetchrow(
                        "SELECT * FROM orders WHERE order_id = $1",
                        order_id
                    )
                    if row:
                        return Order(**dict(row))
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting order {order_id}: {e}")
            return None
    
    async def update_order_status(self, order_id: str, status: str) -> bool:
        """Atualiza o status de um pedido"""
        try:
            if self.db_type == "sqlite":
                await self.connection.execute(
                    "UPDATE orders SET status = ?, updated_at = ? WHERE order_id = ?",
                    (status, datetime.now(), order_id)
                )
                await self.connection.commit()
            else:
                async with self.connection.acquire() as conn:
                    await conn.execute(
                        "UPDATE orders SET status = $1, updated_at = $2 WHERE order_id = $3",
                        status, datetime.now(), order_id
                    )
            
            logger.info(f"Order {order_id} status updated to {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating order status {order_id}: {e}")
            return False
    
    async def get_orders_by_client(self, client_id: int) -> List[Order]:
        """Busca todos os pedidos de um cliente"""
        try:
            orders = []
            
            if self.db_type == "sqlite":
                async with self.connection.execute(
                    "SELECT * FROM orders WHERE client_id = ? ORDER BY created_at DESC",
                    (client_id,)
                ) as cursor:
                    async for row in cursor:
                        orders.append(Order(**dict(row)))
            else:
                async with self.connection.acquire() as conn:
                    rows = await conn.fetch(
                        "SELECT * FROM orders WHERE client_id = $1 ORDER BY created_at DESC",
                        client_id
                    )
                    for row in rows:
                        orders.append(Order(**dict(row)))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error getting orders for client {client_id}: {e}")
            return []
    
    async def get_all_orders(self, status: Optional[str] = None) -> List[Order]:
        """Busca todos os pedidos, opcionalmente filtrados por status"""
        try:
            orders = []
            
            if self.db_type == "sqlite":
                if status:
                    query = "SELECT * FROM orders WHERE status = ? ORDER BY created_at DESC"
                    params = (status,)
                else:
                    query = "SELECT * FROM orders ORDER BY created_at DESC"
                    params = ()
                
                async with self.connection.execute(query, params) as cursor:
                    async for row in cursor:
                        orders.append(Order(**dict(row)))
            else:
                async with self.connection.acquire() as conn:
                    if status:
                        rows = await conn.fetch(
                            "SELECT * FROM orders WHERE status = $1 ORDER BY created_at DESC",
                            status
                        )
                    else:
                        rows = await conn.fetch(
                            "SELECT * FROM orders ORDER BY created_at DESC"
                        )
                    
                    for row in rows:
                        orders.append(Order(**dict(row)))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error getting all orders: {e}")
            return []
    
    # ====================================
    # TICKETS
    # ====================================
    
    async def create_ticket(self, ticket: Ticket) -> Optional[Ticket]:
        """Cria um novo ticket"""
        try:
            if self.db_type == "sqlite":
                cursor = await self.connection.execute(
                    """
                    INSERT INTO tickets 
                    (channel_id, creator_id, creator_name, ticket_type, status, claimed_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (ticket.channel_id, ticket.creator_id, ticket.creator_name,
                     ticket.ticket_type, ticket.status, ticket.claimed_by, ticket.created_at)
                )
                await self.connection.commit()
                ticket.id = cursor.lastrowid
            else:
                async with self.connection.acquire() as conn:
                    row = await conn.fetchrow(
                        """
                        INSERT INTO tickets 
                        (channel_id, creator_id, creator_name, ticket_type, status, claimed_by, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        RETURNING id
                        """,
                        ticket.channel_id, ticket.creator_id, ticket.creator_name,
                        ticket.ticket_type, ticket.status, ticket.claimed_by, ticket.created_at
                    )
                    ticket.id = row['id']
            
            logger.info(f"Ticket created: {ticket.ticket_type} by {ticket.creator_name}")
            return ticket
            
        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            return None
    
    async def get_ticket_by_channel(self, channel_id: int) -> Optional[Ticket]:
        """Busca um ticket pelo ID do canal"""
        try:
            if self.db_type == "sqlite":
                async with self.connection.execute(
                    "SELECT * FROM tickets WHERE channel_id = ?",
                    (channel_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return Ticket(**dict(row))
            else:
                async with self.connection.acquire() as conn:
                    row = await conn.fetchrow(
                        "SELECT * FROM tickets WHERE channel_id = $1",
                        channel_id
                    )
                    if row:
                        return Ticket(**dict(row))
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting ticket by channel {channel_id}: {e}")
            return None
    
    async def get_user_ticket(self, user_id: int, ticket_type: str) -> Optional[Ticket]:
        """Busca ticket aberto de um usuário por tipo"""
        try:
            if self.db_type == "sqlite":
                async with self.connection.execute(
                    "SELECT * FROM tickets WHERE creator_id = ? AND ticket_type = ? AND status = 'open'",
                    (user_id, ticket_type)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return Ticket(**dict(row))
            else:
                async with self.connection.acquire() as conn:
                    row = await conn.fetchrow(
                        "SELECT * FROM tickets WHERE creator_id = $1 AND ticket_type = $2 AND status = 'open'",
                        user_id, ticket_type
                    )
                    if row:
                        return Ticket(**dict(row))
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user ticket: {e}")
            return None
    
    async def close_ticket(self, channel_id: int) -> bool:
        """Fecha um ticket"""
        try:
            if self.db_type == "sqlite":
                await self.connection.execute(
                    "UPDATE tickets SET status = 'closed', closed_at = ? WHERE channel_id = ?",
                    (datetime.now(), channel_id)
                )
                await self.connection.commit()
            else:
                async with self.connection.acquire() as conn:
                    await conn.execute(
                        "UPDATE tickets SET status = 'closed', closed_at = $1 WHERE channel_id = $2",
                        datetime.now(), channel_id
                    )
            
            logger.info(f"Ticket closed: channel {channel_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error closing ticket {channel_id}: {e}")
            return False
    
    async def claim_ticket(self, channel_id: int, user_id: int) -> bool:
        """Atribui um ticket a um staff"""
        try:
            if self.db_type == "sqlite":
                await self.connection.execute(
                    "UPDATE tickets SET claimed_by = ? WHERE channel_id = ?",
                    (user_id, channel_id)
                )
                await self.connection.commit()
            else:
                async with self.connection.acquire() as conn:
                    await conn.execute(
                        "UPDATE tickets SET claimed_by = $1 WHERE channel_id = $2",
                        user_id, channel_id
                    )
            
            logger.info(f"Ticket claimed: channel {channel_id} by user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error claiming ticket {channel_id}: {e}")
            return False
    
    # ====================================
    # TASKS
    # ====================================
    
    async def create_task(self, task: Task) -> Optional[Task]:
        """Cria uma nova tarefa"""
        try:
            if self.db_type == "sqlite":
                cursor = await self.connection.execute(
                    """
                    INSERT INTO tasks 
                    (name, description, assignee_id, assignee_name, priority, status, deadline, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (task.name, task.description, task.assignee_id, task.assignee_name,
                     task.priority, task.status, task.deadline, task.notes, task.created_at)
                )
                await self.connection.commit()
                task.id = cursor.lastrowid
            else:
                async with self.connection.acquire() as conn:
                    row = await conn.fetchrow(
                        """
                        INSERT INTO tasks 
                        (name, description, assignee_id, assignee_name, priority, status, deadline, notes, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        RETURNING id
                        """,
                        task.name, task.description, task.assignee_id, task.assignee_name,
                        task.priority, task.status, task.deadline, task.notes, task.created_at
                    )
                    task.id = row['id']
            
            logger.info(f"Task created: {task.name} (ID: {task.id})")
            return task
            
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return None
    
    async def get_task(self, task_id: int) -> Optional[Task]:
        """Busca uma tarefa pelo ID"""
        try:
            if self.db_type == "sqlite":
                async with self.connection.execute(
                    "SELECT * FROM tasks WHERE id = ?",
                    (task_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return Task(**dict(row))
            else:
                async with self.connection.acquire() as conn:
                    row = await conn.fetchrow(
                        "SELECT * FROM tasks WHERE id = $1",
                        task_id
                    )
                    if row:
                        return Task(**dict(row))
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting task {task_id}: {e}")
            return None
    
    async def update_task_status(self, task_id: int, status: str) -> bool:
        """Atualiza o status de uma tarefa"""
        try:
            completed_at = datetime.now() if status == "completed" else None
            
            if self.db_type == "sqlite":
                await self.connection.execute(
                    "UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?",
                    (status, completed_at, task_id)
                )
                await self.connection.commit()
            else:
                async with self.connection.acquire() as conn:
                    await conn.execute(
                        "UPDATE tasks SET status = $1, completed_at = $2 WHERE id = $3",
                        status, completed_at, task_id
                    )
            
            logger.info(f"Task {task_id} status updated to {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating task status {task_id}: {e}")
            return False
    
    async def get_all_tasks(self, status: Optional[str] = None) -> List[Task]:
        """Busca todas as tarefas, opcionalmente filtradas por status"""
        try:
            tasks = []
            
            if self.db_type == "sqlite":
                if status:
                    query = "SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC"
                    params = (status,)
                else:
                    query = "SELECT * FROM tasks ORDER BY created_at DESC"
                    params = ()
                
                async with self.connection.execute(query, params) as cursor:
                    async for row in cursor:
                        tasks.append(Task(**dict(row)))
            else:
                async with self.connection.acquire() as conn:
                    if status:
                        rows = await conn.fetch(
                            "SELECT * FROM tasks WHERE status = $1 ORDER BY created_at DESC",
                            status
                        )
                    else:
                        rows = await conn.fetch(
                            "SELECT * FROM tasks ORDER BY created_at DESC"
                        )
                    
                    for row in rows:
                        tasks.append(Task(**dict(row)))
            
            return tasks
            
        except Exception as e:
            logger.error(f"Error getting all tasks: {e}")
            return []
    
    # ====================================
    # INVENTORY
    # ====================================
    
    async def create_inventory_item(self, item: InventoryItem) -> Optional[InventoryItem]:
        """Cria um novo item de estoque"""
        try:
            if self.db_type == "sqlite":
                cursor = await self.connection.execute(
                    """
                    INSERT INTO inventory 
                    (name, category, quantity, price, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (item.name, item.category, item.quantity, item.price,
                     item.status, item.created_at, item.updated_at)
                )
                await self.connection.commit()
                item.id = cursor.lastrowid
            else:
                async with self.connection.acquire() as conn:
                    row = await conn.fetchrow(
                        """
                        INSERT INTO inventory 
                        (name, category, quantity, price, status, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        RETURNING id
                        """,
                        item.name, item.category, item.quantity, item.price,
                        item.status, item.created_at, item.updated_at
                    )
                    item.id = row['id']
            
            logger.info(f"Inventory item created: {item.name}")
            return item
            
        except Exception as e:
            logger.error(f"Error creating inventory item: {e}")
            return None
    
    async def get_inventory_item(self, name: str) -> Optional[InventoryItem]:
        """Busca um item de estoque pelo nome"""
        try:
            if self.db_type == "sqlite":
                async with self.connection.execute(
                    "SELECT * FROM inventory WHERE name = ?",
                    (name,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return InventoryItem(**dict(row))
            else:
                async with self.connection.acquire() as conn:
                    row = await conn.fetchrow(
                        "SELECT * FROM inventory WHERE name = $1",
                        name
                    )
                    if row:
                        return InventoryItem(**dict(row))
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting inventory item {name}: {e}")
            return None
    
    async def update_inventory_quantity(self, name: str, quantity: int) -> bool:
        """Atualiza a quantidade de um item"""
        try:
            # Determinar novo status baseado na quantidade
            from config import config
            if quantity == 0:
                status = "out_of_stock"
            elif quantity <= config.LOW_STOCK_THRESHOLD:
                status = "low_stock"
            else:
                status = "available"
            
            if self.db_type == "sqlite":
                await self.connection.execute(
                    "UPDATE inventory SET quantity = ?, status = ?, updated_at = ? WHERE name = ?",
                    (quantity, status, datetime.now(), name)
                )
                await self.connection.commit()
            else:
                async with self.connection.acquire() as conn:
                    await conn.execute(
                        "UPDATE inventory SET quantity = $1, status = $2, updated_at = $3 WHERE name = $4",
                        quantity, status, datetime.now(), name
                    )
            
            logger.info(f"Inventory updated: {name} = {quantity} ({status})")
            return True
            
        except Exception as e:
            logger.error(f"Error updating inventory quantity {name}: {e}")
            return False
    
    async def get_all_inventory(self) -> List[InventoryItem]:
        """Busca todos os itens de estoque"""
        try:
            items = []
            
            if self.db_type == "sqlite":
                async with self.connection.execute(
                    "SELECT * FROM inventory ORDER BY name"
                ) as cursor:
                    async for row in cursor:
                        items.append(InventoryItem(**dict(row)))
            else:
                async with self.connection.acquire() as conn:
                    rows = await conn.fetch(
                        "SELECT * FROM inventory ORDER BY name"
                    )
                    for row in rows:
                        items.append(InventoryItem(**dict(row)))
            
            return items
            
        except Exception as e:
            logger.error(f"Error getting all inventory: {e}")
            return []
    
    # ====================================
    # PURCHASES
    # ====================================
    
    async def create_purchase(self, purchase: Purchase) -> Optional[Purchase]:
        """Registra uma compra"""
        try:
            if self.db_type == "sqlite":
                cursor = await self.connection.execute(
                    "INSERT INTO purchases (user_id, order_id, amount, created_at) VALUES (?, ?, ?, ?)",
                    (purchase.user_id, purchase.order_id, purchase.amount, purchase.created_at)
                )
                await self.connection.commit()
                purchase.id = cursor.lastrowid
            else:
                async with self.connection.acquire() as conn:
                    row = await conn.fetchrow(
                        "INSERT INTO purchases (user_id, order_id, amount, created_at) VALUES ($1, $2, $3, $4) RETURNING id",
                        purchase.user_id, purchase.order_id, purchase.amount, purchase.created_at
                    )
                    purchase.id = row['id']
            
            logger.info(f"Purchase recorded: {purchase.order_id} - R$ {purchase.amount}")
            return purchase
            
        except Exception as e:
            logger.error(f"Error creating purchase: {e}")
            return None
    
    # ====================================
    # LOGS
    # ====================================
    
    async def create_log(self, log_type: str, user_id: Optional[int], action: str, details: Optional[str] = None) -> bool:
        """Cria um registro de log"""
        try:
            if self.db_type == "sqlite":
                await self.connection.execute(
                    "INSERT INTO logs (log_type, user_id, action, details, created_at) VALUES (?, ?, ?, ?, ?)",
                    (log_type, user_id, action, details, datetime.now())
                )
                await self.connection.commit()
            else:
                async with self.connection.acquire() as conn:
                    await conn.execute(
                        "INSERT INTO logs (log_type, user_id, action, details, created_at) VALUES ($1, $2, $3, $4, $5)",
                        log_type, user_id, action, details, datetime.now()
                    )
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating log: {e}")
            return False
    
    # ====================================
    # CONFIGURATION
    # ====================================
    
    async def get_config(self, key: str) -> Optional[str]:
        """Busca uma configuração"""
        try:
            if self.db_type == "sqlite":
                async with self.connection.execute(
                    "SELECT value FROM configuration WHERE key = ?",
                    (key,)
                ) as cursor:
                    row = await cursor.fetchone()
                    return row[0] if row else None
            else:
                async with self.connection.acquire() as conn:
                    value = await conn.fetchval(
                        "SELECT value FROM configuration WHERE key = $1",
                        key
                    )
                    return value
        except Exception as e:
            logger.error(f"Error getting config {key}: {e}")
            return None
    
    async def set_config(self, key: str, value: str) -> bool:
        """Define uma configuração"""
        try:
            if self.db_type == "sqlite":
                await self.connection.execute(
                    """
                    INSERT INTO configuration (key, value, updated_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = ?
                    """,
                    (key, value, datetime.now(), value, datetime.now())
                )
                await self.connection.commit()
            else:
                async with self.connection.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO configuration (key, value, updated_at)
                        VALUES ($1, $2, $3)
                        ON CONFLICT(key) DO UPDATE SET value = $2, updated_at = $3
                        """,
                        key, value, datetime.now()
                    )
            
            logger.info(f"Config set: {key} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting config {key}: {e}")
            return False
