import sqlite3
import os
from datetime import datetime
import json

DB_FILE = "portfolio.db"


def init_database():
    """Initialize the database with required tables."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            action TEXT NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            date TEXT NOT NULL,
            commission REAL DEFAULT 0,
            notes TEXT
        )
        '''
    )

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT UNIQUE NOT NULL,
            added_date TEXT NOT NULL,
            target_buy_price REAL,
            target_sell_price REAL,
            alerts_enabled INTEGER DEFAULT 1
        )
        '''
    )

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS price_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            price_threshold REAL NOT NULL,
            triggered INTEGER DEFAULT 0,
            triggered_date TEXT,
            created_date TEXT NOT NULL
        )
        '''
    )

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS signals_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            signal_type TEXT NOT NULL,
            signal_strength REAL NOT NULL,
            components TEXT NOT NULL,
            date TEXT NOT NULL,
            price REAL NOT NULL,
            confidence REAL NOT NULL
        )
        '''
    )

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS daily_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            portfolio_value REAL NOT NULL,
            daily_change REAL NOT NULL,
            daily_return_percent REAL NOT NULL
        )
        '''
    )

    conn.commit()
    conn.close()


def add_transaction(ticker, action, quantity, price, commission=0, notes=""):
    """Add a transaction to the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        '''
        INSERT INTO transactions (ticker, action, quantity, price, date, commission, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''',
        (ticker.upper(), action.upper(), quantity, price, date, commission, notes),
    )

    conn.commit()
    conn.close()


def get_transactions():
    """Get all transactions."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions ORDER BY date DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows


def add_to_watchlist(ticker, target_buy_price=None, target_sell_price=None):
    """Add a stock to the watchlist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    date = datetime.now().strftime("%Y-%m-%d")

    try:
        cursor.execute(
            '''
            INSERT INTO watchlist (ticker, added_date, target_buy_price, target_sell_price)
            VALUES (?, ?, ?, ?)
            ''',
            (ticker.upper(), date, target_buy_price, target_sell_price),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass

    conn.close()


def get_watchlist():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM watchlist")
    rows = cursor.fetchall()
    conn.close()
    return rows


def add_price_alert(ticker, alert_type, price_threshold):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        '''
        INSERT INTO price_alerts (ticker, alert_type, price_threshold, created_date)
        VALUES (?, ?, ?, ?)
        ''',
        (ticker.upper(), alert_type, price_threshold, date),
    )
    conn.commit()
    conn.close()


def record_signal(ticker, signal_type, signal_strength, components, price, confidence):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        '''
        INSERT INTO signals_history (ticker, signal_type, signal_strength, components, date, price, confidence)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''',
        (ticker.upper(), signal_type, signal_strength, json.dumps(components), date, price, confidence),
    )
    conn.commit()
    conn.close()


def get_signals_history(ticker=None, limit=100):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    if ticker:
        cursor.execute(
            "SELECT * FROM signals_history WHERE ticker = ? ORDER BY date DESC LIMIT ?",
            (ticker.upper(), limit),
        )
    else:
        cursor.execute("SELECT * FROM signals_history ORDER BY date DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def record_daily_performance(portfolio_value, daily_change, daily_return_percent):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    date = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        '''
        INSERT INTO daily_performance (date, portfolio_value, daily_change, daily_return_percent)
        VALUES (?, ?, ?, ?)
        ''',
        (date, portfolio_value, daily_change, daily_return_percent),
    )
    conn.commit()
    conn.close()


def get_portfolio():
    """Calculate current portfolio holdings from transactions."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        '''
        SELECT ticker, action, SUM(quantity) as total_quantity, AVG(price) as avg_price
        FROM transactions
        GROUP BY ticker, action
        '''
    )
    results = cursor.fetchall()
    conn.close()

    portfolio = {}
    for ticker, action, quantity, price in results:
        if ticker not in portfolio:
            portfolio[ticker] = {"BUY": 0.0, "SELL": 0.0}
        portfolio[ticker][action.upper()] += float(quantity or 0)

    net_portfolio = {}
    for ticker, values in portfolio.items():
        net_qty = values["BUY"] - values["SELL"]
        if net_qty > 0:
            net_portfolio[ticker] = {
                "quantity": float(net_qty),
                "avg_buy_price": float(values["BUY"] and values["BUY"] / values["BUY"]),
            }

    return net_portfolio


if not os.path.exists(DB_FILE):
    init_database()
