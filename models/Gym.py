# models/gym.py
from db.connection import get_connection

class Gym:
    """
    Modelo para la tabla 'gym'.
    Representa un gimnasio físico dentro del sistema SmartFit.
    
    - ADMIN: puede crear, modificar o eliminar gimnasios.
    - TRAINER y MEMBER: solo pueden consultar información.
    """

    # ---------- CREATE ----------
    @staticmethod
    def create(name: str, address: str | None = None,
               current_user_roles=None):
        """Crea un nuevo gimnasio (solo ADMIN)."""
        roles = [r.upper() for r in (current_user_roles or [])]
        if "ADMIN" not in roles:
            raise PermissionError("🚫 Solo el administrador puede crear gimnasios.")

        if not name.strip():
            raise ValueError("⚠️ El nombre del gimnasio no puede estar vacío.")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO gym (name, address)
            VALUES (?, ?)
        """, (name.strip(), address.strip() if address else None))
        conn.commit()
        conn.close()

        print(f"✅ Gimnasio '{name}' creado correctamente.")

    # ---------- READ ----------
    @staticmethod
    def all(current_user_roles=None):
        """Devuelve todos los gimnasios (visible a todos los roles)."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, address, created_at, updated_at
            FROM gym
            ORDER BY id ASC
        """)
        rows = cur.fetchall()
        conn.close()
        return rows

    @staticmethod
    def find_by_id(gym_id: int):
        """Busca un gimnasio por ID."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, address, created_at, updated_at
            FROM gym
            WHERE id = ?
        """, (gym_id,))
        row = cur.fetchone()
        conn.close()
        return row

    # ---------- UPDATE ----------
    @staticmethod
    def update(gym_id: int, name: str | None = None,
               address: str | None = None,
               current_user_roles=None):
        """Modifica datos de un gimnasio (solo ADMIN)."""
        roles = [r.upper() for r in (current_user_roles or [])]
        if "ADMIN" not in roles:
            raise PermissionError("🚫 Solo el administrador puede modificar gimnasios.")

        if not name and not address:
            print("⚠️ No se especificaron campos para actualizar.")
            return

        conn = get_connection()
        cur = conn.cursor()

        fields, values = [], []
        if name:
            fields.append("name = ?")
            values.append(name.strip())
        if address:
            fields.append("address = ?")
            values.append(address.strip())

        values.append(gym_id)
        sql = f"UPDATE gym SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        cur.execute(sql, values)
        conn.commit()
        conn.close()

        print(f"🟡 Gimnasio ID {gym_id} actualizado correctamente.")

    # ---------- DELETE ----------
    @staticmethod
    def delete(gym_id: int, current_user_roles=None):
        """Elimina un gimnasio (solo ADMIN)."""
        roles = [r.upper() for r in (current_user_roles or [])]
        if "ADMIN" not in roles:
            raise PermissionError("🚫 Solo el administrador puede eliminar gimnasios.")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM gym WHERE id = ?", (gym_id,))
        conn.commit()
        conn.close()
        print(f"🗑️ Gimnasio ID {gym_id} eliminado correctamente.")
