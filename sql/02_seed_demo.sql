-- TT Generator - demo data
-- Run this after 01_schema.sql while connected to tt_generator.
-- Passwords are intentionally plain for the first login. The Flask app automatically hashes
-- each password after that user logs in successfully.

INSERT INTO users (username, password, role) VALUES
('admin', 'admin123', 'admin'),
('teacher', 'teacher123', 'teacher'),
('student', 'student123', 'student')
ON CONFLICT (username) DO NOTHING;

INSERT INTO classes (class_name, division, strength) VALUES
('SE IoT', 'A', 65),
('TE IoT', 'A', 65),
('BE IoT', 'A', 65)
ON CONFLICT (class_name, division) DO NOTHING;

INSERT INTO subjects (subject_code, subject_name, subject_type, lectures_per_week) VALUES
('IOT501', 'Internet of Things', 'Theory', 3),
('IOT502', 'Computer Networks', 'Theory', 3),
('IOT503', 'IoT Lab', 'Lab', 2),
('IOT504', 'Database Management', 'Theory', 3)
ON CONFLICT (subject_code) DO NOTHING;

INSERT INTO faculty (faculty_code, faculty_name) VALUES
('F001', 'Prof. Sharma'),
('F002', 'Prof. Patil'),
('F003', 'Prof. Khan')
ON CONFLICT (faculty_code) DO NOTHING;

-- Lab capacity is 65 in this demo because the current scheduler treats one lab
-- timetable entry as one class session. Batch records are still included for
-- future batch-aware scheduling.
INSERT INTO rooms (room_name, room_type, capacity) VALUES
('R101', 'Classroom', 65),
('R102', 'Classroom', 65),
('R201', 'Classroom', 65),
('LAB1', 'Lab', 65),
('LAB2', 'Lab', 65),
('LAB3', 'Lab', 65)
ON CONFLICT (room_name) DO NOTHING;

INSERT INTO time_slots (day, start_time, end_time) VALUES
('Monday', '09:00', '10:00'),
('Monday', '10:00', '11:00'),
('Monday', '11:00', '12:00'),
('Monday', '13:00', '14:00'),
('Monday', '14:00', '15:00'),
('Monday', '15:00', '16:00'),
('Tuesday', '09:00', '10:00'),
('Tuesday', '10:00', '11:00'),
('Tuesday', '11:00', '12:00'),
('Tuesday', '13:00', '14:00'),
('Tuesday', '14:00', '15:00'),
('Tuesday', '15:00', '16:00'),
('Wednesday', '09:00', '10:00'),
('Wednesday', '10:00', '11:00'),
('Wednesday', '11:00', '12:00'),
('Wednesday', '13:00', '14:00'),
('Wednesday', '14:00', '15:00'),
('Wednesday', '15:00', '16:00'),
('Thursday', '09:00', '10:00'),
('Thursday', '10:00', '11:00'),
('Thursday', '11:00', '12:00'),
('Thursday', '13:00', '14:00'),
('Thursday', '14:00', '15:00'),
('Thursday', '15:00', '16:00'),
('Friday', '09:00', '10:00'),
('Friday', '10:00', '11:00'),
('Friday', '11:00', '12:00'),
('Friday', '13:00', '14:00'),
('Friday', '14:00', '15:00'),
('Friday', '15:00', '16:00')
ON CONFLICT (day, start_time, end_time) DO NOTHING;

-- Three demo lab batches for each class.
INSERT INTO lab_batches (class_id, batch_name, student_count)
SELECT c.id, b.batch_name, b.student_count
FROM classes c
CROSS JOIN (VALUES ('A1',22), ('A2',22), ('A3',21)) AS b(batch_name, student_count)
ON CONFLICT (class_id, batch_name) DO NOTHING;

-- Each class gets all four subjects. Faculty is distributed so the demo is schedulable.
INSERT INTO teaching_assignments (class_id, subject_id, faculty_id, periods_per_week)
SELECT c.id, s.id, f.id, s.lectures_per_week
FROM classes c
JOIN subjects s ON TRUE
JOIN faculty f ON f.faculty_code = CASE s.subject_code
    WHEN 'IOT501' THEN 'F001'
    WHEN 'IOT502' THEN 'F002'
    WHEN 'IOT503' THEN 'F003'
    WHEN 'IOT504' THEN 'F001'
END
ON CONFLICT (class_id, subject_id, faculty_id) DO NOTHING;

-- Start with every faculty member available in every demo slot.
INSERT INTO faculty_availability (faculty_id, time_slot_id, available)
SELECT f.id, t.id, TRUE
FROM faculty f CROSS JOIN time_slots t
ON CONFLICT (faculty_id, time_slot_id) DO NOTHING;
