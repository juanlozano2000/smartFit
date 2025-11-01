from models.Gym import Gym

class GymService:
    """
    Servicio de gestión de gimnasios.
    Solo el ADMIN puede crear, editar o eliminar.
    Todos los roles pueden listar.
    """

    # ---------- CREATE ----------
    @staticmethod
    def create_gym(name: str, address: str | None = None, current_user_roles=None):
        roles = [r.upper() for r in (current_user_roles or [])]
        if "ADMIN" not in roles:
            raise PermissionError("🚫 Solo el administrador puede crear gimnasios.")

        Gym.create(name, address, current_user_roles=roles)

    # ---------- LIST ----------
    @staticmethod
    def list_gyms(current_user_roles=None):
        """Devuelve todos los gimnasios (visible a todos)."""
        return Gym.all(current_user_roles)

    @staticmethod
    def find_gym_by_id(gym_id: int):
        """Devuelve info de un gimnasio."""
        return Gym.find_by_id(gym_id)

    # ---------- UPDATE ----------
    @staticmethod
    def update_gym(gym_id: int, name: str | None = None,
                   address: str | None = None, current_user_roles=None):
        roles = [r.upper() for r in (current_user_roles or [])]
        if "ADMIN" not in roles:
            raise PermissionError("🚫 Solo el administrador puede actualizar gimnasios.")

        Gym.update(gym_id, name, address, current_user_roles=roles)

    # ---------- DELETE ----------
    @staticmethod
    def delete_gym(gym_id: int, current_user_roles=None):
        roles = [r.upper() for r in (current_user_roles or [])]
        if "ADMIN" not in roles:
            raise PermissionError("🚫 Solo el administrador puede eliminar gimnasios.")

        Gym.delete(gym_id, current_user_roles=roles)
