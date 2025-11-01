# services/class_service.py
from models.Class_session import ClassSession
from models.Booking import Booking
from models.Attendance import Attendance
from db.connection import get_connection
import datetime

class ClassService:
    """
    Servicio para manejo de clases, reservas y asistencias.
    Permite:
      - Crear y listar clases (ADMIN / TRAINER)
      - Reservar y cancelar (MEMBER)
      - Registrar asistencias (TRAINER / ADMIN)
    """

    # ---------- CLASES ----------
    @staticmethod
    def create_class(gym_id: int, trainer_id: int, name: str,
                     start_at: str, end_at: str, capacity: int,
                     room: str | None = None, current_user_roles=None):
        """Crear una clase (solo ADMIN o TRAINER)."""
        roles = [r.upper() for r in (current_user_roles or [])]
        if not any(r in roles for r in ("ADMIN", "TRAINER")):
            raise PermissionError("🚫 Solo administradores o entrenadores pueden crear clases.")

        if not name.strip():
            raise ValueError("⚠️ El nombre de la clase no puede estar vacío.")
        if capacity <= 0:
            raise ValueError("⚠️ La capacidad debe ser mayor que 0.")

        ClassSession.create(gym_id, trainer_id, name, start_at, end_at, capacity, room)
        print(f"✅ Clase '{name}' creada correctamente para el {start_at}.")

    @staticmethod
    def list_classes_for_user(gym_id: int, role: str):
        """Lista clases disponibles según el rol."""
        conn = get_connection()
        cur = conn.cursor()
        if role.upper() == "MEMBER":
            cur.execute("""
                SELECT c.id, c.name, c.start_at, c.end_at, c.capacity, u.full_name AS trainer_name
                FROM class c
                JOIN user u ON u.id = c.trainer_id
                WHERE c.gym_id = ?
                ORDER BY c.start_at ASC
            """, (gym_id,))
        else:
            cur.execute("""
                SELECT c.id, c.name, c.start_at, c.end_at, c.capacity, c.room
                FROM class c
                WHERE c.gym_id = ?
                ORDER BY c.start_at ASC
            """, (gym_id,))
        rows = cur.fetchall()
        conn.close()
        return rows

    # ---------- BOOKING (RESERVAS) ----------
    @staticmethod
    def book_class(class_id: int, member_id: int, current_user_roles=None):
        """Reservar clase (solo MEMBER)."""
        roles = [r.upper() for r in (current_user_roles or [])]
        if "MEMBER" not in roles:
            raise PermissionError("🚫 Solo los miembros pueden reservar clases.")

        conn = get_connection()
        cur = conn.cursor()

        # Verificar capacidad disponible
        cur.execute("SELECT capacity FROM class WHERE id = ?", (class_id,))
        cls = cur.fetchone()
        if not cls:
            conn.close()
            raise ValueError("⚠️ La clase no existe.")

        cur.execute("""
            SELECT COUNT(*) AS total FROM booking
            WHERE class_id = ? AND status = 'BOOKED'
        """, (class_id,))
        booked = cur.fetchone()["total"]

        if booked >= cls["capacity"]:
            status = "WAITLIST"
        else:
            status = "BOOKED"

        cur.execute("""
            INSERT INTO booking (class_id, member_id, booked_at, status)
            VALUES (?, ?, ?, ?)
        """, (class_id, member_id, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), status))
        conn.commit()
        conn.close()

        print(f"✅ Reserva registrada (estado: {status}).")

    @staticmethod
    def cancel_booking(booking_id: int, member_id: int, current_user_roles=None):
        """Cancelar una reserva (solo MEMBER)."""
        roles = [r.upper() for r in (current_user_roles or [])]
        if "MEMBER" not in roles:
            raise PermissionError("🚫 Solo los miembros pueden cancelar reservas.")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE booking
            SET status = 'CANCELLED'
            WHERE id = ? AND member_id = ? AND status = 'BOOKED'
        """, (booking_id, member_id))
        if cur.rowcount == 0:
            print("⚠️ No se encontró una reserva activa para cancelar.")
        else:
            print("🟡 Reserva cancelada correctamente.")
        conn.commit()
        conn.close()

    # ---------- ATTENDANCE ----------
    @staticmethod
    def mark_attendance(booking_id: int, present: bool,
                        current_user_roles=None):
        """Marcar asistencia (solo TRAINER o ADMIN)."""
        roles = [r.upper() for r in (current_user_roles or [])]
        if not any(r in roles for r in ("TRAINER", "ADMIN")):
            raise PermissionError("🚫 Solo entrenadores o administradores pueden registrar asistencias.")

        Attendance.create(booking_id, int(present))
        print("🟢 Asistencia registrada.")

    @staticmethod
    def list_attendance_by_class(class_id: int):
        """Lista asistencia por clase."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT a.id, u.full_name AS member_name, a.present, a.checked_at
            FROM attendance a
            JOIN booking b ON b.id = a.booking_id
            JOIN user u ON u.id = b.member_id
            WHERE b.class_id = ?
        """, (class_id,))
        rows = cur.fetchall()
        conn.close()
        return rows
