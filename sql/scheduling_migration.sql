-- Backward-compatible migration for an EXISTING TT Generator database.
-- If you are doing a fresh install, use 01_schema.sql instead.

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

CREATE INDEX IF NOT EXISTS idx_faculty_availability_faculty ON faculty_availability(faculty_id);
CREATE INDEX IF NOT EXISTS idx_teaching_assignments_class ON teaching_assignments(class_id);
CREATE INDEX IF NOT EXISTS idx_teaching_assignments_faculty ON teaching_assignments(faculty_id);
