from db.connection import get_connection

class TrainingPlan:
    """
    Modelo para la tabla 'training_plan'.
    - TRAINER: puede crear, modificar y cerrar planes.
    - MEMBER: puede ver sus propios planes.
    - ADMIN: puede ver todos los planes, pero no los crea directamente.
    """

    # ---------- CREATE ----------
    @staticmethod
    def create(trainer_id: int, member_id: int, goal: str,
               start_date: str | None = None,
               end_date: str | None = None,
               status: str = "ACTIVE",
               current_user_id=None,
               current_user_roles=None):
        """
        Crea un nuevo plan de entrenamiento.
        - Solo TRAINER o ADMIN pueden crearlo.
        - Valida que el trainer_id coincida con el usuario logueado (si es TRAINER).
        """
        roles = [r.upper() for r in (current_user_roles or [])]
        is_admin = "ADMIN" in roles
        is_trainer = "TRAINER" in roles

        if not (is_admin or is_trainer):
            raise PermissionError("🚫 Solo entrenadores o administradores pueden crear planes de entrenamiento.")

        if is_trainer and current_user_id != trainer_id:
            raise PermissionError("🚫 Un entrenador solo puede crear planes asignados a su propio ID.")

        if status.upper() not in ("ACTIVE", "CLOSED"):
            raise ValueError("⚠️ Estado inválido. Use 'ACTIVE' o 'CLOSED'.")

        conn = get_connection()
        cur = conn.cursor()

        # Validar que el member_id exista
        cur.execute("SELECT id FROM user WHERE id = ?", (member_id,))
        if not cur.fetchone():
            conn.close()
            raise ValueError(f"⚠️ El usuario ID {member_id} no existe.")

        # Crear plan
        cur.execute("""
            INSERT INTO training_plan (trainer_id, member_id, goal, start_date, end_date, status)
            VALUES (?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP), ?, ?)
        """, (trainer_id, member_id, goal.strip(), start_date, end_date, status.upper()))
        conn.commit()
        conn.close()

        print(f"✅ Plan de entrenamiento creado para el usuario ID {member_id} por el entrenador ID {trainer_id}.")

    # ---------- READ ----------
    @staticmethod
    def list_all_training_plans(current_user_id=None, current_user_roles=None):
        """Lista todos los planes visibles según el rol."""
        roles = [r.upper() for r in (current_user_roles or [])]
        is_admin = "ADMIN" in roles
        is_trainer = "TRAINER" in roles
        is_member = "MEMBER" in roles

        conn = get_connection()
        cur = conn.cursor()

        if is_admin:
            cur.execute("""
                SELECT tp.*, u.full_name AS member_name, t.full_name AS trainer_name
                FROM training_plan tp
                JOIN user u ON u.id = tp.member_id
                JOIN user t ON t.id = tp.trainer_id
                ORDER BY tp.id DESC
            """)
        elif is_trainer:
            cur.execute("""
                SELECT tp.*, u.full_name AS member_name
                FROM training_plan tp
                JOIN user u ON u.id = tp.member_id
                WHERE tp.trainer_id = ?
                ORDER BY tp.id DESC
            """, (current_user_id,))
        elif is_member:
            cur.execute("""
                SELECT tp.*, t.full_name AS trainer_name
                FROM training_plan tp
                JOIN user t ON t.id = tp.trainer_id
                WHERE tp.member_id = ?
                ORDER BY tp.id DESC
            """, (current_user_id,))
        else:
            conn.close()
            raise PermissionError("🚫 Rol no autorizado para ver planes.")

        rows = cur.fetchall()
        conn.close()
        return rows

    @staticmethod
    def find_by_member(member_id: int, current_user_id=None, current_user_roles=None):
        """Obtiene los planes de un usuario específico."""
        roles = [r.upper() for r in (current_user_roles or [])]
        is_admin = "ADMIN" in roles
        is_trainer = "TRAINER" in roles
        is_member = "MEMBER" in roles

        if not (is_admin or is_trainer or (is_member and member_id == current_user_id)):
            raise PermissionError("🚫 No podés ver los planes de otro usuario.")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT tp.*, t.full_name AS trainer_name
            FROM training_plan tp
            JOIN user t ON t.id = tp.trainer_id
            WHERE tp.member_id = ?
            ORDER BY tp.start_date DESC
        """, (member_id,))
        rows = cur.fetchall()
        conn.close()
        return rows

    # ---------- UPDATE ----------
    @staticmethod
    def update(plan_id: int, goal=None, end_date=None, status=None,
               current_user_id=None, current_user_roles=None):
        """Actualiza un plan (solo TRAINER o ADMIN)."""
        roles = [r.upper() for r in (current_user_roles or [])]
        is_admin = "ADMIN" in roles
        is_trainer = "TRAINER" in roles

        if not (is_admin or is_trainer):
            raise PermissionError("🚫 Solo entrenadores o administradores pueden modificar planes.")

        conn = get_connection()
        cur = conn.cursor()

        # Validar propiedad del plan si es entrenador
        if is_trainer:
            cur.execute("SELECT trainer_id FROM training_plan WHERE id = ?", (plan_id,))
            row = cur.fetchone()
            if not row:
                conn.close()
                raise ValueError("⚠️ El plan no existe.")
            if row["trainer_id"] != current_user_id:
                conn.close()
                raise PermissionError("🚫 No podés modificar un plan que no creaste.")

        fields, values = [], []
        if goal:
            fields.append("goal = ?")
            values.append(goal.strip())
        if end_date:
            fields.append("end_date = ?")
            values.append(end_date)
        if status:
            if status.upper() not in ("ACTIVE", "CLOSED"):
                raise ValueError("⚠️ Estado inválido.")
            fields.append("status = ?")
            values.append(status.upper())

        if not fields:
            print("⚠️ No se especificaron campos para actualizar.")
            return

        values.append(plan_id)
        sql = f"UPDATE training_plan SET {', '.join(fields)} WHERE id = ?"
        cur.execute(sql, values)
        conn.commit()
        conn.close()
        print(f"✅ Plan {plan_id} actualizado correctamente.")
