from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from config import config
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config.from_object(config[os.getenv('FLASK_ENV', 'development')])

db = SQLAlchemy(app)

UPLOAD_FOLDER = 'static/resumes'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Database Models
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable= False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)    

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

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
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
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
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

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
@login_required(role='admin')
def students():
    all_students = Student.query.all()
    return render_template('students.html', students=all_students)


@app.route('/companies')
@login_required(role='admin')
def companies():
    all_companies = Company.query.all()
    return render_template('companies.html', companies=all_companies)


@app.route('/placements')
@login_required(role='admin')
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

@app.route('/company/create_drive', methods=['GET', 'POST'])
@login_required(role='company')
def create_drive():
    company = Company.query.get(session['user_id'])

    #Defensive check
    if not company.is_approved or company.is_blacklisted:
        flash('Your company is not authorized to create a drive.', 'error')
        return redirect(url_for('company_dashboard'))

    if request.method == 'POST':
        job_title = request.form.get('job_title', '').strip()
        job_description = request.form.get('job_description', '').strip()
        eligibility_criteria = request.form.get('eligibility_criteria', '').strip()
        min_cgpa_str = request.form.get('min_cgpa', '').strip()
        application_deadline = request.form.get('application_deadline', '').strip()

        if not job_title:
            flash('Job title is required.','error')
            return render_template('create_drive.html')

        if not application_deadline:
            flash('Application deadline is required.','error')
            return render_template('create_drive.html')
        # Parse deadline 
        try:
            deadline= datetime.strptime(application_deadline, '%Y-%m-%d').date()
            if deadline < datetime.today().date():
                flash('Application deadline cannot be in the past.','error')
                return render_template('create_drive.html')
        except ValueError:
            flash('Invalid date format. Use YYYY-MM-DD.', 'error')
            return render_template('create_drive.html')

        #parse min_cgpa
        min_cgpa = None 
        if min_cgpa_str:
            try:
                min_cgpa = float(min_cgpa_str)
                if min_cgpa < 0.0 or min_cgpa > 10.0:
                    flash('Minimum CGPA must be between 0.0 and 10.0.','error')
                    return render_template('create_drive.html')
            except ValueError:
                flash('Invalid CGPA format.', 'error')
                return render_template('create_drive.html')

        #Create drive 
        try:
            new_drive = PlacementDrive(
                company_id=company.id,
                job_title=job_title,
                job_description=job_description if job_description else None,
                eligibility_criteria=eligibility_criteria if eligibility_criteria else None,
                min_cgpa=min_cgpa,
                application_deadline=deadline,
                status='Pending'
            )
            
            
            db.session.add(new_drive)
            db.session.commit()
            flash('Placement drive created successfully! Waiting for admin approval.', 'success')
            return redirect(url_for('company_dashboard'))   
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating drive: {str(e)}', 'error')
            return render_template('create_drive.html')
    
    return render_template('create_drive.html')


@app.route('/company/drive/<int:drive_id>/applications')
@login_required(role='company')
def view_drive_applications(drive_id):
    company_id = session.get('user_id')
    drive = PlacementDrive.query.get_or_404(drive_id)
    
    # Verify ownership
    if drive.company_id != company_id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('company_dashboard'))
    
    applications = Application.query.filter_by(drive_id=drive_id).all()
    
    return render_template('drive_applications.html', drive=drive, applications=applications)


@app.route('/company/application/<int:app_id>/update_status', methods=['POST'])
@login_required(role='company')
def update_application_status(app_id):
    company_id = session.get('user_id')
    application = Application.query.get_or_404(app_id)
    
    # Verify ownership
    if application.placement_drive.company_id != company_id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('company_dashboard'))
    
    new_status = request.form.get('status')
    
    # Validate status
    valid_statuses = ['Applied', 'Shortlisted', 'Selected', 'Rejected']
    if new_status not in valid_statuses:
        flash('Invalid status.', 'error')
        return redirect(url_for('view_drive_applications', drive_id=application.drive_id))
    
    try:
        application.status = new_status
        db.session.commit()
        flash(f'Application status updated to {new_status}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating status.', 'error')
    
    return redirect(url_for('view_drive_applications', drive_id=application.drive_id))


