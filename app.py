import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import json

# Create Flask app
app = Flask(__name__)
app.config.from_object('config.Config')

# Ensure instance folder exists
os.makedirs('instance', exist_ok=True)
os.makedirs('static/uploads', exist_ok=True)
os.makedirs('static/pdfs', exist_ok=True)
os.makedirs('static/css', exist_ok=True)

# Initialize database
db = SQLAlchemy(app)


# Global template variables (Fix for current year in base.html)
@app.context_processor
def inject_global_data():
    return {"current_year": datetime.now().year}


# ==================== MODELS ====================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'teacher', 'student'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roll_no = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(15))
    class_name = db.Column(db.String(50))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    results = db.relationship('Result', backref='student', lazy=True, cascade='all, delete-orphan')


class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    max_marks = db.Column(db.Integer, nullable=False, default=100)

    # Fix: Needed for manage_subjects.html + delete_subject check
    results = db.relationship('Result', backref='subject_ref', lazy=True, cascade='all, delete-orphan')


class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    marks_obtained = db.Column(db.Integer, nullable=False)
    exam_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    term = db.Column(db.String(20))  # e.g., "Mid-Term", "Final"

    # Relationship
    subject = db.relationship('Subject')


# ==================== DECORATORS ====================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*required_roles):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            user = User.query.get(session['user_id'])
            if user.role not in required_roles:
                flash('Unauthorized access! You do not have permission to view this page.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ==================== HELPER FUNCTIONS ====================

def get_student_from_roll(roll_no):
    """Get student object from roll number"""
    return Student.query.filter_by(roll_no=roll_no).first()


def calculate_percentage(results):
    """Calculate total and percentage from results"""
    if not results:
        return 0, 0, 0

    total_obtained = sum([r.marks_obtained for r in results])
    total_max = sum([r.subject.max_marks for r in results])

    if total_max == 0:
        return total_obtained, total_max, 0

    percentage = (total_obtained / total_max) * 100
    return total_obtained, total_max, percentage


# ==================== AUTHENTICATION ROUTES ====================

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    # If already logged in, redirect to dashboard
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        role = request.form.get('role')
        username = request.form.get('username').strip()

        if role == 'student':
            # Student login with Roll No and DOB
            dob_str = request.form.get('dob')

            if not dob_str:
                flash('Please enter Date of Birth', 'danger')
                return render_template('login.html')

            try:
                dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format. Use YYYY-MM-DD', 'danger')
                return render_template('login.html')

            # Find student
            student = Student.query.filter_by(roll_no=username).first()

            if student and student.date_of_birth == dob:
                # Create or get user account for student
                user = User.query.filter_by(username=username, role='student').first()
                if not user:
                    user = User(username=username, role='student')
                    # Use DOB as password for student
                    user.set_password(dob_str)
                    db.session.add(user)
                    db.session.commit()

                session['user_id'] = user.id
                session['role'] = user.role
                session['username'] = user.username
                session['student_id'] = student.id
                flash(f'Welcome, {student.full_name}!', 'success')
                return redirect(url_for('student_dashboard'))
            else:
                flash('Invalid Roll Number or Date of Birth', 'danger')

        else:
            # Admin/Teacher login
            password = request.form.get('password')

            user = User.query.filter_by(username=username, role=role).first()

            if user and user.check_password(password):
                session['user_id'] = user.id
                session['role'] = user.role
                session['username'] = user.username
                flash(f'Welcome back, {user.username}!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))


# ==================== DASHBOARD ROUTES ====================

@app.route('/dashboard')
@login_required
def dashboard():
    role = session.get('role')

    if role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif role == 'teacher':
        return redirect(url_for('teacher_dashboard'))
    elif role == 'student':
        return redirect(url_for('student_dashboard'))

    return redirect(url_for('login'))


@app.route('/admin/dashboard')
@role_required('admin')
def admin_dashboard():
    # Statistics
    total_students = Student.query.count()
    total_results = Result.query.count()
    total_subjects = Subject.query.count()

    # Recent students
    recent_students = Student.query.order_by(Student.created_at.desc()).limit(5).all()

    # Recent results
    recent_results = Result.query.order_by(Result.id.desc()).limit(5).all()

    return render_template(
        'dashboard_admin.html',
        total_students=total_students,
        total_results=total_results,
        total_subjects=total_subjects,
        recent_students=recent_students,
        recent_results=recent_results
    )


@app.route('/teacher/dashboard')
@role_required('teacher')
def teacher_dashboard():
    # Teacher can see all students and results
    total_students = Student.query.count()
    results_added = Result.query.count()

    # Get subjects
    subjects = Subject.query.all()

    # Get recent results added by teacher
    recent_results = Result.query.order_by(Result.id.desc()).limit(10).all()

    return render_template(
        'dashboard_teacher.html',
        total_students=total_students,
        results_added=results_added,
        subjects=subjects,
        recent_results=recent_results
    )


@app.route('/student/dashboard')
@role_required('student')
def student_dashboard():
    student_id = session.get('student_id')
    student = Student.query.get_or_404(student_id)

    # Get all results for the student
    results = Result.query.filter_by(student_id=student_id).all()

    # Calculate statistics
    total_obtained, total_max, percentage = calculate_percentage(results)

    # Get term-wise results
    terms = {}
    for result in results:
        term = result.term or 'General'
        if term not in terms:
            terms[term] = []
        terms[term].append(result)

    return render_template(
        'dashboard_student.html',
        student=student,
        results=results,
        terms=terms,
        total_obtained=total_obtained,
        total_max=total_max,
        percentage=round(percentage, 2)
    )


# ==================== STUDENT MANAGEMENT ROUTES ====================

@app.route('/admin/students')
@role_required('admin')
def manage_students():
    students = Student.query.order_by(Student.roll_no).all()
    return render_template('manage_students.html', students=students)


@app.route('/admin/students/add', methods=['GET', 'POST'])
@role_required('admin')
def add_student():
    if request.method == 'POST':
        roll_no = request.form.get('roll_no').strip().upper()
        full_name = request.form.get('full_name').strip()
        dob_str = request.form.get('dob')
        email = request.form.get('email').strip()
        phone = request.form.get('phone').strip()
        class_name = request.form.get('class_name').strip()
        address = request.form.get('address').strip()

        # Validation
        errors = []

        if not roll_no:
            errors.append('Roll number is required')
        if not full_name:
            errors.append('Full name is required')
        if not dob_str:
            errors.append('Date of birth is required')

        # Check if roll number already exists
        existing_student = Student.query.filter_by(roll_no=roll_no).first()
        if existing_student:
            errors.append(f'Roll number {roll_no} already exists')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template(
                'add_edit_student.html',
                roll_no=roll_no,
                full_name=full_name,
                email=email,
                phone=phone,
                class_name=class_name,
                address=address
            )

        try:
            dob = datetime.strptime(dob_str, '%Y-%m-%d').date()

            # Create new student
            student = Student(
                roll_no=roll_no,
                full_name=full_name,
                date_of_birth=dob,
                email=email if email else None,
                phone=phone if phone else None,
                class_name=class_name if class_name else None,
                address=address if address else None
            )

            db.session.add(student)
            db.session.commit()

            flash(f'Student {full_name} added successfully!', 'success')
            return redirect(url_for('manage_students'))

        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD', 'danger')
            return render_template(
                'add_edit_student.html',
                roll_no=roll_no,
                full_name=full_name,
                email=email,
                phone=phone,
                class_name=class_name,
                address=address
            )

    return render_template('add_edit_student.html')


@app.route('/admin/students/<int:student_id>/edit', methods=['GET', 'POST'])
@role_required('admin')
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)

    if request.method == 'POST':
        full_name = request.form.get('full_name').strip()
        email = request.form.get('email').strip()
        phone = request.form.get('phone').strip()
        class_name = request.form.get('class_name').strip()
        address = request.form.get('address').strip()

        if not full_name:
            flash('Full name is required', 'danger')
            return render_template('add_edit_student.html', student=student)

        # Update student
        student.full_name = full_name
        student.email = email if email else None
        student.phone = phone if phone else None
        student.class_name = class_name if class_name else None
        student.address = address if address else None

        db.session.commit()

        flash(f'Student {full_name} updated successfully!', 'success')
        return redirect(url_for('manage_students'))

    return render_template('add_edit_student.html', student=student)


@app.route('/admin/students/<int:student_id>/delete')
@role_required('admin')
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)

    # Also delete associated user account if exists
    user = User.query.filter_by(username=student.roll_no, role='student').first()
    if user:
        db.session.delete(user)

    db.session.delete(student)
    db.session.commit()

    flash(f'Student {student.full_name} deleted successfully!', 'success')
    return redirect(url_for('manage_students'))


