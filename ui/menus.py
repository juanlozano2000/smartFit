import os
import sys

# ---------- Helpers de UI ----------
def clear():
    """Limpia la pantalla de la terminal."""
    try:
        os.system("cls" if os.name == "nt" else "clear")
    except Exception:
        pass

def header(title: str):
    """Muestra un header con título, limpiando la pantalla antes."""
    clear()
    print("🏋️‍♂️  SmartFit Gym")
    print("────────────────────────")
    print(f"{title}\n")

def ask_option(valid: set[str]) -> str:
    """Pide una opción al usuario hasta que sea válida. Devuelve el string elegido."""
    while True:
        opt = input("Elegí una opción: ").strip()
        if opt in valid:
            return opt
        print("⚠️  Opción inválida. Probá de nuevo.")

# ---------- Menú público ----------
def show_public_menu() -> str:
    """
    Menú inicial (sin sesión).
    Devuelve:
      "1" -> login
      "2" -> register
      "0" -> exit
    """
    header("Bienvenido a SmartFit Gym")
    print("1) Iniciar sesión")
    print("2) Registrarse")
    print("0) Salir")
    return ask_option({"1", "2", "0"})

# ---------- Menú MEMBER ----------
def show_member_menu(user_name: str) -> str:
    """
    Menú para Miembros.
    Devuelve un código que tu controllers.py usará para despachar la acción.
    """
    header(f"Menú Miembro · Hola, {user_name} 👋 ¿Qué deseas hacer hoy?")
    print("1) Ver y reservar clases")
    print("2) Mis reservas (ver / cancelar)")
    print("3) Ver mis planes de entrenamiento")
    print("4) Ver mis rutinas del plan")
    print("5) Elegir / cambiar membresía")
    print("6) Ver mis pagos")
    print("9) Cerrar sesión")
    print("0) Salir del sistema")
    return ask_option({"1", "2", "3", "4", "5", "6", "9", "0"})

# ---------- Menú TRAINER ----------
def show_trainer_menu(user_name: str) -> str:
    """
    Menú para Entrenadores.
    """
    header(f"Menú Entrenador · Hola, {user_name} 🧑‍🏫 ¿Qué deseas hacer hoy?")
    print("1) Mis clases (crear / listar)")
    print("2) Ver reservas de una clase")
    print("3) Marcar asistencia")
    print("4) Crear plan para un miembro")
    print("5) Añadir rutina a un plan")
    print("6) Ver mis planes creados")
    print("7) Ver rutinas de un plan")
    print("9) Cerrar sesión")
    print("0) Salir del sistema")
    return ask_option({"1", "2", "3", "4", "5", "6", "7", "9", "0"})

# ---------- Menú ADMIN ----------
def show_admin_menu(user_name: str) -> str:
    """
    Menú para Administradores.
    """
    header(f"Menú Administrador · Hola, {user_name} 🧑‍💼 ¿Qué deseas hacer hoy?")
    print("1) Gimnasios (listar / crear / editar / eliminar)")
    print("2) Usuarios (listar / crear / editar / desactivar)")
    print("3) Membresías (crear / editar / desactivar)")
    print("4) Asignar entrenador a miembro")
    print("5) Pagos (registrar / listar)")
    print("6) Clases (listar)")
    print("7) Reportes (generar / listar)")
    print("9) Cerrar sesión")
    print("0) Salir del sistema")
    return ask_option({"1", "2", "3", "4", "5", "6", "7", "9", "0"})

# ---------- Router por rol ----------
def show_menu_for_roles(session: dict) -> tuple[str, str]:
    """
    Muestra el menú según roles en sesión y devuelve (role, option).
    Prioriza ADMIN > TRAINER > MEMBER.
    session esperado: {"full_name": str, "roles": [..]}
    """
    roles = {r.upper() for r in (session.get("roles") or [])}
    name = session.get("full_name", "Usuario")

    if "ADMIN" in roles:
        opt = show_admin_menu(name)
        return ("ADMIN", opt)
    if "TRAINER" in roles:
        opt = show_trainer_menu(name)
        return ("TRAINER", opt)
    # fallback a MEMBER
    opt = show_member_menu(name)
    return ("MEMBER", opt)
