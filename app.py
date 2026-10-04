import os
import uuid
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

from scheduler.engine import generate_schedule, SchedulingError

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-this-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/tt_generator')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    faculty_id = db.Column(
        db.Integer,
        db.ForeignKey('faculty.id', ondelete='SET NULL')
    )

    class_id = db.Column(
        db.Integer,
        db.ForeignKey('classes.id', ondelete='SET NULL')
    )

    batch_id = db.Column(
        db.Integer,
        db.ForeignKey('lab_batches.id', ondelete='SET NULL')
    )
class Class(db.Model):
    __tablename__='classes'; id=db.Column(db.Integer,primary_key=True); class_name=db.Column(db.String(100),nullable=False); division=db.Column(db.String(20),nullable=False); strength=db.Column(db.Integer,nullable=False)
class Subject(db.Model):
    __tablename__='subjects'; id=db.Column(db.Integer,primary_key=True); subject_code=db.Column(db.String(50),unique=True,nullable=False); subject_name=db.Column(db.String(150),nullable=False); subject_type=db.Column(db.String(20),nullable=False); lectures_per_week=db.Column(db.Integer,nullable=False)
class Faculty(db.Model):
    __tablename__='faculty'; id=db.Column(db.Integer,primary_key=True); faculty_code=db.Column(db.String(50),unique=True,nullable=False); faculty_name=db.Column(db.String(150),nullable=False)
class Room(db.Model):
    __tablename__='rooms'; id=db.Column(db.Integer,primary_key=True); room_name=db.Column(db.String(100),unique=True,nullable=False); room_type=db.Column(db.String(20),nullable=False); capacity=db.Column(db.Integer,nullable=False)
class TimeSlot(db.Model):
    __tablename__='time_slots'; id=db.Column(db.Integer,primary_key=True); day=db.Column(db.String(20),nullable=False); start_time=db.Column(db.Time,nullable=False); end_time=db.Column(db.Time,nullable=False)
class LabBatch(db.Model):
    __tablename__='lab_batches'; id=db.Column(db.Integer,primary_key=True); class_id=db.Column(db.Integer,db.ForeignKey('classes.id'),nullable=False); batch_name=db.Column(db.String(50),nullable=False); student_count=db.Column(db.Integer,nullable=False)
class Timetable(db.Model):
    __tablename__='timetable'; id=db.Column(db.Integer,primary_key=True); session_id=db.Column(db.String(100),nullable=False); class_id=db.Column(db.Integer,db.ForeignKey('classes.id'),nullable=False); subject_id=db.Column(db.Integer,db.ForeignKey('subjects.id'),nullable=False); faculty_id=db.Column(db.Integer,db.ForeignKey('faculty.id')); room_id=db.Column(db.Integer,db.ForeignKey('rooms.id')); time_slot_id=db.Column(db.Integer,db.ForeignKey('time_slots.id'),nullable=False); batch_id=db.Column(db.Integer,db.ForeignKey('lab_batches.id'))
    class_ref=db.relationship('Class'); subject_ref=db.relationship('Subject'); faculty_ref=db.relationship('Faculty'); room_ref=db.relationship('Room'); time_slot_ref=db.relationship('TimeSlot'); batch_ref=db.relationship('LabBatch')
class FacultyAvailability(db.Model):
    __tablename__='faculty_availability'; id=db.Column(db.Integer,primary_key=True); faculty_id=db.Column(db.Integer,db.ForeignKey('faculty.id'),nullable=False); time_slot_id=db.Column(db.Integer,db.ForeignKey('time_slots.id'),nullable=False); available=db.Column(db.Boolean,nullable=False,default=True)
class TeachingAssignment(db.Model):
    __tablename__='teaching_assignments'; id=db.Column(db.Integer,primary_key=True); class_id=db.Column(db.Integer,db.ForeignKey('classes.id'),nullable=False); subject_id=db.Column(db.Integer,db.ForeignKey('subjects.id'),nullable=False); faculty_id=db.Column(db.Integer,db.ForeignKey('faculty.id'),nullable=False); periods_per_week=db.Column(db.Integer,nullable=False)
    class_ref=db.relationship('Class'); subject_ref=db.relationship('Subject'); faculty_ref=db.relationship('Faculty')

