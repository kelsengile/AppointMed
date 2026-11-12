-- ============================================================
-- AppointMed sample data (development and testing only)
-- Location in repo: source/database/seed.sql
--
-- Load ONCE, after schema.sql:
--     mysql -u root -p appointmed < source/database/seed.sql
-- To start over, see "Resetting your database" in CONTRIBUTING.md.
--
-- Everything here is FICTIONAL (cartoon characters). Phone numbers and
-- emails are made up (emails use example.com). Never put real
-- personal or medical data in this file.
--
-- SAMPLE LOGINS
--   username          password     role     character / notes
--   admin             admin123     admin    Eugene H. Krabs (Mr. Krabs)
--   dr.cheeks         doctor123    doctor   Dr. Sandy Cheeks, General Medicine
--   dr.tentacles      doctor123    doctor   Dr. Squidward Tentacles, Pediatrics
--   dr.pearl          doctor123    doctor   Dr. Pearl Krabs, Ophthalmology
--   dr.squarepants    doctor123    doctor   Dr. SpongeBob SquarePants, Orthopedics
--   dr.patrick        doctor123    doctor   Dr. Patrick Star, Neurology
--   nurse.dora        nurse123     nurse    Dora the Explorer, supports dr.cheeks
--   nurse.blossom     nurse123     nurse    Blossom (Powerpuff Girls), supports dr.cheeks
--   nurse.bubbles     nurse123     nurse    Bubbles (Powerpuff Girls), supports dr.tentacles
--   nurse.buttercup   nurse123     nurse    Buttercup (Powerpuff Girls), supports dr.pearl
--
-- PATIENTS (all from different cartoons)
--   Rick and Morty: Rick Sanchez, Morty Smith, Summer Smith
--   Ben 10: Ben Tennyson, Gwen Tennyson
--   Adventure Time: Ice King, Finn Mertens
--   Regular Show: Benson Dunwoody, Mordecai, Rigby
--   The Simpsons: Homer Simpson, Bart Simpson
--   Family Guy: Stewie Griffin
--   Scooby-Doo: Shaggy Rogers, Velma Dinkley
--   Dexter's Laboratory: Dexter
--   Phineas and Ferb: Phineas Flynn
--
-- Appointment dates are relative to the day you load this file
-- (CURDATE()), so "today" always has a live queue to test with.
--
-- NOTE: user ids are NOT hard-coded. They are read back into the
-- variables below (@admin, @sandy, ...), so this file also works when
-- another script adds more users to the same database.
-- ============================================================

SET NAMES utf8mb4;
USE appointmed;

-- ------------------------------------------------------------
-- USERS (admin and doctors first, because nurses reference doctors)
-- Hashes are bcrypt (cost 12): admin123, doctor123, nurse123.
-- ------------------------------------------------------------
INSERT INTO users (username, password_hash, full_name, role, email, specialization, bio, education, years_experience, languages, assigned_doctor_id) VALUES
('admin', '$2b$12$TxWNxJbDxJvnG8UUASINZ.L1X23uGUsn7NaUwSdUV9ag3.E4CcgT6', 'Eugene H. Krabs', 'admin', 'mr.krabs@example.com', NULL,
 'Runs the clinic office, keeps the schedules tidy, and makes sure every patient has a smooth visit from booking to payment.',
 'BS Business Administration, Bikini Bottom University', 25, 'English, Filipino', NULL),
('dr.cheeks', '$2b$12$B83F6RVelKn914j9Aa981.KDbWtde1hWrOCgfPkS0cAf/2abwp636', 'Dr. Sandy Cheeks', 'doctor', 's.cheeks@example.com', 'General Medicine',
 'A family doctor who loves preventive care and clear explanations. Sandy helps patients manage everyday illness and long-term conditions.',
 'Doctor of Medicine, Texas Treedome University; Residency in Family Medicine', 12, 'English, Filipino', NULL),
('dr.tentacles', '$2b$12$B83F6RVelKn914j9Aa981.KDbWtde1hWrOCgfPkS0cAf/2abwp636', 'Dr. Squidward Tentacles', 'doctor', 's.tentacles@example.com', 'Pediatrics',
 'Cares for infants, children, and teens with a calm and patient approach. Special interest in childhood allergies and vaccinations.',
 'Doctor of Medicine, Krusty Krab College of Medicine; Fellowship in Pediatrics', 9, 'English, Filipino, Spanish', NULL),
