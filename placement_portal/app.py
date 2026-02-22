from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from config import config
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.config.from_object(config[os.getenv('FLASK_ENV', 'development')])

db = SQLAlchemy(app)


# Database Models
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable= False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)    

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    phone = db.Column(db.String(20))
    department = db.Column(db.String(50))
    year = db.Column(db.Integer)
    cgpa = db.Column(db.Float)
    resume_path = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    is_blacklisted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<Student {self.name}>'

    


class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)   
    description = db.Column(db.Text)
    website = db.Column(db.String(200))
    contact_email = db.Column(db.String(120), unique=True, nullable=False)
    hr_contact = db.Column(db.String(100))
    is_approved = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    is_blacklisted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)  


    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Company {self.name}>'


class PlacementDrive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    job_title = db.Column(db.String(100), nullable=False)
    job_description = db.Column(db.Text)
    eligibility_criteria = db.Column(db.Text)
    min_cgpa = db.Column(db.Float)
    application_deadline = db.Column(db.Date)
    status = db.Column(db.String(20), default='Pending')  # e.g., 'Open', 'Closed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # relationships
    company = db.relationship('Company', backref='placement_drives')

    def __repr__(self):
        return f'<PlacementDrive {self.job_title}>'


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drive.id'), nullable=False)
    
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Applied')  # e.g., 'Applied', 'Shortlisted', 'Rejected', 'Placed'
    # relationships
    student = db.relationship('Student', backref='applications')
    placement_drive = db.relationship('PlacementDrive', backref='applications')

    __table_args__ = (db.UniqueConstraint('student_id', 'drive_id', name='_student_drive_uc'),)

    def __repr__(self):
        return f'<Application Student {self.student_id} for Drive {self.drive_id}>'    


class Placement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drive.id'), nullable=False)
    position = db.Column(db.String(100))
    package = db.Column(db.Float)
    placement_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='Pending')  # e.g., 'Placed', 'Rejected', 'Pending'
    
    # relationships
    student = db.relationship('Student', backref='placements')
    company = db.relationship('Company', backref='placements')
    drive = db.relationship('PlacementDrive', backref='placements')

    def __repr__(self):
        return f'<Placement {self.position} at {self.company_id}>'


# helper function to check login

def login_required(role = None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please login first', 'error')
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                flash('Unauthorized access', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        
        return wrapper
    return decorator

# Authentiation Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        email = request.form.get('email')
        password = request.form.get('password')

        if role == 'admin':
            user = Admin.query.filter_by(username=email).first()

        elif role == 'student':
            user = Student.query.filter_by(email=email).first()
        elif role == 'company':
            user = Company.query.filter_by(contact_email=email).first()
        else:
            flash('Invalid role selected', 'error')
            return redirect(url_for('login'))
        
        if user and user.check_password(password):
        # Additionally check for company and student
            if role == 'company' and not user.is_approved:
                flash('Your company registration is pending approval', 'warning')
                return redirect(url_for('login'))
            if role == 'company' and user.is_blacklisted:
                flash('Your account has been blacklisted', 'error')
                return redirect(url_for('login'))
            if role == 'student' and user.is_blacklisted:
                flash('Your account has been blacklisted', 'error')
                return redirect(url_for('login'))
            
            
            session['user_id'] = user.id
            session['role'] = role
            session['name'] = user.name if role in ['student','company'] else user.username            
            flash('Login successful', 'success')    
   

            if role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif role == 'company':
                return redirect(url_for('company_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid email or password', 'error')
            
    return render_template('login.html')

# Routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/students')
def students():
    all_students = Student.query.all()
    return render_template('students.html', students=all_students)


@app.route('/companies')
def companies():
    all_companies = Company.query.all()
    return render_template('companies.html', companies=all_companies)


@app.route('/placements')
def placements():
    all_placements = Placement.query.all()
    return render_template('placements.html', placements=all_placements)


@app.route('/register/student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        department = request.form.get('department')
        year = request.form.get('year')
        cgpa = request.form.get('cgpa')

        # agar phale se student exist karta hai to error message show karo
        if Student.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register_student'))

        new_student = Student(
            name=name,
            email=email,
            phone=phone,
            department=department,
            year=int(year) if year else None,
            cgpa=float(cgpa) if cgpa else None
        )
        new_student.set_password(password)

        try:
            db.session.add(new_student)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding student: {str(e)}', 'error')

    return render_template('register_student.html')


@app.route('/register/company', methods=['GET', 'POST'])
def register_company():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        description = request.form.get('description')
        website = request.form.get('website')
        hr_contact = request.form.get('hr_contact')

        if Company.query.filter_by(contact_email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register_company'))

        new_company = Company(
            name=name,
            contact_email=email,
            description=description,
            website=website,
            hr_contact=hr_contact
        )
        new_company.set_password(password)

        try:
            db.session.add(new_company)
            db.session.commit()
            flash('Registered successfully! Wait for admin approval.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding company: {str(e)}', 'error')

    return render_template('register_company.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@login_required(role='admin')
def admin_dashboard():
    total_students = Student.query.count()
    total_companies = Company.query.count()
    total_drives = PlacementDrive.query.count()
    total_applications = Application.query.count()


    pending_companies = Company.query.filter_by(is_approved=False, is_blacklisted=False).all()
    pending_drives = PlacementDrive.query.filter_by(status='Pending').all()

    return render_template('admin_dashboard.html', 
                           total_students=total_students,
                           total_companies=total_companies,
                           total_drives=total_drives,
                           total_applications=total_applications,
                           pending_companies=pending_companies,
                           pending_drives=pending_drives)

@app.route('/company/dashboard')
@login_required(role='company')
def company_dashboard():
    company_id = session.get('user_id')
    company = Company.query.get_or_404(company_id)
    drives = PlacementDrive.query.filter_by(company_id=company_id).all()
    return render_template('company_dashboard.html', company=company, drives=drives)

@app.route('/student/dashboard')
@login_required(role='student')
def student_dashboard():
    student_id = session.get('user_id')
    student = Student.query.get_or_404(student_id)

    # Get approved placement drives 
    approved_drives = PlacementDrive.query.filter_by(status='Approved').all()

    applications = Application.query.filter_by(student_id=student_id).all()
    return render_template('student_dashboard.html', student=student, applications=applications, approved_drives=approved_drives)





// ...existing code...

def init_db():
    """Initialize database with default admin"""
    with app.app_context():
        db.create_all()
        
        # Create default admin if not exists
        if not Admin.query.filter_by(username='admin').first():
            admin = Admin(username='admin', email='admin@placement.com')
            admin.set_password('admin123')  # Change this password!
            db.session.add(admin)
            db.session.commit()
            print("Default admin created - username: admin, password: admin123")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
