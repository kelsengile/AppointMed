-- ============================================================
-- AppointMed sample data (development and testing only)
-- Location in repo: source/database/seed.sql
--
-- Load ONCE, after schema.sql:
--     mysql -u root -p appointmed < source/database/seed.sql
-- To start over, see "Resetting your database" in CONTRIBUTING.md.
--
-- Everything here is FICTIONAL. Staff are SpongeBob SquarePants
-- characters; patients are cartoon characters from Rick and Morty,
-- Ben 10, Adventure Time, and Regular Show. Phone numbers and
-- emails are made up (emails use example.com). Never put real
-- personal or medical data in this file.
--
-- SAMPLE LOGINS
--   username         password     role     notes
--   admin            admin123     admin    Mr. Krabs. CHANGE before any shared use
--   dr.cheeks        doctor123    doctor   Dr. Sandy Cheeks, General Medicine
--   dr.tentacles     doctor123    doctor   Dr. Squidward Tentacles, Pediatrics
--   nurse.spongebob  nurse123     nurse    supports dr.cheeks
--   nurse.patrick    nurse123     nurse    supports dr.tentacles
--
-- Appointment dates are relative to the day you load this file
-- (CURDATE()), so "today" always has a live queue to test with.
--
-- WHAT THE DATA COVERS (so you can test each screen and rule)
--   Notifications : 2 Pending, 2 Converted, 1 Dismissed
--   Appointments  : Scheduled, Checked-in, Consulting, Examined,
--                   Completed, Cancelled; walk-in, notification,
--                   follow-up, and a doctor-booked one (no nurse)
--   Rooms         : Available, Occupied, Maintenance
--   Billing       : one Paid invoice, one Unpaid invoice, and one
--                   examined appointment still waiting to be billed
-- ============================================================

SET NAMES utf8mb4;
USE appointmed;

-- ------------------------------------------------------------
-- USERS (doctors first, because nurses reference them)
-- ------------------------------------------------------------
INSERT INTO users (id, username, password_hash, full_name, role, email, specialization, assigned_doctor_id) VALUES
(1, 'admin',           '$2b$12$TxWNxJbDxJvnG8UUASINZ.L1X23uGUsn7NaUwSdUV9ag3.E4CcgT6', 'Eugene H. Krabs',       'admin',  'mr.krabs@example.com',     NULL,               NULL),
(2, 'dr.cheeks',       '$2b$12$B83F6RVelKn914j9Aa981.KDbWtde1hWrOCgfPkS0cAf/2abwp636', 'Dr. Sandy Cheeks',      'doctor', 's.cheeks@example.com',     'General Medicine', NULL),
(3, 'dr.tentacles',    '$2b$12$B83F6RVelKn914j9Aa981.KDbWtde1hWrOCgfPkS0cAf/2abwp636', 'Dr. Squidward Tentacles','doctor', 's.tentacles@example.com',  'Pediatrics',       NULL),
(4, 'nurse.spongebob', '$2b$12$6P8IiOL2fy.Z7ftsz5BWSeY72I12H5OYgkiCMNvBTc80zj9Xjva4u', 'SpongeBob SquarePants', 'nurse',  'spongebob@example.com',    NULL,               2),
(5, 'nurse.patrick',   '$2b$12$6P8IiOL2fy.Z7ftsz5BWSeY72I12H5OYgkiCMNvBTc80zj9Xjva4u', 'Patrick Star',          'nurse',  'p.star@example.com',       NULL,               3);