@app.route('/company/drive/<int:drive_id>/edit', methods=['GET', 'POST'])
@login_required(role='company')
def edit_drive(drive_id):
    company_id = session.get('user_id')
    drive = PlacementDrive.query.get_or_404(drive_id)
    
    if drive.company_id != company_id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('company_dashboard'))
    
    if drive.status != 'Pending':
        flash('You can only edit drives that are pending approval.', 'error')
        return redirect(url_for('company_dashboard'))
    
    if request.method == 'POST':
        job_title = request.form.get('job_title', '').strip()
        job_description = request.form.get('job_description', '').strip()
        eligibility_criteria = request.form.get('eligibility_criteria', '').strip()
        min_cgpa_str = request.form.get('min_cgpa', '').strip()
        application_deadline = request.form.get('application_deadline', '').strip()
        
        if not job_title:
            flash('Job title is required.', 'error')
            return render_template('edit_drive.html', drive=drive)
        
        if not application_deadline:
            flash('Application deadline is required.', 'error')
            return render_template('edit_drive.html', drive=drive)
        
        try:
            deadline = datetime.strptime(application_deadline, '%Y-%m-%d').date()
            if deadline < datetime.today().date():
                flash('Application deadline cannot be in the past.', 'error')
                return render_template('edit_drive.html', drive=drive)
        except ValueError:
            flash('Invalid date format.', 'error')
            return render_template('edit_drive.html', drive=drive)
        
        min_cgpa = None
        if min_cgpa_str:
            try:
                min_cgpa = float(min_cgpa_str)
                if min_cgpa < 0.0 or min_cgpa > 10.0:
                    flash('Minimum CGPA must be between 0.0 and 10.0.', 'error')
                    return render_template('edit_drive.html', drive=drive)
            except ValueError:
                flash('Invalid CGPA format.', 'error')
                return render_template('edit_drive.html', drive=drive)
        
        try:
            drive.job_title = job_title
            drive.job_description = job_description if job_description else None
            drive.eligibility_criteria = eligibility_criteria if eligibility_criteria else None
            drive.min_cgpa = min_cgpa
            drive.application_deadline = deadline
            db.session.commit()
            flash('Drive updated successfully!', 'success')
            return redirect(url_for('company_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating drive.', 'error')
            return render_template('edit_drive.html', drive=drive)
    
    return render_template('edit_drive.html', drive=drive)


@app.route('/company/drive/<int:drive_id>/close', methods=['POST'])
@login_required(role='company')
def close_drive(drive_id):
    company_id = session.get('user_id')
    drive = PlacementDrive.query.get_or_404(drive_id)
    
    if drive.company_id != company_id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('company_dashboard'))
    
    if drive.status != 'Approved':
        flash('You can only close approved drives.', 'error')
        return redirect(url_for('company_dashboard'))
    
    try:
        drive.status = 'Closed'
        db.session.commit()
        flash('Drive closed successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error closing drive.', 'error')
    
    return redirect(url_for('company_dashboard'))


@app.route('/company/drive/<int:drive_id>/delete', methods=['POST'])
@login_required(role='company')
def delete_drive(drive_id):
    company_id = session.get('user_id')
    drive = PlacementDrive.query.get_or_404(drive_id)
    
    if drive.company_id != company_id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('company_dashboard'))
    
    if drive.status == 'Approved' and len(drive.applications) > 0:
        flash('Cannot delete a drive with existing applications. Close it instead.', 'error')
        return redirect(url_for('company_dashboard'))
    
    try:
        db.session.delete(drive)
        db.session.commit()
        flash('Drive deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting drive.', 'error')
    
    return redirect(url_for('company_dashboard'))


@app.route('/company/edit_profile', methods=['GET', 'POST'])
@login_required(role='company')
def edit_company_profile():
    company_id = session.get('user_id')
    company = Company.query.get_or_404(company_id)
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        contact_email = request.form.get('contact_email', '').strip()
        website = request.form.get('website', '').strip()
        hr_contact = request.form.get('hr_contact', '').strip()
        
        if not name:
            flash('Company name is required.', 'error')
            return render_template('edit_company_profile.html', company=company)
        
        if not contact_email:
            flash('Contact email is required.', 'error')
            return render_template('edit_company_profile.html', company=company)
        
        try:
            company.name = name
            company.contact_email = contact_email
            company.website = website if website else None
            company.hr_contact = hr_contact if hr_contact else None
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('company_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating profile.', 'error')
            return render_template('edit_company_profile.html', company=company)
    
    return render_template('edit_company_profile.html', company=company)


