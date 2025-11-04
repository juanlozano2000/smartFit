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
        """ Listar todos los usuarios con sus roles """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT u.id, u.full_name, u.status, 
                   GROUP_CONCAT(DISTINCT r.name) as roles
            FROM user u
            LEFT JOIN user_role ur ON u.id = ur.user_id
            LEFT JOIN role r ON ur.role_id = r.id
            GROUP BY u.id, u.full_name, u.status
        """)
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
    
    def list_active_users():
        """ Listar todos los usuarios activos con sus roles """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT u.id, u.full_name, u.status,
                   GROUP_CONCAT(DISTINCT r.name) as roles
            FROM user u
            LEFT JOIN user_role ur ON u.id = ur.user_id
            LEFT JOIN role r ON ur.role_id = r.id
            WHERE u.status = 'ACTIVE'
            GROUP BY u.id, u.full_name, u.status
        """)
        users = cur.fetchall()
        conn.close()
        return users
    
    def list_inactive_users():
        """ Listar todos los usuarios inactivos con sus roles """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT u.id, u.full_name, u.status,
                   GROUP_CONCAT(DISTINCT r.name) as roles
            FROM user u
            LEFT JOIN user_role ur ON u.id = ur.user_id
            LEFT JOIN role r ON ur.role_id = r.id
            WHERE u.status = 'INACTIVE'
            GROUP BY u.id, u.full_name, u.status
        """)
        users = cur.fetchall()
        conn.close()
        return users

    
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


    def activate(user_id):        
        """ Rehabilitar un usuario (marca como ACTIVE) """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE user
            SET status = 'ACTIVE',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id,))
        conn.commit()
        conn.close()
        print("🟢 Usuario marcado como ACTIVO (rehabilitado).")