@app.route('/admin/students/search')
@role_required('admin')
def search_students():
    query = request.args.get('q', '').strip()

    if not query:
        return redirect(url_for('manage_students'))

    # Search in roll number, name, or class
    students = Student.query.filter(
        (Student.roll_no.ilike(f'%{query}%')) |
        (Student.full_name.ilike(f'%{query}%')) |
        (Student.class_name.ilike(f'%{query}%'))
    ).order_by(Student.roll_no).all()

    return render_template('manage_students.html', students=students, search_query=query)


# ==================== RESULT MANAGEMENT ROUTES ====================

@app.route('/results')
@role_required('admin', 'teacher')
def manage_results():
    # Get all results with student and subject info
    results = Result.query.join(Student).join(Subject).order_by(Result.id.desc()).all()

    # Get all students and subjects for the form
    students = Student.query.order_by(Student.roll_no).all()
    subjects = Subject.query.order_by(Subject.code).all()

    # Get unique terms
    terms = db.session.query(Result.term).distinct().all()
    terms = [t[0] for t in terms if t[0]]

    return render_template(
        'manage_results.html',
        results=results,
        students=students,
        subjects=subjects,
        terms=terms
    )


@app.route('/results/add', methods=['POST'])
@role_required('admin', 'teacher')
def add_result():
    roll_no = request.form.get('roll_no').strip().upper()
    subject_code = request.form.get('subject_code').strip()
    marks_obtained = request.form.get('marks_obtained')
    term = request.form.get('term').strip()

    # Validation
    errors = []

    if not roll_no:
        errors.append('Roll number is required')
    if not subject_code:
        errors.append('Subject code is required')
    if not marks_obtained:
        errors.append('Marks obtained is required')
    if not term:
        errors.append('Term is required')

    # Find student and subject
    student = Student.query.filter_by(roll_no=roll_no).first()
    subject = Subject.query.filter_by(code=subject_code).first()

    if not student:
        errors.append(f'Student with roll number {roll_no} not found')
    if not subject:
        errors.append(f'Subject with code {subject_code} not found')

    try:
        marks = int(marks_obtained)
        if marks < 0:
            errors.append('Marks cannot be negative')
        if subject and marks > subject.max_marks:
            errors.append(f'Marks cannot exceed {subject.max_marks} for {subject.name}')
    except ValueError:
        errors.append('Marks must be a number')

    if errors:
        for error in errors:
            flash(error, 'danger')
        return redirect(url_for('manage_results'))

    # Check if result already exists for this student, subject, and term
    existing_result = Result.query.filter_by(
        student_id=student.id,
        subject_id=subject.id,
        term=term
    ).first()

    if existing_result:
        # Update existing result
        existing_result.marks_obtained = marks
        db.session.commit()
        flash(f'Result updated for {student.full_name} in {subject.name}', 'success')
    else:
        # Create new result
        result = Result(
            student_id=student.id,
            subject_id=subject.id,
            marks_obtained=marks,
            term=term
        )
        db.session.add(result)
        db.session.commit()
        flash(f'Result added for {student.full_name} in {subject.name}', 'success')

    return redirect(url_for('manage_results'))


