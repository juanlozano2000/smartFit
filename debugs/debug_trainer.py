from db.connection import get_connection

def check_trainer_class(class_id, trainer_id):
    conn = get_connection()
    cur = conn.cursor()
    
    # Verificar la clase y su trainer
    cur.execute("""
        SELECT c.id, c.name, c.trainer_id, u.full_name as trainer_name
        FROM class c
        JOIN user u ON u.id = c.trainer_id
        WHERE c.id = ?
    """, (class_id,))
    
    class_info = cur.fetchone()
    conn.close()
    
    if not class_info:
        print(f"❌ La clase con ID {class_id} no existe")
        return
        
    print(f"\nInformación de la clase:")
    print(f"ID: {class_info['id']}")
    print(f"Nombre: {class_info['name']}")
    print(f"ID del trainer asignado: {class_info['trainer_id']}")
    print(f"Nombre del trainer: {class_info['trainer_name']}")
    print(f"\nID del trainer que intenta acceder: {trainer_id}")
    print(f"¿Coinciden?: {'✅ Sí' if class_info['trainer_id'] == trainer_id else '❌ No'}")

if __name__ == "__main__":
    # Ajusta estos valores según tu caso
    CLASS_ID = 5  # El ID de la clase que estás intentando ver
    TRAINER_ID = 13  # El ID del profesor que intenta acceder
    
    check_trainer_class(CLASS_ID, TRAINER_ID)