('dr.pearl', '$2b$12$B83F6RVelKn914j9Aa981.KDbWtde1hWrOCgfPkS0cAf/2abwp636', 'Dr. Pearl Krabs', 'doctor', 'p.krabs@example.com', 'Ophthalmology',
 'Eye specialist focused on vision tests, dry eye care, and early detection of eye disease for all ages.',
 'Doctor of Medicine, Bikini Bottom University; Residency in Ophthalmology', 7, 'English, Filipino', NULL),
('dr.squarepants', '$2b$12$B83F6RVelKn914j9Aa981.KDbWtde1hWrOCgfPkS0cAf/2abwp636', 'Dr. SpongeBob SquarePants', 'doctor', 'spongebob@example.com', 'Orthopedics',
 'Treats bone, joint, and muscle problems, from sports injuries to long-term joint pain, with plenty of enthusiasm.',
 'Doctor of Medicine, Conch Street Medical School; Residency in Orthopedic Surgery', 10, 'English, Filipino', NULL),
('dr.patrick', '$2b$12$B83F6RVelKn914j9Aa981.KDbWtde1hWrOCgfPkS0cAf/2abwp636', 'Dr. Patrick Star', 'doctor', 'p.star@example.com', 'Neurology',
 'Neurologist who helps patients with headaches, migraines, and nerve conditions, and takes time to explain each step.',
 'Doctor of Medicine, Rock Bottom University; Residency in Neurology', 8, 'English, Filipino', NULL);

SET @admin   := (SELECT id FROM users WHERE username = 'admin');
SET @sandy   := (SELECT id FROM users WHERE username = 'dr.cheeks');
SET @squid   := (SELECT id FROM users WHERE username = 'dr.tentacles');
SET @pearl   := (SELECT id FROM users WHERE username = 'dr.pearl');
SET @bob     := (SELECT id FROM users WHERE username = 'dr.squarepants');
SET @patrick := (SELECT id FROM users WHERE username = 'dr.patrick');

INSERT INTO users (username, password_hash, full_name, role, email, specialization, bio, education, years_experience, languages, assigned_doctor_id) VALUES
('nurse.dora', '$2b$12$6P8IiOL2fy.Z7ftsz5BWSeY72I12H5OYgkiCMNvBTc80zj9Xjva4u', 'Dora Marquez (Dora the Explorer)', 'nurse', 'dora@example.com', NULL,
 'Welcomes patients, checks them in, and keeps Dr. Cheeks''s queue moving. Always ready to explain what happens next.',
 'BS Nursing, Explorer State University', 6, 'English, Filipino, Spanish', @sandy),
('nurse.blossom', '$2b$12$6P8IiOL2fy.Z7ftsz5BWSeY72I12H5OYgkiCMNvBTc80zj9Xjva4u', 'Blossom Utonium', 'nurse', 'blossom@example.com', NULL,
 'Organized and detail-minded. Handles appointment requests, records, and billing for Dr. Cheeks.',
 'BS Nursing, Townsville College', 5, 'English, Filipino', @sandy),
('nurse.bubbles', '$2b$12$6P8IiOL2fy.Z7ftsz5BWSeY72I12H5OYgkiCMNvBTc80zj9Xjva4u', 'Bubbles Utonium', 'nurse', 'bubbles@example.com', NULL,
 'Gentle with young patients and their families. Supports Dr. Tentacles in the pediatric clinic.',
 'BS Nursing, Townsville College; Certificate in Pediatric Nursing', 4, 'English, Filipino', @squid),
('nurse.buttercup', '$2b$12$6P8IiOL2fy.Z7ftsz5BWSeY72I12H5OYgkiCMNvBTc80zj9Xjva4u', 'Buttercup Utonium', 'nurse', 'buttercup@example.com', NULL,
 'Quick, reliable, and calm under pressure. Prepares patients and rooms for Dr. Pearl''s eye examinations.',
 'BS Nursing, Townsville College', 5, 'English, Filipino', @pearl);