@app.route('/results/<int:result_id>/edit', methods=['POST'])
@role_required('admin', 'teacher')
def edit_result(result_id):
    result = Result.query.get_or_404(result_id)

    marks_obtained = request.form.get('marks_obtained')

    if not marks_obtained:
        flash('Marks obtained is required', 'danger')
        return redirect(url_for('manage_results'))

    try:
        marks = int(marks_obtained)
        if marks < 0:
            flash('Marks cannot be negative', 'danger')
            return redirect(url_for('manage_results'))

        if marks > result.subject.max_marks:
            flash(f'Marks cannot exceed {result.subject.max_marks} for {result.subject.name}', 'danger')
            return redirect(url_for('manage_results'))

        result.marks_obtained = marks
        db.session.commit()

        flash('Result updated successfully!', 'success')

    except ValueError:
        flash('Marks must be a number', 'danger')

    return redirect(url_for('manage_results'))


@app.route('/results/<int:result_id>/delete')
@role_required('admin', 'teacher')
def delete_result(result_id):
    result = Result.query.get_or_404(result_id)

    student_name = result.student.full_name
    subject_name = result.subject.name

    db.session.delete(result)
    db.session.commit()

    flash(f'Result for {student_name} in {subject_name} deleted successfully!', 'success')
    return redirect(url_for('manage_results'))