-- ------------------------------------------------------------
-- DOCTOR SCHEDULES (weekday: 1 = Monday ... 7 = Sunday)
-- Dr. Cheeks: Mon-Fri with a lunch break. Dr. Tentacles: Mon/Wed/Fri.
-- ------------------------------------------------------------
INSERT INTO doctor_schedules (doctor_id, weekday, start_time, end_time, slot_minutes) VALUES
(2, 1, '08:00:00', '12:00:00', 30), (2, 1, '13:00:00', '17:00:00', 30),
(2, 2, '08:00:00', '12:00:00', 30), (2, 2, '13:00:00', '17:00:00', 30),
(2, 3, '08:00:00', '12:00:00', 30), (2, 3, '13:00:00', '17:00:00', 30),
(2, 4, '08:00:00', '12:00:00', 30), (2, 4, '13:00:00', '17:00:00', 30),
(2, 5, '08:00:00', '12:00:00', 30), (2, 5, '13:00:00', '17:00:00', 30),
(3, 1, '09:00:00', '15:00:00', 30),
(3, 3, '09:00:00', '15:00:00', 30),
(3, 5, '09:00:00', '15:00:00', 30);

-- ------------------------------------------------------------
-- ROOMS
-- ------------------------------------------------------------
INSERT INTO rooms (id, room_name, status, updated_by) VALUES
(1, 'Room 101',       'Available',   4),
(2, 'Room 102',       'Occupied',    2),
(3, 'Room 103',       'Available',   5),
(4, 'Room 104',       'Maintenance', 1),
(5, 'Procedure Room', 'Available',   4);

-- ------------------------------------------------------------
-- NOTIFICATIONS (appointment requests from the website and phone)
-- ------------------------------------------------------------
INSERT INTO notifications (id, doctor_id, nurse_id, requester_name, contact_number, email, preferred_datetime, reason, origin, status, resolved_at) VALUES
-- Pending: waiting for a nurse to act
(1, 2, 4, 'Finn Mertens', '0900-000-0001', 'finn.mertens@example.com',
    TIMESTAMP(CURDATE() + INTERVAL 2 DAY, '10:00:00'), 'Recurring headaches',   'Website', 'Pending',   NULL),
(2, 3, 5, 'Gwen Tennyson (guardian: Max Tennyson)', '0900-000-0002', 'max.tennyson@example.com',
    TIMESTAMP(CURDATE() + INTERVAL 3 DAY, '09:30:00'), 'Child fever for 2 days', 'Website', 'Pending',   NULL),
-- Converted: already turned into appointments below
(3, 2, 4, 'Mordecai',      '0900-000-0003', 'mordecai@example.com',
    TIMESTAMP(CURDATE(), '09:00:00'),                  'Persistent cough',       'Website', 'Converted', NOW()),
(4, 3, 5, 'Summer Smith',  '0900-000-0004', NULL,
    TIMESTAMP(CURDATE(), '11:00:00'),                  'Vaccination follow-up',  'Phone',   'Converted', NOW()),
-- Dismissed: duplicate request
(5, 2, 4, 'Finn Mertens', '0900-000-0001', 'finn.mertens@example.com',
    TIMESTAMP(CURDATE() + INTERVAL 2 DAY, '10:00:00'), 'Duplicate of request #1', 'Website', 'Dismissed', NOW());

-- ------------------------------------------------------------
-- PATIENTS (people who have already been examined at least once)
--   Rick and Morty : Rick Sanchez, Morty Smith
--   Ben 10         : Ben Tennyson
--   Adventure Time : Ice King (Simon Petrikov)
--   Regular Show   : Benson Dunwoody
-- ------------------------------------------------------------
INSERT INTO patients (id, full_name, birthdate, sex, contact_number, email, address, condition_summary, doctor_id) VALUES
(1, 'Rick Sanchez',       '1958-03-14', 'Male', '0900-000-0101', 'rick.sanchez@example.com',  'Smith Residence Garage, Sample City',  'Hypertension, under monitoring',  2),
(2, 'Morty Smith',        '2011-07-22', 'Male', '0900-000-0102', NULL,                        'Smith Residence, Sample City',         'Seasonal allergic rhinitis',      3),
(3, 'Benson Dunwoody',    '1990-11-02', 'Male', '0900-000-0103', 'benson@example.com',        'The Park House, Sample City',          'Recurring migraines',             2),
(4, 'Ben Tennyson',       '2014-01-30', 'Male', '0900-000-0104', NULL,                        'Bellwood Camper Van, Sample City',     'Routine pediatric checkups',      3),
(5, 'Ice King (Simon Petrikov)', '1960-05-09', 'Male', '0900-000-0105', NULL,                 'Ice Kingdom, Sample City',             'Type 2 diabetes',                 2);