SET @dora      := (SELECT id FROM users WHERE username = 'nurse.dora');
SET @blossom   := (SELECT id FROM users WHERE username = 'nurse.blossom');
SET @bubbles   := (SELECT id FROM users WHERE username = 'nurse.bubbles');
SET @buttercup := (SELECT id FROM users WHERE username = 'nurse.buttercup');

INSERT INTO departments (name, description, icon, is_featured, is_active, sort_order) VALUES
('General Medicine', 'Primary care, routine checkups, preventive health screenings and chronic disease management.', '/dept-general.png', 1, 1, 10),
('Cardiology', 'Heart disease diagnosis and treatment. ECG, Echo, and stress testing available.', '/dept-cardiology.png', 1, 1, 20),
('Neurology', 'Expert care for neurological disorders including stroke, epilepsy, and movement disorders.', '/dept-neurology.png', 1, 1, 30),
('Orthopedics', 'Bone, joint and muscle care including sports injuries, fractures, and joint replacement.', '/dept-orthopedics.png', 1, 1, 40),
('Pediatrics', 'Comprehensive child health care from newborns to adolescents.', '/dept-pediatrics.png', 1, 1, 50),
('Ophthalmology', 'Complete eye care including vision tests, dry eye treatment, and cataract care.', '/dept-ophthalmology.png', 1, 1, 60),
('Dermatology', 'Skin, hair, and nail conditions, including allergies and rashes.', NULL, 0, 1, 100),
('Dentistry', 'Dental checkups, cleaning, fillings, and oral health advice.', NULL, 0, 1, 110),
('Otolaryngology (ENT)', 'Ear, nose, and throat conditions for children and adults.', NULL, 0, 1, 120);

-- ------------------------------------------------------------
-- DOCTOR SCHEDULES (weekday: 1 = Monday ... 7 = Sunday)
-- Dr. Cheeks: Mon-Fri with a lunch break. Dr. Tentacles: Mon/Wed/Fri.
-- Dr. Pearl: Tue/Thu with a lunch break.
-- ------------------------------------------------------------
INSERT INTO doctor_schedules (doctor_id, weekday, start_time, end_time, slot_minutes) VALUES
(@sandy, 1, '08:00:00', '12:00:00', 30), (@sandy, 1, '13:00:00', '17:00:00', 30),
(@sandy, 2, '08:00:00', '12:00:00', 30), (@sandy, 2, '13:00:00', '17:00:00', 30),
(@sandy, 3, '08:00:00', '12:00:00', 30), (@sandy, 3, '13:00:00', '17:00:00', 30),
(@sandy, 4, '08:00:00', '12:00:00', 30), (@sandy, 4, '13:00:00', '17:00:00', 30),
(@sandy, 5, '08:00:00', '12:00:00', 30), (@sandy, 5, '13:00:00', '17:00:00', 30),
(@squid, 1, '09:00:00', '15:00:00', 30),
(@squid, 3, '09:00:00', '15:00:00', 30),
(@squid, 5, '09:00:00', '15:00:00', 30),
(@pearl, 2, '09:00:00', '12:00:00', 30), (@pearl, 2, '13:00:00', '16:00:00', 30),
(@pearl, 4, '09:00:00', '12:00:00', 30), (@pearl, 4, '13:00:00', '16:00:00', 30),
(@bob,   1, '08:00:00', '12:00:00', 30), (@bob,   1, '13:00:00', '16:00:00', 30),
(@bob,   2, '08:00:00', '12:00:00', 30), (@bob,   2, '13:00:00', '16:00:00', 30),
(@bob,   3, '08:00:00', '12:00:00', 30), (@bob,   3, '13:00:00', '16:00:00', 30),
(@bob,   4, '08:00:00', '12:00:00', 30), (@bob,   4, '13:00:00', '16:00:00', 30),
(@patrick, 2, '10:00:00', '16:00:00', 30),
(@patrick, 4, '10:00:00', '16:00:00', 30),
(@patrick, 6, '09:00:00', '13:00:00', 30);

-- A day off, so the calendars show a "not available" date (no appointments are booked on it).
INSERT INTO doctor_days_off (doctor_id, off_date, reason) VALUES
(@squid, CURDATE() + INTERVAL 10 DAY, 'Pediatrics conference');

