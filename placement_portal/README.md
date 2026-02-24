# Placement Portal Application

A comprehensive web-based placement management system designed to streamline campus recruitment activities for educational institutions. The portal connects three key stakeholders: Admin (Institute Placement Cell), Companies, and Students.

## 🎯 Project Overview

This placement portal enables:
- **Admins** to manage companies, students, and placement drives
- **Companies** to create placement drives and recruit students
- **Students** to apply for placement opportunities and track their applications

## ✨ Features

### Admin (Institute Placement Cell)
- ✅ Pre-existing superuser with full system access
- ✅ Approve or reject company registrations
- ✅ Approve or reject placement drives created by companies
- ✅ View and manage all students, companies, and placement drives
- ✅ Search students by name, ID, or contact information
- ✅ Search companies by name
- ✅ Blacklist or deactivate student and company accounts
- ✅ View comprehensive dashboard with statistics

### Company
- ✅ Register and create company profile
- ✅ Login only after admin approval
- ✅ Create placement drives (job postings)
- ✅ View student applications for their drives
- ✅ Shortlist students and update application status
- ✅ Manage company profile and placement drives

### Student
- ✅ Self-register and login
- ✅ Update profile and upload resume
- ✅ View approved placement drives
- ✅ Apply for placement drives
- ✅ View application status and placement history
- ✅ Track placement statistics on dashboard

## 🛠️ Tech Stack

### Backend
- **Flask 3.0.0** - Python web framework
- **Flask-SQLAlchemy 3.1.1** - ORM for database operations
- **SQLite** - Database (programmatically created)
- **Werkzeug 3.0.1** - Password hashing and security
- **Python-dotenv 1.0.0** - Environment variable management

### Frontend
- **Jinja2** - Templating engine
- **Bootstrap 5.3.0** - CSS framework (responsive design)
- **Font Awesome 6.4.0** - Icons
- **HTML5 & CSS3** - Structure and styling

### Security
- **PBKDF2-SHA256** - Password hashing algorithm
- **Session-based authentication** - Role-based access control
- **CSRF protection** - Form security

## 📋 Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git (for version control)

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Shivanshmanitiwari/placement_portal_project.git
cd placement_portal_project
```

### 2. Create Virtual Environment

```bash
cd placement_portal
python3 -m venv .venv
```

### 3. Activate Virtual Environment

**On macOS/Linux:**
```bash
source .venv/bin/activate
```

**On Windows:**
```bash
.venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure Environment Variables

The `.env` file contains:
```
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///placement_portal.db
DEBUG=True
```

### 6. Run the Application

```bash
python app.py
```

The application will:
- Create the database automatically
- Initialize tables (Admin, Student, Company, PlacementDrive, Application, Placement)
- Create default admin account
- Start the development server at `http://127.0.0.1:5000`

## 🔑 Default Credentials

### Admin Login
- **Username:** `admin`
- **Password:** `admin123`
- **Role:** Admin

⚠️ **Important:** Change the admin password after first login in production!

## 📁 Project Structure

```
placement_portal_project/
├── placement_portal/
│   ├── .venv/                      # Virtual environment
│   ├── static/                     # Static files (CSS, JS, uploads)
│   ├── templates/                  # HTML templates
│   │   ├── base.html              # Base template with navbar
│   │   ├── index.html             # Home page
│   │   ├── login.html             # Login page
│   │   ├── register_student.html  # Student registration
│   │   ├── register_company.html  # Company registration
│   │   ├── admin_dashboard.html   # Admin dashboard
│   │   ├── student_dashboard.html # Student dashboard
│   │   ├── company_dashboard.html # Company dashboard
│   │   ├── students.html          # View all students
│   │   ├── companies.html         # View all companies
│   │   └── placements.html        # View all placements
│   ├── app.py                     # Main application file
│   ├── config.py                  # Configuration settings
│   ├── requirements.txt           # Python dependencies
│   ├── .env                       # Environment variables
│   └── .gitignore                 # Git ignore rules
├── .git/                          # Git repository
└── README.md                      # Project documentation
```

## 🗄️ Database Schema

### Admin
- `id` (Primary Key)
- `username` (Unique)
- `password_hash`
- `email` (Unique)
- `created_at`

### Student
- `id` (Primary Key)
- `name`
- `email` (Unique)
- `password_hash`
- `phone`
- `department`
- `year`
- `cgpa`
- `resume_path`
- `is_active`
- `is_blacklisted`
- `created_at`

### Company
- `id` (Primary Key)
- `name`
- `password_hash`
- `description`
- `website`
- `contact_email` (Unique)
- `hr_contact`
- `is_approved`
- `is_active`
- `is_blacklisted`
- `created_at`

### PlacementDrive
- `id` (Primary Key)
- `company_id` (Foreign Key → Company)
- `job_title`
- `job_description`
- `eligibility_criteria`
- `min_cgpa`
- `application_deadline`
- `status` (Pending, Approved, Closed)
- `created_at`

### Application
- `id` (Primary Key)
- `student_id` (Foreign Key → Student)
- `drive_id` (Foreign Key → PlacementDrive)
- `application_date`
- `status` (Applied, Shortlisted, Selected, Rejected)
- **Unique Constraint:** (student_id, drive_id) - Prevents duplicate applications

