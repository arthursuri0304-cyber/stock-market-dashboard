import sqlite3
import os
from datetime import datetime

DB_FILE = "wealth_portfolio.db"

def init_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY,
            symbol TEXT,
            shares REAL,
            avg_cost REAL,
            date TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contributions (
            id INTEGER PRIMARY KEY,
            date TEXT,
            amount REAL,
            symbol TEXT,
            shares REAL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY,
            name TEXT,
            target_amount REAL,
            current REAL,
            target_date TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY,
            date TEXT,
            symbol TEXT,
            action TEXT,
            shares REAL,
            price REAL,
            total REAL,
            signal TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY,
            symbol TEXT,
            alert_type TEXT,
            price_level REAL,
            active INTEGER
        )
    ''')

    conn.commit()
    conn.close()

def add_holding(symbol, shares, avg_cost):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    date = datetime.now().strftime("%Y-%m-%d")
    cursor.execute('INSERT INTO portfolio (symbol, shares, avg_cost, date) VALUES (?,?,?,?)',
                   (symbol.upper(), shares, avg_cost, date))
    conn.commit()
    conn.close()

def add_contribution(amount, symbol=None, shares=None):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    date = datetime.now().strftime("%Y-%m-%d")
    cursor.execute('INSERT INTO contributions (date, amount, symbol, shares) VALUES (?,?,?,?)',
                   (date, amount, symbol, shares))
    conn.commit()
    conn.close()

def add_goal(name, target_amount, target_date):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO goals (name, target_amount, current, target_date) VALUES (?,?,?,?)',
                   (name, target_amount, 0, target_date))
    conn.commit()
    conn.close()

def add_trade(symbol, action, shares, price, signal):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = shares * price
    cursor.execute('INSERT INTO trades (date, symbol, action, shares, price, total, signal) VALUES (?,?,?,?,?,?,?)',
                   (date, symbol.upper(), action, shares, price, total, signal))
    conn.commit()
    conn.close()

def get_portfolio():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM portfolio')
    data = cursor.fetchall()
    conn.close()
    return data

def get_contributions():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM contributions ORDER BY date DESC')
    data = cursor.fetchall()
    conn.close()
    return data

def get_goals():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM goals')
    data = cursor.fetchall()
    conn.close()
    return data

def get_trades():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM trades ORDER BY date DESC')
    data = cursor.fetchall()
    conn.close()
    return data

def add_alert(symbol, alert_type, price_level):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO alerts (symbol, alert_type, price_level, active) VALUES (?,?,?,1)',
                   (symbol.upper(), alert_type, price_level))
    conn.commit()
    conn.close()

if not os.path.exists(DB_FILE):
    init_database()