@app.route('/student/dashboard')
@login_required(role='student')
def student_dashboard():
    student_id = session.get('user_id')
    student = Student.query.get_or_404(student_id)

    # Get approved placement drives 
    approved_drives = PlacementDrive.query.filter_by(status='Approved').all()

    applications = Application.query.filter_by(student_id=student_id).all()
    return render_template('student_dashboard.html', student=student, applications=applications, approved_drives=approved_drives)


@app.route('/student/apply/<int:drive_id>', methods=['POST'])
@login_required(role='student')
def apply_to_drive(drive_id):
    student_id = session.get('user_id')
    student = Student.query.get_or_404(student_id)
    drive = PlacementDrive.query.get_or_404(drive_id)
    
    # Validation checks
    if student.is_blacklisted:
        flash('Your account is blacklisted and cannot apply.', 'error')
        return redirect(url_for('student_dashboard'))
    
    if drive.status != 'Approved':
        flash('This drive is not available for applications.', 'error')
        return redirect(url_for('student_dashboard'))
    
    if drive.application_deadline < datetime.utcnow().date():
        flash('Application deadline has passed.', 'error')
        return redirect(url_for('student_dashboard'))
    
    # Check CGPA eligibility
    if drive.min_cgpa and student.cgpa and student.cgpa < drive.min_cgpa:
        flash(f'You do not meet the minimum CGPA requirement of {drive.min_cgpa}.', 'error')
        return redirect(url_for('student_dashboard'))
    
    # Check for duplicate application
    existing = Application.query.filter_by(student_id=student_id, drive_id=drive_id).first()
    if existing:
        flash('You have already applied to this drive.', 'warning')
        return redirect(url_for('student_dashboard'))
    
    # Create application
    try:
        new_application = Application(
            student_id=student_id,
            drive_id=drive_id,
            status='Applied'
        )
        db.session.add(new_application)
        db.session.commit()
        flash('Application submitted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error submitting application. Please try again.', 'error')
    
    return redirect(url_for('student_dashboard'))


@app.route('/student/edit_profile', methods=['GET', 'POST'])
@login_required(role='student')
def edit_student_profile():
    student_id = session.get('user_id')
    student = Student.query.get_or_404(student_id)
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        year = request.form.get('year', '').strip()
        cgpa_str = request.form.get('cgpa', '').strip()
        
        # Validation
        if not name:
            flash('Name is required.', 'error')
            return render_template('edit_student_profile.html', student=student)
        
        # Parse CGPA
        cgpa = None
        if cgpa_str:
            try:
                cgpa = float(cgpa_str)
                if cgpa < 0.0 or cgpa > 10.0:
                    flash('CGPA must be between 0.0 and 10.0.', 'error')
                    return render_template('edit_student_profile.html', student=student)
            except ValueError:
                flash('Invalid CGPA format.', 'error')
                return render_template('edit_student_profile.html', student=student)
        
        try:
            student.name = name
            student.phone = phone if phone else None
            student.department = department if department else None
            student.year = year if year else None
            student.cgpa = cgpa
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('student_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating profile.', 'error')
            return render_template('edit_student_profile.html', student=student)
    
    return render_template('edit_student_profile.html', student=student)

