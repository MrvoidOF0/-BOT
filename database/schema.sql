-- ====================================
-- 🌑 VOID Store Bot - Database Schema
-- ====================================

-- Tabela de usuários
CREATE TABLE IF NOT EXISTS users (
    discord_id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    total_spent REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de pedidos
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT UNIQUE NOT NULL,
    client_id INTEGER NOT NULL,
    client_name TEXT NOT NULL,
    product TEXT NOT NULL,
    value REAL NOT NULL,
    responsible_id INTEGER,
    responsible_name TEXT,
    status TEXT DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES users(discord_id)
);

-- Tabela de tickets
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER UNIQUE NOT NULL,
    creator_id INTEGER NOT NULL,
    creator_name TEXT NOT NULL,
    ticket_type TEXT NOT NULL,
    status TEXT DEFAULT 'open',
    claimed_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    FOREIGN KEY (creator_id) REFERENCES users(discord_id)
);

-- Tabela de tarefas
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    assignee_id INTEGER,
    assignee_name TEXT,
    priority TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'pending',
    deadline TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Tabela de estoque
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,
    quantity INTEGER DEFAULT 0,
    price REAL NOT NULL,
    status TEXT DEFAULT 'available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de compras (histórico)
CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    order_id TEXT NOT NULL,
    amount REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(discord_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- Tabela de logs
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_type TEXT NOT NULL,
    user_id INTEGER,
    action TEXT NOT NULL,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de configurações
CREATE TABLE IF NOT EXISTS configuration (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para melhorar performance
CREATE INDEX IF NOT EXISTS idx_orders_client ON orders(client_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_tickets_creator ON tickets(creator_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON tasks(assignee_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_purchases_user ON purchases(user_id);
CREATE INDEX IF NOT EXISTS idx_logs_type ON logs(log_type);
CREATE INDEX IF NOT EXISTS idx_logs_user ON logs(user_id);

-- Tabela de canais de compra
CREATE TABLE IF NOT EXISTS buy_channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    product_id TEXT NOT NULL,
    product_name TEXT NOT NULL,
    value REAL NOT NULL,
    status TEXT DEFAULT 'pending',
    pix_txid TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(discord_id)
);

-- Tabela de pagamentos PIX
CREATE TABLE IF NOT EXISTS pix_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    txid TEXT UNIQUE NOT NULL,
    channel_id INTEGER,
    user_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'pending',
    approved_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(discord_id)
);

-- Tabela de serviços
CREATE TABLE IF NOT EXISTS service_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    service_id TEXT NOT NULL,
    service_name TEXT NOT NULL,
    status TEXT DEFAULT 'open',
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(discord_id)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_buy_channels_user ON buy_channels(user_id);
CREATE INDEX IF NOT EXISTS idx_buy_channels_status ON buy_channels(status);
CREATE INDEX IF NOT EXISTS idx_pix_payments_txid ON pix_payments(txid);
CREATE INDEX IF NOT EXISTS idx_service_requests_user ON service_requests(user_id);
