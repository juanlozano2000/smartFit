# utils/inputs.py
import re
from datetime import datetime

# ---------- TEXT ----------
def ask_text(prompt: str, min_len: int = 1, allow_empty: bool = False) -> str:
    """
    Pide texto y valida longitud mínima.
    Si allow_empty=True, devuelve "" si el usuario deja vacío.
    """
    while True:
        val = input(f"{prompt}: ").strip()
        if not val and allow_empty:
            return ""
        if len(val) < min_len:
            print(f"⚠️ Debe tener al menos {min_len} caracteres.")
        else:
            return val

# ---------- NÚMEROS ----------
def ask_int(prompt: str, min_value: int | None = None, max_value: int | None = None) -> int:
    """Pide un entero dentro de un rango opcional."""
    while True:
        try:
            val = int(input(f"{prompt}: ").strip())
            if min_value is not None and val < min_value:
                print(f"⚠️ Debe ser mayor o igual a {min_value}.")
                continue
            if max_value is not None and val > max_value:
                print(f"⚠️ Debe ser menor o igual a {max_value}.")
                continue
            return val
        except ValueError:
            print("⚠️ Ingresá un número entero válido.")

def ask_float(prompt: str, min_value: float | None = None) -> float:
    """Pide un número decimal con validación mínima."""
    while True:
        try:
            val = float(input(f"{prompt}: ").replace(",", "."))
            if min_value is not None and val < min_value:
                print(f"⚠️ Debe ser mayor o igual a {min_value}.")
                continue
            return val
        except ValueError:
            print("⚠️ Ingresá un valor numérico válido.")

# ---------- BOOLEAN ----------
def confirm(prompt: str = "¿Confirmar? (s/n)") -> bool:
    """Devuelve True si el usuario responde 's'."""
    while True:
        val = input(f"{prompt} ").strip().lower()
        if val in ("s", "si", "sí"):
            return True
        if val in ("n", "no"):
            return False
        print("⚠️ Escribí 's' o 'n'.")

# ---------- FECHAS ----------
def ask_date(prompt: str = "Fecha (YYYY-MM-DD)") -> str:
    """Pide una fecha en formato YYYY-MM-DD y valida formato."""
    while True:
        val = input(f"{prompt}: ").strip()
        try:
            datetime.strptime(val, "%Y-%m-%d")
            return val
        except ValueError:
            print("⚠️ Formato inválido. Usá YYYY-MM-DD.")

def ask_datetime(prompt: str = "Fecha y hora (YYYY-MM-DD HH:MM)") -> str:
    """Pide fecha y hora con validación."""
    while True:
        val = input(f"{prompt}: ").strip()
        try:
            datetime.strptime(val, "%Y-%m-%d %H:%M")
            return val
        except ValueError:
            print("⚠️ Formato inválido. Usá YYYY-MM-DD HH:MM.")

# ---------- VALIDACIONES ----------
def ask_phone(prompt: str = "Teléfono (solo números)") -> str:
    """Valida formato de teléfono."""
    while True:
        val = input(f"{prompt}: ").strip()
        if not re.match(r"^\d{6,15}$", val):
            print("⚠️ Ingresá solo números (mínimo 6 dígitos).")
        else:
            return val

def ask_password(prompt: str = "Contraseña (mínimo 8 caracteres)") -> str:
    """
    Pide contraseña y aplica validaciones básicas:
    - Mínimo 8 caracteres
    - 1 mayúscula
    - 1 minúscula
    - 1 número
    - 1 caracter especial
    """
    pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?\":{}|<>]).{8,}$"
    while True:
        val = input(f"{prompt}: ").strip()
        if not re.match(pattern, val):
            print("⚠️ La contraseña debe incluir mayúscula, minúscula, número y símbolo.")
        else:
            return val
