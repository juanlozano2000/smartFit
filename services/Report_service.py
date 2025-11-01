# services/report_service.py
from db.connection import get_connection
import datetime
import json
import csv
import os

class ReportService:
    """
    Servicio de generación de reportes administrativos.
    Tipos de reporte: FINANCE, ATTENDANCE, OCCUPANCY, SALES, PERFORMANCE
    - Solo ADMIN puede generarlos.
    - Se guarda el archivo CSV y un registro en la tabla `report`.
    """

    REPORT_DIR = r"C:\\Users\\Juani\\Documents\\POO_Ifts\\smartFit\\smartFit\\db\\reports"

    # ---------- UTILITY ----------
    @staticmethod
    def _ensure_report_dir():
        if not os.path.exists(ReportService.REPORT_DIR):
            os.makedirs(ReportService.REPORT_DIR, exist_ok=True)

    # ---------- GENERATE ----------
    @staticmethod
    def generate_report(gym_id: int, requested_by: int, kind: str,
                        params: dict | None = None, current_user_roles=None):
        """Genera un reporte según el tipo seleccionado (solo ADMIN)."""
        roles = [r.upper() for r in (current_user_roles or [])]
        if "ADMIN" not in roles:
            raise PermissionError("🚫 Solo el administrador puede generar reportes.")

        valid_kinds = {"FINANCE", "ATTENDANCE", "OCCUPANCY", "SALES", "PERFORMANCE"}
        if kind.upper() not in valid_kinds:
            raise ValueError(f"⚠️ Tipo de reporte inválido. Opciones: {', '.join(valid_kinds)}")

        ReportService._ensure_report_dir()

        conn = get_connection()
        cur = conn.cursor()

        # ---------- FINANCE ----------
        if kind.upper() == "FINANCE":
            cur.execute("""
                SELECT p.id, u.full_name AS member_name, p.amount, p.method,
                       p.purpose, p.status, p.paid_at
                FROM payment p
                JOIN member_membership mm ON mm.id = p.member_membership_id
                JOIN user u ON u.id = mm.user_id
                WHERE u.gym_id = ?
                ORDER BY p.paid_at DESC
            """, (gym_id,))
            rows = cur.fetchall()
            filename = f"finance_report_{datetime.date.today()}.csv"

        # ---------- ATTENDANCE ----------
        elif kind.upper() == "ATTENDANCE":
            cur.execute("""
                SELECT c.name AS class_name, u.full_name AS member_name,
                       a.present, a.checked_at
                FROM attendance a
                JOIN booking b ON b.id = a.booking_id
                JOIN class c ON c.id = b.class_id
                JOIN user u ON u.id = b.member_id
                WHERE c.gym_id = ?
                ORDER BY a.checked_at DESC
            """, (gym_id,))
            rows = cur.fetchall()
            filename = f"attendance_report_{datetime.date.today()}.csv"

        # ---------- OCCUPANCY ----------
        elif kind.upper() == "OCCUPANCY":
            cur.execute("""
                SELECT c.name AS class_name, COUNT(b.id) AS total_booked,
                       c.capacity, (COUNT(b.id)*100.0/c.capacity) AS occupancy_rate
                FROM class c
                LEFT JOIN booking b ON b.class_id = c.id AND b.status = 'BOOKED'
                WHERE c.gym_id = ?
                GROUP BY c.id
            """, (gym_id,))
            rows = cur.fetchall()
            filename = f"occupancy_report_{datetime.date.today()}.csv"

        # ---------- SALES ----------
        elif kind.upper() == "SALES":
            cur.execute("""
                SELECT m.name AS membership_name, COUNT(mm.id) AS total_sold,
                       SUM(p.amount) AS total_revenue
                FROM membership m
                LEFT JOIN member_membership mm ON mm.membership_id = m.id
                LEFT JOIN payment p ON p.member_membership_id = mm.id
                WHERE m.gym_id = ?
                GROUP BY m.id
            """, (gym_id,))
            rows = cur.fetchall()
            filename = f"sales_report_{datetime.date.today()}.csv"

        # ---------- PERFORMANCE ----------
        elif kind.upper() == "PERFORMANCE":
            cur.execute("""
                SELECT u.full_name AS trainer_name,
                       COUNT(tp.id) AS total_plans,
                       SUM(CASE WHEN tp.status='CLOSED' THEN 1 ELSE 0 END) AS completed
                FROM training_plan tp
                JOIN user u ON u.id = tp.trainer_id
                WHERE u.gym_id = ?
                GROUP BY u.id
            """, (gym_id,))
            rows = cur.fetchall()
            filename = f"performance_report_{datetime.date.today()}.csv"

        # ---------- WRITE FILE ----------
        ReportService._ensure_report_dir()
        filepath = os.path.join(ReportService.REPORT_DIR, filename)
        if rows:
            with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        else:
            with open(filepath, "w", encoding="utf-8") as csvfile:
                csvfile.write("No data found.\n")

        # ---------- SAVE RECORD ----------
        cur.execute("""
            INSERT INTO report (gym_id, requested_by, kind, params, generated_at, file_path)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            gym_id,
            requested_by,
            kind.upper(),
            json.dumps(params or {}, ensure_ascii=False),
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            filepath
        ))
        conn.commit()
        conn.close()

        print(f"📊 Reporte '{kind}' generado y guardado en: {filepath}")

    # ---------- LIST ----------
    @staticmethod
    def list_reports(gym_id: int, current_user_roles=None):
        """Lista los reportes generados (solo ADMIN)."""
        roles = [r.upper() for r in (current_user_roles or [])]
        if "ADMIN" not in roles:
            raise PermissionError("🚫 Solo el administrador puede ver reportes.")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, kind, generated_at, file_path
            FROM report
            WHERE gym_id = ?
            ORDER BY generated_at DESC
        """, (gym_id,))
        rows = cur.fetchall()
        conn.close()
        return rows
