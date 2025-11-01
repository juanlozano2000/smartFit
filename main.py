from services.Auth_service import AuthService
from ui.menus import show_public_menu, show_menu_for_roles
from ui.controllers import Controllers
from utils.inputs import ask_text, ask_password, ask_int
import time

def main():
    session = {}  # Guarda datos del usuario logueado
    ctrl = None

    while True:
        # --- Usuario no logueado ---
        if not session or not session.get("user_id"):
            opt = show_public_menu()

            #Iniciar sesion
            if opt == "1":
                print("\n🔐 Iniciar sesión")
                dni = ask_text("DNI")
                pwd = ask_password("Contraseña")
                try:
                    session = AuthService.login(dni, pwd)
                    ctrl = Controllers(session)
                    print(f"\n👋 Bienvenido {session['full_name']} ({', '.join(session['roles'])})")
                except Exception as e:
                    print(f"\n❌ {e}")
                input("\nPresioná Enter para continuar...")
            
            # Registrar nuevo usuario
            elif opt == "2":
                print("\n📝 Registro de nuevo usuario")
                full = ask_text("Nombre completo", min_len=3)
                dni = ask_text("DNI")
                phone = ask_text("Teléfono")
                pwd = ask_password("Contraseña (mínimo 8 caracteres)")
                gym_id = ask_int("ID del gimnasio (por ahora 1)", min_value=1)
                role = ask_text("Sos Profesor o Miembro?")
                if role.upper() == "PROFESOR":
                    role_profesor = "TRAINER"
                else:
                    role_profesor = "MEMBER"

                try:
                    AuthService.register(full, dni, phone, pwd, gym_id, role_code=role_profesor)
                except Exception as e:
                    print(f"\n❌ {e}")
                time.sleep(1)
                print("✅ Muchas gracias por unirte a SmartFit.\n Ya podes iniciar sesión.")
                input("\nPresioná Enter para continuar...")
            elif opt == "0":
                print("\n👋 Saliendo de SmartFit... ¡Nos vemos!")
                time.sleep(1)
                break
            # volver al inicio del loop
            continue

        # 🧍 --- Usuario logueado ---
        role, opt = show_menu_for_roles(session)

        # Despacho según rol
        if role == "MEMBER":
            if opt == "9":
                print("👋 Sesión cerrada.")
                session, ctrl = {}, None
                time.sleep(1)
                continue
            elif opt == "0":
                break
            else:
                try:
                    ctrl.member_actions(opt)
                except Exception as e:
                    print(f"\n❌ {e}")
            input("\nPresioná Enter para continuar...")

        elif role == "TRAINER":
            if opt == "9":
                print("👋 Sesión cerrada.")
                session, ctrl = {}, None
                continue
            elif opt == "0":
                break
            else:
                try:
                    ctrl.trainer_actions(opt)
                except Exception as e:
                    print(f"\n❌ {e}")
            input("\nPresioná Enter para continuar...")

        elif role == "ADMIN":
            if opt == "9":
                print("👋 Sesión cerrada.")
                session, ctrl = {}, None
                continue
            elif opt == "0":
                break
            else:
                try:
                    ctrl.admin_actions(opt)
                except Exception as e:
                    print(f"\n❌ {e}")
            input("\nPresioná Enter para continuar...")

if __name__ == "__main__":
    main()
