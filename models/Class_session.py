from db.connection import get_connection

class ClassSession:
    """
    Modelo para la tabla 'class' (renombrada a 'class_session' en código).
    Representa una clase grupal del gimnasio.
    
    - TRAINER: puede crear, modificar y eliminar clases propias.
    - ADMIN: puede crear o modificar cualquier clase.
    - MEMBER: puede ver las clases disponibles (no crearlas).
    """

    # ---------- CREATE ----------
    @staticmethod
    def create(gym_id: int, trainer_id: int, name: str,
               start_at: str, end_at: str, capacity: int,
               room: str | None = None,
               current_user_id=None, current_user_roles=None):
        """
        Crea una nueva clase.
        - Solo TRAINER (propia) o ADMIN pueden crear clases.
        - Fechas deben ser válidas (start_at < end_at).
        """
        roles = [r.upper() for r in (current_user_roles or [])]
        is_admin = "ADMIN" in roles
        is_trainer = "TRAINER" in roles

        if not (is_admin or is_trainer):
            raise PermissionError("🚫 Solo entrenadores o administradores pueden crear clases.")

        if start_at >= end_at:
            raise ValueError("⚠️ La hora de inicio debe ser anterior a la de fin.")
        if capacity <= 0:
            raise ValueError("⚠️ La capacidad debe ser mayor a 0.")

        conn = get_connection()
        cur = conn.cursor()

        # Si es trainer, validar que se esté creando con su propio ID
        if is_trainer and current_user_id != trainer_id:
            conn.close()
            raise PermissionError("🚫 Un entrenador solo puede crear clases asignadas a su propio ID.")

        cur.execute("""
            INSERT INTO class (gym_id, trainer_id, name, start_at, end_at, capacity, room)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (gym_id, trainer_id, name.strip(), start_at, end_at, capacity, room))
        conn.commit()
        conn.close()

        print(f"✅ Clase '{name}' creada para el gimnasio ID {gym_id} (Trainer ID {trainer_id}).")

    # ---------- READ ----------
    @staticmethod
    def list_all_classes(current_user_id=None, current_user_roles=None, include_past=False):
        """
        Lista las clases según el rol.
        - ADMIN ve todas.
        - TRAINER ve las suyas.
        - MEMBER ve las activas/futuras.
        """
        roles = [r.upper() for r in (current_user_roles or [])]
        is_admin = "ADMIN" in roles
        is_trainer = "TRAINER" in roles
        is_member = "MEMBER" in roles

        conn = get_connection()
        cur = conn.cursor()

        if is_admin:
            query = """
                SELECT c.*, t.full_name AS trainer_name
                FROM class c
                JOIN user t ON t.id = c.trainer_id
                ORDER BY c.start_at ASC
            """
            cur.execute(query)
        elif is_trainer:
            query = """
                SELECT c.*, t.full_name AS trainer_name
                FROM class c
                JOIN user t ON t.id = c.trainer_id
                WHERE c.trainer_id = ?
                ORDER BY c.start_at ASC
            """
            cur.execute(query, (current_user_id,))
        elif is_member:
            query = """
                SELECT c.*, t.full_name AS trainer_name
                FROM class c
                JOIN user t ON t.id = c.trainer_id
                WHERE c.start_at >= CURRENT_TIMESTAMP
                ORDER BY c.start_at ASC
            """
            cur.execute(query)
        else:
            conn.close()
            raise PermissionError("🚫 Rol no autorizado para ver clases.")

        rows = cur.fetchall()
        conn.close()
        return rows

    # ---------- UPDATE ----------
    @staticmethod
    def update(class_id: int, name=None, start_at=None, end_at=None, capacity=None, room=None,
               current_user_id=None, current_user_roles=None):
        """Actualiza los datos de una clase (solo ADMIN o TRAINER dueño)."""
        roles = [r.upper() for r in (current_user_roles or [])]
        is_admin = "ADMIN" in roles
        is_trainer = "TRAINER" in roles

        if not (is_admin or is_trainer):
            raise PermissionError("🚫 Solo entrenadores o administradores pueden modificar clases.")

        conn = get_connection()
        cur = conn.cursor()

        # Validar propiedad si es entrenador
        if is_trainer:
            cur.execute("SELECT trainer_id FROM class WHERE id = ?", (class_id,))
            row = cur.fetchone()
            if not row:
                conn.close()
                raise ValueError("⚠️ Clase no encontrada.")
            if row["trainer_id"] != current_user_id:
                conn.close()
                raise PermissionError("🚫 No podés modificar clases que no te pertenecen.")

        # Construcción dinámica del UPDATE
        fields, values = [], []
        if name:
            fields.append("name = ?")
            values.append(name.strip())
        if start_at:
            fields.append("start_at = ?")
            values.append(start_at)
        if end_at:
            fields.append("end_at = ?")
            values.append(end_at)
        if capacity is not None:
            if capacity <= 0:
                raise ValueError("⚠️ La capacidad debe ser mayor a 0.")
            fields.append("capacity = ?")
            values.append(capacity)
        if room:
            fields.append("room = ?")
            values.append(room.strip())

        if not fields:
            print("⚠️ No se especificaron campos para actualizar.")
            return

        values.append(class_id)
        sql = f"UPDATE class SET {', '.join(fields)} WHERE id = ?"
        cur.execute(sql, values)
        conn.commit()
        conn.close()

        print(f"✅ Clase ID {class_id} actualizada correctamente.")

    # ---------- DELETE ----------
    @staticmethod
    def delete(class_id: int, current_user_id=None, current_user_roles=None):
        """Elimina una clase (solo ADMIN o TRAINER dueño)."""
        roles = [r.upper() for r in (current_user_roles or [])]
        is_admin = "ADMIN" in roles
        is_trainer = "TRAINER" in roles

        if not (is_admin or is_trainer):
            raise PermissionError("🚫 Solo entrenadores o administradores pueden eliminar clases.")

        conn = get_connection()
        cur = conn.cursor()

        if is_trainer:
            cur.execute("SELECT trainer_id FROM class WHERE id = ?", (class_id,))
            row = cur.fetchone()
            if not row:
                conn.close()
                raise ValueError("⚠️ Clase no encontrada.")
            if row["trainer_id"] != current_user_id:
                conn.close()
                raise PermissionError("🚫 No podés eliminar clases que no son tuyas.")

        cur.execute("DELETE FROM class WHERE id = ?", (class_id,))
        conn.commit()
        conn.close()
        print(f"🗑️ Clase ID {class_id} eliminada correctamente.")
