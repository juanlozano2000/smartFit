# models/booking.py
from db.connection import get_connection

class Booking:
    """
    Maneja reservas de clases (tabla 'booking').
    - MEMBER: puede reservar/cancelar solo para sí mismo.
    - TRAINER: puede ver reservas de sus clases y cancelar reservas de su propia clase.
    - ADMIN: puede reservar/cancelar para cualquiera.
    Reglas:
      * Sin reservas duplicadas (BOOKED/WAITLIST) para la misma clase y miembro.
      * Si la clase está llena -> WAITLIST.
      * Al cancelar una reserva BOOKED: se promueve el primer WAITLIST (FIFO).
    """

    _STATUSES = {"BOOKED", "CANCELLED", "WAITLIST"}

    # ---------- HELPERS PRIVADOS ----------
    @staticmethod
    def _class_info(class_id: int):
        """Devuelve info de la clase + booked_count."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT c.*, 
                   (SELECT COUNT(*) FROM booking b WHERE b.class_id = c.id AND b.status = 'BOOKED') AS booked_count
            FROM class c
            WHERE c.id = ?
        """, (class_id,))
        row = cur.fetchone()
        conn.close()
        return row

    @staticmethod
    def _has_active_booking(class_id: int, member_id: int):
        """True si ya existe BOOKED o WAITLIST para ese member en esa clase."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 1
            FROM booking
            WHERE class_id = ? AND member_id = ? AND status IN ('BOOKED','WAITLIST')
            LIMIT 1
        """, (class_id, member_id))
        exists = cur.fetchone() is not None
        conn.close()
        return exists

    @staticmethod
    def _is_trainer_of_class(class_id: int, trainer_id: int):
        """True si el trainer_id es el entrenador de la clase class_id."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM class WHERE id = ? AND trainer_id = ?", (class_id, trainer_id))
        ok = cur.fetchone() is not None
        conn.close()
        return ok

    @staticmethod
    def _promote_waitlist(class_id: int):
        """Promueve el WAITLIST más antiguo a BOOKED (si hay lugar)."""
        info = Booking._class_info(class_id)
        if not info:
            return
        if info["booked_count"] >= info["capacity"]:
            return  # aún no hay lugar

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id FROM booking
            WHERE class_id = ? AND status = 'WAITLIST'
            ORDER BY booked_at ASC, id ASC
            LIMIT 1
        """, (class_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return

        cur.execute("""
            UPDATE booking
            SET status = 'BOOKED'
            WHERE id = ?
        """, (row["id"],))
        conn.commit()
        conn.close()

    # ---------- CREATE ----------
    @staticmethod
    def create(class_id: int, member_id: int,
               current_user_id=None, current_user_roles=None):
        """
        Crea una reserva.
        Permisos:
          - ADMIN: puede reservar para cualquiera.
          - MEMBER: solo puede reservar para sí mismo.
          - TRAINER: puede reservar para sus miembros (opcional) o se limita a admin/member (aquí lo restringimos a admin/self).
        Lógica:
          - Evita reservas duplicadas (BOOKED/WAITLIST).
          - Si cupo lleno -> WAITLIST, si hay lugar -> BOOKED.
          - No permite reservar clases ya iniciadas.
        """
        roles = [r.upper() for r in (current_user_roles or [])]
        is_admin = "ADMIN" in roles
        is_member = "MEMBER" in roles
        is_self = current_user_id == member_id

        if not (is_admin or (is_member and is_self)):
            raise PermissionError("🚫 No tenés permiso para reservar para otro usuario.")

        # Info de la clase
        info = Booking._class_info(class_id)
        if not info:
            raise ValueError("⚠️ La clase no existe.")

        # Validar que no haya empezado (SQLite: comparar texto funciona si formato es YYYY-MM-DD HH:MM:SS)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT CASE WHEN ? <= CURRENT_TIMESTAMP THEN 1 ELSE 0 END AS started", (info["start_at"],))
        started = cur.fetchone()["started"] == 1
        conn.close()
        if started:
            raise ValueError("⚠️ No se puede reservar una clase que ya empezó.")

        # Evitar duplicados
        if Booking._has_active_booking(class_id, member_id):
            raise ValueError("⚠️ Ya tenés una reserva o estás en lista de espera para esta clase.")

        # Decidir estado según cupo
        status = "BOOKED" if info["booked_count"] < info["capacity"] else "WAITLIST"

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO booking (class_id, member_id, status)
            VALUES (?, ?, ?)
        """, (class_id, member_id, status))
        conn.commit()
        conn.close()

        if status == "BOOKED":
            print("✅ Reserva confirmada (BOOKED).")
        else:
            print("🕒 Clase llena. Fuiste agregado a la lista de espera (WAITLIST).")

    # ---------- CANCEL ----------
    @staticmethod
    def cancel(booking_id: int, current_user_id=None, current_user_roles=None):
        """
        Cancela una reserva.
        Permisos:
          - ADMIN: puede cancelar cualquiera.
          - MEMBER: solo cancela reservas propias.
          - TRAINER: puede cancelar reservas de sus clases.
        Al cancelar una BOOKED, promueve el primer WAITLIST (si existe).
        """
        roles = [r.upper() for r in (current_user_roles or [])]
        is_admin = "ADMIN" in roles
        is_member = "MEMBER" in roles
        is_trainer = "TRAINER" in roles

        # Traer la reserva con info de clase/miembro
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT b.*, c.trainer_id
            FROM booking b
            JOIN class c ON c.id = b.class_id
            WHERE b.id = ?
        """, (booking_id,))
        bk = cur.fetchone()
        if not bk:
            conn.close()
            raise ValueError("⚠️ Reserva no encontrada.")

        # Permisos
        if is_admin:
            pass
        elif is_member and bk["member_id"] == current_user_id:
            pass
        elif is_trainer and bk["trainer_id"] == current_user_id:
            pass
        else:
            conn.close()
            raise PermissionError("🚫 No tenés permiso para cancelar esta reserva.")

        # Si ya está cancelada, salir
        if bk["status"] == "CANCELLED":
            conn.close()
            print("ℹ️ La reserva ya estaba cancelada.")
            return

        # Cancelar
        cur.execute("""
            UPDATE booking
            SET status = 'CANCELLED'
            WHERE id = ?
        """, (booking_id,))
        conn.commit()
        conn.close()

        # Promover waitlist si la que se canceló estaba BOOKED
        if bk["status"] == "BOOKED":
            Booking._promote_waitlist(bk["class_id"])

        print("🟡 Reserva cancelada correctamente.")

    # ---------- READ ----------
    @staticmethod
    def list_by_class(class_id: int, current_user_id=None, current_user_roles=None):
        """
        Lista reservas de una clase.
        - ADMIN: todas
        - TRAINER: solo si es su clase
        - MEMBER: permitido (para ver disponibilidad), pero no incluye datos sensibles del resto.
        """
        roles = [r.upper() for r in (current_user_roles or [])]
        is_admin = "ADMIN" in roles
        is_trainer = "TRAINER" in roles
        is_member = "MEMBER" in roles

        # Validar trainer propietario si aplica
        if is_trainer and not Booking._is_trainer_of_class(class_id, current_user_id):
            raise PermissionError("🚫 No podés ver reservas de clases que no dictás.")

        conn = get_connection()
        cur = conn.cursor()

        if is_admin or is_trainer:
            cur.execute("""
                SELECT b.id, b.member_id, u.full_name, b.status, b.booked_at
                FROM booking b
                JOIN user u ON u.id = b.member_id
                WHERE b.class_id = ?
                ORDER BY 
                    CASE b.status WHEN 'BOOKED' THEN 1 WHEN 'WAITLIST' THEN 2 ELSE 3 END,
                    b.booked_at ASC, b.id ASC
            """, (class_id,))
        elif is_member:
            # Para members: lista anónima (cuántos BOOKED/WAITLIST) + su propio estado
            cur.execute("""
                SELECT status, COUNT(*) as cnt
                FROM booking
                WHERE class_id = ?
                GROUP BY status
            """, (class_id,))
            summary = cur.fetchall()

            cur.execute("""
                SELECT status
                FROM booking
                WHERE class_id = ? AND member_id = ?
                ORDER BY booked_at DESC, id DESC
                LIMIT 1
            """, (class_id, current_user_id))
            mine = cur.fetchone()

            conn.close()
            return {
                "summary": {row["status"]: row["cnt"] for row in summary},
                "my_status": mine["status"] if mine else None
            }
        else:
            conn.close()
            raise PermissionError("🚫 Rol no autorizado.")

        rows = cur.fetchall()
        conn.close()
        return rows

    @staticmethod
    def list_by_user(member_id: int, current_user_id=None, current_user_roles=None):
        """
        Lista reservas de un usuario.
        - ADMIN: cualquiera
        - MEMBER: solo las propias
        - TRAINER: no aplica (a menos que agregues reglas extra)
        """
        roles = [r.upper() for r in (current_user_roles or [])]
        is_admin = "ADMIN" in roles
        is_member = "MEMBER" in roles

        if not (is_admin or (is_member and member_id == current_user_id)):
            raise PermissionError("🚫 No podés ver reservas de otro usuario.")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT b.id, b.class_id, c.name AS class_name, c.start_at, c.end_at, b.status, b.booked_at
            FROM booking b
            JOIN class c ON c.id = b.class_id
            WHERE b.member_id = ?
            ORDER BY c.start_at DESC, b.id DESC
        """, (member_id,))
        rows = cur.fetchall()
        conn.close()
        return rows

    # ---------- UTILIDADES ----------
    @staticmethod
    def seats_left(class_id: int):
        """Devuelve (capacidad, booked_count, libres)."""
        info = Booking._class_info(class_id)
        if not info:
            raise ValueError("⚠️ La clase no existe.")
        libres = int(info["capacity"]) - int(info["booked_count"])
        return int(info["capacity"]), int(info["booked_count"]), max(0, libres)
