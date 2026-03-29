import sqlite3
import os
import logging
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "polymarket_data.db")

def get_connection():
    return sqlite3.connect(DB_FILE)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    logging.info("Dang ket noi vao Kho du lieu SQLite...")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS markets (
            id TEXT PRIMARY KEY,
            question TEXT,
            end_date TEXT,
            active INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS volume_history (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            market_id TEXT,
            volume REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (market_id) REFERENCES markets (id)
        )
    ''')

    conn.commit()
    conn.close()
    logging.info("Da khoi tao cau truc Bang (Tables) thanh cong!")

def save_data_to_db(df):
    if df is None or df.empty:
        return

    conn = get_connection()
    cursor = conn.cursor()

    for index, row in df.iterrows():
        market_id = str(row.get('id', row.get('question', 'unknown')))
        question = str(row.get('question', ''))
        end_date = str(row.get('endDate', ''))
        volume = float(row.get('volume', 0.0))

        cursor.execute('''
            INSERT OR REPLACE INTO markets (id, question, end_date, active)
            VALUES (?, ?, ?, ?)
        ''', (market_id, question, end_date, 1))

        cursor.execute('''
            INSERT INTO volume_history (market_id, volume)
            VALUES (?, ?)
        ''', (market_id, volume))

    conn.commit()
    conn.close()
    logging.info(f"Da boc do xong du lieu cua {len(df)} keo vao Kho!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    init_db()