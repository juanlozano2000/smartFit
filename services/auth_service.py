from models.User import User
from models.Role import Role
from models.User_role import UserRole
from db.connection import get_connection
import re
import hashlib
import datetime

class AuthService:
    """
    Servicio de autenticación.
    Se encarga de:
      - Registro de usuarios
      - Login
      - Validación de contraseñas
      - Generación de sesión
    """

    # ---------- VALIDADORES ----------
    @staticmethod
    def _validate_password(password: str):
        """Valida la complejidad mínima del password."""
        if len(password) < 8:
            raise ValueError("⚠️ La contraseña debe tener al menos 8 caracteres.")
        if not re.search(r"[A-Z]", password):
            raise ValueError("⚠️ La contraseña debe tener al menos una letra mayúscula.")
        if not re.search(r"[a-z]", password):
            raise ValueError("⚠️ La contraseña debe tener al menos una letra minúscula.")
        if not re.search(r"[0-9]", password):
            raise ValueError("⚠️ La contraseña debe tener al menos un número.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise ValueError("⚠️ La contraseña debe tener al menos un carácter especial.")

    @staticmethod
    def _hash_password(password: str) -> str:
        """Devuelve el hash SHA256 de la contraseña."""
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    # ---------- REGISTRO ----------
    @staticmethod
    def register(full_name: str, phone: str, password: str,
                 gym_id: int, role_code: str = "MEMBER"):
        """
        Registra un nuevo usuario.
        - Rol por defecto: MEMBER
        - Valida formato y duplicados.
        """
        AuthService._validate_password(password)
        password_hash = AuthService._hash_password(password)

        conn = get_connection()
        cur = conn.cursor()

        # Validar duplicado (mismo teléfono)
        cur.execute("SELECT id FROM user WHERE phone = ?", (phone,))
        if cur.fetchone():
            conn.close()
            raise ValueError("⚠️ Ya existe un usuario con ese teléfono.")

        # Crear usuario
        cur.execute("""
            INSERT INTO user (gym_id, full_name, phone, status, created_at)
            VALUES (?, ?, ?, 'ACTIVE', ?)
        """, (gym_id, full_name.strip(), phone.strip(),
              datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        user_id = cur.lastrowid

        # Asignar rol
        cur.execute("""
            SELECT id FROM role WHERE code = ?
        """, (role_code.upper(),))
        role = cur.fetchone()
        if not role:
            conn.close()
            raise ValueError(f"⚠️ Rol '{role_code}' no existe en la base de datos.")
        role_id = role["id"]

        cur.execute("""
            INSERT INTO user_role (user_id, role_id)
            VALUES (?, ?)
        """, (user_id, role_id))

        # Guardar hash de password en tabla auxiliar (opcional)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_auth (
                user_id INTEGER PRIMARY KEY,
                password_hash TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
            )
        """)
        cur.execute("""
            INSERT INTO user_auth (user_id, password_hash)
            VALUES (?, ?)
        """, (user_id, password_hash))

        conn.commit()
        conn.close()
        print(f"✅ Usuario '{full_name}' registrado correctamente con rol {role_code}.")

    # ---------- LOGIN ----------
    @staticmethod
    def login(phone: str, password: str):
        """Valida credenciales y devuelve los datos de sesión."""
        password_hash = AuthService._hash_password(password)

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT u.id, u.full_name, u.gym_id, u.status, r.code AS role_code
            FROM user u
            JOIN user_role ur ON ur.user_id = u.id
            JOIN role r ON r.id = ur.role_id
            WHERE u.phone = ?
        """, (phone,))
        user = cur.fetchone()
        if not user:
            conn.close()
            raise ValueError("❌ Usuario no encontrado.")

        # Verificar contraseña
        cur.execute("SELECT password_hash FROM user_auth WHERE user_id = ?", (user["id"],))
        auth = cur.fetchone()
        if not auth or auth["password_hash"] != password_hash:
            conn.close()
            raise ValueError("❌ Contraseña incorrecta.")

        if user["status"] != "ACTIVE":
            conn.close()
            raise ValueError("🚫 El usuario está inactivo.")

        conn.close()
        print(f"👋 Bienvenido, {user['full_name']} ({user['role_code']}).")

        return {
            "user_id": user["id"],
            "full_name": user["full_name"],
            "gym_id": user["gym_id"],
            "roles": [user["role_code"]]
        }

    # ---------- UTILIDADES ----------
    @staticmethod
    def deactivate_user(user_id: int, current_user_roles=None):
        """Inactiva un usuario (solo ADMIN)."""
        roles = [r.upper() for r in (current_user_roles or [])]
        if "ADMIN" not in roles:
            raise PermissionError("🚫 Solo el administrador puede desactivar usuarios.")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE user
            SET status = 'INACTIVE', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id,))
        conn.commit()
        conn.close()
        print(f"🟡 Usuario ID {user_id} desactivado correctamente.")