-- ------------------------------------------------------------
-- ROOMS
-- ------------------------------------------------------------
INSERT INTO rooms (id, room_name, status, updated_by) VALUES
(1, 'Room 101',       'Available',   @dora),
(2, 'Room 102',       'Occupied',    @sandy),
(3, 'Room 103',       'Available',   @bubbles),
(4, 'Room 104',       'Maintenance', @admin),
(5, 'Procedure Room', 'Available',   @buttercup);

-- ------------------------------------------------------------
-- NOTIFICATIONS (appointment requests from the website and phone)
--   Pending: 1, 2, 6   Converted: 3, 4   Dismissed: 5
-- ------------------------------------------------------------
INSERT INTO notifications
  (id, doctor_id, nurse_id, requester_name, contact_number, email, birthdate, sex, address,
   preferred_datetime, reason, origin, status, decision_note, decided_by, resolved_at) VALUES
(1, @sandy, @dora,    'Finn Mertens',  '0900-000-0001', 'finn.mertens@example.com',  '2008-09-05', 'Male',   'Tree Fort, Land of Ooo',
    TIMESTAMP(CURDATE() + INTERVAL 2 DAY, '10:00:00'), 'Recurring headaches',      'Website', 'Pending',   NULL, NULL, NULL),
(2, @squid, @bubbles, 'Gwen Tennyson', '0900-000-0002', 'max.tennyson@example.com',   '2013-05-10', 'Female', 'Bellwood Camper Van, Sample City',
    TIMESTAMP(CURDATE() + INTERVAL 3 DAY, '09:30:00'), 'Fever for 2 days',         'Website', 'Pending',   NULL, NULL, NULL),
(3, @sandy, @dora,    'Mordecai',      '0900-000-0003', 'mordecai@example.com',      '1992-04-18', 'Male',   'The Park House, Sample City',
    TIMESTAMP(CURDATE(), '09:00:00'),                  'Persistent cough',         'Website', 'Converted', NULL, @dora, NOW()),
(4, @squid, @bubbles, 'Summer Smith',  '0900-000-0004', NULL,                        '2005-08-01', 'Female', 'Smith Residence, Sample City',
    TIMESTAMP(CURDATE(), '11:00:00'),                  'Vaccination follow-up',    'Phone',   'Converted', NULL, @bubbles, NOW()),
(5, @sandy, @dora,    'Finn Mertens',  '0900-000-0001', 'finn.mertens@example.com',  '2008-09-05', 'Male',   'Tree Fort, Land of Ooo',
    TIMESTAMP(CURDATE() + INTERVAL 2 DAY, '10:00:00'), 'Duplicate of request #1',  'Website', 'Dismissed', 'This is a duplicate of an earlier request.', @dora, NOW()),
(6, @pearl, @buttercup, 'Dee Dee',     '0900-000-0006', 'deedee@example.com',        '2000-02-14', 'Female', 'Laboratory Lane, Sample City',
    TIMESTAMP(CURDATE() + INTERVAL 4 DAY, '10:00:00'), 'Blurry vision',            'Website', 'Pending',   NULL, NULL, NULL);

