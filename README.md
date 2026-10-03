# TT Generator 

Automated College Timetable Generator using **Python + Flask + SQLAlchemy + PostgreSQL + HTML/CSS**.

## 1. ROLES

### ADMIN
- Manage Classes
- Manage Subjects
- Manage Faculty
- Manage Rooms/Labs
- Manage Time Slots
- Generate Timetable
- View Timetable

### FACULTY
- View Timetable

### STUDENT
- View Timetable


## 2. Project flow

Login → Enter/manage data → Teaching assignments → Faculty availability → Generate timetable → Hard constraint checking → Backtracking → Save to PostgreSQL → View timetable.

## 3. Fresh setup — exact order

### Step A — Install software

Install:
1. PostgreSQL
2. pgAdmin 4
3. Python 3.11+ recommended
4. VS Code or another editor

PostgreSQL normally uses port `5432`.

### Step B — Create the database

Open pgAdmin and connect to your PostgreSQL server.

Open the Query Tool on the default `postgres` database and run:

`sql/00_create_database.sql`

This creates:

`tt_generator`

If the database already exists, skip this file.

### Step C — Create all tables

In pgAdmin, connect to the **tt_generator** database.

Run:

`sql/01_schema.sql`

This creates:
- users
- classes
- subjects
- faculty
- rooms
- time_slots
- lab_batches
- timetable
- faculty_availability
- teaching_assignments

### Step D — Insert demo data

Still connected to **tt_generator**, run:

`sql/02_seed_demo.sql`

This inserts demo users, classes, subjects, faculty, rooms, time slots, lab batches, teaching assignments and faculty availability.

### Step E — Verify the database

Run:

`sql/03_verify_demo.sql`

You should see rows in all major tables.

### Step F — Install Python packages

Open a terminal in the project folder:

```bash
python -m venv venv
```

Windows:

```bash
venv\\Scripts\\activate
```

Then:

```bash
pip install -r requirements.txt
```

### Step G — Set the PostgreSQL connection

The app reads `DATABASE_URL` from the environment.

Example Windows Command Prompt:

```cmd
set DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/tt_generator
set SECRET_KEY=change-this-secret
```

Or edit the default connection string in `app.py` for local development.

Important: replace `YOUR_PASSWORD` with the password you chose for PostgreSQL.

### Step H — Start Flask

```bash
python app.py
```

Open:

`http://127.0.0.1:5000`

Database test:

`http://127.0.0.1:5000/db-test`

It should say:

`Database connection successful.`

## 4. Demo login accounts

| Username | Password | Role |
|---|---|---|
| admin | admin123 | ADMIN |
| teacher | teacher123 | FACULTY |
| student | student123 | STUDENT |

The first successful login converts the demo plaintext password into a secure password hash in PostgreSQL.

## 5. How to generate the demo timetable

1. Log in as `admin`.
2. Open **Manage Classes** and confirm classes exist.
3. Open **Manage Subjects** and confirm subjects exist.
4. Open **Manage Faculty** and confirm faculty exists.
5. Open **Manage Rooms/Labs** and confirm rooms exist.
6. Open **Manage Time Slots** and confirm slots exist.
7. Open **Teaching Assignments** and confirm class + subject + faculty mappings exist.
8. Open **Faculty Availability** and keep the demo availability checked.
9. Open **Generate Timetable**.
10. Click the generate button.
11. Open **View Timetable**.

## 6. Hard constraints enforced by the scheduler

- A faculty member cannot teach two sessions in the same time slot.
- A class cannot have two sessions in the same time slot.
- A room cannot host two sessions in the same time slot.
- An unavailable faculty member cannot be assigned.
- Lab subjects use Lab rooms.
- Theory subjects use Classroom rooms.
- Room capacity must be at least the class strength.
- Every teaching-assignment period is scheduled.
- If the current choices lead to a dead end, the scheduler backtracks and tries another choice.

## 7. Why teaching_assignments exists

The original basic tables contain classes, subjects and faculty separately. They do not contain the relationship saying which faculty teaches which subject to which class.

`teaching_assignments` supplies that missing scheduling information.

Example:

`SE IoT + Internet of Things + Prof. Sharma + 3 periods/week`

## 8. Why faculty_availability exists

The scheduler needs to know when a faculty member can teach. `faculty_availability` stores one availability value for each faculty/time-slot combination.

## 9. Existing database migration

If your teammate already has the older TT Generator database, do NOT delete it.

Instead run:

`sql/scheduling_migration.sql`

It adds only the two scheduling-support tables and their indexes.

## 10. Important lab note

The current scheduler represents one lab timetable entry as one class session and therefore requires a lab room whose capacity can accommodate the whole class. The included demo uses lab capacity `65` so the demo is immediately schedulable.

`lab_batches` is included in the database because batch-aware lab scheduling can be added as a later improvement without redesigning the whole project.

## 11. Reset only generated timetable data

If you want to generate a fresh timetable while keeping all input data:

Run:

`sql/04_reset_generated_timetable.sql`

Normally the Flask Generate Timetable page already replaces the previous generated timetable.

## 12. Important development rule

Do not add `db.create_all()` to this project. The PostgreSQL tables are created by the SQL scripts so the database structure stays explicit and reproducible.

## 13. Project structure

```text
TT_Generator_Final/
│
├── app.py
├── requirements.txt
├── .env.example
├── README.md
├── SETUP_GUIDE.md
├── PROJECT_STRUCTURE.txt
│
├── scheduler/
│   ├── __init__.py
│   └── engine.py
│
├── sql/
│   ├── 00_create_database.sql
│   ├── 01_schema.sql
│   ├── 02_seed_demo.sql
│   ├── 03_verify_demo.sql
│   ├── 04_reset_generated_timetable.sql
│   └── scheduling_migration.sql
│
├── templates/
└── static/
```

## 14. Viva explanation

PostgreSQL stores the input data and the generated timetable. Flask handles the web application and database operations. The scheduling engine reads the data, checks hard constraints, uses backtracking when necessary, and returns a conflict-free timetable when the supplied data permits one.
