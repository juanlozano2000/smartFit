from db.connection import get_connection

class UserRole:
    """
    Modelo para gestionar la relación entre usuarios y roles.
    Tabla: user_role
    """

    @staticmethod
    def assign_user_role(user_id: int, role_code: str):
        """Asigna un rol permitido (TRAINER o MEMBER) a un usuario. Evita duplicados y roles no permitidos a través de la app."""
        allowed = {"TRAINER", "MEMBER"}
        role_code = role_code.upper().strip()

        if role_code not in allowed:
            raise ValueError(f"🚫 No se puede asignar el rol '{role_code}'. Solo se permiten: {', '.join(allowed)}")

        conn = get_connection()
        cur = conn.cursor()

        # Buscar role_id
        cur.execute("SELECT id FROM role WHERE code = ?", (role_code,))
        role = cur.fetchone()
        if not role:
            conn.close()
            raise ValueError(f"❌ Rol '{role_code}' no existe en la base.")

        role_id = role["id"]

        # Evitar duplicados
        cur.execute("SELECT 1 FROM user_role WHERE user_id = ? AND role_id = ?", (user_id, role_id))
        if cur.fetchone():
            conn.close()
            print(f"⚠️ El usuario {user_id} ya tiene asignado el rol {role_code}.")
            return

        cur.execute("INSERT INTO user_role (user_id, role_id) VALUES (?, ?)", (user_id, role_id))
        conn.commit()
        conn.close()
        print(f"✅ Rol '{role_code}' asignado al usuario ID {user_id}.")

    # ---------- READ ----------
    @staticmethod
    def get_roles_by_user(user_id: int):
        """Devuelve todos los roles (codes) de un usuario."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT r.code
            FROM role r
            JOIN user_role ur ON ur.role_id = r.id
            WHERE ur.user_id = ?
        """, (user_id,))
        roles = [row["code"] for row in cur.fetchall()]
        conn.close()
        return roles

    @staticmethod
    def list_all():
        """Lista todas las asignaciones (usuario + rol)."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT u.id AS user_id, u.full_name, r.code AS role
            FROM user_role ur
            JOIN user u ON u.id = ur.user_id
            JOIN role r ON r.id = ur.role_id
            ORDER BY u.id
        """)
        rows = cur.fetchall()
        conn.close()
        return rows