-- ------------------------------------------------------------
-- PATIENTS (people who have already been examined or are in the clinic)
-- ------------------------------------------------------------
INSERT INTO patients (id, full_name, birthdate, sex, contact_number, email, address, condition_summary, doctor_id) VALUES
(1,  'Rick Sanchez',                '1958-03-14', 'Male',   '0900-000-0101', 'rick.sanchez@example.com', 'Smith Residence Garage, Sample City', 'Hypertension, under monitoring',  @sandy),
(2,  'Morty Smith',                 '2011-07-22', 'Male',   '0900-000-0102', NULL,                       'Smith Residence, Sample City',        'Seasonal allergic rhinitis',      @squid),
(3,  'Benson Dunwoody',             '1990-11-02', 'Male',   '0900-000-0103', 'benson@example.com',       'The Park House, Sample City',         'Recurring migraines',             @sandy),
(4,  'Ben Tennyson',                '2014-01-30', 'Male',   '0900-000-0104', NULL,                       'Bellwood Camper Van, Sample City',    'Routine pediatric checkups',      @squid),
(5,  'Ice King (Simon Petrikov)',   '1960-05-09', 'Male',   '0900-000-0105', NULL,                       'Ice Kingdom, Sample City',            'Type 2 diabetes',                 @sandy),
(6,  'Bart Simpson',                '2013-04-01', 'Male',   '0900-000-0106', NULL,                       '742 Evergreen Terrace, Springfield',  'Frequent minor sprains',          @squid),
(7,  'Homer Simpson',               '1978-05-12', 'Male',   '0900-000-0107', 'homer@example.com',        '742 Evergreen Terrace, Springfield',  'High cholesterol',                @sandy),
(8,  'Stewie Griffin',              '2022-12-20', 'Male',   '0900-000-0108', NULL,                       '31 Spooner Street, Quahog',           'Routine infant checkups',         @squid),
(9,  'Dexter',                      '2015-06-06', 'Male',   '0900-000-0109', NULL,                       'Dexter Laboratory House, Sample City','Nearsightedness',                 @pearl),
(10, 'Velma Dinkley',               '1996-01-15', 'Female', '0900-000-0110', 'velma@example.com',        'Mystery Machine Garage, Coolsville',  'Dry eyes, uses eyeglasses',       @pearl),
(11, 'Shaggy Rogers',               '1994-03-30', 'Male',   '0900-000-0111', NULL,                       'Mystery Machine Garage, Coolsville',  'Food allergies',                  @sandy),
(12, 'Phineas Flynn',               '2014-08-16', 'Male',   '0900-000-0112', NULL,                       'Flynn-Fletcher House, Danville',      'Routine pediatric checkups',      @squid);

-- ------------------------------------------------------------
-- APPOINTMENTS
-- Each doctor has at most one non-cancelled appointment per time,
-- as the double-booking guard in the schema requires.
-- ------------------------------------------------------------
INSERT INTO appointments
  (id, notification_id, patient_id, full_name, doctor_id, nurse_id, room_id, source, scheduled_time, reason, status, checked_in_at) VALUES
