-- ============================================================
-- AppointMed landing page data (departments + extra doctors)
-- Location in repo: source/database/landing_update.sql
--
-- Run as root, AFTER schema.sql (and seed.sql). Safe to run more than once.
--     mysql -u root -p appointmed < source/database/landing_update.sql
--
-- Adds:
--   * the `departments` table (shown on the front page and in the "View All" popup)
--   * three more fictional doctors so the front page can show five doctor cards
--   * weekly schedules for them (needed for the booking page and the "Available" badge)
--
-- NEW SAMPLE LOGINS (password: doctor123)
--   dr.spongebob  Dr. SpongeBob SquarePants  Orthopedics
--   dr.krabs      Dr. Eugene Krabs           Cardiology
--   dr.star       Dr. Patrick Star           Neurology
--
-- Everything here is FICTIONAL.
-- ============================================================

SET NAMES utf8mb4;
USE appointmed;

-- ------------------------------------------------------------
-- DEPARTMENTS: clinical departments shown on the public front page.
-- is_featured = shown as a card on the page. All active rows appear in the popup.
-- A department's doctor count is the number of active doctors whose
-- specialization equals the department name.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS departments (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255) NOT NULL,
    icon        VARCHAR(100) NULL,                         -- image under frontend/public, e.g. /dept-cardiology.png
    is_featured BOOLEAN NOT NULL DEFAULT FALSE,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order  INT NOT NULL DEFAULT 100,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_departments_order (is_featured, sort_order)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- EXTRA DOCTORS (same bcrypt hash as the other sample doctors: doctor123)
-- ------------------------------------------------------------
INSERT IGNORE INTO users (username, password_hash, full_name, role, email, specialization) VALUES
('dr.spongebob', '$2b$12$B83F6RVelKn914j9Aa981.KDbWtde1hWrOCgfPkS0cAf/2abwp636', 'Dr. SpongeBob SquarePants', 'doctor', 'dr.spongebob@example.com', 'Orthopedics'),
('dr.krabs',     '$2b$12$B83F6RVelKn914j9Aa981.KDbWtde1hWrOCgfPkS0cAf/2abwp636', 'Dr. Eugene Krabs',          'doctor', 'dr.krabs@example.com',     'Cardiology'),
('dr.star',      '$2b$12$B83F6RVelKn914j9Aa981.KDbWtde1hWrOCgfPkS0cAf/2abwp636', 'Dr. Patrick Star',          'doctor', 'dr.star@example.com',      'Neurology');

-- Weekly schedules (weekday: 1 = Monday ... 7 = Sunday)
-- Dr. SpongeBob: Mon-Thu 08:00-16:00
INSERT IGNORE INTO doctor_schedules (doctor_id, weekday, start_time, end_time, slot_minutes)
SELECT u.id, w.weekday, '08:00:00', '16:00:00', 30
FROM users u
JOIN (SELECT 1 AS weekday UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4) w
WHERE u.username = 'dr.spongebob';

-- Dr. Krabs: Mon-Fri 09:00-15:00
INSERT IGNORE INTO doctor_schedules (doctor_id, weekday, start_time, end_time, slot_minutes)
SELECT u.id, w.weekday, '09:00:00', '15:00:00', 30
FROM users u
JOIN (SELECT 1 AS weekday UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5) w
WHERE u.username = 'dr.krabs';

-- Dr. Patrick Star: Tue, Thu, Sat 10:00-16:00
INSERT IGNORE INTO doctor_schedules (doctor_id, weekday, start_time, end_time, slot_minutes)
SELECT u.id, w.weekday, '10:00:00', '16:00:00', 30
FROM users u
JOIN (SELECT 2 AS weekday UNION ALL SELECT 4 UNION ALL SELECT 6) w
WHERE u.username = 'dr.star';

-- ------------------------------------------------------------
-- DEPARTMENTS (6 featured cards + the rest, 26 in total)
-- ------------------------------------------------------------
INSERT IGNORE INTO departments (name, description, icon, is_featured, sort_order) VALUES
('Cardiology',      'Heart disease diagnosis, treatment and cardiac surgery. ECG, Echo, and stress testing available.',                  '/dept-cardiology.png',   TRUE, 1),
('Neurology',       'Expert care for neurological disorders including stroke, epilepsy, and movement disorders.',                        '/dept-neurology.png',    TRUE, 2),
('Orthopedics',     'Bone, joint and muscle care including sports injuries, fractures, and joint replacement surgery.',                  '/dept-orthopedics.png',  TRUE, 3),
('Pediatrics',      'Comprehensive child health care from newborns to adolescents with specialized pediatric specialists.',              '/dept-pediatrics.png',   TRUE, 4),
('Ophthalmology',   'Complete eye care services including LASIK, cataract surgery, and vision treatments.',                              '/dept-ophthalmology.png',TRUE, 5),
('General Medicine','Primary care, routine checkups, preventive health screenings and chronic disease management.',                      '/dept-general.png',      TRUE, 6),
('Dermatology',               'Skin, hair and nail conditions, acne and allergy treatment, and skin cancer screening.',        NULL, FALSE, 10),
('Gynecology',                'Women''s reproductive health, screenings, and family planning.',                                 NULL, FALSE, 11),
('Obstetrics',                'Prenatal care, delivery planning, and postnatal checkups for mothers and babies.',               NULL, FALSE, 12),
('Psychiatry',                'Mental health assessment, counseling referrals, and medication management.',                     NULL, FALSE, 13),
('Urology',                   'Kidney stones, urinary tract conditions, and men''s health.',                                    NULL, FALSE, 14),
('Nephrology',                'Kidney disease management, dialysis referrals, and blood pressure related kidney care.',         NULL, FALSE, 15),
('Gastroenterology',          'Digestive system disorders, liver care, and endoscopy referrals.',                               NULL, FALSE, 16),
('Pulmonology',               'Asthma, COPD, sleep apnea, and other lung and breathing conditions.',                            NULL, FALSE, 17),
('Endocrinology',             'Diabetes, thyroid disorders, and hormone related conditions.',                                   NULL, FALSE, 18),
('Oncology',                  'Cancer screening, diagnosis support, and coordination of treatment.',                            NULL, FALSE, 19),
('Rheumatology',              'Arthritis, lupus, gout, and other autoimmune and joint conditions.',                             NULL, FALSE, 20),
('ENT (Otolaryngology)',      'Ear, nose and throat conditions, hearing tests, and sinus care.',                                NULL, FALSE, 21),
('Dentistry',                 'Dental checkups, cleaning, fillings, and oral health advice.',                                   NULL, FALSE, 22),
('Radiology',                 'X-ray, ultrasound, and imaging services to support diagnosis.',                                  NULL, FALSE, 23),
('Emergency Medicine',        'Urgent care for sudden illness and injury that cannot wait.',                                    NULL, FALSE, 24),
('Physical Therapy',          'Rehabilitation after injury or surgery, and mobility and strength programs.',                    NULL, FALSE, 25),
('Nutrition and Dietetics',   'Personalized meal planning and diet guidance for weight and chronic conditions.',                NULL, FALSE, 26),
('Allergy and Immunology',    'Allergy testing and treatment, and immune system disorders.',                                    NULL, FALSE, 27),
('Hematology',                'Blood disorders such as anemia, clotting problems, and blood count monitoring.',                 NULL, FALSE, 28),
('Geriatrics',                'Healthcare for older adults, including memory, mobility, and medication reviews.',               NULL, FALSE, 29);