# ==================== SEARCH AND VIEW ROUTES ====================

@app.route('/search')
@login_required
def search_results():
    roll_no = request.args.get('roll_no', '').strip().upper()

    if not roll_no:
        flash('Please enter a roll number to search', 'warning')
        return render_template('view_result.html')

    # Check authorization
    if session['role'] == 'student':
        # Students can only search their own results
        student = Student.query.get(session['student_id'])
        if student.roll_no != roll_no:
            flash('You can only view your own results', 'danger')
            return redirect(url_for('student_dashboard'))

    # Find student
    student = Student.query.filter_by(roll_no=roll_no).first()

    if not student:
        flash(f'No student found with roll number {roll_no}', 'warning')
        return render_template('view_result.html', roll_no=roll_no)

    # Get results
    results = Result.query.filter_by(student_id=student.id).all()

    # Calculate statistics
    total_obtained, total_max, percentage = calculate_percentage(results)

    # Group by term
    terms = {}
    for result in results:
        term = result.term or 'General'
        if term not in terms:
            terms[term] = []
        terms[term].append(result)

    return render_template(
        'view_result.html',
        student=student,
        results=results,
        terms=terms,
        total_obtained=total_obtained,
        total_max=total_max,
        percentage=round(percentage, 2),
        roll_no=roll_no
    )


# ==================== PDF EXPORT ROUTES ====================

@app.route('/download/result/<roll_no>')
@login_required
def download_result(roll_no):
    # Authorization check
    if session['role'] == 'student':
        student = Student.query.get(session['student_id'])
        if student.roll_no != roll_no:
            flash('You can only download your own result', 'danger')
            return redirect(url_for('student_dashboard'))

    # Find student
    student = Student.query.filter_by(roll_no=roll_no).first()

    if not student:
        flash(f'No student found with roll number {roll_no}', 'danger')
        return redirect(url_for('search_results'))

    # Get results
    results = Result.query.filter_by(student_id=student.id).all()

    if not results:
        flash('No results found for this student', 'warning')
        return redirect(url_for('search_results', roll_no=roll_no))

    # Import PDF generator
    from utils.pdf_generator import generate_result_pdf

    try:
        # Generate PDF
        pdf_path = generate_result_pdf(student, results)

        # Send file for download
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f'Result_{student.roll_no}_{datetime.now().strftime("%Y%m%d")}.pdf',
            mimetype='application/pdf'
        )
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'danger')
        return redirect(url_for('search_results', roll_no=roll_no))


# ==================== SUBJECT MANAGEMENT ROUTES ====================

@app.route('/admin/subjects')
@role_required('admin')
def manage_subjects():
    subjects = Subject.query.order_by(Subject.code).all()
    return render_template('manage_subjects.html', subjects=subjects)