-- Past, completed encounters
(1,  NULL, 1,    'Rick Sanchez',  @sandy, @dora,      1,    'Walk-in',      TIMESTAMP(CURDATE() - INTERVAL 7 DAY, '09:00:00'), 'Blood pressure check',        'Completed',  TIMESTAMP(CURDATE() - INTERVAL 7 DAY, '08:50:00')),
(2,  NULL, 2,    'Morty Smith',   @squid, @bubbles,   3,    'Walk-in',      TIMESTAMP(CURDATE() - INTERVAL 3 DAY, '10:00:00'), 'Sneezing and runny nose',     'Completed',  TIMESTAMP(CURDATE() - INTERVAL 3 DAY, '09:55:00')),
(12, NULL, 10,   'Velma Dinkley', @pearl, @buttercup, 5,    'Walk-in',      TIMESTAMP(CURDATE() - INTERVAL 5 DAY, '09:00:00'), 'Dry and itchy eyes',          'Completed',  TIMESTAMP(CURDATE() - INTERVAL 5 DAY, '08:50:00')),
-- Cancelled
(3,  NULL, NULL, 'Rigby (Walk-in)', @sandy, @blossom, NULL, 'Walk-in',      TIMESTAMP(CURDATE() - INTERVAL 2 DAY, '15:00:00'), 'Patient did not show up',      'Cancelled',  NULL),
-- Today, Dr. Cheeks
(4,  NULL, 5,    'Ice King (Simon Petrikov)', @sandy, @dora, NULL, 'Walk-in', TIMESTAMP(CURDATE(), '08:30:00'),               'Diabetes review',             'Examined',   TIMESTAMP(CURDATE(), '08:25:00')),
(5,  3,    NULL, 'Mordecai',      @sandy, @dora,      1,    'Notification', TIMESTAMP(CURDATE(), '09:00:00'),                  'Persistent cough',            'Checked-in', TIMESTAMP(CURDATE(), '08:58:00')),
(6,  NULL, 3,    'Benson Dunwoody', @sandy, @dora,    2,    'Walk-in',      TIMESTAMP(CURDATE(), '09:30:00'),                  'Migraine flare-up',           'Consulting', TIMESTAMP(CURDATE(), '09:20:00')),
(7,  NULL, 1,    'Rick Sanchez',  @sandy, @dora,      NULL, 'Follow-up',    TIMESTAMP(CURDATE(), '10:00:00'),                  'Blood pressure follow-up',    'Scheduled',  NULL),
(13, NULL, 11,   'Shaggy Rogers', @sandy, @blossom,   3,    'Walk-in',      TIMESTAMP(CURDATE(), '10:30:00'),                  'Stomach ache after a snack',  'Checked-in', TIMESTAMP(CURDATE(), '10:20:00')),
(11, NULL, 7,    'Homer Simpson', @sandy, @blossom,   NULL, 'Walk-in',      TIMESTAMP(CURDATE(), '11:00:00'),                  'Cholesterol check',           'Scheduled',  NULL),
(8,  NULL, NULL, 'Dr. Cheeks (personal checkup)', @sandy, NULL, NULL, 'Walk-in', TIMESTAMP(CURDATE(), '14:00:00'),             'Booked by the doctor, no nurse', 'Scheduled', NULL),
-- Today and tomorrow, Dr. Tentacles
(9,  4,    NULL, 'Summer Smith',  @squid, @bubbles,   NULL, 'Notification', TIMESTAMP(CURDATE(), '11:00:00'),                  'Vaccination follow-up',       'Scheduled',  NULL),
(14, NULL, 8,    'Stewie Griffin', @squid, @bubbles,  NULL, 'Walk-in',      TIMESTAMP(CURDATE(), '11:30:00'),                  'Routine infant checkup',      'Scheduled',  NULL),
(10, NULL, 4,    'Ben Tennyson',  @squid, @bubbles,   NULL, 'Walk-in',      TIMESTAMP(CURDATE() + INTERVAL 1 DAY, '09:00:00'), 'Routine checkup',             'Scheduled',  NULL),
-- Today, Dr. Pearl
(15, NULL, 9,    'Dexter',        @pearl, @buttercup, 5,    'Walk-in',      TIMESTAMP(CURDATE(), '10:00:00'),                  'Vision test',                 'Checked-in', TIMESTAMP(CURDATE(), '09:50:00'));

-- ------------------------------------------------------------
-- EXAMINATIONS
--   #1 -> appointment 1, follow-up scheduled (appointment 7)
--   #2 -> appointment 2, sent to history
--   #3 -> appointment 4, sent to history (still awaiting billing)
--   #4 -> appointment 12, sent to history (Dr. Pearl)
-- ------------------------------------------------------------
INSERT INTO examinations (id, appointment_id, patient_id, doctor_id, diagnosis, notes, outcome, follow_up_appointment_id, examined_at) VALUES
(1, 1,  1,  @sandy, 'Stage 1 hypertension',       'BP 145/92. Advised low-salt diet and daily walks. Recheck in one week.',          'Follow-up Scheduled', 7,    NOW() - INTERVAL 7 DAY),
(2, 2,  2,  @squid, 'Allergic rhinitis',          'No fever. Avoid dust exposure. Medication prescribed.',                           'Sent to History',     NULL, NOW() - INTERVAL 3 DAY),
(3, 4,  5,  @sandy, 'Type 2 diabetes, stable',    'Fasting glucose acceptable. Continue current diet. Next review in 3 months.',     'Sent to History',     NULL, NOW() - INTERVAL 30 MINUTE),
(4, 12, 10, @pearl, 'Dry eye syndrome',           'Mild irritation. Use lubricant drops and reduce screen time.',                    'Sent to History',     NULL, NOW() - INTERVAL 5 DAY);

-- ------------------------------------------------------------
-- PRESCRIPTIONS AND ITEMS (unit prices are billed on the invoice)
-- ------------------------------------------------------------
INSERT INTO prescriptions (id, examination_id, patient_id, doctor_id, notes, issued_at) VALUES
(1, 1, 1,  @sandy, 'Monitor blood pressure at home each morning.', NOW() - INTERVAL 7 DAY),
(2, 2, 2,  @squid, 'Return if symptoms worsen.',                    NOW() - INTERVAL 3 DAY),
(3, 4, 10, @pearl, 'Return if redness or pain continues.',          NOW() - INTERVAL 5 DAY);

