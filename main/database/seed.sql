-- AppointMed — sample seed data for testing login
-- Run this in MySQL Workbench AFTER running schema.sql
-- (File > Open SQL Script > select this file > Execute lightning-bolt icon)

USE appointmed_db;

-- Doctor account
-- username: drdiaz   password: doctor123
INSERT INTO users (username, password_hash, full_name, role, specialization)
VALUES (
    'drdiaz',
    '$2b$12$Zwb88zjbFyan00Chy7a/MO.vD2Jh/vfTSdgEFETM5c6ksYTgUGIZa',
    'Juan Diaz',
    'doctor',
    'Pediatrics'
);

-- Nurse account, assigned to the doctor above
-- username: nursejane   password: nurse123
-- (MySQL won't allow a subquery on `users` while inserting into `users`,
-- so we grab the doctor's id into a variable first)
SET @doctor_id = (SELECT id FROM users WHERE username = 'drdiaz');

INSERT INTO users (username, password_hash, full_name, role, assigned_doctor_id)
VALUES (
    'nursejane',
    '$2b$12$wNBbwNwqRQBxjgQGjuyg2.3GbJlu5OTMkfeqDX2swj3ATsJzzDWMy',
    'Jane Santos',
    'nurse',
    @doctor_id
);

-- Admin account
-- username: admin   password: admin123
INSERT INTO users (username, password_hash, full_name, role)
VALUES (
    'admin',
    '$2b$12$u8SOjtYBy/luDEQVlo6.lOlW.qHTlLZ3AIcTsrAdcwtPyy3lgUoH6',
    'System Administrator',
    'admin'
);

-- Optional: a couple of sample patients so you can test appointment creation
INSERT INTO patients (full_name, birthdate, contact_number, address) VALUES
    ('Liam Mercado', '2015-03-14', '09171234567', 'Quezon City'),
    ('Rosa Torres', '1988-11-02', '09281234567', 'Makati City');