-- ------------------------------------------------------------
-- APPOINTMENTS
-- Doctor 2 (Cheeks) and doctor 3 (Tentacles) each have at most one
-- non-cancelled appointment per time, as the schema requires.
-- ------------------------------------------------------------
INSERT INTO appointments (id, notification_id, patient_id, full_name, doctor_id, nurse_id, room_id, source, scheduled_time, reason, status, checked_in_at) VALUES
-- Past, completed encounters
(1, NULL, 1,    'Rick Sanchez',       2, 4,    1,    'Walk-in',      TIMESTAMP(CURDATE() - INTERVAL 7 DAY, '09:00:00'), 'Blood pressure check',      'Completed',  TIMESTAMP(CURDATE() - INTERVAL 7 DAY, '08:50:00')),
(2, NULL, 2,    'Morty Smith',        3, 5,    3,    'Walk-in',      TIMESTAMP(CURDATE() - INTERVAL 3 DAY, '10:00:00'), 'Sneezing and runny nose',   'Completed',  TIMESTAMP(CURDATE() - INTERVAL 3 DAY, '09:55:00')),
-- Cancelled
(3, NULL, NULL, 'Rigby (Walk-in)',    2, 4,    NULL, 'Walk-in',      TIMESTAMP(CURDATE() - INTERVAL 2 DAY, '15:00:00'), 'Patient did not show up',    'Cancelled',  NULL),
-- Today, doctor 2 (Cheeks)
(4, NULL, 5,    'Ice King (Simon Petrikov)', 2, 4, NULL, 'Walk-in',  TIMESTAMP(CURDATE(), '08:30:00'),                  'Diabetes review',            'Examined',   TIMESTAMP(CURDATE(), '08:25:00')),
(5, 3,    NULL, 'Mordecai',           2, 4,    NULL, 'Notification', TIMESTAMP(CURDATE(), '09:00:00'),                  'Persistent cough',           'Checked-in', TIMESTAMP(CURDATE(), '08:58:00')),
(6, NULL, 3,    'Benson Dunwoody',    2, 4,    2,    'Walk-in',      TIMESTAMP(CURDATE(), '09:30:00'),                  'Migraine flare-up',          'Consulting', TIMESTAMP(CURDATE(), '09:20:00')),
(7, NULL, 1,    'Rick Sanchez',       2, 4,    NULL, 'Follow-up',    TIMESTAMP(CURDATE(), '10:00:00'),                  'Blood pressure follow-up',   'Scheduled',  NULL),
(8, NULL, NULL, 'Dr. Cheeks (personal checkup)', 2, NULL, NULL, 'Walk-in', TIMESTAMP(CURDATE(), '14:00:00'), 'Booked by the doctor, no nurse', 'Scheduled', NULL),
-- Today and tomorrow, doctor 3 (Tentacles)
(9,  4,   NULL, 'Summer Smith',       3, 5,    NULL, 'Notification', TIMESTAMP(CURDATE(), '11:00:00'),                  'Vaccination follow-up',      'Scheduled',  NULL),
(10, NULL, 4,   'Ben Tennyson',       3, 5,    NULL, 'Walk-in',      TIMESTAMP(CURDATE() + INTERVAL 1 DAY, '09:00:00'), 'Routine checkup',            'Scheduled',  NULL);

