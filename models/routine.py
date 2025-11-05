from db.connection import get_connection

class Routine:
    """
    Modelo para la tabla 'routine'.
    - TRAINER: puede crear, modificar o borrar rutinas de sus propios planes.
    - MEMBER: puede ver las rutinas de su plan activo.
    - ADMIN: puede ver todas las rutinas, pero no crearlas.
    """

    # ---------- CREATE ----------
    @staticmethod
    def create(plan_id: int, name: str, weekday: int, notes: str = "",
               current_user_id=None, current_user_roles=None):
        """
        Crea una rutina para un plan.
        - Solo TRAINER o ADMIN pueden crear.
        - Si es TRAINER, debe ser dueño del plan.
        """
        roles = [r.upper() for r in (current_user_roles or [])]
        is_admin = "ADMIN" in roles
        is_trainer = "TRAINER" in roles

        if not (1 <= weekday <= 7):
            raise ValueError("⚠️ El día de la semana (weekday) debe estar entre 1 y 7.")

        conn = get_connection()
        cur = conn.cursor()

        # Validar propiedad del plan si es entrenador
        if is_trainer:
            cur.execute("SELECT trainer_id FROM training_plan WHERE id = ?", (plan_id,))
            row = cur.fetchone()
            if not row:
                conn.close()
                raise ValueError(f"⚠️ El plan ID {plan_id} no existe.")
            if row["trainer_id"] != current_user_id:
                conn.close()
                raise PermissionError("🚫 No podés crear rutinas en planes que no te pertenecen.")

        # Crear rutina
        cur.execute("""
            INSERT INTO routine (plan_id, name, weekday, notes)
            VALUES (?, ?, ?, ?)
        """, (plan_id, name.strip(), weekday, notes.strip()))
        conn.commit()
        conn.close()

        print(f"✅ Rutina '{name}' agregada al plan ID {plan_id} (día {weekday}).")

    # ---------- READ ----------
    @staticmethod
    def list_by_plan(plan_id: int, current_user_id=None, current_user_roles=None):
        """Devuelve todas las rutinas de un plan (según permisos)."""
        roles = [r.upper() for r in (current_user_roles or [])]
        is_admin = "ADMIN" in roles
        is_trainer = "TRAINER" in roles
        is_member = "MEMBER" in roles

        conn = get_connection()
        cur = conn.cursor()

        # Validar acceso según rol
        if is_trainer:
            cur.execute("SELECT trainer_id FROM training_plan WHERE id = ?", (plan_id,))
            plan = cur.fetchone()
            if not plan:
                conn.close()
                raise ValueError("⚠️ El plan no existe.")
            if plan["trainer_id"] != current_user_id:
                conn.close()
                raise PermissionError("🚫 No podés ver rutinas de planes ajenos.")
        elif is_member:
            cur.execute("SELECT member_id FROM training_plan WHERE id = ?", (plan_id,))
            plan = cur.fetchone()
            if not plan:
                conn.close()
                raise ValueError("⚠️ El plan no existe.")
            if plan["member_id"] != current_user_id:
                conn.close()
                raise PermissionError("🚫 Solo podés ver rutinas de tus propios planes.")

        cur.execute("""
            SELECT id, name, weekday, notes
            FROM routine
            WHERE plan_id = ?
            ORDER BY weekday ASC
        """, (plan_id,))
        rows = cur.fetchall()
        conn.close()
        return rows

    # ---------- UPDATE ----------
    @staticmethod
    def update(routine_id: int, name=None, weekday=None, notes=None,
               current_user_id=None, current_user_roles=None):
        """Modifica una rutina existente (solo TRAINER o ADMIN)."""
        roles = [r.upper() for r in (current_user_roles or [])]
        is_admin = "ADMIN" in roles
        is_trainer = "TRAINER" in roles

        if not (is_admin or is_trainer):
            raise PermissionError("🚫 Solo entrenadores o administradores pueden modificar rutinas.")

        conn = get_connection()
        cur = conn.cursor()

        # Validar propiedad si es entrenador
        if is_trainer:
            cur.execute("""
                SELECT tp.trainer_id
                FROM routine r
                JOIN training_plan tp ON tp.id = r.plan_id
                WHERE r.id = ?
            """, (routine_id,))
            row = cur.fetchone()
            if not row:
                conn.close()
                raise ValueError("⚠️ Rutina no encontrada.")
            if row["trainer_id"] != current_user_id:
                conn.close()
                raise PermissionError("🚫 No podés modificar rutinas de otros entrenadores.")

        fields, values = [], []
        if name:
            fields.append("name = ?")
            values.append(name.strip())
        if weekday:
            if not (1 <= weekday <= 7):
                raise ValueError("⚠️ weekday debe estar entre 1 y 7.")
            fields.append("weekday = ?")
            values.append(weekday)
        if notes is not None:
            fields.append("notes = ?")
            values.append(notes.strip())

        if not fields:
            print("⚠️ No se especificaron campos para actualizar.")
            return

        values.append(routine_id)
        sql = f"UPDATE routine SET {', '.join(fields)} WHERE id = ?"
        cur.execute(sql, values)
        conn.commit()
        conn.close()
        print(f"✅ Rutina ID {routine_id} actualizada correctamente.")

    # ---------- DELETE ----------
    @staticmethod
    def delete(routine_id: int, current_user_id=None, current_user_roles=None):
        """Elimina una rutina (solo TRAINER dueño o ADMIN)."""
        roles = [r.upper() for r in (current_user_roles or [])]
        is_admin = "ADMIN" in roles
        is_trainer = "TRAINER" in roles

        if not (is_admin or is_trainer):
            raise PermissionError("🚫 Solo entrenadores o administradores pueden borrar rutinas.")

        conn = get_connection()
        cur = conn.cursor()

        if is_trainer:
            cur.execute("""
                SELECT tp.trainer_id
                FROM routine r
                JOIN training_plan tp ON tp.id = r.plan_id
                WHERE r.id = ?
            """, (routine_id,))
            row = cur.fetchone()
            if not row:
                conn.close()
                raise ValueError("⚠️ Rutina no encontrada.")
            if row["trainer_id"] != current_user_id:
                conn.close()
                raise PermissionError("🚫 No podés eliminar rutinas que no son tuyas.")

        cur.execute("DELETE FROM routine WHERE id = ?", (routine_id,))
        conn.commit()
        conn.close()
        print(f"🗑️ Rutina ID {routine_id} eliminada correctamente.")
