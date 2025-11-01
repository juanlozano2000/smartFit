-- ============================
-- SMARTFIT DB SCHEMA (MVP)
-- ============================

PRAGMA foreign_keys = ON;

-------------------------------------------------------
-- 1. Gimnasios
-------------------------------------------------------
CREATE TABLE IF NOT EXISTS gym (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);



-------------------------------------------------------
-- 2. USUARIOS
-------------------------------------------------------
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gym_id INTEGER NOT NULL,
    full_name TEXT NOT NULL,
    phone TEXT,
    status TEXT CHECK(status IN ('ACTIVE','INACTIVE')) DEFAULT 'ACTIVE',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (gym_id) REFERENCES gym(id) ON DELETE CASCADE
);

-------------------------------------------------------
-- 3. Relación USER - ROLE
-------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_role (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES role(id) ON DELETE CASCADE
);

-------------------------------------------------------
-- 4. Roles
-------------------------------------------------------
CREATE TABLE IF NOT EXISTS role (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL CHECK(code IN ('ADMIN','OWNER','TRAINER','MEMBER')),
    name TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-------------------------------------------------------
-- 5. MEMBRESÍAS
-------------------------------------------------------
CREATE TABLE IF NOT EXISTS membership (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gym_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    duration_months INTEGER CHECK(duration_months > 0),
    price REAL NOT NULL CHECK(price >= 0),
    status TEXT CHECK(status IN ('ACTIVE','INACTIVE')) DEFAULT 'ACTIVE',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (gym_id) REFERENCES gym(id) ON DELETE CASCADE
);

-------------------------------------------------------
-- 6. RELACIÓN USUARIO - MEMBRESÍA
-------------------------------------------------------
CREATE TABLE IF NOT EXISTS member_membership (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    membership_id INTEGER NOT NULL,
    start_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_date DATETIME,
    status TEXT CHECK(status IN ('ACTIVE','EXPIRED','PAUSED')) DEFAULT 'ACTIVE',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (membership_id) REFERENCES membership(id) ON DELETE CASCADE
);

-------------------------------------------------------
-- 7. PAGOS
-------------------------------------------------------
CREATE TABLE IF NOT EXISTS payment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_membership_id INTEGER NOT NULL,
    paid_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    amount DECIMAL(12,2) NOT NULL CHECK(amount >= 0),
    method TEXT CHECK(method IN ('CASH','CARD','TRANSFER','OTHER')) NOT NULL,
    purpose TEXT CHECK(purpose IN ('SIGNUP','RENEWAL','DEBT','OTHER')) NOT NULL,
    status TEXT CHECK(status IN ('APPROVED','PENDING','REJECTED')) DEFAULT 'APPROVED',
    period_start DATETIME,
    period_end DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_membership_id) REFERENCES member_membership(id) ON DELETE CASCADE
);

-------------------------------------------------------
-- 8. PLANES DE ENTRENAMIENTO
-------------------------------------------------------
CREATE TABLE IF NOT EXISTS training_plan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trainer_id INTEGER NOT NULL,
    member_id INTEGER NOT NULL,
    goal TEXT NOT NULL,
    start_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_date DATETIME,
    status TEXT CHECK(status IN ('ACTIVE','CLOSED')) DEFAULT 'ACTIVE',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trainer_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES user(id) ON DELETE CASCADE
);

-------------------------------------------------------
-- 9. RUTINAS
-------------------------------------------------------
CREATE TABLE IF NOT EXISTS routine (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    weekday TINYINT CHECK(weekday BETWEEN 1 AND 7),
    notes TEXT,
    FOREIGN KEY (plan_id) REFERENCES training_plan(id) ON DELETE CASCADE
);
-------------------------------------------------------
-- 10. Clase
-------------------------------------------------------
CREATE TABLE IF NOT EXISTS class (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gym_id INTEGER NOT NULL,
    trainer_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    start_at DATETIME NOT NULL,
    end_at DATETIME NOT NULL,
    capacity INTEGER CHECK(capacity > 0),
    room TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (gym_id) REFERENCES gym(id) ON DELETE CASCADE,
    FOREIGN KEY (trainer_id) REFERENCES user(id) ON DELETE CASCADE
);

-------------------------------------------------------
-- 11. Booking/reservas de clases
-------------------------------------------------------
CREATE TABLE IF NOT EXISTS booking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL,
    member_id INTEGER NOT NULL,
    booked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT CHECK(status IN ('BOOKED','CANCELLED','WAITLIST')) DEFAULT 'BOOKED',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (class_id) REFERENCES class(id) ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES user(id) ON DELETE CASCADE
);

-------------------------------------------------------
-- 12. Attendance/Asistencia a clases
-------------------------------------------------------
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL,
    present BOOLEAN NOT NULL DEFAULT 0,
    checked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES booking(id) ON DELETE CASCADE
);


-------------------------------------------------------
-- 13. Reportes
-------------------------------------------------------
CREATE TABLE IF NOT EXISTS report (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gym_id INTEGER NOT NULL,
    requested_by INTEGER NOT NULL,
    kind TEXT CHECK(kind IN ('FINANCE','ATTENDANCE','OCCUPANCY','SALES','PERFORMANCE')) NOT NULL,
    params JSON,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    file_path TEXT,
    FOREIGN KEY (gym_id) REFERENCES gym(id) ON DELETE CASCADE,
    FOREIGN KEY (requested_by) REFERENCES user(id) ON DELETE CASCADE
);

-------------------------------------------------------
-- 14. ASIGNACIÓN DE ENTRENADORES A SOCIOS
-------------------------------------------------------
CREATE TABLE IF NOT EXISTS trainer_assignment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trainer_id INTEGER NOT NULL,
    member_id INTEGER NOT NULL,
    start_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_date DATETIME,
    status TEXT CHECK(status IN ('ACTIVE','ENDED')) DEFAULT 'ACTIVE',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trainer_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES user(id) ON DELETE CASCADE
);