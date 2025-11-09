from models.Booking import Booking

def test_list_by_class():
    # Prueba como admin
    try:
        print("\n--- Test como ADMIN ---")
        result = Booking.list_by_class(
            class_id=1,  # Ajusta este ID según tu base de datos
            current_user_id=1,  # ID del usuario admin
            current_user_roles=["ADMIN"]
        )
        print(f"Resultado admin: {result}")
    except Exception as e:
        print(f"Error en test admin: {e}")

    # Prueba como trainer
    try:
        print("\n--- Test como TRAINER ---")
        result = Booking.list_by_class(
            class_id=1,  # Ajusta este ID según tu base de datos
            current_user_id=2,  # ID del trainer (debe ser el trainer de la clase)
            current_user_roles=["TRAINER"]
        )
        print(f"Resultado trainer: {result}")
    except Exception as e:
        print(f"Error en test trainer: {e}")

    # Prueba como member
    try:
        print("\n--- Test como MEMBER ---")
        result = Booking.list_by_class(
            class_id=1,  # Ajusta este ID según tu base de datos
            current_user_id=3,  # ID de un miembro
            current_user_roles=["MEMBER"]
        )
        print(f"Resultado member: {result}")
    except Exception as e:
        print(f"Error en test member: {e}")

if __name__ == "__main__":
    test_list_by_class()