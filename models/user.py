from db.connection import get_connection

class User:
    """ Model class for User: en esta clase se manejan los metodos para la tabla user, ejemplo crear, listar, buscar por id para un control mejor de los usuarios """

    # Inicializador de la clase User
    def __init__(self, id=None, gym_id=None, full_name=None, phone=None, status="ACTIVE"):
        self.id = id
        self.gym_id = gym_id
        self.full_name = full_name
        self.phone = phone
        self.status = status

    @staticmethod
    def list_all_users():
        """ Listar todos los usuarios """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM user")
        users = cur.fetchall()
        conn.close()
        return users

    @staticmethod
    def create(gym_id, full_name, phone, status="ACTIVE"):
        """ Crear un nuevo usuario. Devuelve el ID creado. """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO user (gym_id, full_name, phone, status) VALUES (?, ?, ?, ?)",
            (gym_id, full_name, phone, status),
        )
        new_id = cur.lastrowid
        conn.commit()
        conn.close()
        return new_id

    @staticmethod
    def find_by_id(user_id):
        """ Buscar un usuario por su ID """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM user WHERE id = ?", (user_id,))
        user = cur.fetchone()
        conn.close()
        return user
    
    @staticmethod
    def find_by_name(full_name):
        """ Buscar un usuario por su nombre completo """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM user WHERE full_name = ? AND status = 'ACTIVE'", (full_name,))
        user = cur.fetchone()
        conn.close()
        return user

    
    @staticmethod
    def update(user_id, full_name=None, phone=None, status=None):
        """ Actualizar un usuario existente """
        conn = get_connection()
        cur = conn.cursor()

        # Armamos los campos dinámicos
        fields, values = [], []
        if full_name:
            fields.append("full_name = ?")
            values.append(full_name)
        if phone:
            fields.append("phone = ?")
            values.append(phone)
        if status:
            fields.append("status = ?")
            values.append(status)

        if not fields:
            print("⚠️ No se especificaron campos para actualizar.")
            return

        values.append(user_id)
        sql = f"UPDATE user SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        cur.execute(sql, values)
        conn.commit()
        conn.close()
        print("✅ Usuario actualizado correctamente.")

    # ---------- SOFT DELETE ----------
    @staticmethod
    def deactivate(user_id):
        """ Baja lógica de un usuario (marca como INACTIVE) """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE user
            SET status = 'INACTIVE',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id,))
        conn.commit()
        conn.close()
        print("🟡 Usuario marcado como INACTIVO (baja lógica).")
