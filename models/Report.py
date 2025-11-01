from db.connection import get_connection
import json

class Report:
    """
    Modelo para la tabla 'report'.
    Los reportes pueden ser:
      - FINANCE: resumen de pagos, ingresos, deudas.
      - ATTENDANCE: asistencias y ausencias.
      - OCCUPANCY: uso de clases y cupos.
      - SALES: ventas de membresías.
      - PERFORMANCE: efectividad de entrenadores.

    - ADMIN: puede crear, ver y borrar reportes.
    - TRAINER: puede ver sus reportes de performance.
    - MEMBER: puede ver solo reportes públicos (en este MVP no aplica).
    """

    _KINDS = {"FINANCE", "ATTENDANCE", "OCCUPANCY", "SALES", "PERFORMANCE"}

    # ---------- CREATE ----------
    @staticmethod
    def create(gym_id: int, requested_by: int, kind: str,
               params: dict | None = None,
               file_path: str | None = None,
               current_user_roles=None):
        """
        Crea un nuevo registro de reporte (solo ADMIN).
        Guarda metadatos y parámetros en JSON (por ejemplo, filtros de fechas).
        """
        roles = [r.upper() for r in (current_user_roles or [])]
        if "ADMIN" not in roles:
            raise PermissionError("🚫 Solo los administradores pueden generar reportes.")

        if kind.upper() not in Report._KINDS:
            raise ValueError(f"⚠️ Tipo de reporte inválido. Use uno de: {', '.join(Report._KINDS)}")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO report (gym_id, requested_by, kind, params, file_path)
            VALUES (?, ?, ?, ?, ?)
        """, (gym_id, requested_by, kind.upper(), json.dumps(params or {}), file_path))
        conn.commit()
        conn.close()
        print(f"✅ Reporte '{kind}' creado correctamente.")

    # ---------- READ ----------
    @staticmethod
    def all(current_user_id=None, current_user_roles=None):
        """
        Devuelve todos los reportes visibles según el rol:
        - ADMIN: todos
        - TRAINER: solo los propios (performance)
        - MEMBER: ninguno
        """
        roles = [r.upper() for r in (current_user_roles or [])]
        conn = get_connection()
        cur = conn.cursor()

        if "ADMIN" in roles:
            cur.execute("""
                SELECT r.*, u.full_name AS requested_by_name
                FROM report r
                JOIN user u ON u.id = r.requested_by
                ORDER BY r.generated_at DESC
            """)
        elif "TRAINER" in roles:
            cur.execute("""
                SELECT r.id, r.kind, r.generated_at, r.file_path
                FROM report r
                WHERE r.kind = 'PERFORMANCE' AND r.requested_by = ?
                ORDER BY r.generated_at DESC
            """, (current_user_id,))
        else:
            conn.close()
            raise PermissionError("🚫 No tenés permiso para ver reportes.")

        rows = cur.fetchall()
        conn.close()
        return rows

    @staticmethod
    def find_by_id(report_id: int, current_user_id=None, current_user_roles=None):
        """Obtiene los detalles de un reporte (según permisos)."""
        roles = [r.upper() for r in (current_user_roles or [])]
        is_admin = "ADMIN" in roles
        is_trainer = "TRAINER" in roles

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT r.*, u.full_name AS requested_by_name
            FROM report r
            JOIN user u ON u.id = r.requested_by
            WHERE r.id = ?
        """, (report_id,))
        row = cur.fetchone()
        conn.close()

        if not row:
            raise ValueError("⚠️ Reporte no encontrado.")

        if is_admin:
            return row
        elif is_trainer and row["requested_by"] == current_user_id:
            return row
        else:
            raise PermissionError("🚫 No podés ver este reporte.")

    # ---------- UPDATE ----------
    @staticmethod
    def update_file(report_id: int, file_path: str, current_user_roles=None):
        """Actualiza la ruta del archivo generado (solo ADMIN)."""
        roles = [r.upper() for r in (current_user_roles or [])]
        if "ADMIN" not in roles:
            raise PermissionError("🚫 Solo los administradores pueden modificar reportes.")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE report
            SET file_path = ?
            WHERE id = ?
        """, (file_path, report_id))
        conn.commit()
        conn.close()
        print(f"🟡 Ruta del reporte ID {report_id} actualizada.")

    # ---------- DELETE ----------
    @staticmethod
    def delete(report_id: int, current_user_roles=None):
        """Elimina un reporte (solo ADMIN)."""
        roles = [r.upper() for r in (current_user_roles or [])]
        if "ADMIN" not in roles:
            raise PermissionError("🚫 Solo los administradores pueden eliminar reportes.")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM report WHERE id = ?", (report_id,))
        conn.commit()
        conn.close()
        print(f"🗑️ Reporte ID {report_id} eliminado correctamente.")