@app.route('/admin/subjects/add', methods=['POST'])
@role_required('admin')
def add_subject():
    code = request.form.get('code').strip().upper()
    name = request.form.get('name').strip()
    max_marks = request.form.get('max_marks', 100)

    if not code or not name:
        flash('Subject code and name are required', 'danger')
        return redirect(url_for('manage_subjects'))

    # Check if subject already exists
    existing = Subject.query.filter_by(code=code).first()
    if existing:
        flash(f'Subject with code {code} already exists', 'danger')
        return redirect(url_for('manage_subjects'))

    try:
        max_marks_int = int(max_marks)
        if max_marks_int <= 0:
            flash('Maximum marks must be positive', 'danger')
            return redirect(url_for('manage_subjects'))
    except ValueError:
        flash('Maximum marks must be a number', 'danger')
        return redirect(url_for('manage_subjects'))

    subject = Subject(
        code=code,
        name=name,
        max_marks=max_marks_int
    )

    db.session.add(subject)
    db.session.commit()

    flash(f'Subject {name} added successfully!', 'success')
    return redirect(url_for('manage_subjects'))


@app.route('/admin/subjects/<int:subject_id>/delete')
@role_required('admin')
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)

    # Check if subject has results
    if subject.results:
        flash('Cannot delete subject with existing results. Delete results first.', 'danger')
        return redirect(url_for('manage_subjects'))

    db.session.delete(subject)
    db.session.commit()

    flash(f'Subject {subject.name} deleted successfully!', 'success')
    return redirect(url_for('manage_subjects'))


# ==================== ADMIN SETUP ROUTES ====================

@app.route('/admin/setup')
@role_required('admin')
def admin_setup():
    # Get statistics for setup page
    admin_count = User.query.filter_by(role='admin').count()
    teacher_count = User.query.filter_by(role='teacher').count()
    student_count = Student.query.count()
    subject_count = Subject.query.count()

    return render_template(
        'admin_setup.html',
        admin_count=admin_count,
        teacher_count=teacher_count,
        student_count=student_count,
        subject_count=subject_count
    )


@app.route('/admin/add-user', methods=['POST'])
@role_required('admin')
def add_user():
    username = request.form.get('username').strip()
    password = request.form.get('password')
    role = request.form.get('role')

    if not username or not password or not role:
        flash('All fields are required', 'danger')
        return redirect(url_for('admin_setup'))

    # Check if user already exists
    existing = User.query.filter_by(username=username).first()
    if existing:
        flash(f'User {username} already exists', 'danger')
        return redirect(url_for('admin_setup'))

    # Create new user
    user = User(username=username, role=role)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    flash(f'{role.title()} {username} added successfully!', 'success')
    return redirect(url_for('admin_setup'))


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(403)
def forbidden(e):
    flash('Access forbidden. You do not have permission to access this page.', 'danger')
    return redirect(url_for('dashboard'))


@app.errorhandler(500)
def internal_server_error(e):
    flash('An internal server error occurred. Please try again later.', 'danger')
    return redirect(url_for('dashboard'))


# ==================== INITIALIZATION ====================

def create_default_data():
    """Create default admin user and subjects if not exists"""
    with app.app_context():
        # Create tables
        db.create_all()

        # Create admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            print("Created default admin user: admin / admin123")

        # Create teacher user if not exists
        teacher = User.query.filter_by(username='teacher').first()
        if not teacher:
            teacher = User(username='teacher', role='teacher')
            teacher.set_password('teacher123')
            db.session.add(teacher)
            print("Created default teacher user: teacher / teacher123")

        # Create default subjects if not exist
        default_subjects = [
            {'code': 'MATH101', 'name': 'Mathematics', 'max_marks': 100},
            {'code': 'PHY101', 'name': 'Physics', 'max_marks': 100},
            {'code': 'CHEM101', 'name': 'Chemistry', 'max_marks': 100},
            {'code': 'ENG101', 'name': 'English', 'max_marks': 100},
            {'code': 'CS101', 'name': 'Computer Science', 'max_marks': 100},
            {'code': 'BIO101', 'name': 'Biology', 'max_marks': 100},
        ]

        for subj_data in default_subjects:
            subject = Subject.query.filter_by(code=subj_data['code']).first()
            if not subject:
                subject = Subject(**subj_data)
                db.session.add(subject)

        db.session.commit()
        print("Database initialized with default data.")


if __name__ == '__main__':
    create_default_data()
    app.run(debug=True, port=5000)
