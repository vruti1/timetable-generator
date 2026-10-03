# TT Generator — Teammate Setup Guide

Follow these steps in order. Do not skip the database steps.

## PART 1 — PostgreSQL

### Step 1: Open pgAdmin

Open pgAdmin 4 and connect to your PostgreSQL server.

### Step 2: Create the project database

Open **Query Tool** while connected to the default `postgres` database.

Open:

`sql/00_create_database.sql`

Run it.

Expected result: a database named `tt_generator` is created.

If `tt_generator` already exists, skip this step.

### Step 3: Connect to tt_generator

In pgAdmin, refresh the Databases list and open:

`tt_generator`

Then open its Query Tool.

### Step 4: Create every table

Open:

`sql/01_schema.sql`

Run the complete file.

Do not manually create the tables one by one.

### Step 5: Insert demo data

Open:

`sql/02_seed_demo.sql`

Run the complete file.

This creates:
- 3 login users
- 3 classes
- 4 subjects
- 3 faculty members
- 6 rooms/labs
- 30 time slots
- 9 lab batches
- teaching assignments
- faculty availability rows

### Step 6: Verify

Open:

`sql/03_verify_demo.sql`

Run it.

If rows are returned, the database setup is complete.

## PART 2 — Python / Flask

### Step 7: Open the project folder

Extract the ZIP and open the extracted `TT_Generator_Final` folder in VS Code.

### Step 8: Open terminal

In VS Code:

**Terminal → New Terminal**

Make sure the terminal is inside the project folder.

### Step 9: Create virtual environment

```bash
python -m venv venv
```

### Step 10: Activate it on Windows

Command Prompt:

```cmd
venv\\Scripts\\activate
```

PowerShell:

```powershell
.\\venv\\Scripts\\Activate.ps1
```

### Step 11: Install packages

```bash
pip install -r requirements.txt
```

### Step 12: Configure PostgreSQL password

Open `app.py` and find the default `DATABASE_URL`.

Change:

```text
YOUR_PASSWORD
```

to the actual PostgreSQL password.

For example:

```text
postgresql+psycopg2://postgres:MyPassword@localhost:5432/tt_generator
```

Alternatively set the `DATABASE_URL` environment variable as described in `README.md`.

### Step 13: Start the project

```bash
python app.py
```

### Step 14: Open the website

Go to:

`http://127.0.0.1:5000`

### Step 15: Test the database connection

Go to:

`http://127.0.0.1:5000/db-test`

Expected:

`Database connection successful.`

## PART 3 — Login test

Use:

**Admin**
- Username: `admin`
- Password: `admin123`

**Faculty**
- Username: `teacher`
- Password: `teacher123`

**Student**
- Username: `student`
- Password: `student123`

The app changes the demo password to a hash after successful login.

## PART 4 — Generate timetable

Log in as Admin.

Check these pages in this order:

1. Manage Classes
2. Manage Subjects
3. Manage Faculty
4. Manage Rooms/Labs
5. Manage Time Slots
6. Teaching Assignments
7. Faculty Availability
8. Generate Timetable
9. View Timetable

The demo data is already inserted, so you can test generation immediately.

## PART 5 — If generation fails

Read the red error message on the Generate Timetable page.

Common causes:
- too few time slots
- no suitable room
- room capacity too small
- faculty unavailable for too many slots
- missing teaching assignment
- too many periods requested for the available schedule

For the included demo data, leave faculty availability checked and do not delete the demo rooms or time slots before the first test.

## PART 6 — Existing older database

If you are not starting fresh and already have the earlier database, do not run the fresh schema script blindly.

Run only:

`sql/scheduling_migration.sql`

This adds the scheduling-support tables needed by the complete Flask project.

## Final test checklist

- [ ] PostgreSQL installed
- [ ] `tt_generator` database exists
- [ ] All tables created
- [ ] Demo data inserted
- [ ] Python virtual environment created
- [ ] Requirements installed
- [ ] PostgreSQL password configured
- [ ] `/db-test` works
- [ ] Admin login works
- [ ] Faculty login works
- [ ] Student login works
- [ ] Teaching assignments visible
- [ ] Faculty availability visible
- [ ] Timetable generated
- [ ] Timetable displayed