def required(role=None):
    def deco(fn):
        @wraps(fn)
        def inner(*args,**kwargs):
            if 'user_id' not in session: return redirect(url_for('login'))
            if role and session.get('role') != role: return redirect(url_for('dashboard'))
            return fn(*args,**kwargs)
        return inner
    return deco

def positive(value,label):
    n=int(value)
    if n<=0: raise ValueError(f'{label} must be greater than 0.')
    return n

def times(start,end):
    a=datetime.strptime(start,'%H:%M').time(); b=datetime.strptime(end,'%H:%M').time()
    if b<=a: raise ValueError('End time must be after start time.')
    return a,b

@app.route('/',methods=['GET','POST'])
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        user=User.query.filter_by(username=request.form.get('username','').strip()).first(); pw=request.form.get('password','')
        if not user: flash('Invalid username or password.','error'); return render_template('login.html')
        ok=check_password_hash(user.password,pw) if user.password.startswith(('pbkdf2:','scrypt:','argon2:')) else user.password==pw
        if not ok: flash('Invalid username or password.','error'); return render_template('login.html')
        if not user.password.startswith(('pbkdf2:','scrypt:','argon2:')): user.password=generate_password_hash(pw); db.session.commit()
        session.clear(); session.update(user_id=user.id,username=user.username,role=user.role)
        return redirect(url_for('dashboard'))
    return render_template('login.html')
@app.get('/logout')
def logout(): session.clear(); return redirect(url_for('login'))
@app.get('/dashboard')
@required()
def dashboard(): return redirect(url_for('admin_dashboard' if session['role']=='admin' else 'timetable'))
@app.get('/admin')
@required('admin')
def admin_dashboard(): return render_template('admin_dashboard.html')
@app.get('/users')
@required('admin')
def users():
    users = User.query.order_by(User.id).all()
    return render_template('users.html', users=users)
@app.route('/add-user', methods=['GET', 'POST'])
@required('admin')
def add_user():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', '')

        if not username or not password or role not in ['teacher', 'student']:
            flash('Please fill all required fields.', 'error')
            return render_template('add_user.html')

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('add_user.html')

        faculty_id = request.form.get('faculty_id') or None

        class_id = request.form.get('class_id') or None

        user = User(
            username=username,
            password=generate_password_hash(password),
            role=role,
            faculty_id=faculty_id,
            class_id=class_id
        )

        db.session.add(user)
        db.session.commit()

        flash('User created successfully.', 'success')
        return redirect(url_for('users'))
    return render_template(
        'add_user.html',
        faculty=Faculty.query.order_by(Faculty.faculty_name).all(),
        classes=Class.query.order_by(Class.id).all()

    )
@app.route('/change-password/<int:id>', methods=['GET', 'POST'])
@required('admin')
def change_password(id):
    user = db.get_or_404(User, id)

    if request.method == 'POST':
        new_password = request.form.get('password', '')

        if not new_password:
            flash('Password cannot be empty.', 'error')
            return render_template('change_password.html', user=user)

        user.password = generate_password_hash(new_password)
        db.session.commit()

        flash('Password changed successfully.', 'success')
        return redirect(url_for('users'))

    return render_template('change_password.html', user=user)
    
@app.get('/delete-user/<int:id>')
@required('admin')
def delete_user(id):
    user = db.get_or_404(User, id)

    if user.role == 'admin':
        flash('Admin users cannot be deleted.', 'error')
        return redirect(url_for('users'))

    try:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Could not delete user.', 'error')

    return redirect(url_for('users'))
# CRUD helper routes
@app.get('/classes')
@required('admin')
def classes(): return render_template('classes.html',classes=Class.query.order_by(Class.id).all())
@app.post('/add-class')
@required('admin')
def add_class():
    try: db.session.add(Class(class_name=request.form['class_name'].strip(),division=request.form['division'].strip(),strength=positive(request.form['strength'],'Strength'))); db.session.commit(); flash('Class added.','success')
    except Exception as e: db.session.rollback(); flash(str(e),'error')
    return redirect(url_for('classes'))
