# ui/controllers.py

from services.Membership_Service import MembershipService
from services.Class_service import ClassService
from services.Training_service import TrainingService
from services.Payment_service import PaymentService
from services.Report_service import ReportService
from services.Gym import Gym
from services.Auth_service import AuthService
from models.Booking import Booking

class Controllers:
    """
    Controlador principal que orquesta los servicios según el rol y opción elegida.
    Cada método se invoca desde main.py según (role, option).

    Member: reservar clases, ver planes, rutinas, pagos, membresías.
    Trainer: crear clases, marcar asistencia, crear planes y rutinas.
    Admin: gestionar gyms, users, membresías, pagos y reportes.
    Interactúa directamente con tus services, sin SQL ni prints crudos.
    """

    def __init__(self, session: dict):
        self.session = session  # {"user_id":..., "roles": [...], "gym_id":..., "full_name":...}

    # ========== MEMBER ==========
    def member_actions(self, opt: str):
        if opt == "1":
            print("\n📅 Clases disponibles:")
            classes = ClassService.list_classes_for_user(self.session["gym_id"], "MEMBER")
            for c in classes:
                print(f"{c['id']}. {c['name']} ({c['start_at']} - {c['end_at']})")
            cid = int(input("\nElegí ID de clase para reservar: "))
            ClassService.book_class(cid, self.session["user_id"], self.session["roles"])

        elif opt == "2":
            print("\n🎫 Tus clases reservadas:")
            bookings = Booking.list_by_user(self.session["user_id"], self.session["user_id"], self.session["roles"])
            if not bookings:
                print("\n❗ Todavía no reservaste clases.")
                if input("¿Deseas reservar una clase? (s/n): ").lower() == 's':
                    self.member_actions("1")  # Redirigir a la opción de reservar
                return
            
            for b in bookings:
                if b['status'] == 'BOOKED':  # Solo mostrar las reservadas (no canceladas)
                    print(f"{b['id']}. {b['class_name']} ({b['start_at']} - {b['end_at']})")
            
            if input("\n¿Deseas cancelar alguna clase? (s/n): ").lower() == 's':
                bid = int(input("\nIngresa el ID de la reserva a cancelar: "))
                ClassService.cancel_booking(bid, self.session["user_id"], self.session["roles"])

        elif opt == "3":
            print("\n📋 Tus planes de entrenamiento:")
            plans = TrainingService.list_plans_by_member(self.session["user_id"])
            
            if not plans:
                print("\n❗ Todavía no tenés ningún plan de entrenamiento.")
                print("\n💡 Para crear un nuevo plan, consultá con tu profesor en el gimnasio.")
                print("   El podrá diseñar un plan personalizado según tus objetivos.")
                return
            
            for p in plans:
                print(f"Plan {p['id']} - {p['goal']} ({p['start_date']} - {p['end_date']}) [{p['status']}]")
        
        elif opt == "4":
            print("\n📋 Tus planes de entrenamiento:")
            plans = TrainingService.list_plans_by_member(self.session["user_id"])
            
            if not plans:
                print("\n❗ Todavía no tenés ningún plan de entrenamiento.")
                print("\n💡 Para crear un nuevo plan, consultá con tu profesor en el gimnasio.")
                print("   El podrá diseñar un plan personalizado según tus objetivos.")
                return
            
            for p in plans:
                print(f"Plan {p['id']} - {p['goal']} ({p['start_date']} - {p['end_date']}) [{p['status']}]")
            
            pid = int(input("\nIngresa el ID del plan para ver las rutinas: "))
            routines = TrainingService.list_routines_by_plan(pid)
            
            if not routines:
                print("\n❗ Este plan todavía no tiene rutinas asignadas.")
                print("\n💡 Tu profesor aún no creó las rutinas para este plan.")
                print("   Consultale para que diseñe tus ejercicios diarios.")
                return
            
            print("\n🏋️‍♂️ Tus rutinas para este plan:")
            for r in routines:
                print(f"🗓️ Día {r['weekday']}: {r['name']} - {r['notes'] or ''}")
        
        elif opt == "5":
            print("\n🎯 Tu membresía actual:")
            current = MembershipService.get_user_membership(self.session["user_id"])
            
            if not current:
                print("❗ No tenés ninguna membresía activa.")
            else:
                print(f"📌 {current['name']} - ${current['price']} ({current['duration_months']} meses)")
            
            print("\n💫 Otras membresías disponibles:")
            mships = MembershipService.list_active_memberships()
            available_mships = []
            
            for m in mships:
                # No mostrar la membresía actual del usuario
                if not current or m['name'] != current['name']:
                    available_mships.append(m)
                    print(f"{m['id']}. {m['name']} - ${m['price']} ({m['duration_months']} meses)")
            
            if not available_mships:
                print("❗ No hay otras membresías disponibles en este momento.")
                return
                
            if input("\n¿Deseas cambiar tu membresía? (s/n): ").lower() == 's':
                mid = int(input("Elegí ID de la nueva membresía: "))
                MembershipService.choose_membership(self.session["user_id"], mid, self.session["roles"])
        
        elif opt == "6":
            print("\n💰 Tus pagos:")
            rows = PaymentService.list_user_payments(self.session["user_id"])
            for p in rows:
                print(f"{p['paid_at']} - ${p['amount']} [{p['status']}]")
        else:
            print("⚠️ Opción no reconocida.")

    # ========== TRAINER ==========
    def trainer_actions(self, opt: str):
        if opt == "1":
            print("\n📚 Crear nueva clase:")
            name = input("Nombre: ")
            start = input("Inicio (YYYY-MM-DD HH:MM): ")
            end = input("Fin (YYYY-MM-DD HH:MM): ")
            capacity = int(input("Capacidad: "))
            room = input("Sala: ")
            ClassService.create_class(self.session["gym_id"], self.session["user_id"], name, start, end, capacity, room, self.session["roles"])
        elif opt == "2":
            cid = int(input("ID de clase: "))
            rows = ClassService.list_attendance_by_class(cid)
            for r in rows:
                estado = "✅ Presente" if r["present"] else "❌ Ausente"
                print(f"{r['member_name']} - {estado} ({r['checked_at']})")
        elif opt == "3":
            bid = int(input("ID de reserva: "))
            pres = input("¿Asistió? (s/n): ").lower() == "s"
            ClassService.mark_attendance(bid, pres, self.session["roles"])
        elif opt == "4":
            mid = int(input("ID del miembro: "))
            goal = input("Objetivo: ")
            TrainingService.create_plan(self.session["user_id"], mid, goal, current_user_roles=self.session["roles"])
        elif opt == "5":
            pid = int(input("ID del plan: "))
            name = input("Nombre de rutina: ")
            day = int(input("Día (1-Lun ... 7-Dom): "))
            notes = input("Notas: ")
            TrainingService.add_routine(pid, name, day, notes, self.session["roles"])
        elif opt == "6":
            plans = TrainingService.list_plans_by_trainer(self.session["user_id"])
            for p in plans:
                print(f"Plan {p['id']} → {p['member_name']} | {p['goal']} [{p['status']}]")
        elif opt == "7":
            pid = int(input("ID del plan: "))
            routines = TrainingService.list_routines_by_plan(pid)
            for r in routines:
                print(f"{r['weekday']} - {r['name']} ({r['notes'] or ''})")
        else:
            print("⚠️ Opción no reconocida.")

    # ========== ADMIN ==========
    def admin_actions(self, opt: str):
        if opt == "1":
            print("\n🏋️‍♂️ Gimnasios:")
            gyms = Gym.all(self.session["roles"])
            for g in gyms:
                print(f"{g['id']}. {g['name']} - {g['address'] or ''}")
        elif opt == "2":
            uid = int(input("ID de usuario a desactivar: "))
            AuthService.deactivate_user(uid, self.session["roles"])
        elif opt == "3":
            print("\n📦 Crear nueva membresía:")
            name = input("Nombre: ")
            dur = int(input("Duración (meses): "))
            price = float(input("Precio: "))
            MembershipService.admin_create_membership(self.session["gym_id"], name, dur, price, self.session["roles"])
        elif opt == "4":
            print("\n🚻 Asignar entrenador a miembro (no implementado aún).")
        elif opt == "5":
            mmid = int(input("ID member_membership: "))
            amount = float(input("Monto: "))
            method = input("Método (CASH/CARD/TRANSFER): ").upper()
            PaymentService.create_payment(mmid, amount, method, "SIGNUP", "APPROVED", self.session["roles"])
        elif opt == "6":
            print("\nClases disponibles:")
            rows = ClassService.list_classes_for_user(self.session["gym_id"], "ADMIN")
            for r in rows:
                print(f"{r['id']}. {r['name']} ({r['start_at']})")
        elif opt == "7":
            print("\n📊 Generar reporte:")
            kind = input("Tipo (FINANCE/ATTENDANCE/OCCUPANCY/SALES/PERFORMANCE): ").upper()
            ReportService.generate_report(self.session["gym_id"], self.session["user_id"], kind, {}, self.session["roles"])
        else:
            print("⚠️ Opción no reconocida.")
