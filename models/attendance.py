from db.connection import get_connection

class Attendance:
    """
    Modelo para la tabla 'attendance'.
    - TRAINER: puede registrar asistencia de sus clases.
    - ADMIN: puede marcar o modificar asistencias de cualquier clase.
    - MEMBER: solo puede consultar su propio historial (no modificar).
    """

    # ---------- CREATE / REGISTER ----------
    @staticmethod
    def mark_attendance(booking_id: int, present: bool,
                        current_user_id=None, current_user_roles=None):
        """
        Marca la asistencia de una reserva BOOKED.
        - Solo TRAINER dueño de la clase o ADMIN pueden marcar.
        - No se puede registrar asistencia de reservas CANCELLED o WAITLIST.
        - Si ya existe, se actualiza (re-marcación).
        """
        roles = [r.upper() for r in (current_user_roles or [])]
        is_admin = "ADMIN" in roles
        is_trainer = "TRAINER" in roles

        if not (is_admin or is_trainer):
            raise PermissionError("🚫 Solo entrenadores o administradores pueden registrar asistencia.")

        conn = get_connection()
        cur = conn.cursor()

        # Verificar reserva y su clase
        cur.execute("""
            SELECT b.id, b.member_id, b.status, c.trainer_id
            FROM booking b
            JOIN class c ON c.id = b.class_id
            WHERE b.id = ?
        """, (booking_id,))
        booking = cur.fetchone()
        if not booking:
            conn.close()
            raise ValueError("⚠️ La reserva no existe.")

        if booking["status"] != "BOOKED":
            conn.close()
            raise ValueError("⚠️ Solo se puede marcar asistencia de reservas BOOKED.")

        if is_trainer and booking["trainer_id"] != current_user_id:
            conn.close()
            raise PermissionError("🚫 No podés marcar asistencia en clases ajenas.")

        # Verificar si ya existe registro
        cur.execute("SELECT id FROM attendance WHERE booking_id = ?", (booking_id,))
        existing = cur.fetchone()

        if existing:
            cur.execute("""
                UPDATE attendance
                SET present = ?, checked_at = CURRENT_TIMESTAMP
                WHERE booking_id = ?
            """, (int(present), booking_id))
            print("🟡 Asistencia actualizada.")
        else:
            cur.execute("""
                INSERT INTO attendance (booking_id, present)
                VALUES (?, ?)
            """, (booking_id, int(present)))
            print("✅ Asistencia registrada.")

        conn.commit()
        conn.close()

    # ---------- READ ----------
    @staticmethod
    def list_by_class(class_id: int, current_user_id=None, current_user_roles=None):
        """
        Lista asistencias de una clase.
        - ADMIN: todas
        - TRAINER: solo sus clases
        - MEMBER: no autorizado
        """
        roles = [r.upper() for r in (current_user_roles or [])]
        is_admin = "ADMIN" in roles
        is_trainer = "TRAINER" in roles

        if not (is_admin or is_trainer):
            raise PermissionError("🚫 Solo entrenadores o administradores pueden ver asistencias por clase.")

        conn = get_connection()
        cur = conn.cursor()

        if is_trainer:
            cur.execute("""
                SELECT a.id, u.full_name AS member_name, a.present, a.checked_at
                FROM attendance a
                JOIN booking b ON b.id = a.booking_id
                JOIN user u ON u.id = b.member_id
                JOIN class c ON c.id = b.class_id
                WHERE c.id = ? AND c.trainer_id = ?
                ORDER BY a.checked_at DESC
            """, (class_id, current_user_id))
        else:
            cur.execute("""
                SELECT a.id, u.full_name AS member_name, a.present, a.checked_at
                FROM attendance a
                JOIN booking b ON b.id = a.booking_id
                JOIN user u ON u.id = b.member_id
                JOIN class c ON c.id = b.class_id
                WHERE c.id = ?
                ORDER BY a.checked_at DESC
            """, (class_id,))
        rows = cur.fetchall()
        conn.close()
        return rows

    @staticmethod
    def list_by_member(member_id: int, current_user_id=None, current_user_roles=None):
        """
        Lista asistencias de un usuario (para ver historial).
        - ADMIN: cualquiera
        - MEMBER: solo las propias
        """
        roles = [r.upper() for r in (current_user_roles or [])]
        is_admin = "ADMIN" in roles
        is_member = "MEMBER" in roles

        if not (is_admin or (is_member and member_id == current_user_id)):
            raise PermissionError("🚫 No podés ver asistencias de otro usuario.")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT c.name AS class_name, c.start_at, a.present, a.checked_at
            FROM attendance a
            JOIN booking b ON b.id = a.booking_id
            JOIN class c ON c.id = b.class_id
            WHERE b.member_id = ?
            ORDER BY c.start_at DESC
        """, (member_id,))
        rows = cur.fetchall()
        conn.close()
        return rows

    # ---------- DELETE ----------
    @staticmethod
    def delete(booking_id: int, current_user_id=None, current_user_roles=None):
        """
        Permite borrar un registro de asistencia (solo ADMIN).
        """
        roles = [r.upper() for r in (current_user_roles or [])]
        if "ADMIN" not in roles:
            raise PermissionError("🚫 Solo administradores pueden eliminar registros de asistencia.")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM attendance WHERE booking_id = ?", (booking_id,))
        conn.commit()
        conn.close()
        print(f"🗑️ Asistencia eliminada para booking_id {booking_id}.")