@app.route('/edit-class/<int:id>',methods=['GET','POST'])
@required('admin')
def edit_class(id):
    x=db.get_or_404(Class,id)
    if request.method=='POST':
        try: x.class_name=request.form['class_name'].strip(); x.division=request.form['division'].strip(); x.strength=positive(request.form['strength'],'Strength'); db.session.commit(); flash('Class updated.','success'); return redirect(url_for('classes'))
        except Exception as e: db.session.rollback(); flash(str(e),'error')
    return render_template('edit_class.html',class_data=x)
@app.get('/delete-class/<int:id>')
@required('admin')
def delete_class(id):
    try: db.session.delete(db.get_or_404(Class,id)); db.session.commit(); flash('Class deleted.','success')
    except Exception: db.session.rollback(); flash('Could not delete class; it may be referenced by other data.','error')
    return redirect(url_for('classes'))

@app.get('/subjects')
@required('admin')
def subjects(): return render_template('subjects.html',subjects=Subject.query.order_by(Subject.id).all())
@app.post('/add-subject')
@required('admin')
def add_subject():
    try:
        code=request.form['subject_code'].strip(); name=request.form['subject_name'].strip(); typ=request.form['subject_type']; lec=positive(request.form['lectures_per_week'],'Lectures per week')
        if Subject.query.filter_by(subject_code=code).first(): raise ValueError('Subject code already exists.')
        db.session.add(Subject(subject_code=code,subject_name=name,subject_type=typ,lectures_per_week=lec)); db.session.commit(); flash('Subject added.','success')
    except Exception as e: db.session.rollback(); flash(str(e),'error')
    return redirect(url_for('subjects'))
@app.route('/edit-subject/<int:id>',methods=['GET','POST'])
@required('admin')
def edit_subject(id):
    x=db.get_or_404(Subject,id)
    if request.method=='POST':
        try:
            code=request.form['subject_code'].strip()
            if Subject.query.filter(Subject.subject_code==code,Subject.id!=id).first(): raise ValueError('Subject code already exists.')
            x.subject_code=code; x.subject_name=request.form['subject_name'].strip(); x.subject_type=request.form['subject_type']; x.lectures_per_week=positive(request.form['lectures_per_week'],'Lectures per week'); db.session.commit(); flash('Subject updated.','success'); return redirect(url_for('subjects'))
        except Exception as e: db.session.rollback(); flash(str(e),'error')
    return render_template('edit_subject.html',subject=x)
@app.get('/delete-subject/<int:id>')
@required('admin')
def delete_subject(id):
    try: db.session.delete(db.get_or_404(Subject,id)); db.session.commit(); flash('Subject deleted.','success')
    except Exception: db.session.rollback(); flash('Could not delete subject; it may be referenced by timetable data.','error')
    return redirect(url_for('subjects'))

@app.get('/faculty')
@required('admin')
def faculty(): return render_template('faculty.html',faculty=Faculty.query.order_by(Faculty.id).all())
@app.post('/add-faculty')
@required('admin')
def add_faculty():
    try:
        code=request.form['faculty_code'].strip(); name=request.form['faculty_name'].strip()
        if Faculty.query.filter_by(faculty_code=code).first(): raise ValueError('Faculty code already exists.')
        db.session.add(Faculty(faculty_code=code,faculty_name=name)); db.session.commit(); flash('Faculty added.','success')
    except Exception as e: db.session.rollback(); flash(str(e),'error')
    return redirect(url_for('faculty'))
@app.route('/edit-faculty/<int:id>',methods=['GET','POST'])
@required('admin')
def edit_faculty(id):
    x=db.get_or_404(Faculty,id)
    if request.method=='POST':
        try:
            code=request.form['faculty_code'].strip()
            if Faculty.query.filter(Faculty.faculty_code==code,Faculty.id!=id).first(): raise ValueError('Faculty code already exists.')
            x.faculty_code=code; x.faculty_name=request.form['faculty_name'].strip(); db.session.commit(); flash('Faculty updated.','success'); return redirect(url_for('faculty'))
        except Exception as e: db.session.rollback(); flash(str(e),'error')
    return render_template('edit_faculty.html',faculty=x)
@app.get('/delete-faculty/<int:id>')
@required('admin')
def delete_faculty(id):
    try: db.session.delete(db.get_or_404(Faculty,id)); db.session.commit(); flash('Faculty deleted.','success')
    except Exception: db.session.rollback(); flash('Could not delete faculty; it may be referenced by scheduling data.','error')
    return redirect(url_for('faculty'))