@app.route('/student/upload_resume', methods=['POST'])
@login_required(role='student')
def upload_resume():
    student_id = session.get('user_id')
    student = Student.query.get_or_404(student_id)

    if 'resume' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('student_dashboard'))

    file = request.files['resume']

    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('student_dashboard'))

    if file and allowed_file(file.filename):
        filename = secure_filename(f"student_{student_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        try:
            if student.resume_path and os.path.exists(student.resume_path):
                os.remove(student.resume_path)
            file.save(file_path)
            student.resume_path = file_path
            db.session.commit()
            flash('Resume uploaded successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error uploading resume.', 'error')
    else:
        flash('Invalid file type. Allowed types: pdf, doc, docx.', 'error')
    return redirect(url_for('student_dashboard'))


@app.route('/student/drive/<int:drive_id>')
@login_required(role='student')
def view_drive_details(drive_id):
    student_id = session.get('user_id')
    student = Student.query.get_or_404(student_id)
    drive = PlacementDrive.query.get_or_404(drive_id)
    
    # Check if student already applied
    application = Application.query.filter_by(student_id=student_id, drive_id=drive_id).first()
    
    # Check eligibility
    eligible = True
    reasons = []
    
    if drive.status != 'Approved':
        eligible = False
        reasons.append('Drive is not currently open for applications')
    
    if drive.application_deadline < datetime.utcnow().date():
        eligible = False
        reasons.append('Application deadline has passed')
    
    if drive.min_cgpa and student.cgpa and student.cgpa < drive.min_cgpa:
        eligible = False
        reasons.append(f'Your CGPA ({student.cgpa}) is below the requirement ({drive.min_cgpa})')
    
    if student.is_blacklisted:
        eligible = False
        reasons.append('Your account is blacklisted')
    
    return render_template('drive_details.html', 
                         drive=drive, 
                         application=application,
                         eligible=eligible,
                         reasons=reasons)


@app.route('/student/placement_history')
@login_required(role='student')
def student_placement_history():
    student_id = session.get('user_id')
    placements = Placement.query.filter_by(student_id=student_id).all()
    return render_template('placement_history.html', placements=placements)


# Company Approval
@app.route('/admin/approve_company/<int:company_id>', methods=['POST'])
@login_required(role='admin')
def approve_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.is_approved = True
    try:
        db.session.commit()
        flash(f'Company "{company.name}" has been approved successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error approving company: {str(e)}', 'error')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/reject_company/<int:company_id>', methods=['POST'])
@login_required(role='admin')
def reject_company(company_id):
    company = Company.query.get_or_404(company_id)
    try:
        db.session.delete(company)
        db.session.commit()
        flash(f'Company "{company.name}" has been rejected and removed.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error rejecting company: {str(e)}', 'error')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/blacklist_company/<int:company_id>', methods=['POST'])
@login_required(role='admin')
def blacklist_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.is_blacklisted = not company.is_blacklisted
    status = "blacklisted" if company.is_blacklisted else "unblacklisted"
    try:
        db.session.commit()
        flash(f'Company "{company.name}" has been {status}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('companies'))


# Drive Approval  
@app.route('/admin/approve_drive/<int:drive_id>', methods=['POST'])
@login_required(role='admin')
def approve_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = 'Approved'
    try:
        db.session.commit()
        flash(f'Placement drive "{drive.job_title}" has been approved!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error approving drive: {str(e)}', 'error')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/reject_drive/<int:drive_id>', methods=['POST'])
@login_required(role='admin')
def reject_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = 'Rejected'
    try:
        db.session.commit()
        flash(f'Placement drive "{drive.job_title}" has been rejected.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Error rejecting drive: {str(e)}', 'error')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/blacklist_student/<int:student_id>', methods=['POST'])
@login_required(role='admin')
def blacklist_student(student_id):
    student = Student.query.get_or_404(student_id)
    student.is_blacklisted = not student.is_blacklisted
    status = "blacklisted" if student.is_blacklisted else "unblacklisted"
    try:
        db.session.commit()
        flash(f'Student "{student.name}" has been {status}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('students'))

# search functionality
@app.route('/admin/search_students', methods=['GET'])
@login_required(role='admin')
def search_students():
    query = request.args.get('query', '').strip()
    if query:
        students = Student.query.filter(
            (Student.name.ilike(f'%{query}%')) |
            (Student.email.ilike(f'%{query}%')) |
            (Student.phone.ilike(f'%{query}%')) if query else True
        ).all()
    else:
        students = Student.query.all()
    return render_template('students.html', students=students, query=query)


@app.route('/admin/search_companies', methods=['GET'])
@login_required(role='admin')
def search_companies():
    query = request.args.get('query', '').strip()
    if query:
        companies = Company.query.filter(
            Company.name.ilike(f'%{query}%')
        ).all()
    else:
        companies = Company.query.all()
    return render_template('companies.html', companies=companies, query=query)


@app.route('/admin/student/<int:student_id>/edit', methods=['GET', 'POST'])
@login_required(role='admin')
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        year = request.form.get('year', '').strip()
        cgpa_str = request.form.get('cgpa', '').strip()
        
        if not name or not email:
            flash('Name and email are required.', 'error')
            return render_template('edit_student.html', student=student)
        
        cgpa = None
        if cgpa_str:
            try:
                cgpa = float(cgpa_str)
                if cgpa < 0.0 or cgpa > 10.0:
                    flash('CGPA must be between 0.0 and 10.0.', 'error')
                    return render_template('edit_student.html', student=student)
            except ValueError:
                flash('Invalid CGPA format.', 'error')
                return render_template('edit_student.html', student=student)
        
        try:
            student.name = name
            student.email = email
            student.phone = phone if phone else None
            student.department = department if department else None
            student.year = int(year) if year else None
            student.cgpa = cgpa
            db.session.commit()
            flash('Student updated successfully!', 'success')
            return redirect(url_for('students'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating student.', 'error')
            return render_template('edit_student.html', student=student)
    
    return render_template('edit_student.html', student=student)


@app.route('/admin/student/<int:student_id>/delete', methods=['POST'])
@login_required(role='admin')
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    
    try:
        Application.query.filter_by(student_id=student_id).delete()
        Placement.query.filter_by(student_id=student_id).delete()
        db.session.delete(student)
        db.session.commit()
        flash('Student deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting student.', 'error')
    
    return redirect(url_for('students'))


@app.route('/admin/student/<int:student_id>/toggle_active', methods=['POST'])
@login_required(role='admin')
def toggle_student_active(student_id):
    student = Student.query.get_or_404(student_id)
    
    try:
        student.is_active = not student.is_active
        db.session.commit()
        status = 'activated' if student.is_active else 'deactivated'
        flash(f'Student {status} successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating student status.', 'error')
    
    return redirect(url_for('students'))


@app.route('/admin/company/<int:company_id>/edit', methods=['GET', 'POST'])
@login_required(role='admin')
def edit_company(company_id):
    company = Company.query.get_or_404(company_id)
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        contact_email = request.form.get('contact_email', '').strip()
        website = request.form.get('website', '').strip()
        hr_contact = request.form.get('hr_contact', '').strip()
        
        if not name or not contact_email:
            flash('Company name and contact email are required.', 'error')
            return render_template('edit_company.html', company=company)
        
        try:
            company.name = name
            company.contact_email = contact_email
            company.website = website if website else None
            company.hr_contact = hr_contact if hr_contact else None
            db.session.commit()
            flash('Company updated successfully!', 'success')
            return redirect(url_for('companies'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating company.', 'error')
            return render_template('edit_company.html', company=company)
    
    return render_template('edit_company.html', company=company)


@app.route('/admin/company/<int:company_id>/delete', methods=['POST'])
@login_required(role='admin')
def delete_company(company_id):
    company = Company.query.get_or_404(company_id)
    
    try:
        for drive in company.placement_drives:
            Application.query.filter_by(drive_id=drive.id).delete()
            db.session.delete(drive)
        db.session.delete(company)
        db.session.commit()
        flash('Company deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting company.', 'error')
    
    return redirect(url_for('companies'))


@app.route('/admin/company/<int:company_id>/toggle_active', methods=['POST'])
@login_required(role='admin')
def toggle_company_active(company_id):
    company = Company.query.get_or_404(company_id)
    
    try:
        company.is_active = not company.is_active
        db.session.commit()
        status = 'activated' if company.is_active else 'deactivated'
        flash(f'Company {status} successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating company status.', 'error')
    
    return redirect(url_for('companies'))


@app.route('/admin/applications')
@login_required(role='admin')
def view_all_applications():
    all_applications = Application.query.order_by(Application.application_date.desc()).all()
    return render_template('all_applications.html', applications=all_applications)


@app.route('/admin/create_placement/<int:app_id>', methods=['POST'])
@login_required(role='admin')
def create_placement_record(app_id):
    application = Application.query.get_or_404(app_id)
    
    if application.status != 'Selected':
        flash('Can only create placement for selected applications.', 'error')
        return redirect(url_for('view_all_applications'))
    
    existing = Placement.query.filter_by(
        student_id=application.student_id,
        company_id=application.placement_drive.company_id
    ).first()
    
    if existing:
        flash('Placement record already exists for this student-company pair.', 'warning')
        return redirect(url_for('view_all_applications'))
    
    try:
        placement = Placement(
            student_id=application.student_id,
            company_id=application.placement_drive.company_id,
            drive_id=application.drive_id,
            position=application.placement_drive.job_title,
            placement_date=datetime.utcnow().date(),
            status='Placed'
        )
        db.session.add(placement)
        db.session.commit()
        flash('Placement record created successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error creating placement record.', 'error')
    
    return redirect(url_for('view_all_applications'))


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
