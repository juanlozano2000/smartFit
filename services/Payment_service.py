# services/payment_service.py
from models.Payment import Payment
from db.connection import get_connection
import datetime

class PaymentService:
    """
    Servicio de pagos de membresías.
    - Solo ADMIN puede registrar pagos manuales.
    - Los pagos se asocian a una relación miembro↔membresía activa.
    """

    # ---------- CREAR PAGO ----------
    @staticmethod
    def create_payment(member_membership_id: int, amount: float,
                       method: str, purpose: str = "SIGNUP",
                       status: str = "APPROVED",
                       current_user_roles=None):
        """
        Crea un pago.
        - ADMIN puede crear cualquier pago
        - MEMBER solo puede crear pagos para su propia membresía activa
        """
        roles = [r.upper() for r in (current_user_roles or [])]
        if "ADMIN" not in roles and "MEMBER" not in roles:
            raise PermissionError("🚫 Solo administradores o miembros pueden registrar pagos.")
        
        # Si es MEMBER, validar que el pago sea para su propia membresía
        if "ADMIN" not in roles:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT user_id FROM member_membership 
                WHERE id = ? AND status = 'ACTIVE'
            """, (member_membership_id,))
            mm = cur.fetchone()
            conn.close()
            
            if not mm:
                raise ValueError("❌ La membresía no existe o no está activa.")

        allowed_methods = {"CASH", "CARD", "TRANSFER", "OTHER"}
        allowed_purposes = {"SIGNUP", "RENEWAL", "DEBT", "OTHER"}
        allowed_statuses = {"APPROVED", "PENDING", "REJECTED"}

        if method.upper() not in allowed_methods:
            raise ValueError(f"⚠️ Método inválido. Opciones: {', '.join(allowed_methods)}")
        if purpose.upper() not in allowed_purposes:
            raise ValueError(f"⚠️ Motivo inválido. Opciones: {', '.join(allowed_purposes)}")
        if status.upper() not in allowed_statuses:
            raise ValueError(f"⚠️ Estado inválido. Opciones: {', '.join(allowed_statuses)}")

        conn = get_connection()
        cur = conn.cursor()

        # Validar que la membresía exista
        cur.execute("""
            SELECT id, start_date, end_date FROM member_membership
            WHERE id = ? AND status = 'ACTIVE'
        """, (member_membership_id,))
        mm = cur.fetchone()
        if not mm:
            conn.close()
            raise ValueError("⚠️ La membresía no existe o no está activa.")

        cur.execute("""
            INSERT INTO payment (
                member_membership_id, paid_at, amount, method,
                purpose, status, period_start, period_end
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            member_membership_id,
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            round(amount, 2),
            method.upper(),
            purpose.upper(),
            status.upper(),
            mm["start_date"],
            mm["end_date"]
        ))
        conn.commit()
        conn.close()
        print(f"💰 Pago registrado correctamente (membresía #{member_membership_id}, monto ${amount:.2f}).")

    # ---------- LISTAR PAGOS ----------
    @staticmethod
    def list_all_payments(current_user_roles=None):
        """Devuelve todos los pagos (solo ADMIN)."""
        roles = [r.upper() for r in (current_user_roles or [])]
        if "ADMIN" not in roles:
            raise PermissionError("🚫 Solo el administrador puede ver todos los pagos.")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.id, u.full_name AS member_name, p.amount, p.method,
                   p.purpose, p.status, p.paid_at
            FROM payment p
            JOIN member_membership mm ON mm.id = p.member_membership_id
            JOIN user u ON u.id = mm.user_id
            ORDER BY p.paid_at DESC
        """)
        rows = cur.fetchall()
        conn.close()
        return rows

    @staticmethod
    def list_user_payments(user_id: int):
        """Devuelve los pagos de un usuario específico."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.id, p.amount, p.method, p.purpose, p.status, p.paid_at
            FROM payment p
            JOIN member_membership mm ON mm.id = p.member_membership_id
            WHERE mm.user_id = ?
            ORDER BY p.paid_at DESC
        """, (user_id,))
        rows = cur.fetchall()
        conn.close()
        return rows

    # ---------- FILTROS Y CONSULTAS ----------
    @staticmethod
    def list_pending_payments():
        """Lista los pagos con estado PENDING (por aprobar)."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.id, u.full_name, p.amount, p.method, p.purpose, p.paid_at
            FROM payment p
            JOIN member_membership mm ON mm.id = p.member_membership_id
            JOIN user u ON u.id = mm.user_id
            WHERE p.status = 'PENDING'
        """)
        rows = cur.fetchall()
        conn.close()
        return rows

    @staticmethod
    def update_status(payment_id: int, new_status: str, current_user_roles=None):
        """Cambia el estado de un pago (solo ADMIN)."""
        roles = [r.upper() for r in (current_user_roles or [])]
        if "ADMIN" not in roles:
            raise PermissionError("🚫 Solo el administrador puede modificar pagos.")

        if new_status.upper() not in {"APPROVED", "PENDING", "REJECTED"}:
            raise ValueError("⚠️ Estado inválido (APPROVED / PENDING / REJECTED).")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE payment
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_status.upper(), payment_id))
        conn.commit()
        conn.close()
        print(f"🟢 Pago ID {payment_id} actualizado a estado {new_status.upper()}.")