@app.get('/rooms')
@required('admin')
def rooms(): return render_template('rooms.html',rooms=Room.query.order_by(Room.id).all())
@app.post('/add-room')
@required('admin')
def add_room():
    try:
        name=request.form['room_name'].strip(); typ=request.form['room_type']; cap=positive(request.form['capacity'],'Capacity')
        if Room.query.filter_by(room_name=name).first(): raise ValueError('Room name already exists.')
        db.session.add(Room(room_name=name,room_type=typ,capacity=cap)); db.session.commit(); flash('Room added.','success')
    except Exception as e: db.session.rollback(); flash(str(e),'error')
    return redirect(url_for('rooms'))
@app.route('/edit-room/<int:id>',methods=['GET','POST'])
@required('admin')
def edit_room(id):
    x=db.get_or_404(Room,id)
    if request.method=='POST':
        try:
            name=request.form['room_name'].strip()
            if Room.query.filter(Room.room_name==name,Room.id!=id).first(): raise ValueError('Room name already exists.')
            x.room_name=name; x.room_type=request.form['room_type']; x.capacity=positive(request.form['capacity'],'Capacity'); db.session.commit(); flash('Room updated.','success'); return redirect(url_for('rooms'))
        except Exception as e: db.session.rollback(); flash(str(e),'error')
    return render_template('edit_room.html',room=x)
@app.get('/delete-room/<int:id>')
@required('admin')
def delete_room(id):
    try: db.session.delete(db.get_or_404(Room,id)); db.session.commit(); flash('Room deleted.','success')
    except Exception: db.session.rollback(); flash('Could not delete room; it may be referenced by timetable data.','error')
    return redirect(url_for('rooms'))

@app.get('/time-slots')
@required('admin')
def time_slots(): return render_template('time_slots.html',time_slots=TimeSlot.query.order_by(TimeSlot.id).all())
@app.post('/add-time-slot')
@required('admin')
def add_time_slot():
    try:
        a,b=times(request.form['start_time'],request.form['end_time']); db.session.add(TimeSlot(day=request.form['day'],start_time=a,end_time=b)); db.session.commit(); flash('Time slot added.','success')
    except Exception as e: db.session.rollback(); flash(str(e),'error')
    return redirect(url_for('time_slots'))
@app.route('/edit-time-slot/<int:id>',methods=['GET','POST'])
@required('admin')
def edit_time_slot(id):
    x=db.get_or_404(TimeSlot,id)
    if request.method=='POST':
        try: a,b=times(request.form['start_time'],request.form['end_time']); x.day=request.form['day']; x.start_time=a; x.end_time=b; db.session.commit(); flash('Time slot updated.','success'); return redirect(url_for('time_slots'))
        except Exception as e: db.session.rollback(); flash(str(e),'error')
    return render_template('edit_time_slot.html',time_slot=x)
@app.get('/delete-time-slot/<int:id>')
@required('admin')
def delete_time_slot(id):
    try: db.session.delete(db.get_or_404(TimeSlot,id)); db.session.commit(); flash('Time slot deleted.','success')
    except Exception: db.session.rollback(); flash('Could not delete time slot; it may be referenced by timetable data.','error')
    return redirect(url_for('time_slots'))

@app.get('/assignments')
@required('admin')
def assignments():
    return render_template('assignments.html',assignments=TeachingAssignment.query.all(),classes=Class.query.all(),subjects=Subject.query.all(),faculty=Faculty.query.all())
@app.post('/add-assignment')
@required('admin')
def add_assignment():
    try:
        cid,sid,fid=map(int,(request.form['class_id'],request.form['subject_id'],request.form['faculty_id'])); p=positive(request.form['periods_per_week'],'Periods per week'); sub=db.get_or_404(Subject,sid)
        if p>sub.lectures_per_week: raise ValueError('Periods per week cannot exceed the subject setting.')
        if TeachingAssignment.query.filter_by(class_id=cid,subject_id=sid,faculty_id=fid).first(): raise ValueError('This teaching assignment already exists.')
        db.session.add(TeachingAssignment(class_id=cid,subject_id=sid,faculty_id=fid,periods_per_week=p)); db.session.commit(); flash('Teaching assignment added.','success')
    except Exception as e: db.session.rollback(); flash(str(e),'error')
    return redirect(url_for('assignments'))
