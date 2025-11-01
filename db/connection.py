import sqlite3

DB_PATH = r"C:\\Users\\Juani\\Documents\\POO_Ifts\\smartFit\\smartFit\\db\\smartFit.db"

def get_connection():
    """Devuelve una conexión SQLite lista para usar"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # permite acceder a columnas por nombre
    return conn
