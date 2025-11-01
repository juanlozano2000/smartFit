from db.connection import get_connection

class Role:
    """
    Modelo para la tabla 'role'.
    En esta clase se manejan los métodos para la tabla role, como crear, listar, buscar por id o código, actualizar, y asignar roles a usuarios.
    """

    # ---------- CREATE ----------
    @staticmethod
    def create(code: str, name: str):
        """Crear un nuevo rol permitido (solo TRAINER o MEMBER), ya que NO se deberia poder crear ADMIN u OWNER desde la app, sino es Hackeable y peligroso."""
        valid_roles = {"TRAINER", "MEMBER"}

        code = code.upper().strip()
        name = name.strip()

        # Validar código permitido
        if code not in valid_roles:
            raise ValueError(f"❌ Rol inválido: '{code}'. Solo se permiten: {', '.join(valid_roles)}")

        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute(
                "INSERT INTO role (code, name) VALUES (?, ?)",
                (code, name)
            )
            conn.commit()
            print(f"✅ Rol '{code}' creado correctamente.")
        except Exception as e:
            print(f"⚠️ No se pudo crear el rol ({e}).")
        finally:
            conn.close()

    # ---------- READ ----------
    @staticmethod
    def list_all_roles():
        """ Listar todos los roles """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM role ORDER BY id")
        rows = cur.fetchall()
        conn.close()
        return rows

    @staticmethod
    def find_by_code(code: str):
        """ Buscar un rol por su código """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM role WHERE code = ?", (code.upper(),))
        row = cur.fetchone()
        conn.close()
        return row

    @staticmethod
    def find_by_id(role_id: int):
        """ Buscar un rol por su ID """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM role WHERE id = ?", (role_id,))
        row = cur.fetchone()
        conn.close()
        return row

    # ---------- UPDATE ----------
    @staticmethod
    def update_name(code: str, new_name: str):
        """Actualizar el nombre descriptivo de un rol permitido (TRAINER o MEMBER). Asegurarse de no permitir cambios a ADMIN u OWNER siendo MEMBER or TRAINER."""
        allowed = {"TRAINER", "MEMBER"}

        code = code.upper().strip()
        new_name = new_name.strip()

        # Validar que el código sea de un rol permitido
        if code not in allowed:
            raise ValueError(f"🚫 No se puede modificar el rol '{code}'. Solo TRAINER o MEMBER pueden editarse.")

        # Validar que el nuevo nombre no intente parecerse a ADMIN/OWNER
        dangerous_words = {"ADMIN", "OWNER", "SUPERUSER", "ROOT"}
        if any(word in new_name.upper() for word in dangerous_words):
            raise ValueError("⚠️ El nombre no puede contener referencias a roles administrativos.")

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "UPDATE role SET name = ? WHERE code = ?",
            (new_name, code)
        )
        conn.commit()
        conn.close()

        print(f"✅ Rol '{code}' actualizado correctamente a '{new_name}'.")

    # ---------- UTILS ----------
    @staticmethod
    def seed_defaults():
        """
        Inserta roles base si no existen.
        """
        base = [
            ("ADMIN", "Administrador"),
            ("OWNER", "Propietario"),
            ("TRAINER", "Entrenador"),
            ("MEMBER", "Socio"),
        ]
        conn = get_connection()
        cur = conn.cursor()
        cur.executemany(
            "INSERT OR IGNORE INTO role (code, name) VALUES (?, ?)",
            base
        )
        conn.commit()
        conn.close()

    # ---------- USER <-> ROLE helpers ----------
    @staticmethod
    def assign_to_user(user_id: int, role_code: str):
        """
        Asigna un rol a un usuario usando la tabla user_role.
        """
        conn = get_connection()
        cur = conn.cursor()
        # Obtener role_id por code
        cur.execute("SELECT id FROM role WHERE code = ?", (role_code.upper(),))
        role = cur.fetchone()
        if not role:
            conn.close()
            raise ValueError(f"Rol '{role_code}' no existe. Crealo primero.")

        role_id = role["id"]
        # Evitar duplicados
        cur.execute(
            "SELECT 1 FROM user_role WHERE user_id = ? AND role_id = ?",
            (user_id, role_id)
        )
        if cur.fetchone():
            conn.close()
            return  # ya asignado, no hacer nada

        cur.execute(
            "INSERT INTO user_role (user_id, role_id) VALUES (?, ?)",
            (user_id, role_id)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def remove_from_user(user_id: int, role_code: str):
        """
        Quita un rol de un usuario (user_role).
        """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM role WHERE code = ?", (role_code.upper(),))
        role = cur.fetchone()
        if not role:
            conn.close()
            return
        role_id = role["id"]

        cur.execute(
            "DELETE FROM user_role WHERE user_id = ? AND role_id = ?",
            (user_id, role_id)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_user_roles(user_id: int):
        """
        Devuelve lista de códigos de rol del usuario.
        """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT r.code
            FROM role r
            JOIN user_role ur ON ur.role_id = r.id
            WHERE ur.user_id = ?
            ORDER BY r.code
        """, (user_id,))
        roles = [row["code"] for row in cur.fetchall()]
        conn.close()
        return roles

    @staticmethod
    def list_users_by_role(role_code: str):
        """
        Lista usuarios que tienen un rol específico.
        """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT u.*
            FROM user u
            JOIN user_role ur ON ur.user_id = u.id
            JOIN role r ON r.id = ur.role_id
            WHERE r.code = ?
            ORDER BY u.id
        """, (role_code.upper(),))
        rows = cur.fetchall()
        conn.close()
        return rows
