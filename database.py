import sqlite3
import bcrypt
from contextlib import contextmanager
import os


DATABASE_NAME = os.path.dirname(os.path.realpath(__file__)) + '\\cruise_system.db'

@contextmanager
def db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    try:
        yield conn
    finally:
        conn.close()

def initialize_database():
    with db_connection() as conn:
        cursor = conn.cursor()
        
        #тут также все можно убирать
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT CHECK(role IN ('user', 'manager', 'admin')) NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tours (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                base_price REAL NOT NULL,
                departure_date DATE NOT NULL,
                destination TEXT NOT NULL,
                duration INTEGER NOT NULL,
                comfort_level TEXT,
                available_cabins INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS special_offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tour_id INTEGER NOT NULL,
            discount_percent REAL NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            FOREIGN KEY(tour_id) REFERENCES tours(id)
            )
        ''')
        
        #Создание индексов для столбцов, по которым часто выполняется поиск (можно убрать)
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tours_destination ON tours(destination)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tours_departure ON tours(departure_date)')

        #Другие таблицы (бронирование, отзывы) будут добавлены обычным образом
        conn.commit()