### Placement
- `id` (Primary Key)
- `student_id` (Foreign Key → Student)
- `company_id` (Foreign Key → Company)
- `drive_id` (Foreign Key → PlacementDrive)
- `position`
- `package`
- `placement_date`
- `status`

## 🧪 Testing Flow

### 1. Test Admin Functionality
```
1. Visit http://127.0.0.1:5000
2. Click "Login"
3. Select Role: Admin
4. Username: admin
5. Password: admin123
6. Explore admin dashboard
```

### 2. Test Student Registration
```
1. Click "Register as Student"
2. Fill in details:
   - Name: John Doe
   - Email: john@example.com
   - Password: password123
   - Phone: 1234567890
   - Department: Computer Science
   - Year: 4
   - CGPA: 8.5
3. Submit registration
4. Login with student credentials
5. View student dashboard
```

### 3. Test Company Registration & Approval
```
1. Click "Register as Company"
2. Fill in details:
   - Company Name: TechCorp Inc.
   - Email: hr@techcorp.com
   - Password: company123
   - Website: https://techcorp.com
   - HR Contact: Jane Smith
3. Submit registration
4. Try to login (should show "pending approval")
5. Login as admin
6. Approve the company from admin dashboard
7. Logout and login as company
8. View company dashboard
```

## 🔒 Security Features

- ✅ Password hashing using PBKDF2-SHA256
- ✅ Role-based access control (Admin, Company, Student)
- ✅ Session management with Flask sessions
- ✅ Login required decorators for protected routes
- ✅ Approval workflow for companies
- ✅ Blacklist functionality for accounts
- ✅ Unique constraint preventing duplicate applications

## 📊 Core Requirements Implemented

### Authentication System
- ✅ Login system for admin, company, and student
- ✅ Registration for company and student only
- ✅ Pre-existing admin in database

### Admin Dashboard
- ✅ Display total students, companies, drives, applications
- ✅ Approve/reject company registrations
- ✅ Approve/reject placement drives
- ✅ View all placement drives and applications
- ✅ Search students by name, ID, contact
- ✅ Search companies by name
- ✅ Blacklist/deactivate accounts

### Company Dashboard
- ✅ Company registration and profile management
- ✅ Display company details and created drives
- ✅ Create placement drives (after admin approval)
- ✅ View student applications
- ✅ Update application status (Shortlist/Select/Reject)

### Student Dashboard
- ✅ Student self-registration and login
- ✅ Display approved placement drives
- ✅ Apply for placement drives
- ✅ View application status
- ✅ View placement history
- ✅ Profile editing capability

### Business Logic
- ✅ Prevent duplicate applications (unique constraint)
- ✅ Only approved companies can create drives
- ✅ Dynamic application status updates
- ✅ Only approved drives visible to students
- ✅ Complete application history maintained

## 🌐 Deployment Considerations

### Development Server (Current)
```bash
python app.py
```

### Production Deployment
For production, use a WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

**Production Checklist:**
- [ ] Change `SECRET_KEY` in `.env`
- [ ] Change admin password
- [ ] Set `DEBUG=False` in config
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS
- [ ] Configure proper CORS settings
- [ ] Set up backups
- [ ] Monitor application logs

## 🐛 Troubleshooting

### Issue: `python: command not found`
**Solution:** Use `python3` instead of `python`

### Issue: `ModuleNotFoundError: No module named 'flask'`
**Solution:** Activate virtual environment and install dependencies
```bash
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Issue: `TemplateNotFound: login.html`
**Solution:** Ensure all HTML files are in the `templates/` folder

### Issue: Database not created
**Solution:** The database is created automatically on first run. Check if `placement_portal.db` exists in the project folder.

### Issue: Password hashing error (scrypt)
**Solution:** Already fixed - using `pbkdf2:sha256` method compatible with Python 3.9+

## 📝 Future Enhancements

- [ ] API endpoints (REST API with Flask-RESTful)
- [ ] Resume upload functionality
- [ ] Email notifications for status updates
- [ ] Advanced search and filters
- [ ] Data export (CSV/PDF reports)
- [ ] Charts and analytics (ChartJS integration)
- [ ] Multi-file resume upload
- [ ] Interview scheduling system
- [ ] Feedback and rating system
- [ ] Mobile responsive improvements
- [ ] Two-factor authentication

## 📄 License

This project is created for educational purposes as part of a placement management system assignment.

## 👨‍💻 Author

**Shivansh Mani Tiwari**
- GitHub: [@Shivanshmanitiwari](https://github.com/Shivanshmanitiwari)
- Email: shivanshmanitiwari@gmail.com

## 🙏 Acknowledgments

- Flask documentation
- Bootstrap documentation
- Font Awesome icons
- IIT Madras BS Degree Program

---

**Note:** This is a development version. For production deployment, please follow security best practices and use appropriate production-grade servers and databases.

## 📞 Support

For issues, questions, or contributions:
1. Create an issue on GitHub
2. Submit a pull request
3. Contact the author

---

**Last Updated:** February 22, 2026
