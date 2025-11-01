# SmartFit – Gestión integral para gimnasios

Solución pensada para digitalizar y sistematizar la operación diaria de gimnasios: socios, membresías, reservas de clases, asistencia, pagos, rutinas y reportes. SmartFit está desarrollada como proyecto académico de Programación Orientada a Objetos (POO), con foco en arquitectura, capas y buenas prácticas, pero con ambición real de uso para gimnasios pequeños y medianos.

> Propuesta de valor: Reducí el trabajo manual y los errores en planillas. Centralizá toda la operación en una app simple y extensible. Tomá decisiones con datos reales (reportes) y mejorá la experiencia de tus socios.


## Funcionalidades principales

- Autenticación y roles (Admin, Entrenador, Socio)
	- Inicio de sesión y control de permisos.
	- Asignación de roles por usuario.
- Socios y membresías
	- Altas, bajas, edición de socios.
	- Tipos de membresía, vigencias y estado.
	- Pagos y control de deudas.
- Clases y reservas
	- Gestión de clases/sesiones (cupos, horarios, entrenador asignado).
	- Reservas y cancelaciones por socio.
- Asistencias
	- Registro de asistencia por clase/socio.
- Rutinas y planes de entrenamiento
	- Rutinas personalizadas y planes por socio.
	- Asignación y seguimiento por entrenador.
- Reportes
	- Listados de pagos, asistencias, membresías activas/vencidas, ocupación de clases.


## Para quién es

- Gimnasios y estudios boutique que quieren dejar el Excel y tener control unificado.
- Emprendedores del fitness que necesitan una solución rápida, local y económica.
- Alumnos y docentes que desean un ejemplo claro de POO aplicada a un caso real.


## Requisitos

- Python 3.10 o superior
- SQLite (incluido por defecto con Python vía `sqlite3`)
- Windows PowerShell (instrucciones también válidas para macOS/Linux con mínimas adaptaciones)


## Instalación (Windows PowerShell)

1) Clonar el repositorio

```powershell
git clone https://github.com/juanlozano2000/smartFit.git
cd smartFit/smartFit
```

2) Crear y activar entorno virtual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3) Inicializar la base de datos

```powershell
python .\db\init_db.py
```

4) Ejecutar la aplicación (CLI)

```powershell
python .\main.py
```


## Uso rápido (flujo típico)

1) Iniciar sesión (Admin, Entrenador o Socio) desde el menú.
2) Según el rol:
	 - Admin: crear/editar usuarios, roles, membresías; ver reportes; administrar clases.
	 - Entrenador: gestionar clases, registrar asistencias, asignar rutinas/planes.
	 - Socio: ver/actualizar datos, reservar clases, consultar estado de membresía/pagos.


## Estructura del proyecto

```
smartFit/
├─ main.py                 # Punto de entrada CLI
├─ db/
│  ├─ connection.py        # Conexión y helpers de base de datos (SQLite)
│  ├─ init_db.py           # Inicialización de esquema y datos base
│  └─ schema.sql           # Esquema SQL
├─ models/                 # Entidades del dominio (POO)
│  ├─ User.py, Role.py, User_role.py
│  ├─ Membership.py, Member_membership.py
│  ├─ Class_session.py, Booking.py, Attendance.py
│  ├─ Routine.py, Training_plan.py, Trainer_assigment.py
│  ├─ Gym.py, Payment.py, Report.py
│  └─ __init__.py
├─ services/               # Lógica de aplicación (casos de uso)
│  ├─ auth_service.py
│  ├─ admin_service.py
│  ├─ trainer_service.py
│  └─ member_service.py
└─ utils/                  # Utilidades de UI/validación/menús
	 ├─ menu.py, ui.py, validations.py
	 └─ __init__.py
```

- Capa de modelos: Define las entidades y sus responsabilidades (POO pura).
- Capa de servicios: Orquesta casos de uso, valida reglas de negocio y colabora con la capa de persistencia (db).
- Capa de utilidades/UI: Menú de consola, interacción con el usuario y validaciones comunes.


## Diseño POO y buenas prácticas

- Principios aplicados
	- SRP: Cada clase/modelo tiene una responsabilidad clara (p. ej., `Membership`, `Booking`).
	- OCP: Nuevos tipos de membresía o reportes se agregan sin modificar código existente crítico.
	- LSP/ISP: Modelos y servicios con interfaces simples y coherentes.
	- DIP: Los servicios dependen de abstracciones (contratos), no de implementaciones concretas.
- Separación de capas: modelos (dominio), servicios (aplicación), db (infraestructura), utils (presentación).
- Persistencia: SQLite mediante scripts en `db/` para fácil reproducción del entorno.


## Roadmap (ideas futuras)

- Interfaz web (FastAPI/Flask + frontend ligero) y despliegue cloud.
- Notificaciones (recordatorios de clase y vencimiento de membresía).
- Pasarela de pago integrada.
- Exportación/Importación de datos (CSV/Excel).
- Auditoría y logs avanzados.


## Contribución

1) Crear rama feature: `git checkout -b feature/nombre-feature`
2) Commits claros y pequeños.
3) Abrir PR describiendo el cambio y cómo probarlo.

Estilo sugerido: tipado gradual cuando sea posible, funciones y clases pequeñas, y validaciones en `services`.


## Licencia

MIT (puede ajustarse según necesidad del curso o del cliente final).


## Contacto

Proyecto académico para la materia de POO.
- Autor: Juan Lozano
- GitHub: https://github.com/juanlozano2000
- Soporte/Consultas: abrir un Issue en este repositorio.

