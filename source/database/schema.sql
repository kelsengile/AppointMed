-- ============================================================
-- AppointMed database schema
-- Location in repo: source/database/schema.sql
--
-- Load as root, from the project root, AFTER creating the
-- `appointmed` database (see CONTRIBUTING.md, Step 4):
--     mysql -u root -p appointmed < source/database/schema.sql
--
-- This file contains structure only. Sample data lives in seed.sql.
--
-- WORKFLOW THIS SCHEMA SUPPORTS
-- 1. A patient requests an appointment on the public website (or by
--    phone). The request is stored in `notifications`, addressed to
--    the doctor they chose and to a nurse assigned to that doctor.
--    The request carries the patient's details (name, birthdate, sex,
--    contact, email, address) so a patient record can be created.
-- 2. The nurse (or the doctor) approves the notification, which creates
--    the patient record (or reuses a matching one) and an appointment,
--    or dismisses it. Either way the requester is emailed.
-- 3. The nurse checks the patient in (checked_in_at orders the waiting
--    queue). The doctor starts the examination (status Consulting, only
--    one at a time per doctor). Starting it creates the invoice. When
--    the doctor finishes, the examination, prescription and invoice
--    totals (consultation fee + medicines) are saved.
-- 4. The doctor or the nurse marks the invoice paid. The appointment
--    becomes Completed and shows up in History and Patient records.
-- 5. The admin (desktop app) manages users, clinic settings, and can
--    review the audit log. Admins do not take part in appointments.
--
-- Role rules (doctor/nurse/admin checks on foreign-key targets) cannot
-- be expressed in plain SQL, so they are enforced in the backend.
--
-- The website and desktop app never talk to MySQL directly; both go
-- through the FastAPI backend, which uses the limited `appointmed_user`.
-- ============================================================

SET NAMES utf8mb4;
USE appointmed;

-- ============================================================
-- USERS: clinic staff only (doctors, nurses, admins).
-- Patients booking on the website do not have accounts.
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    username           VARCHAR(50)  NOT NULL UNIQUE,
    password_hash      VARCHAR(255) NOT NULL,              -- bcrypt hash, never plain text
    full_name          VARCHAR(100) NOT NULL,
    role               ENUM('doctor', 'nurse', 'admin') NOT NULL,
    email              VARCHAR(100) NULL,
    specialization     VARCHAR(100) NULL,                  -- doctors only
    assigned_doctor_id INT NULL,                           -- nurses only: the doctor they support
    avatar             MEDIUMBLOB NULL,                    -- profile picture (small JPEG)
    is_active          BOOLEAN NOT NULL DEFAULT TRUE,      -- admin can deactivate instead of deleting
    last_login_at      TIMESTAMP NULL,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_users_assigned_doctor
        FOREIGN KEY (assigned_doctor_id) REFERENCES users(id),
    INDEX idx_users_role (role),
    INDEX idx_users_assigned_doctor (assigned_doctor_id)
) ENGINE=InnoDB;

