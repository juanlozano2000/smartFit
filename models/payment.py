# models/payment.py
from db.connection import get_connection

class Payment:
    """
    Modelo para la tabla 'payment'.
    - Solo ADMIN puede crear pagos o cambiar su estado.
    - Métodos de consulta (listar/buscar/sumar) son libres.
    """

    _METHODS = {"CASH", "CARD", "TRANSFER", "OTHER"}
    _PURPOSES = {"SIGNUP", "RENEWAL", "DEBT", "OTHER"}
    _STATUSES = {"APPROVED", "PENDING", "REJECTED"}

    # ---------- CREATE ----------
    @staticmethod
    def create(member_membership_id: int,
               amount: float,
               method: str,
               purpose: str,
               paid_at: str | None = None,
               period_start: str | None = None,
               period_end: str | None = None,
               status: str = "APPROVED",
               current_user_roles=None):
        """Crea un pago (solo ADMIN). Fechas en formato ISO 'YYYY-MM-DD' o DATETIME válido para SQLite."""
        roles = [r.upper() for r in (current_user_roles or [])]
        if "ADMIN" not in roles:
            raise PermissionError("Error: Solo un usuario con rol ADMIN puede registrar pagos.")

        method = method.upper().strip()
        purpose = purpose.upper().strip()
        status = status.upper().strip()

        if amount < 0:
            raise ValueError("⚠️ El monto no puede ser negativo.")
        if method not in Payment._METHODS:
            raise ValueError(f"⚠️ Método inválido. Use uno de: {', '.join(Payment._METHODS)}")
        if purpose not in Payment._PURPOSES:
            raise ValueError(f"⚠️ Propósito inválido. Use uno de: {', '.join(Payment._PURPOSES)}")
        if status not in Payment._STATUSES:
            raise ValueError(f"⚠️ Estado inválido. Use uno de: {', '.join(Payment._STATUSES)}")

        # Validación simple de periodo (si se proveen ambos)
        if period_start and period_end and period_end < period_start:
            raise ValueError("⚠️ period_end no puede ser anterior a period_start.")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO payment (
                member_membership_id, paid_at, amount, method, purpose, status, period_start, period_end
            ) VALUES (
                ?, COALESCE(?, CURRENT_TIMESTAMP), ?, ?, ?, ?, ?, ?
            )
        """, (member_membership_id, paid_at, amount, method, purpose, status, period_start, period_end))
        conn.commit()
        conn.close()
        print("✅ Pago registrado correctamente.")

    @staticmethod
    def create_for_user(user_id: int,
                        amount: float,
                        method: str,
                        purpose: str,
                        paid_at: str | None = None,
                        period_start: str | None = None,
                        period_end: str | None = None,
                        status: str = "APPROVED",
                        current_user_roles=None):
        """
        Crea un pago buscando la member_membership ACTIVA del usuario (solo ADMIN).
        Útil cuando no conocés el ID de la relación.
        """
        roles = [r.upper() for r in (current_user_roles or [])]
        if "ADMIN" not in roles:
            raise PermissionError("🚫 Solo un usuario con rol ADMIN puede registrar pagos.")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id FROM member_membership
            WHERE user_id = ? AND status = 'ACTIVE'
            ORDER BY start_date DESC
            LIMIT 1
        """, (user_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            raise ValueError(f"⚠️ El usuario {user_id} no tiene una membresía ACTIVA.")

        return Payment.create(
            member_membership_id=row["id"],
            amount=amount,
            method=method,
            purpose=purpose,
            paid_at=paid_at,
            period_start=period_start,
            period_end=period_end,
            status=status,
            current_user_roles=roles
        )

    # ---------- READ ----------
    @staticmethod
    def find_by_id(payment_id: int):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM payment WHERE id = ?", (payment_id,))
        row = cur.fetchone()
        conn.close()
        return row

    @staticmethod
    def list_by_membership(member_membership_id: int):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM payment
            WHERE member_membership_id = ?
            ORDER BY paid_at DESC, id DESC
        """, (member_membership_id,))
        rows = cur.fetchall()
        conn.close()
        return rows

    @staticmethod
    def list_by_user(user_id: int):
        """Lista pagos del usuario (join a member_membership)."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.*
            FROM payment p
            JOIN member_membership mm ON mm.id = p.member_membership_id
            WHERE mm.user_id = ?
            ORDER BY p.paid_at DESC, p.id DESC
        """, (user_id,))
        rows = cur.fetchall()
        conn.close()
        return rows

    @staticmethod
    def list_filtered(status: str | None = None,
                      date_from: str | None = None,
                      date_to: str | None = None):
        """
        Lista pagos con filtros opcionales:
        - status: APPROVED/PENDING/REJECTED
        - date_from / date_to: filtra por 'paid_at' (inclusive) en formato 'YYYY-MM-DD' o DATETIME válido.
        """
        clauses, values = [], []
        if status:
            status = status.upper().strip()
            if status not in Payment._STATUSES:
                raise ValueError(f"⚠️ Estado inválido. Use uno de: {', '.join(Payment._STATUSES)}")
            clauses.append("p.status = ?")
            values.append(status)
        if date_from:
            clauses.append("p.paid_at >= ?")
            values.append(date_from)
        if date_to:
            clauses.append("p.paid_at <= ?")
            values.append(date_to)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"""
            SELECT p.*, mm.user_id
            FROM payment p
            JOIN member_membership mm ON mm.id = p.member_membership_id
            {where}
            ORDER BY p.paid_at DESC, p.id DESC
        """

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(sql, tuple(values))
        rows = cur.fetchall()
        conn.close()
        return rows

    # ---------- UPDATE STATUS (ADMIN) ----------
    @staticmethod
    def update_status(payment_id: int, new_status: str, current_user_roles=None):
        roles = [r.upper() for r in (current_user_roles or [])]
        if "ADMIN" not in roles:
            raise PermissionError("🚫 Solo un usuario con rol ADMIN puede cambiar el estado de un pago.")

        new_status = new_status.upper().strip()
        if new_status not in Payment._STATUSES:
            raise ValueError(f"⚠️ Estado inválido. Use uno de: {', '.join(Payment._STATUSES)}")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE payment
            SET status = ?, created_at = created_at  -- mantiene created_at; no hay updated_at en la tabla
            WHERE id = ?
        """, (new_status, payment_id))
        conn.commit()
        conn.close()
        print(f"🔄 Estado del pago {payment_id} actualizado a '{new_status}'.")

    # ---------- REPORT HELPERS ----------
    @staticmethod
    def total_paid_by_user(user_id: int, status: str = "APPROVED"):
        """Suma montos por usuario (por defecto, solo pagos APPROVED)."""
        status = status.upper().strip()
        if status not in Payment._STATUSES:
            raise ValueError(f"⚠️ Estado inválido. Use uno de: {', '.join(Payment._STATUSES)}")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT COALESCE(SUM(p.amount), 0) AS total
            FROM payment p
            JOIN member_membership mm ON mm.id = p.member_membership_id
            WHERE mm.user_id = ? AND p.status = ?
        """, (user_id, status))
        row = cur.fetchone()
        conn.close()
        return row["total"] if row else 0.0

    @staticmethod
    def total_paid_in_period(date_from: str, date_to: str, status: str = "APPROVED"):
        """Suma montos en un rango de fechas (por paid_at)."""
        status = status.upper().strip()
        if status not in Payment._STATUSES:
            raise ValueError(f"⚠️ Estado inválido. Use uno de: {', '.join(Payment._STATUSES)}")

        if date_to < date_from:
            raise ValueError("⚠️ date_to no puede ser anterior a date_from.")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM payment
            WHERE status = ?
              AND paid_at >= ?
              AND paid_at <= ?
        """, (status, date_from, date_to))
        row = cur.fetchone()
        conn.close()
        return row["total"] if row else 0.0
