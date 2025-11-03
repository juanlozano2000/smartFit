# services/membership_service.py
from models.Membership import Membership
from models.Member_membership import MemberMembership
from db.connection import get_connection
import datetime

class MembershipService:
    """
    Servicio de gestión de membresías.
    Maneja:
      - Alta y baja de tipos de membresía (ADMIN)
      - Asignación/compra de membresía por miembros
      - Listado y renovación
    """

    # ---------- ADMIN: CREAR / EDITAR / DESACTIVAR PLANES ----------
    @staticmethod
    def admin_create_membership(gym_id: int, name: str, duration_months: int, price: float,
                                current_user_roles=None):
        roles = [r.upper() for r in (current_user_roles or [])]
        if "ADMIN" not in roles:
            raise PermissionError("🚫 Solo el administrador puede crear membresías.")

        Membership.create(gym_id=gym_id, name=name, duration_months=duration_months, price=price)

    @staticmethod
    def admin_update_membership(membership_id: int, name=None, duration_months=None,
                                price=None, status=None, current_user_roles=None):
        roles = [r.upper() for r in (current_user_roles or [])]
        if "ADMIN" not in roles:
            raise PermissionError("🚫 Solo el administrador puede modificar membresías.")

        Membership.update(membership_id, name, duration_months, price, status)

    @staticmethod
    def admin_deactivate_membership(membership_id: int, current_user_roles=None):
        roles = [r.upper() for r in (current_user_roles or [])]
        if "ADMIN" not in roles:
            raise PermissionError("🚫 Solo el administrador puede desactivar membresías.")

        Membership.deactivate(membership_id)

    # ---------- MEMBER: ELEGIR MEMBRESÍA ----------
    @staticmethod
    def choose_membership(user_id: int, membership_id: int, current_user_roles=None):
        """
        Un miembro elige/comprar una membresía.
        - Si ya tiene una activa → la finaliza
        - Calcula fecha de fin en base a duración.
        """
        roles = [r.upper() for r in (current_user_roles or [])]
        if "MEMBER" not in roles and "ADMIN" not in roles:
            raise PermissionError("🚫 Solo miembros o administradores pueden asignar membresías.")

        conn = get_connection()
        cur = conn.cursor()

        # Obtener duración del plan nuevo
        cur.execute("SELECT duration_months FROM membership WHERE id = ? AND status = 'ACTIVE'", (membership_id,))
        plan = cur.fetchone()
        if not plan:
            conn.close()
            raise ValueError("⚠️ La membresía no existe o está inactiva.")

        # Si tiene una membresía activa, finalizarla
        cur.execute("""
            UPDATE member_membership 
            SET status = 'EXPIRED', end_date = CURRENT_TIMESTAMP 
            WHERE user_id = ? AND status = 'ACTIVE'
        """, (user_id,))

        # Crear nueva membresía
        start_date = datetime.datetime.now()
        end_date = start_date + datetime.timedelta(days=30 * plan["duration_months"])

        cur.execute("""
            INSERT INTO member_membership (user_id, membership_id, start_date, end_date, status)
            VALUES (?, ?, ?, ?, 'ACTIVE')
        """, (user_id, membership_id, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))

        conn.commit()
        conn.close()

        print(f"✅ Membresía cambiada exitosamente. Activa hasta {end_date.strftime('%Y-%m-%d')}.")

    # ---------- MEMBER / ADMIN: VER MEMBRESÍAS ----------
    @staticmethod
    def list_active_memberships():
        """Devuelve todas las membresías activas disponibles para los usuarios."""
        return Membership.all(include_inactive=False)

    @staticmethod
    def list_all_memberships(current_user_roles=None):
        """Devuelve todas las membresías (solo ADMIN)."""
        roles = [r.upper() for r in (current_user_roles or [])]
        if "ADMIN" not in roles:
            raise PermissionError("🚫 Solo el administrador puede listar todas las membresías.")

        return Membership.all(include_inactive=True)

    # ---------- VER MEMBRESÍA DE UN USUARIO ----------
    @staticmethod
    def get_user_membership(user_id: int):
        """Devuelve la membresía activa de un usuario."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT mm.id, m.name, m.duration_months, m.price, mm.start_date, mm.end_date, mm.status
            FROM member_membership mm
            JOIN membership m ON m.id = mm.membership_id
            WHERE mm.user_id = ? AND mm.status = 'ACTIVE'
        """, (user_id,))
        membership = cur.fetchone()
        conn.close()
        return membership

    # ---------- ADMIN: RENOVAR / FINALIZAR ----------
    @staticmethod
    def admin_renew_membership(user_id: int, current_user_roles=None):
        """Renueva la membresía de un usuario activo."""
        roles = [r.upper() for r in (current_user_roles or [])]
        if "ADMIN" not in roles:
            raise PermissionError("🚫 Solo el administrador puede renovar membresías.")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT mm.id, m.duration_months, mm.end_date
            FROM member_membership mm
            JOIN membership m ON m.id = mm.membership_id
            WHERE mm.user_id = ? AND mm.status = 'ACTIVE'
        """, (user_id,))
        mm = cur.fetchone()
        if not mm:
            conn.close()
            raise ValueError("⚠️ El usuario no tiene una membresía activa.")

        old_end = datetime.datetime.strptime(mm["end_date"], "%Y-%m-%d")
        new_end = old_end + datetime.timedelta(days=30 * mm["duration_months"])

        cur.execute("""
            UPDATE member_membership
            SET end_date = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_end.strftime("%Y-%m-%d"), mm["id"]))
        conn.commit()
        conn.close()

        print(f"♻️ Membresía del usuario {user_id} renovada hasta {new_end.strftime('%Y-%m-%d')}.")

    @staticmethod
    def admin_end_membership(user_id: int, current_user_roles=None):
        """Finaliza la membresía activa de un usuario."""
        roles = [r.upper() for r in (current_user_roles or [])]
        if "ADMIN" not in roles:
            raise PermissionError("🚫 Solo el administrador puede finalizar membresías.")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE member_membership
            SET status = 'EXPIRED', end_date = CURRENT_TIMESTAMP
            WHERE user_id = ? AND status = 'ACTIVE'
        """, (user_id,))
        conn.commit()
        conn.close()

        print(f"🟡 Membresía del usuario {user_id} marcada como EXPIRED.")
