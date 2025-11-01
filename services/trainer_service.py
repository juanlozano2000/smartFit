# services/training_service.py
from models.Training_plan import TrainingPlan
from models.Routine import Routine
from db.connection import get_connection
import datetime

class TrainingService:
    """
    Servicio para planes de entrenamiento y rutinas.
    Permite:
      - Crear planes (solo TRAINER)
      - Consultar planes (trainer o miembro)
      - Agregar / editar rutinas
      - Cerrar planes finalizados
    """

    # ---------- PLANES DE ENTRENAMIENTO ----------
    @staticmethod
    def create_plan(trainer_id: int, member_id: int, goal: str,
                    start_date=None, end_date=None, current_user_roles=None):
        """Crea un nuevo plan (solo TRAINER)."""
        roles = [r.upper() for r in (current_user_roles or [])]
        if "TRAINER" not in roles:
            raise PermissionError("🚫 Solo un entrenador puede crear planes.")

        if not goal.strip():
            raise ValueError("⚠️ El objetivo no puede estar vacío.")

        start = start_date or datetime.date.today()
        end = end_date or (start + datetime.timedelta(days=30))

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO training_plan (trainer_id, member_id, goal, start_date, end_date, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'ACTIVE', ?)
        """, (trainer_id, member_id, goal.strip(),
              start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"),
              datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()

        print(f"✅ Plan creado correctamente para el miembro {member_id} con objetivo '{goal}'.")

    @staticmethod
    def list_plans_by_trainer(trainer_id: int):
        """Devuelve todos los planes creados por un entrenador."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT tp.id, u.full_name AS member_name, tp.goal, tp.start_date, tp.end_date, tp.status
            FROM training_plan tp
            JOIN user u ON u.id = tp.member_id
            WHERE tp.trainer_id = ?
            ORDER BY tp.created_at DESC
        """, (trainer_id,))
        rows = cur.fetchall()
        conn.close()
        return rows

    @staticmethod
    def list_plans_by_member(member_id: int):
        """Devuelve los planes activos de un miembro."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT tp.id, u.full_name AS trainer_name, tp.goal, tp.start_date, tp.end_date, tp.status
            FROM training_plan tp
            JOIN user u ON u.id = tp.trainer_id
            WHERE tp.member_id = ?
            ORDER BY tp.created_at DESC
        """, (member_id,))
        rows = cur.fetchall()
        conn.close()
        return rows

    @staticmethod
    def close_plan(plan_id: int, current_user_roles=None):
        """Cierra un plan (solo TRAINER o ADMIN)."""
        roles = [r.upper() for r in (current_user_roles or [])]
        if "TRAINER" not in roles and "ADMIN" not in roles:
            raise PermissionError("🚫 Solo entrenadores o administradores pueden cerrar planes.")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE training_plan
            SET status = 'CLOSED', end_date = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (plan_id,))
        conn.commit()
        conn.close()
        print(f"🟡 Plan ID {plan_id} cerrado correctamente.")

    # ---------- RUTINAS ----------
    @staticmethod
    def add_routine(plan_id: int, name: str, weekday: int,
                    notes=None, current_user_roles=None):
        """Agrega una rutina a un plan (solo TRAINER)."""
        roles = [r.upper() for r in (current_user_roles or [])]
        if "TRAINER" not in roles:
            raise PermissionError("🚫 Solo un entrenador puede agregar rutinas.")

        if not (1 <= weekday <= 7):
            raise ValueError("⚠️ El día debe estar entre 1 (Lunes) y 7 (Domingo).")

        Routine.create(plan_id, name, weekday, notes)
        print(f"✅ Rutina '{name}' agregada al plan {plan_id} para el día {weekday}.")

    @staticmethod
    def list_routines_by_plan(plan_id: int):
        """Lista las rutinas de un plan."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, weekday, notes
            FROM routine
            WHERE plan_id = ?
            ORDER BY weekday ASC
        """, (plan_id,))
        rows = cur.fetchall()
        conn.close()
        return rows

    @staticmethod
    def update_routine(routine_id: int, name=None, weekday=None, notes=None,
                       current_user_roles=None):
        """Actualiza una rutina (solo TRAINER)."""
        roles = [r.upper() for r in (current_user_roles or [])]
        if "TRAINER" not in roles:
            raise PermissionError("🚫 Solo un entrenador puede modificar rutinas.")

        conn = get_connection()
        cur = conn.cursor()
        fields, values = [], []
        if name:
            fields.append("name = ?")
            values.append(name.strip())
        if weekday:
            if not (1 <= weekday <= 7):
                raise ValueError("⚠️ El día debe estar entre 1 y 7.")
            fields.append("weekday = ?")
            values.append(weekday)
        if notes is not None:
            fields.append("notes = ?")
            values.append(notes.strip() if notes else None)

        if not fields:
            print("⚠️ No se especificaron campos a actualizar.")
            conn.close()
            return

        values.append(routine_id)
        sql = f"UPDATE routine SET {', '.join(fields)} WHERE id = ?"
        cur.execute(sql, values)
        conn.commit()
        conn.close()

        print(f"🟢 Rutina ID {routine_id} actualizada correctamente.")
