from models.Booking import Booking

def test_trainer_access():
    # Usamos los valores que sabemos que son correctos
    CLASS_ID = 5
    TRAINER_ID = 13
    
    print("\n=== Test acceso del profesor ===")
    print(f"Intentando acceder a clase {CLASS_ID} como profesor {TRAINER_ID}")
    
    try:
        result = Booking.list_by_class(
            class_id=CLASS_ID,
            current_user_id=TRAINER_ID,
            current_user_roles=["TRAINER"]  # o ["ENTRENADOR"] según corresponda
        )
        print("\n✅ Acceso exitoso!")
        print(f"Reservas encontradas: {result}")
        
    except Exception as e:
        print(f"\n❌ Error al acceder: {str(e)}")
        print("\nDetalles adicionales:")
        print(f"- Class ID: {CLASS_ID}")
        print(f"- Trainer ID: {TRAINER_ID}")
        
if __name__ == "__main__":
    test_trainer_access()