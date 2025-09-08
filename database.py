import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

# 数据库文件路径
DB_PATH = "crypto_tracker.db"

def init_database():
    """初始化数据库，创建必要的表"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 创建加密货币信息表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cryptocurrencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                slug TEXT,
                first_historical_data TEXT,
                last_historical_data TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建价格历史数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                crypto_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                price REAL NOT NULL,
                market_cap REAL,
                volume_24h REAL,
                percent_change_1h REAL,
                percent_change_24h REAL,
                percent_change_7d REAL,
                circulating_supply REAL,
                FOREIGN KEY (crypto_id) REFERENCES cryptocurrencies (id),
                UNIQUE(crypto_id, timestamp)
            )
        ''')

        # 创建用户关注表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                user_notes TEXT,
                alert_price REAL,
                alert_enabled BOOLEAN DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建用户投资组合表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                quantity REAL NOT NULL,
                buy_price REAL NOT NULL,
                buy_date TEXT NOT NULL,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建索引提高查询性能
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_price_history_crypto_timestamp
            ON price_history(crypto_id, timestamp)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_cryptocurrencies_symbol
            ON cryptocurrencies(symbol)
        ''')

        conn.commit()
        print("数据库初始化完成")

@contextmanager
def get_db_connection():
    """数据库连接上下文管理器"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
    try:
        yield conn
    finally:
        conn.close()

def save_crypto_data(crypto_data):
    """保存加密货币数据到数据库"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 插入或更新加密货币信息
        cursor.execute('''
            INSERT OR REPLACE INTO cryptocurrencies
            (symbol, name, slug)
            VALUES (?, ?, ?)
        ''', (crypto_data['symbol'], crypto_data['name'], crypto_data['symbol'].lower()))

        # 获取crypto_id
        cursor.execute('SELECT id FROM cryptocurrencies WHERE symbol = ?', (crypto_data['symbol'],))
        result = cursor.fetchone()
        crypto_id = result[0] if result else None

        if crypto_id:
            # 插入价格历史数据
            cursor.execute('''
                INSERT OR IGNORE INTO price_history
                (crypto_id, timestamp, price, market_cap, volume_24h,
                 percent_change_1h, percent_change_24h, percent_change_7d, circulating_supply)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                crypto_id,
                datetime.now().isoformat(),
                crypto_data['price'],
                crypto_data['market_cap'],
                crypto_data['volume_24h'],
                crypto_data.get('percent_change_1h', 0),
                crypto_data['percent_change_24h'],
                crypto_data['percent_change_7d'],
                crypto_data.get('circulating_supply', 0)
            ))

        conn.commit()
        return crypto_id

def get_historical_prices(symbol, days=30):
    """获取指定货币的历史价格数据"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute('''
            SELECT ph.timestamp, ph.price, ph.percent_change_24h
            FROM price_history ph
            JOIN cryptocurrencies c ON ph.crypto_id = c.id
            WHERE c.symbol = ?
            AND ph.timestamp >= datetime('now', '-{} days')
            ORDER BY ph.timestamp DESC
        '''.format(days), (symbol,))

        return cursor.fetchall()

def add_to_watchlist(symbol, notes="", alert_price=None):
    """添加到用户关注列表"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR IGNORE INTO user_watchlist
            (symbol, user_notes, alert_price)
            VALUES (?, ?, ?)
        ''', (symbol, notes, alert_price))

        conn.commit()
        return cursor.rowcount > 0

def get_watchlist():
    """获取用户关注列表"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute('''
            SELECT symbol, user_notes, alert_price, alert_enabled, created_at
            FROM user_watchlist
            ORDER BY created_at DESC
        ''')

        return cursor.fetchall()

def add_to_portfolio(symbol, quantity, buy_price, buy_date, notes=""):
    """添加到投资组合"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO user_portfolio
            (symbol, quantity, buy_price, buy_date, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (symbol, quantity, buy_price, buy_date, notes))

        conn.commit()
        return cursor.lastrowid

def get_portfolio():
    """获取用户投资组合"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute('''
            SELECT symbol, quantity, buy_price, buy_date, notes, created_at
            FROM user_portfolio
            ORDER BY created_at DESC
        ''')

        return cursor.fetchall()

# 测试数据库功能
if __name__ == "__main__":
    # 初始化数据库
    init_database()
    print("数据库功能测试完成")