INSERT INTO prescription_items (prescription_id, medicine_name, dosage, quantity, unit_price, instructions) VALUES
(1, 'Amlodipine',                '5 mg',  30, 8.00,   'Take one tablet every morning'),
(1, 'Losartan',                  '50 mg', 30, 10.00,  'Take one tablet every evening'),
(2, 'Cetirizine',                '5 mg',  10, 5.00,   'Take once daily at bedtime for 10 days'),
(3, 'Lubricant eye drops',       '10 mL',  2, 150.00, 'One drop in each eye, three times a day');

-- ------------------------------------------------------------
-- INVOICES (appointment 4 is intentionally NOT billed yet)
--   #1: 500.00 + 540.00 = 1040.00, paid   (appointment 1, Completed)
--   #2: 450.00 +  50.00 =  500.00, paid   (appointment 2, Completed)
--   #3: 500.00 +   0.00 =  500.00, unpaid (appointment 6, Consulting: created when the exam started)
--   #4: 600.00 + 300.00 =  900.00, paid   (appointment 12, Completed)
-- ------------------------------------------------------------
INSERT INTO invoices (id, patient_id, appointment_id, issued_by, consultation_fee, medicines_total, amount, status, issued_at, paid_at, paid_by) VALUES
(1, 1,  1,  @dora,      500.00, 540.00, 1040.00, 'Paid',   NOW() - INTERVAL 7 DAY,     NOW() - INTERVAL 7 DAY, @dora),
(2, 2,  2,  @bubbles,   450.00,  50.00,  500.00, 'Paid',   NOW() - INTERVAL 3 DAY,     NOW() - INTERVAL 3 DAY, @bubbles),
(3, 3,  6,  @sandy,     500.00,   0.00,  500.00, 'Unpaid', NOW() - INTERVAL 20 MINUTE, NULL,                   NULL),
(4, 10, 12, @buttercup, 600.00, 300.00,  900.00, 'Paid',   NOW() - INTERVAL 5 DAY,     NOW() - INTERVAL 5 DAY, @buttercup);

-- ------------------------------------------------------------
-- CLINIC SETTINGS (managed by the admin)
-- ------------------------------------------------------------
INSERT INTO clinic_settings (setting_key, setting_value, description, updated_by) VALUES
('clinic_name',            'AppointMed Bikini Bottom Clinic', 'Name shown on the website and printed invoices', @admin),
('clinic_address',         '124 Conch Street, Bikini Bottom', 'Clinic address (fictional)',                     @admin),
('consultation_fee',       '500.00',                          'Default fee used when an examination starts',    @admin),
('default_slot_minutes',   '30',                              'Default length of one appointment slot',         @admin),
('online_booking_enabled', 'true',                            'Turns the public booking website on or off',     @admin),
('booking_window_days',    '30',                              'How many days ahead patients can book online',   @admin);

-- ------------------------------------------------------------
-- AUDIT LOGS (sample entries for the admin log screen)
-- ------------------------------------------------------------
INSERT INTO audit_logs (user_id, action, entity, entity_id, details) VALUES
(@admin,   'LOGIN',               'users',           @admin,  'Admin signed in'),
(@admin,   'CREATE_USER',         'users',           @dora,   'Created nurse account nurse.dora'),
(@admin,   'CREATE_USER',         'users',           @bubbles,'Created nurse account nurse.bubbles'),
(@admin,   'UPDATE_SETTING',      'clinic_settings', NULL,    'Changed consultation_fee to 500.00'),
(@dora,    'LOGIN',               'users',           @dora,   'Nurse signed in'),
(@blossom, 'CANCEL_APPOINTMENT',  'appointments',    3,       'Patient did not show up'),
(@sandy,   'LOGIN',               'users',           @sandy,  'Doctor signed in'),
(@pearl,   'LOGIN',               'users',           @pearl,  'Doctor signed in'),
(NULL,     'BOOKING_REQUEST',     'notifications',   1,       'New request from the public website');