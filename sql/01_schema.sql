-- TT Generator - complete fresh database schema
-- Run this after connecting to the tt_generator database.

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'teacher', 'student'))
);

CREATE TABLE IF NOT EXISTS classes (
    id SERIAL PRIMARY KEY,
    class_name VARCHAR(100) NOT NULL,
    division VARCHAR(20) NOT NULL,
    strength INTEGER NOT NULL CHECK (strength > 0),
    UNIQUE (class_name, division)
);

CREATE TABLE IF NOT EXISTS subjects (
    id SERIAL PRIMARY KEY,
    subject_code VARCHAR(50) NOT NULL UNIQUE,
    subject_name VARCHAR(150) NOT NULL,
    subject_type VARCHAR(20) NOT NULL CHECK (subject_type IN ('Theory', 'Lab')),
    lectures_per_week INTEGER NOT NULL CHECK (lectures_per_week > 0)
);

CREATE TABLE IF NOT EXISTS faculty (
    id SERIAL PRIMARY KEY,
    faculty_code VARCHAR(50) NOT NULL UNIQUE,
    faculty_name VARCHAR(150) NOT NULL
);

CREATE TABLE IF NOT EXISTS rooms (
    id SERIAL PRIMARY KEY,
    room_name VARCHAR(100) NOT NULL UNIQUE,
    room_type VARCHAR(20) NOT NULL CHECK (room_type IN ('Classroom', 'Lab')),
    capacity INTEGER NOT NULL CHECK (capacity > 0)
);

CREATE TABLE IF NOT EXISTS time_slots (
    id SERIAL PRIMARY KEY,
    day VARCHAR(20) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    CHECK (end_time > start_time),
    UNIQUE (day, start_time, end_time)
);

CREATE TABLE IF NOT EXISTS lab_batches (
    id SERIAL PRIMARY KEY,
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    batch_name VARCHAR(50) NOT NULL,
    student_count INTEGER NOT NULL CHECK (student_count > 0),
    UNIQUE (class_id, batch_name)
);

CREATE TABLE IF NOT EXISTS timetable (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    faculty_id INTEGER REFERENCES faculty(id) ON DELETE SET NULL,
    room_id INTEGER REFERENCES rooms(id) ON DELETE SET NULL,
    time_slot_id INTEGER NOT NULL REFERENCES time_slots(id) ON DELETE CASCADE,
    batch_id INTEGER REFERENCES lab_batches(id) ON DELETE SET NULL
);

-- Scheduling support tables.
CREATE TABLE IF NOT EXISTS faculty_availability (
    id SERIAL PRIMARY KEY,
    faculty_id INTEGER NOT NULL REFERENCES faculty(id) ON DELETE CASCADE,
    time_slot_id INTEGER NOT NULL REFERENCES time_slots(id) ON DELETE CASCADE,
    available BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (faculty_id, time_slot_id)
);

CREATE TABLE IF NOT EXISTS teaching_assignments (
    id SERIAL PRIMARY KEY,
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    faculty_id INTEGER NOT NULL REFERENCES faculty(id) ON DELETE RESTRICT,
    periods_per_week INTEGER NOT NULL CHECK (periods_per_week > 0),
    UNIQUE (class_id, subject_id, faculty_id)
);

CREATE INDEX IF NOT EXISTS idx_timetable_class ON timetable(class_id);
CREATE INDEX IF NOT EXISTS idx_timetable_time_slot ON timetable(time_slot_id);
CREATE INDEX IF NOT EXISTS idx_timetable_faculty ON timetable(faculty_id);
CREATE INDEX IF NOT EXISTS idx_faculty_availability_faculty ON faculty_availability(faculty_id);
CREATE INDEX IF NOT EXISTS idx_teaching_assignments_class ON teaching_assignments(class_id);
CREATE INDEX IF NOT EXISTS idx_teaching_assignments_faculty ON teaching_assignments(faculty_id);
