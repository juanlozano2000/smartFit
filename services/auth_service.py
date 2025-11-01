from db.connection import get_connection

class AuthService:

    # ---------------- REGISTER ----------------
    @staticmethod
    def register(full_name: str, dni: str, phone: str, password: str, gym_id: int, role_code="MEMBER"):
        """Registrar nuevo usuario."""
        conn = get_connection()
        cur = conn.cursor()

        # Crear usuario base
        cur.execute("""
            INSERT INTO user (gym_id, full_name, dni, phone)
            VALUES (?, ?, ?, ?)
        """, (gym_id, full_name.strip(), dni.strip(), phone.strip()))
        user_id = cur.lastrowid

        # Guardar credenciales
        cur.execute("""
            INSERT INTO user_auth (user_id, password)
            VALUES (?, ?)
        """, (user_id, password.strip()))

        # Asignar rol
        cur.execute("""
            INSERT INTO user_role (user_id, role_id)
            SELECT ?, id FROM role WHERE code = ?
        """, (user_id, role_code.upper()))

        conn.commit()
        conn.close()
        print(f"✅ Usuario {full_name} (DNI {dni}) registrado con rol {role_code}")

    # ---------------- LOGIN ----------------
    @staticmethod
    def login(dni: str, password: str):
        """Login con DNI y contraseña."""
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT u.id, u.full_name, u.gym_id,
                   GROUP_CONCAT(r.code) AS roles
            FROM user_auth a
            JOIN user u ON a.user_id = u.id
            JOIN user_role ur ON ur.user_id = u.id
            JOIN role r ON ur.role_id = r.id
            WHERE u.dni = ? AND a.password = ?
            GROUP BY u.id
        """, (dni.strip(), password.strip()))

        row = cur.fetchone()
        conn.close()

        if not row:
            raise Exception("❌ DNI o contraseña incorrectos.")

        return {
            "user_id": row["id"],
            "full_name": row["full_name"],
            "gym_id": row["gym_id"],
            "roles": row["roles"].split(",") if row["roles"] else []
        }

    # ---------------- DEACTIVATE ----------------
    @staticmethod
    def deactivate_user(user_id: int, current_user_roles):
        roles = [r.upper() for r in (current_user_roles or [])]
        if "ADMIN" not in roles:
            raise PermissionError("🚫 Solo el admin puede desactivar usuarios.")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE user SET status = 'INACTIVE' WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
