-- AppointMed central database schema
-- Run this once on the server that will host the shared MySQL instance.
-- (Or let the app run it automatically — see database/initializer.py)

CREATE DATABASE IF NOT EXISTS appointmed_db;
USE appointmed_db;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role ENUM('doctor', 'nurse', 'admin') NOT NULL,
    specialization VARCHAR(100) NULL,          -- doctors only
    assigned_doctor_id INT NULL,               -- nurses only
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assigned_doctor_id) REFERENCES users(id)
);

-- Default admin account so there's always a way to log in and create
-- everyone else (doctors, nurses) from inside the app.
-- username: admin   password: admin123
-- CHANGE THIS PASSWORD after first login in a real deployment.
INSERT INTO users (username, password_hash, full_name, role)
SELECT 'admin', '$2b$12$h.pRIt4ry8kG15BxpNSEu.lNzk2xJMVok5nHAw.ycdUVI19SFBXx2',
       'System Administrator', 'admin'
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin');

CREATE TABLE IF NOT EXISTS patients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    birthdate DATE,
    contact_number VARCHAR(20),
    address VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    scheduled_time DATETIME NOT NULL,
    reason VARCHAR(255),
    status ENUM('Scheduled', 'Checked-in', 'Completed', 'Cancelled') DEFAULT 'Scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (doctor_id) REFERENCES users(id)
);