-- ============================================================
-- DOCTOR_SCHEDULES: weekly working hours per doctor. The website
-- and the booking screen use this to compute available slots.
-- A doctor with a lunch break gets two rows for the same weekday.
-- ============================================================
CREATE TABLE IF NOT EXISTS doctor_schedules (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    doctor_id    INT NOT NULL,
    weekday      TINYINT NOT NULL,                         -- 1 = Monday ... 7 = Sunday (ISO)
    start_time   TIME NOT NULL,
    end_time     TIME NOT NULL,
    slot_minutes SMALLINT NOT NULL DEFAULT 30,
    CONSTRAINT fk_schedules_doctor FOREIGN KEY (doctor_id) REFERENCES users(id),
    CONSTRAINT chk_schedules_weekday CHECK (weekday BETWEEN 1 AND 7),
    CONSTRAINT chk_schedules_times CHECK (end_time > start_time),
    UNIQUE KEY uq_schedule_block (doctor_id, weekday, start_time)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS doctor_days_off (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    doctor_id  INT NOT NULL,
    off_date   DATE NOT NULL,
    reason     VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_days_off_doctor FOREIGN KEY (doctor_id) REFERENCES users(id),
    UNIQUE KEY uq_doctor_off_date (doctor_id, off_date)
) ENGINE=InnoDB;

-- ============================================================
-- ROOMS: simple availability board, editable by a nurse or doctor
-- ============================================================
CREATE TABLE IF NOT EXISTS rooms (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    room_name  VARCHAR(50) NOT NULL UNIQUE,
    status     ENUM('Available', 'Occupied', 'Maintenance') NOT NULL DEFAULT 'Available',
    updated_by INT NULL,                                   -- nurse or doctor who last changed it
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_rooms_updated_by FOREIGN KEY (updated_by) REFERENCES users(id)
) ENGINE=InnoDB;

-- ============================================================
-- NOTIFICATIONS: incoming appointment requests (mostly from the
-- public website) routed to a doctor and a nurse. Staff resolve
-- each one by approving it (creates the appointment) or dismissing it.
-- The requester's personal details are kept here so the patient record
-- can be created on approval.
-- ============================================================
CREATE TABLE IF NOT EXISTS notifications (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    doctor_id          INT NOT NULL,                       -- doctor the requester chose
    nurse_id           INT NULL,                           -- nurse it is routed to (backend picks one assigned to the doctor)
    requester_name     VARCHAR(100) NOT NULL,
    contact_number     VARCHAR(20),
    email              VARCHAR(100),
    birthdate          DATE NULL,
    sex                ENUM('Male', 'Female', 'Other') NULL,
    address            VARCHAR(255) NULL,
    preferred_datetime DATETIME NULL,                      -- slot the requester picked on the website
    reason             VARCHAR(255),
    origin             ENUM('Website', 'Phone', 'Other') NOT NULL DEFAULT 'Website',
    status             ENUM('Pending', 'Converted', 'Dismissed') NOT NULL DEFAULT 'Pending',
    decision_note      VARCHAR(255) NULL,                  -- reason given when dismissed (emailed to the requester)
    decided_by         INT NULL,                           -- staff member who approved or dismissed
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at        TIMESTAMP NULL,
    CONSTRAINT fk_notifications_doctor     FOREIGN KEY (doctor_id)  REFERENCES users(id),
    CONSTRAINT fk_notifications_nurse      FOREIGN KEY (nurse_id)   REFERENCES users(id),
    CONSTRAINT fk_notifications_decided_by FOREIGN KEY (decided_by) REFERENCES users(id),
    INDEX idx_notifications_nurse_status (nurse_id, status),
    INDEX idx_notifications_doctor_status (doctor_id, status)
) ENGINE=InnoDB;

-- ============================================================
-- PATIENTS: the person's clinical record. A row is created when a
-- booking request is approved (or reused if the same name and
-- birthdate already exist).
-- ============================================================
CREATE TABLE IF NOT EXISTS patients (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    full_name         VARCHAR(100) NOT NULL,
    birthdate         DATE,
    sex               ENUM('Male', 'Female', 'Other') NULL,
    contact_number    VARCHAR(20),
    email             VARCHAR(100),
    address           VARCHAR(255),
    condition_summary VARCHAR(255),
    doctor_id         INT NULL,                            -- current/primary doctor
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_patients_doctor FOREIGN KEY (doctor_id) REFERENCES users(id),
    INDEX idx_patients_name (full_name)
) ENGINE=InnoDB;

-- ============================================================
-- APPOINTMENTS: created when a notification is approved, by a nurse
-- as a walk-in, by a doctor for themselves, or as a follow-up.
-- Status flow: Scheduled -> Checked-in (nurse) -> Consulting (doctor)
-- -> Examined (doctor, awaiting payment) -> Completed (invoice paid).
-- ============================================================
CREATE TABLE IF NOT EXISTS appointments (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    notification_id INT NULL,                              -- NULL unless converted from a notification
    patient_id      INT NULL,
    full_name       VARCHAR(100) NOT NULL,                 -- appointee's name (before they are a patient)
    doctor_id       INT NOT NULL,
    nurse_id        INT NULL,                              -- NULL when the doctor booked it themselves
    room_id         INT NULL,
    source          ENUM('Notification', 'Walk-in', 'Follow-up') NOT NULL DEFAULT 'Walk-in',
    scheduled_time  DATETIME NOT NULL,
    reason          VARCHAR(255),
    status          ENUM('Scheduled', 'Checked-in', 'Consulting', 'Examined', 'Completed', 'Cancelled')
                    NOT NULL DEFAULT 'Scheduled',
    checked_in_at   DATETIME NULL,                         -- orders the waiting queue
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Double-booking guard: a doctor cannot have two non-cancelled
    -- appointments at the same time. Cancelled rows become NULL here,
    -- and MySQL allows many NULLs in a unique index, so a cancelled
    -- slot can be rebooked.
    active_slot DATETIME GENERATED ALWAYS AS
        (CASE WHEN status = 'Cancelled' THEN NULL ELSE scheduled_time END) VIRTUAL,

    CONSTRAINT fk_appointments_notification FOREIGN KEY (notification_id) REFERENCES notifications(id),
    CONSTRAINT fk_appointments_patient      FOREIGN KEY (patient_id)      REFERENCES patients(id),
    CONSTRAINT fk_appointments_doctor       FOREIGN KEY (doctor_id)       REFERENCES users(id),
    CONSTRAINT fk_appointments_nurse        FOREIGN KEY (nurse_id)        REFERENCES users(id),
    CONSTRAINT fk_appointments_room         FOREIGN KEY (room_id)         REFERENCES rooms(id),
    UNIQUE KEY uq_doctor_active_slot (doctor_id, active_slot),
    INDEX idx_appointments_time (scheduled_time),
    INDEX idx_appointments_doctor_status (doctor_id, status),
    INDEX idx_appointments_patient (patient_id)
) ENGINE=InnoDB;

-- ============================================================
-- EXAMINATIONS: the doctor's record of seeing the patient.
-- ============================================================
CREATE TABLE IF NOT EXISTS examinations (
    id                       INT AUTO_INCREMENT PRIMARY KEY,
    appointment_id           INT NOT NULL UNIQUE,          -- one examination per appointment
    patient_id               INT NOT NULL,
    doctor_id                INT NOT NULL,
    diagnosis                TEXT,
    notes                    TEXT,
    outcome                  ENUM('Follow-up Scheduled', 'Sent to History') NOT NULL,
    follow_up_appointment_id INT NULL,                     -- set when outcome = Follow-up Scheduled
    examined_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_exam_appointment FOREIGN KEY (appointment_id)           REFERENCES appointments(id),
    CONSTRAINT fk_exam_patient     FOREIGN KEY (patient_id)               REFERENCES patients(id),
    CONSTRAINT fk_exam_doctor      FOREIGN KEY (doctor_id)                REFERENCES users(id),
    CONSTRAINT fk_exam_followup    FOREIGN KEY (follow_up_appointment_id) REFERENCES appointments(id),
    INDEX idx_exam_patient (patient_id)
) ENGINE=InnoDB;

-- ============================================================
-- PRESCRIPTIONS: written by the doctor after an examination. Each
-- item carries a unit price, and the total is billed on the invoice.
-- ============================================================
CREATE TABLE IF NOT EXISTS prescriptions (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    examination_id INT NOT NULL,
    patient_id     INT NOT NULL,
    doctor_id      INT NOT NULL,
    notes          VARCHAR(255),                           -- optional general instructions
    issued_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_rx_exam    FOREIGN KEY (examination_id) REFERENCES examinations(id),
    CONSTRAINT fk_rx_patient FOREIGN KEY (patient_id)     REFERENCES patients(id),
    CONSTRAINT fk_rx_doctor  FOREIGN KEY (doctor_id)      REFERENCES users(id),
    INDEX idx_rx_patient (patient_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS prescription_items (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    prescription_id INT NOT NULL,
    medicine_name   VARCHAR(150) NOT NULL,
    dosage          VARCHAR(100),
    quantity        INT NOT NULL DEFAULT 1,
    unit_price      DECIMAL(10,2) NOT NULL DEFAULT 0,      -- price per unit, billed on the invoice
    instructions    VARCHAR(255),                          -- e.g. "Take twice daily after meals"
    CONSTRAINT fk_rx_items_rx FOREIGN KEY (prescription_id) REFERENCES prescriptions(id)
        ON DELETE CASCADE,
    CONSTRAINT chk_rx_items_qty CHECK (quantity > 0),
    CONSTRAINT chk_rx_items_price CHECK (unit_price >= 0)
) ENGINE=InnoDB;

-- ============================================================
-- INVOICES: one per appointment. Created when the doctor starts the
-- examination (consultation fee only), then updated when the doctor
-- finishes (consultation fee + prescribed medicines). Paid by the
-- doctor or a nurse; paying completes the appointment.
-- ============================================================
CREATE TABLE IF NOT EXISTS invoices (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    patient_id       INT NOT NULL,
    appointment_id   INT NOT NULL UNIQUE,
    issued_by        INT NOT NULL,                         -- staff member who started the examination or billed it
    consultation_fee DECIMAL(10,2) NOT NULL DEFAULT 0,
    medicines_total  DECIMAL(10,2) NOT NULL DEFAULT 0,
    amount           DECIMAL(10,2) NOT NULL,               -- consultation_fee + medicines_total
    status           ENUM('Unpaid', 'Paid', 'Cancelled') NOT NULL DEFAULT 'Unpaid',
    issued_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid_at          TIMESTAMP NULL,
    paid_by          INT NULL,                             -- doctor or nurse who received the payment
    CONSTRAINT fk_invoices_patient     FOREIGN KEY (patient_id)     REFERENCES patients(id),
    CONSTRAINT fk_invoices_appointment FOREIGN KEY (appointment_id) REFERENCES appointments(id),
    CONSTRAINT fk_invoices_issued_by   FOREIGN KEY (issued_by)      REFERENCES users(id),
    CONSTRAINT fk_invoices_paid_by     FOREIGN KEY (paid_by)        REFERENCES users(id),
    CONSTRAINT chk_invoices_amount CHECK (amount >= 0),
    CONSTRAINT chk_invoices_parts  CHECK (consultation_fee >= 0 AND medicines_total >= 0),
    CONSTRAINT chk_invoices_total  CHECK (amount = consultation_fee + medicines_total),
    INDEX idx_invoices_status (status)
) ENGINE=InnoDB;

-- ============================================================
-- CLINIC_SETTINGS: key/value configuration managed by the admin
-- (clinic name, default fee, whether online booking is open, ...).
-- ============================================================
CREATE TABLE IF NOT EXISTS clinic_settings (
    setting_key   VARCHAR(50) PRIMARY KEY,
    setting_value VARCHAR(255) NOT NULL,
    description   VARCHAR(255),
    updated_by    INT NULL,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_settings_updated_by FOREIGN KEY (updated_by) REFERENCES users(id)
) ENGINE=InnoDB;

-- ============================================================
-- AUDIT_LOGS: who did what, for the admin to review. The backend
-- writes a row on logins, user changes, and status changes.
-- Rows are append-only; do not store passwords or medical details here.
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT NULL,                                   -- NULL for system or unauthenticated actions
    action     VARCHAR(50) NOT NULL,                       -- e.g. LOGIN, CREATE_USER, CANCEL_APPOINTMENT
    entity     VARCHAR(50) NULL,                           -- table or concept affected
    entity_id  INT NULL,
    details    VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_audit_created (created_at),
    INDEX idx_audit_user (user_id)
) ENGINE=InnoDB;