@app.get('/delete-assignment/<int:id>')
@required('admin')
def delete_assignment(id): db.session.delete(db.get_or_404(TeachingAssignment,id)); db.session.commit(); return redirect(url_for('assignments'))

@app.get('/availability')
@required('admin')
def availability():
    return render_template('availability.html',faculty=Faculty.query.all(),time_slots=TimeSlot.query.all(),saved={(x.faculty_id,x.time_slot_id):x.available for x in FacultyAvailability.query.all()})
@app.post('/save-availability')
@required('admin')
def save_availability():
    try:
        FacultyAvailability.query.delete()
        for f in Faculty.query.all():
            for t in TimeSlot.query.all(): db.session.add(FacultyAvailability(faculty_id=f.id,time_slot_id=t.id,available=request.form.get(f'availability_{f.id}_{t.id}')=='on'))
        db.session.commit(); flash('Faculty availability saved.','success')
    except Exception as e: db.session.rollback(); flash(str(e),'error')
    return redirect(url_for('availability'))

@app.route('/generate-timetable',methods=['GET','POST'])
@required('admin')
def generate_timetable():
    if request.method=='POST':
        try:
            teaching=TeachingAssignment.query.all()
            if not teaching: raise SchedulingError('Add teaching assignments first.')
            slots=TimeSlot.query.all(); rooms=Room.query.all()
            if not slots: raise SchedulingError('Add time slots first.')
            if not rooms: raise SchedulingError('Add rooms/labs first.')
            Timetable.query.delete(); db.session.commit()
            placements=generate_schedule(teaching,Class.query.all(),Subject.query.all(),rooms,slots,LabBatch.query.all(),FacultyAvailability.query.all())
            sid=str(uuid.uuid4())
            for p in placements: db.session.add(Timetable(session_id=sid,class_id=p.class_id,subject_id=p.subject_id,faculty_id=p.faculty_id,room_id=p.room_id,time_slot_id=p.time_slot_id,batch_id=p.batch_id))
            db.session.commit(); flash(f'Timetable generated: {len(placements)} sessions.','success'); return redirect(url_for('timetable'))
        except Exception as e: db.session.rollback(); flash(str(e),'error')
    return render_template('generate_timetable.html',assignment_count=TeachingAssignment.query.count(),room_count=Room.query.count(),slot_count=TimeSlot.query.count())

@app.get('/timetable')
@required()
def timetable():

    query = Timetable.query

    # Teacher sees only their timetable
    if session['role'] == 'teacher':

        user = db.session.get(
            User,
            session['user_id']
        )

        if not user.faculty_id:
            flash(
                'No faculty is linked to this account.',
                'error'
            )
            return render_template(
                'timetable.html',
                timetable=[],
                classes=[]
            )

        query = query.filter_by(
            faculty_id=user.faculty_id
        )

    # Student sees only their class
    elif session['role'] == 'student':

        user = db.session.get(
            User,
            session['user_id']
        )

        if not user.class_id:
            flash(
                'No class is linked to this account.',
                'error'
            )
            return render_template(
                'timetable.html',
                timetable=[],
                classes=[]
            )

        query = query.filter_by(
            class_id=user.class_id
        )

        if user.batch_id:
            query = query.filter(
                (Timetable.batch_id == user.batch_id) |
                (Timetable.batch_id.is_(None))
            )

    # Admin can select SE / TE
    else:

        selected_class_id = request.args.get(
            'class_id',
            type=int
        )

        if selected_class_id:
            query = query.filter_by(
                class_id=selected_class_id
            )

    timetable_data = query.order_by(
        Timetable.class_id,
        Timetable.time_slot_id
    ).all()

    classes = Class.query.order_by(
        Class.id
    ).all()

    selected_class_id = request.args.get(
        'class_id',
        type=int
    )

    return render_template(
        'timetable.html',
        timetable=timetable_data,
        classes=classes,
        time_slots=time_slots,
        selected_class_id=selected_class_id
    )
@app.get('/db-test')
def db_test():
    try: db.session.execute(db.text('SELECT 1')); return 'Database connection successful.'
    except Exception as e: return f'Database connection failed: {e}',500

if __name__=='__main__': app.run(debug=True)