-- ------------------------------------------------------------
-- EXAMINATIONS
--   #1 -> appointment 1, doctor scheduled follow-up (appointment 7)
--   #2 -> appointment 2, sent to history
--   #3 -> appointment 4, sent to history (still awaiting billing)
-- ------------------------------------------------------------
INSERT INTO examinations (id, appointment_id, patient_id, doctor_id, diagnosis, notes, outcome, follow_up_appointment_id, examined_at) VALUES
(1, 1, 1, 2, 'Stage 1 hypertension', 'BP 145/92. Advised low-salt diet and daily walks. Recheck in one week.',          'Follow-up Scheduled', 7,    NOW() - INTERVAL 7 DAY),
(2, 2, 2, 3, 'Allergic rhinitis',    'No fever. Avoid dust exposure. Medication prescribed.',                           'Sent to History',     NULL, NOW() - INTERVAL 3 DAY),
(3, 4, 5, 2, 'Type 2 diabetes, stable', 'Fasting glucose acceptable. Continue current diet. Next review in 3 months.', 'Sent to History',     NULL, NOW() - INTERVAL 30 MINUTE);

-- ------------------------------------------------------------
-- PRESCRIPTIONS AND ITEMS (unit prices are billed on the invoice)
-- ------------------------------------------------------------
INSERT INTO prescriptions (id, examination_id, patient_id, doctor_id, notes, issued_at) VALUES
(1, 1, 1, 2, 'Monitor blood pressure at home each morning.', NOW() - INTERVAL 7 DAY),
(2, 2, 2, 3, 'Return if symptoms worsen.',                    NOW() - INTERVAL 3 DAY);

INSERT INTO prescription_items (prescription_id, medicine_name, dosage, quantity, unit_price, instructions) VALUES
(1, 'Amlodipine',     '5 mg',  30, 8.00,  'Take one tablet every morning'),
(1, 'Losartan',       '50 mg', 30, 10.00, 'Take one tablet every evening'),
(2, 'Cetirizine',     '5 mg',  10, 5.00,  'Take once daily at bedtime for 10 days');

-- ------------------------------------------------------------
-- INVOICES (appointment 4 is intentionally NOT billed yet)
--   #1: 500.00 fee + 540.00 medicines (30 x 8 + 30 x 10) = 1040.00, paid
--   #2: 450.00 fee +  50.00 medicines (10 x 5)           =  500.00, unpaid
-- ------------------------------------------------------------
INSERT INTO invoices (id, patient_id, appointment_id, issued_by, consultation_fee, medicines_total, amount, status, issued_at, paid_at, paid_by) VALUES
(1, 1, 1, 4, 500.00, 540.00, 1040.00, 'Paid',   NOW() - INTERVAL 7 DAY, NOW() - INTERVAL 7 DAY, 4),
(2, 2, 2, 5, 450.00,  50.00,  500.00, 'Unpaid', NOW() - INTERVAL 3 DAY, NULL, NULL);

-- ------------------------------------------------------------
-- CLINIC SETTINGS (managed by the admin)
-- ------------------------------------------------------------
INSERT INTO clinic_settings (setting_key, setting_value, description, updated_by) VALUES
('clinic_name',            'AppointMed Bikini Bottom Clinic', 'Name shown on the website and printed invoices', 1),
('clinic_address',         '124 Conch Street, Bikini Bottom', 'Clinic address (fictional)',                     1),
('consultation_fee',       '500.00',                          'Default fee used when an examination starts',    1),
('default_slot_minutes',   '30',                              'Default length of one appointment slot',         1),
('online_booking_enabled', 'true',                            'Turns the public booking website on or off',     1),
('booking_window_days',    '30',                              'How many days ahead patients can book online',   1);

-- ------------------------------------------------------------
-- AUDIT LOGS (sample entries for the admin log screen)
-- ------------------------------------------------------------
INSERT INTO audit_logs (user_id, action, entity, entity_id, details) VALUES
(1, 'LOGIN',                'users',         1, 'Admin signed in'),
(1, 'CREATE_USER',          'users',         4, 'Created nurse account nurse.spongebob'),
(1, 'UPDATE_SETTING',       'clinic_settings', NULL, 'Changed consultation_fee to 500.00'),
(4, 'LOGIN',                'users',         4, 'Nurse signed in'),
(4, 'CANCEL_APPOINTMENT',   'appointments',  3, 'Patient did not show up'),
(2, 'LOGIN',                'users',         2, 'Doctor signed in'),
(NULL, 'BOOKING_REQUEST',   'notifications', 1, 'New request from the public website');