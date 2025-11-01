import sqlite3
import os

DB_PATH = r"C:\\Users\\Juani\\Documents\\POO_Ifts\\smartFit\\smartFit\\db\\smartFit.db"
SCHEMA_PATH = "db/schema.sql"

def init_db():
    # Asegura que la carpeta exista
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    # Conexión a la base
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Ejecuta el esquema
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        cursor.executescript(f.read())

    conn.commit()
    conn.close()
    print("Base de datos creada correctamente en:")
    print(DB_PATH)

if __name__ == "__main__":
    init_db()
