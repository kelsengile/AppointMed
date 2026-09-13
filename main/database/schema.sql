-- AppointMed central database schema
-- Run this once on the server that will host the shared MySQL instance.
--
-- WORKFLOW THIS SCHEMA SUPPORTS
-- 1. A notification for an appointment arrives, addressed to a specific
--    nurse (the nurse assigned to a specific doctor).
-- 2. The nurse either converts that notification into an appointment,
--    or creates a walk-in appointment directly (no notification).
-- 3. The assigned doctor sees the appointee. The doctor's examination
--    creates/links a patient record, and the doctor decides to either
--    (a) schedule a follow-up appointment, or (b) close the encounter
--    to history. The doctor may also write a prescription, which is
--    handed directly to the patient to buy elsewhere (no pharmacist
--    role or in-house billing for it).
-- 4. The nurse bills the patient for the session.
-- 5. Rooms are a simple availability table that a nurse or doctor can
--    update (enforced by application logic, since role checks on FK
--    targets aren't expressible in plain SQL).

CREATE DATABASE IF NOT EXISTS appointmed_db;
USE appointmed_db;

-- ============================================================
-- USERS: doctors, nurses, admins
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role ENUM('doctor', 'nurse', 'admin') NOT NULL,
    specialization VARCHAR(100) NULL,          -- doctors only
    assigned_doctor_id INT NULL,               -- nurses only: which doctor they support
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assigned_doctor_id) REFERENCES users(id)
);

-- ============================================================
-- ROOMS: simple availability board, editable by nurse or doctor
-- ============================================================
CREATE TABLE IF NOT EXISTS rooms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_name VARCHAR(50) UNIQUE NOT NULL,
    status ENUM('Available', 'Occupied', 'Maintenance') NOT NULL DEFAULT 'Available',
    updated_by INT NULL,       -- the nurse or doctor who last changed the status
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (updated_by) REFERENCES users(id)
);

-- ============================================================
-- NOTIFICATIONS: incoming appointment requests routed to a
-- nurse for a specific doctor. A nurse resolves these by either
-- converting them into an appointment or dismissing them.
-- ============================================================
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    doctor_id INT NOT NULL,
    nurse_id INT NOT NULL,
    requester_name VARCHAR(100) NOT NULL,
    contact_number VARCHAR(20),
    reason VARCHAR(255),
    status ENUM('Pending', 'Converted', 'Dismissed') NOT NULL DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    FOREIGN KEY (doctor_id) REFERENCES users(id),
    FOREIGN KEY (nurse_id) REFERENCES users(id)
);

-- ============================================================
-- PATIENTS: the person's clinical record. A row here is created
-- the first time a doctor formally examines an appointee.
-- ============================================================
CREATE TABLE IF NOT EXISTS patients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    birthdate DATE,
    contact_number VARCHAR(20),
    address VARCHAR(255),
    condition_summary VARCHAR(255),
    doctor_id INT NULL,                 -- current/primary doctor
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doctor_id) REFERENCES users(id)
);

-- ============================================================
-- APPOINTMENTS: created by a nurse either from a notification
-- or as a walk-in. patient_id starts NULL for a first-time
-- visitor and gets filled in once the doctor's examination
-- links/creates the patient record.
-- ============================================================
CREATE TABLE IF NOT EXISTS appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    notification_id INT NULL,           -- NULL if this was a walk-in
    patient_id INT NULL,                -- filled in once linked to a patient
    full_name VARCHAR(100) NOT NULL,    -- appointee's name (pre-patient)
    doctor_id INT NOT NULL,
    nurse_id INT NOT NULL,              -- nurse who booked/manages it
    room_id INT NULL,
    source ENUM('Notification', 'Walk-in') NOT NULL DEFAULT 'Walk-in',
    scheduled_time DATETIME NOT NULL,
    reason VARCHAR(255),
    status ENUM('Scheduled', 'Checked-in', 'Examined', 'Completed', 'Cancelled')
        NOT NULL DEFAULT 'Scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (notification_id) REFERENCES notifications(id),
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (doctor_id) REFERENCES users(id),
    FOREIGN KEY (nurse_id) REFERENCES users(id),
    FOREIGN KEY (room_id) REFERENCES rooms(id)
);

-- ============================================================
-- EXAMINATIONS: the doctor's record of seeing the appointee.
-- This is the step where an appointee becomes a patient, and
-- where the doctor decides "follow-up" vs "history".
-- ============================================================
CREATE TABLE IF NOT EXISTS examinations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    appointment_id INT NOT NULL UNIQUE,   -- one examination per appointment
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    diagnosis TEXT,
    notes TEXT,
    outcome ENUM('Follow-up Scheduled', 'Sent to History') NOT NULL,
    follow_up_appointment_id INT NULL,    -- set when outcome = Follow-up Scheduled
    examined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (appointment_id) REFERENCES appointments(id),
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (doctor_id) REFERENCES users(id),
    FOREIGN KEY (follow_up_appointment_id) REFERENCES appointments(id)
);

-- ============================================================
-- PRESCRIPTIONS: written by the doctor during/after examination
-- and given directly to the patient to purchase elsewhere.
-- There is no pharmacist role and no in-house billing for these;
-- they exist purely as a record of what was prescribed.
-- ============================================================
CREATE TABLE IF NOT EXISTS prescriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    examination_id INT NOT NULL,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    notes VARCHAR(255),                 -- optional general instructions
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (examination_id) REFERENCES examinations(id),
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (doctor_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS prescription_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prescription_id INT NOT NULL,
    medicine_name VARCHAR(150) NOT NULL,
    dosage VARCHAR(100),
    quantity INT NOT NULL DEFAULT 1,
    instructions VARCHAR(255),          -- e.g. "Take twice daily after meals"
    FOREIGN KEY (prescription_id) REFERENCES prescriptions(id)
);

-- ============================================================
-- INVOICES: session billing only, issued by a nurse against
-- an appointment.
-- ============================================================
CREATE TABLE IF NOT EXISTS invoices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    appointment_id INT NOT NULL,
    issued_by INT NOT NULL,             -- nurse who issued the invoice
    amount DECIMAL(10,2) NOT NULL,
    status ENUM('Unpaid', 'Paid', 'Cancelled') NOT NULL DEFAULT 'Unpaid',
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (appointment_id) REFERENCES appointments(id),
    FOREIGN KEY (issued_by) REFERENCES users(id)
);

-- ============================================================
-- Default admin account so there's always a way to log in
-- username: admin   password: admin123
-- CHANGE THIS PASSWORD after first login in a real deployment.
-- ============================================================
INSERT INTO users (username, password_hash, full_name, role)
SELECT 'admin', '$2b$12$h.pRIt4ry8kG15BxpNSEu.lNzk2xJMVok5nHAw.ycdUVI19SFBXx2',
       'System Administrator', 'admin'
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin');