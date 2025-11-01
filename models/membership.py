# models/membership.py
from db.connection import get_connection

class Membership:
    """
    Modelo para la tabla 'membership'.
    Representa los tipos de membresías o planes disponibles en el gimnasio.
    Podes crear, leer, actualizar y desactivar membresías.
    Cada membresía tiene un nombre, duración en meses, precio y estado (ACTIVA/INACTIVA).
    """

    # ---------- CREATE ----------
    @staticmethod
    def create(gym_id: int, name: str, duration_months: int, price: float, status: str = "ACTIVE"):
        """Crea una nueva membresía activa."""
        if duration_months <= 0:
            raise ValueError("⚠️ La duración debe ser mayor a 0 meses.")
        if price < 0:
            raise ValueError("⚠️ El precio no puede ser negativo.")
        if status.upper() not in ("ACTIVE", "INACTIVE"):
            raise ValueError("⚠️ Estado inválido. Use 'ACTIVE' o 'INACTIVE'.")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO membership (gym_id, name, duration_months, price, status)
            VALUES (?, ?, ?, ?, ?)
        """, (gym_id, name.strip(), duration_months, price, status.upper()))
        conn.commit()
        conn.close()
        print(f"✅ Membresía '{name}' creada correctamente.")

    # ---------- READ ----------
    @staticmethod
    def all(include_inactive: bool = False):
        """Devuelve todas las membresías, opcionalmente incluyendo las inactivas."""
        conn = get_connection()
        cur = conn.cursor()
        if include_inactive:
            cur.execute("SELECT * FROM membership ORDER BY id")
        else:
            cur.execute("SELECT * FROM membership WHERE status = 'ACTIVE' ORDER BY id")
        rows = cur.fetchall()
        conn.close()
        return rows

    @staticmethod
    def find_by_id(membership_id: int):
        """Busca una membresía por su ID."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM membership WHERE id = ?", (membership_id,))
        row = cur.fetchone()
        conn.close()
        return row

    # ---------- UPDATE ----------
    @staticmethod
    def update(membership_id: int, name=None, duration_months=None, price=None, status=None):
        """Actualiza los campos indicados de una membresía."""
        conn = get_connection()
        cur = conn.cursor()

        fields, values = [], []

        if name:
            fields.append("name = ?")
            values.append(name.strip())
        if duration_months is not None:
            if duration_months <= 0:
                raise ValueError("⚠️ La duración debe ser mayor a 0.")
            fields.append("duration_months = ?")
            values.append(duration_months)
        if price is not None:
            if price < 0:
                raise ValueError("⚠️ El precio no puede ser negativo.")
            fields.append("price = ?")
            values.append(price)
        if status:
            if status.upper() not in ("ACTIVE", "INACTIVE"):
                raise ValueError("⚠️ Estado inválido.")
            fields.append("status = ?")
            values.append(status.upper())

        if not fields:
            print("⚠️ No se especificaron campos para actualizar.")
            return

        values.append(membership_id)
        sql = f"UPDATE membership SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        cur.execute(sql, values)
        conn.commit()
        conn.close()
        print("✅ Membresía actualizada correctamente.")

    # ---------- SOFT DELETE ----------
    @staticmethod
    def deactivate(membership_id: int):
        """Marca la membresía como INACTIVA (baja lógica)."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE membership
            SET status = 'INACTIVE', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (membership_id,))
        conn.commit()
        conn.close()
        print(f"🟡 Membresía ID {membership_id} marcada como INACTIVA.")
