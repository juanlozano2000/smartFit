from services.Membership_Service import MembershipService
from services.Class_service import ClassService
from services.Training_service import TrainingService
from services.Payment_service import PaymentService
from services.Report_service import ReportService
from services.Gym import Gym
from models.User import User
from models.Booking import Booking
from models.Trainer_assigment import TrainerAssignment

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
                # Guardar el precio de la membresía elegida
                selected_membership = next((m for m in mships if m['id'] == mid), None)
                if not selected_membership:
                    print("❗ ID de membresía inválido.")
                    return
                    
                print("\n💳 Método de pago:")
                print("1. CASH (Efectivo)")
                print("2. CARD (Tarjeta)")
                print("3. TRANSFER (Transferencia)")
                
                method_map = {"1": "CASH", "2": "CARD", "3": "TRANSFER"}
                method_choice = input("\nElegí el método de pago (1-3): ")
                if method_choice not in method_map:
                    print("❗ Método de pago inválido.")
                    return
                
                # Primero asignar la membresía
                MembershipService.choose_membership(self.session["user_id"], mid, self.session["roles"])
                
                # Luego crear el pago
                current = MembershipService.get_user_membership(self.session["user_id"])
                if current:
                    PaymentService.create_payment(
                        current['id'],
                        selected_membership['price'],
                        method_map[method_choice],
                        "SIGNUP",
                        "APPROVED",
                        self.session["roles"]
                    )
        
        elif opt == "6":
            print("\n💰 Tus pagos:")
            rows = PaymentService.list_user_payments(self.session["user_id"])
            
            if not rows:
                print("\n❗ Todavía no realizaste ningún pago.")
                print("\n💡 Para comprar una membresía:")
                print("   1. Volvé al menú principal")
                print("   2. Elegí la opción 5 (Elegir / cambiar membresía)")
                print("   3. Seleccioná el plan que prefieras y realizá el pago")
                return
                
            for p in rows:
                print(f"{p['paid_at']} - ${p['amount']} [{p['status']}]")
        else:
            print("⚠️ Opción no reconocida.")

    # ========== TRAINER ==========
    def trainer_actions(self, opt: str):
        if opt == "1":
            while True:
                print("\n📚 Gestión de Clases")
                print("1. Listar mis clases")
                print("2. Ver todas las clases")
                print("3. Crear nueva clase")
                print("4. Volver al menú principal")
                
                class_opt = input("\nElegí una opción (1-4): ")
                
                if class_opt == "1":
                    print("\n📋 Mis clases:")
                    classes = ClassService.list_classes_by_trainer(self.session["user_id"])
                    if not classes:
                        print("❗ No tenés clases asignadas.")
                    else:
                        for c in classes:
                            print(f"{c['id']}. {c['name']} ({c['start_at']} - {c['end_at']})")
                            print(f"   📍 Sala: {c['room']}")
                            print(f"   👥 Capacidad: {c['capacity']} personas")
                
                elif class_opt == "2":
                    print("\n📋 Todas las clases del gimnasio:")
                    classes = ClassService.list_classes_for_user(self.session["gym_id"], "TRAINER")
                    if not classes:
                        print("❗ No hay clases registradas.")
                    else:
                        for c in classes:
                            trainer = "👤 Tú" if c['trainer_id'] == self.session["user_id"] else f"👤 {c['trainer_name']}"
                            print(f"{c['id']}. {c['name']} ({c['start_at']} - {c['end_at']})")
                            print(f"   📍 Sala: {c['room']} - {trainer}")
                
                elif class_opt == "3":
                    print("\n✨ Crear nueva clase:")
                    name = input("Nombre: ").strip()
                    if not name:
                        print("❗ El nombre es obligatorio")
                        continue
                        
                    try:
                        start = input("Inicio (YYYY-MM-DD HH:MM): ").strip()
                        end = input("Fin (YYYY-MM-DD HH:MM): ").strip()
                        
                        try:
                            capacity = int(input("Capacidad (número de alumnos): "))
                            if capacity <= 0:
                                print("❗ La capacidad debe ser mayor a 0")
                                continue
                        except ValueError:
                            print("❗ La capacidad debe ser un número")
                            continue
                            
                        room = input("Sala: ").strip()
                        if not room:
                            print("❗ La sala es obligatoria")
                            continue
                        
                        print("\n📝 Resumen de la clase:")
                        print(f"Nombre: {name}")
                        print(f"Inicio: {start}")
                        print(f"Fin: {end}")
                        print(f"Capacidad: {capacity}")
                        print(f"Sala: {room}")
                        
                        if input("\n¿Confirmar la creación de la clase? (s/n): ").lower() == 's':
                            ClassService.create_class(
                                self.session["gym_id"], 
                                self.session["user_id"], 
                                name, start, end, capacity, room
                            )
                            print("✅ Clase creada exitosamente!")
                    except Exception as e:
                        print(f"❗ Error: {str(e)}")
                
                elif class_opt == "4":
                    break
                
                else:
                    print("⚠️ Opción no válida")
                
                input("\nPresiona Enter para continuar...")
                
        elif opt == "2":
            while True:
                print("\n📋 Control de Asistencias")
                print("\nTus clases disponibles:")
                classes = ClassService.list_classes_by_trainer(self.session["user_id"])
                
                if not classes:
                    print("❗ No tenés clases asignadas.")
                    input("\nPresiona Enter para volver...")
                    break
                    
                for c in classes:
                    print(f"{c['id']}. {c['name']} ({c['start_at']} - {c['end_at']})")
                    print(f"   📍 Sala: {c['room']}")
                
                print("\nOpciones:")
                print("1. Ver asistencia de una clase")
                print("2. Volver al menú principal")
                
                att_opt = input("\nElegí una opción (1-2): ")
                
                if att_opt == "1":
                    try:
                        cid = int(input("\nIngresá el ID de la clase: "))
                        # Verificar que la clase exista y pertenezca al profesor
                        class_exists = any(c['id'] == cid for c in classes)
                        
                        if not class_exists:
                            print("❗ ID de clase inválido o no te pertenece")
                            continue
                            
                        print("\n📊 Lista de asistencias:")
                        rows = ClassService.list_attendance_by_class(cid)
                        
                        if not rows:
                            print("❗ No hay registros de asistencia para esta clase")
                        else:
                            for r in rows:
                                estado = "✅ Presente" if r["present"] else "❌ Ausente"
                                print(f"{r['member_name']} - {estado} ({r['checked_at']})")
                                
                    except ValueError:
                        print("❗ El ID debe ser un número")
                        
                elif att_opt == "2":
                    break
                    
                else:
                    print("⚠️ Opción no válida")
                    
                input("\nPresiona Enter para continuar...")
                
        elif opt == "3":
            while True:
                print("\n✅ Control de Asistencias")
                print("\nTus clases disponibles:")
                print("\nAquí iría la lógica para marcar asistencia (similar a la opción 2)")
                
        elif opt == "4":
            while True:
                print("\n🏋️‍♂️ Gestión de Planes de Entrenamiento")
                print("\n👥 Lista de miembros disponibles:")
                members = User.list_users_by_role("Miembro", self.session["gym_id"])
                
                if not members:
                    print("❗ No hay miembros disponibles para asignar planes.")
                    input("\nPresiona Enter para volver...")
                    break
                
                for m in members:
                    # Obtener planes activos del miembro
                    plans = TrainingService.list_plans_by_member(m['id'])
                    plan_status = "✅ Con plan activo" if any(p['status'] == 'ACTIVE' for p in plans) else "❌ Sin plan"
                    print(f"{m['id']}. {m['full_name']} - {plan_status}")
                
                print("\nOpciones:")
                print("1. Crear nuevo plan")
                print("2. Volver al menú principal")
                
                plan_opt = input("\nElegí una opción (1-2): ")
                
                if plan_opt == "1":
                    try:
                        mid = int(input("\nID del miembro: "))
                        # Verificar que el miembro exista
                        member_exists = any(m['id'] == mid for m in members)
                        
                        if not member_exists:
                            print("❗ ID de miembro inválido")
                            continue
                        
                        # Obtener el nombre del miembro para mostrar en el resumen
                        member_name = next(m['full_name'] for m in members if m['id'] == mid)
                        
                        print("\n📝 Crear plan de entrenamiento")
                        goal = input("Objetivo del plan: ").strip()
                        if not goal:
                            print("❗ El objetivo es obligatorio")
                            continue
                        
                        print("\n📋 Resumen del plan:")
                        print(f"Miembro: {member_name}")
                        print(f"Objetivo: {goal}")
                        
                        if input("\n¿Confirmar la creación del plan? (s/n): ").lower() == 's':
                            TrainingService.create_plan(
                                self.session["user_id"], 
                                mid, 
                                goal, 
                                current_user_roles=self.session["roles"]
                            )
                            print("✅ Plan creado exitosamente!")
                            print("\n💡 Recordá agregar rutinas al plan desde la opción 5 del menú principal")
                            
                    except ValueError:
                        print("❗ El ID debe ser un número")
                        
                elif plan_opt == "2":
                    break
                    
                else:
                    print("⚠️ Opción no válida")
                
                input("\nPresiona Enter para continuar...")
                
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
            while True:
                print("\n🏋️‍♂️ Gestión de Gimnasios")
                print("1. Listar gimnasios")
                print("2. Crear nuevo gimnasio")
                print("3. Editar gimnasio")
                print("4. Eliminar gimnasio")
                print("5. Volver al menú principal")
                
                gym_opt = input("\nElegí una opción (1-5): ")
                
                if gym_opt == "1":
                    print("\n📋 Lista de Gimnasios:")
                    gyms = Gym.all(self.session["roles"])
                    for g in gyms:
                        print(f"{g['id']}. {g['name']} - {g['address'] or ''}")
                        
                elif gym_opt == "2":
                    print("\n✨ Crear nuevo gimnasio:")
                    name = input("Nombre: ")
                    address = input("Dirección: ")
                    Gym.create(name, address, self.session["roles"])
                    print("✅ Gimnasio creado exitosamente!")
                    
                elif gym_opt == "3":
                    print("\n📝 Editar gimnasio:")
                    gyms = Gym.all(self.session["roles"])
                    for g in gyms:
                        print(f"{g['id']}. {g['name']} - {g['address'] or ''}")
                    
                    gid = input("\nID del gimnasio a editar: ")
                    name = input("Nuevo nombre (Enter para mantener): ")
                    address = input("Nueva dirección (Enter para mantener): ")
                    Gym.update(gid, name, address, self.session["roles"])
                    print("✅ Gimnasio actualizado exitosamente!")
                    
                elif gym_opt == "4":
                    print("\n❌ Eliminar gimnasio:")
                    gyms = Gym.all(self.session["roles"])
                    for g in gyms:
                        print(f"{g['id']}. {g['name']} - {g['address'] or ''}")
                    
                    gid = input("\nID del gimnasio a eliminar: ")
                    if input("¿Estás seguro? Esta acción no se puede deshacer (s/n): ").lower() == 's':
                        Gym.delete(gid, self.session["roles"])
                        print("✅ Gimnasio eliminado exitosamente!")
                    
                elif gym_opt == "5":
                    break
                
                else:
                    print("⚠️ Opción no válida")
                
                input("\nPresiona Enter para continuar...")
                
        elif opt == "2":
            while True:
                print("\n👥 Gestión de Usuarios")
                print("1. Listar todos los usuarios")
                print("2. Listar usuarios activos")
                print("3. Listar usuarios inactivos")
                print("4. Re-Activar usuario")
                print("5. Desactivar usuario")
                print("6. Volver al menú principal")
                
                user_opt = input("\nElegí una opción (1-6): ")
                
                if user_opt == "1":
                    print("\n📋 Lista de todos los usuarios:")
                    users = User.list_all_users()
                    for u in users:
                        status = "✅ Activo" if u['status'] == "ACTIVE" else "❌ Inactivo"
                        roles = u['roles'].split(',') if u['roles'] else ["NO-ROLE"]
                        role_icons = []
                        for role in roles:
                            if role == "Miembro":
                                role_icons.append("👤")
                            elif role == "Entrenador":
                                role_icons.append("🏋️‍♂️")
                            elif role == "Administrador":
                                role_icons.append("👑")
                            elif role == "NO-ROLE":
                                role_icons.append("❓")
                        role_display = " ".join([f"{icon} {role}" for icon, role in zip(role_icons, roles)])
                        print(f"{u['id']}. {u['full_name']} - {role_display} - {status}")
                        
                elif user_opt == "2":
                    print("\n📋 Usuarios activos:")
                    users = User.list_active_users()
                    if not users:
                        print("❗ No hay usuarios activos.")
                    else:
                        for u in users:
                            roles = u['roles'].split(',') if u['roles'] else ["NO-ROLE"]
                            role_icons = []
                            for role in roles:
                                if role == "Miembro":
                                    role_icons.append("👤")
                                elif role == "Entrenador":
                                    role_icons.append("🏋️‍♂️")
                                elif role == "Administrador":
                                    role_icons.append("👑")
                                elif role == "NO-ROLE":
                                    role_icons.append("❓")
                            role_display = " ".join([f"{icon} {role}" for icon, role in zip(role_icons, roles)])
                            print(f"{u['id']}. {u['full_name']} - {role_display}")
                            
                elif user_opt == "3":
                    print("\n📋 Usuarios inactivos:")
                    users = User.list_inactive_users()
                    if not users:
                        print("❗ No hay usuarios inactivos.")
                    else:
                        for u in users:
                            roles = u['roles'].split(',') if u['roles'] else ["NO-ROLE"]
                            role_icons = []
                            for role in roles:
                                if role == "Miembro":
                                    role_icons.append("👤")
                                elif role == "Entrenador":
                                    role_icons.append("🏋️‍♂️")
                                elif role == "Administrador":
                                    role_icons.append("👑")
                                elif role == "NO-ROLE":
                                    role_icons.append("❓")
                            role_display = " ".join([f"{icon} {role}" for icon, role in zip(role_icons, roles)])
                            print(f"{u['id']}. {u['full_name']} - {role_display}")
                            
                elif user_opt == "4":
                    print("\n✨ Activar usuario:")
                    users = User.list_inactive_users()
                    if not users:
                        print("❗ No hay usuarios inactivos para activar.")
                    else:
                        for u in users:
                            print(f"{u['id']}. {u['full_name']}")
                        uid = int(input("\nID del usuario a activar: "))
                        User.activate(uid)
                        print("✅ Usuario activado exitosamente!")
                        
                elif user_opt == "5":
                    print("\n❌ Desactivar usuario:")
                    users = User.list_active_users()
                    if not users:
                        print("❗ No hay usuarios activos para desactivar.")
                    else:
                        for u in users:
                            print(f"{u['id']}. {u['full_name']}")
                        uid = int(input("\nID del usuario a desactivar: "))
                        if uid == self.session["user_id"]:
                            print("❗ No puedes desactivar tu propio usuario")
                        else:
                            if input("¿Estás seguro? Esta acción deshabilitará el acceso del usuario (s/n): ").lower() == 's':
                                User.deactivate(uid)
                                print("✅ Usuario desactivado exitosamente!")
                                
                elif user_opt == "6":
                    break
                
                else:
                    print("⚠️ Opción no válida")
                
                input("\nPresiona Enter para continuar...")
                
        elif opt == "3":
            while True:
                print("\n� Gestión de Membresías")
                print("1. Listar membresías")
                print("2. Crear nueva membresía")
                print("3. Editar membresía")
                print("4. Desactivar membresía")
                print("5. Volver al menú principal")
                
                membership_opt = input("\nElegí una opción (1-5): ")
                
                if membership_opt == "1":
                    print("\n📋 Lista de Membresías:")
                    memberships = MembershipService.list_all_memberships(self.session["roles"])
                    for m in memberships:
                        status = "✅ Activa" if m['status'] == "ACTIVE" else "❌ Inactiva"
                        print(f"{m['id']}. {m['name']} - ${m['price']} ({m['duration_months']} meses) - {status}")
                        
                elif membership_opt == "2":
                    print("\n✨ Crear nueva membresía:")
                    name = input("Nombre: ")
                    dur = int(input("Duración (meses): "))
                    price = float(input("Precio: "))
                    MembershipService.admin_create_membership(self.session["gym_id"], name, dur, price, self.session["roles"])
                    print("✅ Membresía creada exitosamente!")
                    
                elif membership_opt == "3":
                    print("\n📝 Editar membresía:")
                    memberships = MembershipService.list_all_memberships(self.session["roles"])
                    for m in memberships:
                        status = "✅ Activa" if m['status'] == "ACTIVE" else "❌ Inactiva"
                        print(f"{m['id']}. {m['name']} - ${m['price']} ({m['duration_months']} meses) - {status}")
                    
                    mid = input("\nID de la membresía a editar: ")
                    print("\nDeja en blanco para mantener el valor actual")
                    name = input("Nuevo nombre: ")
                    dur_str = input("Nueva duración (meses): ")
                    price_str = input("Nuevo precio: ")
                    
                    # Convertir valores si no están vacíos
                    dur = int(dur_str) if dur_str.strip() else None
                    price = float(price_str) if price_str.strip() else None
                    
                    MembershipService.admin_update_membership(mid, name, dur, price, self.session["roles"])
                    print("✅ Membresía actualizada exitosamente!")
                    
                elif membership_opt == "4":
                    print("\n❌ Desactivar membresía:")
                    memberships = MembershipService.list_active_memberships()
                    if not memberships:
                        print("❗ No hay membresías activas para desactivar.")
                    else:
                        for m in memberships:
                            print(f"{m['id']}. {m['name']} - ${m['price']} ({m['duration_months']} meses)")
                        
                        mid = input("\nID de la membresía a desactivar: ")
                        if input("¿Estás seguro? Esta acción impedirá nuevas suscripciones (s/n): ").lower() == 's':
                            MembershipService.admin_deactivate_membership(mid, self.session["roles"])
                            print("✅ Membresía desactivada exitosamente!")
                    
                elif membership_opt == "5":
                    break
                
                else:
                    print("⚠️ Opción no válida")
                
                input("\nPresiona Enter para continuar...")
                
        elif opt == "4":
            while True:
                print("\n🚻 Gestión de Asignaciones de Entrenadores")
                print("1. Ver asignaciones actuales")
                print("2. Asignar entrenador a miembro")
                print("3. Modificar asignación")
                print("4. Eliminar asignación")
                print("5. Volver al menú principal")
                
                assign_opt = input("\nElegí una opción (1-5): ")
                
                if assign_opt == "1":
                    print("\n📋 Asignaciones actuales:")
                    assignments = TrainerAssignment.list_all_assignments(self.session["user_id"], self.session["roles"])
                    if not assignments:
                        print("❗ No hay asignaciones registradas.")
                    else:
                        for a in assignments:
                            status = "✅ Activa" if a['status'] == "ACTIVE" else "❌ Inactiva"
                            print(f"{a['id']}. 🏋️‍♂️ {a['trainer']} → 👤 {a['member']} - {status}")
                
                elif assign_opt == "2":
                    print("\n✨ Nueva asignación:")
                    print("\n👤 Lista de miembros disponibles:")
                    members = User.list_users_by_role("Miembro", self.session["gym_id"])
                    if not members:
                        print("❗ No hay miembros disponibles.")
                        continue
                    for m in members:
                        print(f"{m['id']}. {m['full_name']}")
                    
                    mid = int(input("\nID del miembro: "))
                    
                    print("\n🏋️‍♂️ Lista de entrenadores disponibles:")
                    trainers = User.list_users_by_role("Entrenador", self.session["gym_id"])
                    if not trainers:
                        print("❗ No hay entrenadores disponibles.")
                        continue
                    for t in trainers:
                        print(f"{t['id']}. {t['full_name']}")
                    
                    tid = int(input("\nID del entrenador: "))
                    TrainerAssignment.assign(tid, mid, self.session["gym_id"])
                    print("✅ Entrenador asignado exitosamente!")
                
                elif assign_opt == "3":
                    print("\n📝 Modificar asignación:")
                    print("Aún esta seccion no esta lista! Pronto lo estará.")
                
                elif assign_opt == "4":
                    print("\n❌ Eliminar asignación:")
                    assignments = TrainerAssignment.list_active_assignments_for_trainer(self.session["user_id"])
                    if not assignments:
                        print("❗ No hay asignaciones activas para eliminar.")
                        continue
                        
                    for a in assignments:
                        print(f"{a['id']}. 🏋️‍♂️ {a['trainer_name']} → 👤 {a['member_name']}")
                    
                    aid = int(input("\nID de la asignación a eliminar: "))
                    if input("¿Estás seguro? Esta acción finalizará la asignación (s/n): ").lower() == 's':
                        TrainerAssignment.delete(aid)
                        print("✅ Asignación eliminada exitosamente!")
                
                elif assign_opt == "5":
                    break
                
                else:
                    print("⚠️ Opción no válida")
                
                input("\nPresiona Enter para continuar...")
                
        elif opt == "5":
            while True:
                print("\n💰 Gestión de Pagos")
                print("1. Listar todos los pagos")
                print("2. Registrar nuevo pago")
                print("3. Actualizar estado de pago")
                print("4. Volver al menú principal")
                
                payment_opt = input("\nElegí una opción (1-4): ")
                
                if payment_opt == "1":
                    print("\n📋 Lista de todos los pagos:")
                    payments = PaymentService.list_all_payments(self.session["roles"])
                    if not payments:
                        print("❗ No hay pagos registrados.")
                    else:
                        for p in payments:
                            status_icon = "✅" if p['status'] == "APPROVED" else "⏳" if p['status'] == "PENDING" else "❌"
                            print(f"{p['id']}. {p['member_name']} - ${p['amount']} - {p['method']} - {status_icon} {p['status']}")
                
                elif payment_opt == "2":
                    print("\n✨ Registrar nuevo pago:")
                    
                    # Listar miembros activos con membresías activas
                    print("\n👤 Membresías activas:")
                    memberships = MembershipService.list_active_memberships()
                    if not memberships:
                        print("❗ No hay membresías activas.")
                        continue
                        
                    for m in memberships:
                        print(f"{m['id']}. - {m['name']} (${m['price']})")
                    
                    mmid = int(input("\nID de la membresía: "))
                    amount = float(input("Monto: $"))
                    
                    print("\n💳 Método de pago:")
                    print("1. CASH (Efectivo)")
                    print("2. CARD (Tarjeta)")
                    print("3. TRANSFER (Transferencia)")
                    
                    method_map = {"1": "CASH", "2": "CARD", "3": "TRANSFER"}
                    method_choice = input("\nElegí el método de pago (1-3): ")
                    
                    if method_choice not in method_map:
                        print("❗ Método de pago inválido.")
                        continue
                    
                    print("\n🎯 Motivo del pago:")
                    print("1. SIGNUP (Nueva suscripción)")
                    print("2. RENEWAL (Renovación)")
                    print("3. DEBT (Deuda pendiente)")
                    print("4. OTHER (Otro)")
                    
                    purpose_map = {
                        "1": "SIGNUP",
                        "2": "RENEWAL",
                        "3": "DEBT",
                        "4": "OTHER"
                    }
                    purpose_choice = input("\nElegí el motivo (1-4): ")
                    
                    if purpose_choice not in purpose_map:
                        print("❗ Motivo inválido.")
                        continue
                    
                    print("\n📊 Estado inicial del pago:")
                    print("1. APPROVED (Aprobado)")
                    print("2. PENDING (Pendiente)")
                    
                    status_map = {"1": "APPROVED", "2": "PENDING"}
                    status_choice = input("\nElegí el estado (1-2): ")
                    
                    if status_choice not in status_map:
                        print("❗ Estado inválido.")
                        continue
                    
                    PaymentService.create_payment(
                        mmid,
                        amount,
                        method_map[method_choice],
                        purpose_map[purpose_choice],
                        status_map[status_choice],
                        self.session["roles"]
                    )
                    print("✅ Pago registrado exitosamente!")
                
                elif payment_opt == "3":
                    print("\n🔄 Actualizar estado de pago pendiente:")
                    print("\nPagos pendientes:")
                    pending = PaymentService.list_pending_payments()
                    if not pending:
                        print("❗ No hay pagos pendientes para actualizar.")
                        continue
                        
                    for p in pending:
                        print(f"{p['id']}. {p['full_name']} - ${p['amount']} - {p['method']} ({p['purpose']})")
                    
                    pid = int(input("\nID del pago a actualizar: "))
                    print("\nNuevo estado:")
                    print("1. APPROVED (Aprobar pago)")
                    print("2. REJECTED (Rechazar pago)")
                    
                    status_map = {"1": "APPROVED", "2": "REJECTED"}
                    status_choice = input("\nElegí el nuevo estado (1-2): ")
                    
                    if status_choice not in status_map:
                        print("❗ Estado inválido.")
                        continue
                    
                    PaymentService.update_status(pid, status_map[status_choice], self.session["roles"])
                    print("✅ Estado del pago actualizado exitosamente!")
                
                elif payment_opt == "4":
                    break
                
                else:
                    print("⚠️ Opción no válida")
                
                input("\nPresiona Enter para continuar...")
                
        elif opt == "6":
            print("\nClases disponibles:")
            rows = ClassService.list_classes_for_user(self.session["gym_id"], "ADMIN")
            for r in rows:
                print(f"{r['id']}. {r['name']} ({r['start_at']})")
        elif opt == "7":
            while True:
                print("\n📊 Gestión de Reportes")
                print("1. Reporte Financiero")
                print("2. Reporte de Asistencias")
                print("3. Reporte de Ocupación")
                print("4. Reporte de Ventas")
                print("5. Reporte de Rendimiento")
                print("6. Volver al menú principal")
                
                report_opt = input("\nElegí una opción (1-6): ")
                
                if report_opt == "1":
                    print("\n💰 Generando Reporte Financiero")
                    print("\nPeríodo del reporte:")
                    print("1. Último mes")
                    print("2. Último trimestre")
                    print("3. Último año")
                    print("4. Personalizado")
                    
                    period = input("\nElegí el período (1-4): ")
                    params = {}
                    
                    if period == "4":
                        start = input("Fecha inicio (YYYY-MM-DD): ")
                        end = input("Fecha fin (YYYY-MM-DD): ")
                        params = {"start_date": start, "end_date": end}
                    
                    ReportService.generate_report(self.session["gym_id"], self.session["user_id"], "FINANCE", params, self.session["roles"])
                
                elif report_opt == "2":
                    print("\n👥 Generando Reporte de Asistencias")
                    print("\nTipo de reporte:")
                    print("1. General")
                    print("2. Por clase")
                    print("3. Por miembro")
                    
                    type_opt = input("\nElegí el tipo (1-3): ")
                    params = {"type": type_opt}
                    
                    if type_opt == "2":
                        classes = ClassService.list_classes_for_user(self.session["gym_id"], "ADMIN")
                        for c in classes:
                            print(f"{c['id']}. {c['name']}")
                        class_id = input("\nID de la clase: ")
                        params["class_id"] = class_id
                    elif type_opt == "3":
                        members = User.list_users_by_role("Miembro", self.session["gym_id"])
                        for m in members:
                            print(f"{m['id']}. {m['full_name']}")
                        member_id = input("\nID del miembro: ")
                        params["member_id"] = member_id
                    
                    ReportService.generate_report(self.session["gym_id"], self.session["user_id"], "ATTENDANCE", params, self.session["roles"])
                
                elif report_opt == "3":
                    print("\n📈 Generando Reporte de Ocupación")
                    print("\nVista:")
                    print("1. Por día")
                    print("2. Por semana")
                    print("3. Por mes")
                    
                    view = input("\nElegí la vista (1-3): ")
                    params = {"view": view}
                    
                    ReportService.generate_report(self.session["gym_id"], self.session["user_id"], "OCCUPANCY", params, self.session["roles"])
                
                elif report_opt == "4":
                    print("\n💎 Generando Reporte de Ventas")
                    print("\nAgrupar por:")
                    print("1. Membresías")
                    print("2. Método de pago")
                    print("3. Período")
                    
                    group = input("\nElegí agrupación (1-3): ")
                    params = {"group": group}
                    
                    ReportService.generate_report(self.session["gym_id"], self.session["user_id"], "SALES", params, self.session["roles"])
                
                elif report_opt == "5":
                    print("\n🎯 Generando Reporte de Rendimiento")
                    print("\nEntidad a evaluar:")
                    print("1. Entrenadores")
                    print("2. Clases")
                    print("3. Membresías")
                    
                    entity = input("\nElegí entidad (1-3): ")
                    params = {"entity": entity}
                    
                    ReportService.generate_report(self.session["gym_id"], self.session["user_id"], "PERFORMANCE", params, self.session["roles"])
                
                elif report_opt == "6":
                    break
                
                else:
                    print("⚠️ Opción no válida")
                
                input("\nPresiona Enter para continuar...")
                
        else:
            print("⚠️ Opción no reconocida.")
