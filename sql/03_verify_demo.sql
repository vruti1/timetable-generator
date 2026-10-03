-- Optional verification queries. Run while connected to tt_generator.
SELECT 'users' AS table_name, COUNT(*) AS rows FROM users
UNION ALL SELECT 'classes', COUNT(*) FROM classes
UNION ALL SELECT 'subjects', COUNT(*) FROM subjects
UNION ALL SELECT 'faculty', COUNT(*) FROM faculty
UNION ALL SELECT 'rooms', COUNT(*) FROM rooms
UNION ALL SELECT 'time_slots', COUNT(*) FROM time_slots
UNION ALL SELECT 'lab_batches', COUNT(*) FROM lab_batches
UNION ALL SELECT 'teaching_assignments', COUNT(*) FROM teaching_assignments
UNION ALL SELECT 'faculty_availability', COUNT(*) FROM faculty_availability;

SELECT c.class_name, c.division, s.subject_code, s.subject_name,
       f.faculty_code, f.faculty_name, a.periods_per_week
FROM teaching_assignments a
JOIN classes c ON c.id = a.class_id
JOIN subjects s ON s.id = a.subject_id
JOIN faculty f ON f.id = a.faculty_id
ORDER BY c.id, s.id;
