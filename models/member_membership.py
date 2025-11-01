from db.connection import get_connection

class MemberMembership:
    """
    Modelo para la tabla 'member_membership'.
    - El socio puede elegir su propia membresía.
    - El admin puede asignar o actualizar membresías de cualquier usuario.
    - Un usuario solo puede tener UNA membresía activa o pausada a la vez.
    """

    # ---------- CREATE ----------
    @staticmethod
    def create(user_id: int, membership_id: int, start_date=None, end_date=None, status: str = "ACTIVE",
               current_user_id=None, current_user_roles=None):
        """
        Registra una nueva membresía contratada por un socio.
        - Si es ADMIN: puede asignar a cualquier usuario.
        - Si es MEMBER: solo puede asignarse a sí mismo.
        - Un usuario no puede tener más de una membresía activa/pausada.
        """
        roles = [r.upper() for r in (current_user_roles or [])]
        is_admin = "ADMIN" in roles
        is_self = current_user_id == user_id

        if not (is_admin or is_self):
            raise PermissionError("🚫 No tenés permiso para asignar membresías a otros usuarios.")

        status = status.upper()
        if status not in ("ACTIVE", "EXPIRED", "PAUSED"):
            raise ValueError("⚠️ Estado inválido. Use 'ACTIVE', 'EXPIRED' o 'PAUSED'.")

        conn = get_connection()
        cur = conn.cursor()

        # 🔒 Validar si ya tiene una membresía activa o pausada
        cur.execute("""
            SELECT id, status FROM member_membership
            WHERE user_id = ? AND status IN ('ACTIVE', 'PAUSED')
            LIMIT 1
        """, (user_id,))
        existing = cur.fetchone()

        if existing:
            conn.close()
            raise ValueError(f"⚠️ El usuario ID {user_id} ya tiene una membresía '{existing['status']}' activa. "
                             f"No puede tener más de una simultáneamente.")

        # Crear nueva membresía
        cur.execute("""
            INSERT INTO member_membership (user_id, membership_id, start_date, end_date, status)
            VALUES (?, ?, COALESCE(?, CURRENT_TIMESTAMP), ?, ?)
        """, (user_id, membership_id, start_date, end_date, status))
        conn.commit()
        conn.close()

        print(f"✅ Se asignó la membresía ID {membership_id} al usuario ID {user_id} ({status}).")

    # ---------- READ ----------
    @staticmethod
    def find_active_by_user(user_id: int):
        """Devuelve la membresía activa del usuario (si tiene una)."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT mm.*, m.name AS membership_name, m.price
            FROM member_membership mm
            JOIN membership m ON m.id = mm.membership_id
            WHERE mm.user_id = ? AND mm.status = 'ACTIVE'
            ORDER BY mm.start_date DESC
            LIMIT 1
        """, (user_id,))
        row = cur.fetchone()
        conn.close()
        return row

    # ---------- UPDATE ----------
    @staticmethod
    def update_status(member_membership_id: int, new_status: str, current_user_roles=None):
        """Actualiza el estado de una membresía (solo ADMIN)."""
        if not current_user_roles or "ADMIN" not in [r.upper() for r in current_user_roles]:
            raise PermissionError("🚫 Solo un usuario con rol ADMIN puede cambiar el estado de una membresía.")

        new_status = new_status.upper().strip()
        if new_status not in ("ACTIVE", "EXPIRED", "PAUSED"):
            raise ValueError("⚠️ Estado inválido. Use 'ACTIVE', 'EXPIRED' o 'PAUSED'.")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE member_membership
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_status, member_membership_id))
        conn.commit()
        conn.close()
        print(f"🔄 Estado de la membresía ID {member_membership_id} actualizado a '{new_status}'.")

    # ---------- AUTO-EXPIRE ----------
    @staticmethod
    def expire_expired_memberships():
        """Marca como EXPIRED las membresías cuya fecha de fin ya pasó."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE member_membership
            SET status = 'EXPIRED', updated_at = CURRENT_TIMESTAMP
            WHERE end_date IS NOT NULL
              AND end_date < CURRENT_TIMESTAMP
              AND status = 'ACTIVE'
        """)
        conn.commit()
        conn.close()
        print("⏳ Se actualizaron las membresías vencidas.")
