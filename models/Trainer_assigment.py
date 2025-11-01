from db.connection import get_connection

class TrainerAssignment:
    """
    Modelo para la tabla 'trainer_assignment'.
    Permite asignar entrenadores a miembros.
    
    - ADMIN: puede asignar o finalizar cualquier relación.
    - TRAINER: solo puede ver a sus miembros asignados.
    - MEMBER: puede ver quién es su entrenador, pero no modificar.
    """

    # ---------- CREATE ----------
    @staticmethod
    def assign(trainer_id: int, member_id: int,
               start_date: str | None = None,
               end_date: str | None = None,
               status: str = "ACTIVE",
               current_user_id=None,
               current_user_roles=None):
        """
        Asigna un entrenador a un miembro.
        - Solo ADMIN puede crear asignaciones.
        - Un miembro solo puede tener 1 asignación activa.
        """
        roles = [r.upper() for r in (current_user_roles or [])]
        if "ADMIN" not in roles:
            raise PermissionError("🚫 Solo el administrador puede asignar entrenadores.")

        if status.upper() not in ("ACTIVE", "ENDED"):
            raise ValueError("⚠️ Estado inválido. Use 'ACTIVE' o 'ENDED'.")

        conn = get_connection()
        cur = conn.cursor()

        # Validar que el trainer y el member existan y tengan roles correctos
        cur.execute("SELECT id FROM user WHERE id = ?", (trainer_id,))
        if not cur.fetchone():
            conn.close()
            raise ValueError(f"⚠️ Trainer ID {trainer_id} no existe.")

        cur.execute("SELECT id FROM user WHERE id = ?", (member_id,))
        if not cur.fetchone():
            conn.close()
            raise ValueError(f"⚠️ Member ID {member_id} no existe.")

        # Validar que el miembro no tenga ya una asignación activa
        cur.execute("""
            SELECT id FROM trainer_assignment
            WHERE member_id = ? AND status = 'ACTIVE'
        """, (member_id,))
        if cur.fetchone():
            conn.close()
            raise ValueError("⚠️ Este miembro ya tiene un entrenador asignado activo.")

        cur.execute("""
            INSERT INTO trainer_assignment (trainer_id, member_id, start_date, end_date, status)
            VALUES (?, ?, COALESCE(?, CURRENT_TIMESTAMP), ?, ?)
        """, (trainer_id, member_id, start_date, end_date, status.upper()))
        conn.commit()
        conn.close()
        print(f"✅ Entrenador ID {trainer_id} asignado al miembro ID {member_id}.")

    # ---------- READ ----------
    @staticmethod
    def list_all_assignments(current_user_id=None, current_user_roles=None):
        """
        Lista todas las asignaciones visibles según rol:
        - ADMIN: todas.
        - TRAINER: solo sus miembros.
        - MEMBER: solo su propio entrenador.
        """
        roles = [r.upper() for r in (current_user_roles or [])]
        conn = get_connection()
        cur = conn.cursor()

        if "ADMIN" in roles:
            cur.execute("""
                SELECT ta.id, t.full_name AS trainer, m.full_name AS member,
                       ta.start_date, ta.end_date, ta.status
                FROM trainer_assignment ta
                JOIN user t ON t.id = ta.trainer_id
                JOIN user m ON m.id = ta.member_id
                ORDER BY ta.start_date DESC
            """)
        elif "TRAINER" in roles:
            cur.execute("""
                SELECT ta.id, m.full_name AS member, ta.start_date, ta.status
                FROM trainer_assignment ta
                JOIN user m ON m.id = ta.member_id
                WHERE ta.trainer_id = ?
                ORDER BY ta.start_date DESC
            """, (current_user_id,))
        elif "MEMBER" in roles:
            cur.execute("""
                SELECT ta.id, t.full_name AS trainer, ta.start_date, ta.status
                FROM trainer_assignment ta
                JOIN user t ON t.id = ta.trainer_id
                WHERE ta.member_id = ?
                ORDER BY ta.start_date DESC
            """, (current_user_id,))
        else:
            conn.close()
            raise PermissionError("🚫 Rol no autorizado.")

        rows = cur.fetchall()
        conn.close()
        return rows

    # ---------- UPDATE ----------
    @staticmethod
    def update_status(assignment_id: int, status: str,
                      end_date: str | None = None,
                      current_user_roles=None):
        """Actualiza el estado (solo ADMIN)."""
        roles = [r.upper() for r in (current_user_roles or [])]
        if "ADMIN" not in roles:
            raise PermissionError("🚫 Solo el administrador puede modificar asignaciones.")

        if status.upper() not in ("ACTIVE", "ENDED"):
            raise ValueError("⚠️ Estado inválido. Use 'ACTIVE' o 'ENDED'.")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE trainer_assignment
            SET status = ?, end_date = COALESCE(?, end_date)
            WHERE id = ?
        """, (status.upper(), end_date, assignment_id))
        conn.commit()
        conn.close()
        print(f"🟡 Asignación ID {assignment_id} actualizada a estado {status}.")

    # ---------- DELETE ----------
    @staticmethod
    def delete(assignment_id: int, current_user_roles=None):
        """Elimina una asignación (solo ADMIN)."""
        roles = [r.upper() for r in (current_user_roles or [])]
        if "ADMIN" not in roles:
            raise PermissionError("🚫 Solo el administrador puede eliminar asignaciones.")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM trainer_assignment WHERE id = ?", (assignment_id,))
        conn.commit()
        conn.close()
        print(f"🗑️ Asignación ID {assignment_id} eliminada correctamente.")
