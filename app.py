import json
import os
import sqlite3
from datetime import datetime

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = 'lms-auto-machine-secret-key'
DB_PATH = os.path.join(os.path.dirname(__file__), 'lms.db')


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_user_by_id(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return dict(user) if user else None


def get_course_instructor(course):
    instructor = get_user_by_id(course['instructor_id'])
    return instructor['name'] if instructor else 'Unknown Instructor'


def init_db():
    conn = get_db_connection()
    conn.executescript(
        '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student',
            bio TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            instructor_id INTEGER NOT NULL,
            status TEXT DEFAULT 'published',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(instructor_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            video_url TEXT,
            duration TEXT,
            content TEXT,
            FOREIGN KEY(course_id) REFERENCES courses(id)
        );

        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            progress INTEGER DEFAULT 0,
            enrolled_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, course_id),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(course_id) REFERENCES courses(id)
        );

        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            due_date TEXT,
            max_score INTEGER DEFAULT 100,
            created_by INTEGER NOT NULL,
            FOREIGN KEY(course_id) REFERENCES courses(id),
            FOREIGN KEY(created_by) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS assignment_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assignment_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            submission_text TEXT,
            submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
            grade INTEGER DEFAULT 0,
            feedback TEXT,
            FOREIGN KEY(assignment_id) REFERENCES assignments(id),
            FOREIGN KEY(student_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            questions TEXT NOT NULL,
            created_by INTEGER NOT NULL,
            FOREIGN KEY(course_id) REFERENCES courses(id),
            FOREIGN KEY(created_by) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            score INTEGER DEFAULT 0,
            total INTEGER DEFAULT 0,
            submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(quiz_id) REFERENCES quizzes(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            completed_lessons INTEGER DEFAULT 0,
            total_lessons INTEGER DEFAULT 0,
            percent INTEGER DEFAULT 0,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, course_id),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(course_id) REFERENCES courses(id)
        );

        CREATE TABLE IF NOT EXISTS certificates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            certificate_name TEXT NOT NULL,
            issued_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, course_id),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(course_id) REFERENCES courses(id)
        );

        CREATE TABLE IF NOT EXISTS chatbot_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT NOT NULL,
            reply TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        '''
    )
    conn.close()


def seed_data():
    conn = get_db_connection()
    user_count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    if user_count > 0:
        conn.close()
        return

    admin_password = generate_password_hash('admin123')
    teacher_password = generate_password_hash('teacher123')
    student_password = generate_password_hash('student123')

    conn.execute(
        'INSERT INTO users (name, email, password, role, bio) VALUES (?, ?, ?, ?, ?)',
        ('Admin User', 'admin@lms.com', admin_password, 'admin', 'Platform administrator')
    )
    conn.execute(
        'INSERT INTO users (name, email, password, role, bio) VALUES (?, ?, ?, ?, ?)',
        ('Teacher John', 'teacher@lms.com', teacher_password, 'teacher', 'Experienced software instructor')
    )
    conn.execute(
        'INSERT INTO users (name, email, password, role, bio) VALUES (?, ?, ?, ?, ?)',
        ('Student Maya', 'student@lms.com', student_password, 'student', 'Learning to grow in tech')
    )

    teacher_id = conn.execute('SELECT id FROM users WHERE email = ?', ('teacher@lms.com',)).fetchone()[0]
    course_rows = [
        ('Python for Beginners', 'Programming', 'Learn Python fundamentals, syntax, functions, and practical projects.', teacher_id, 'published'),
        ('AI Foundations', 'AI', 'Explore machine learning basics, AI workflows, and smart problem solving.', teacher_id, 'published'),
        ('Web Development Bootcamp', 'Web Development', 'Build modern responsive websites with HTML, CSS, JavaScript, and Flask.', teacher_id, 'published'),
        ('Data Analytics Essentials', 'Data', 'Understand data cleaning, visualization, and insight generation.', teacher_id, 'published')
    ]
    for title, category, description, instructor_id, status in course_rows:
        conn.execute(
            'INSERT INTO courses (title, category, description, instructor_id, status) VALUES (?, ?, ?, ?, ?)',
            (title, category, description, instructor_id, status)
        )

    courses = conn.execute('SELECT id, title FROM courses ORDER BY id').fetchall()
    lesson_map = {
        'Python for Beginners': [
            ('Intro to Python', 'https://www.youtube.com/watch?v=kqtD5dpn9C8', '08:32', 'Get ready to understand Python basics and how code executes.'),
            ('Variables and Data Types', 'https://www.youtube.com/watch?v=Z1Yd7upQsXY', '09:12', 'Learn strings, numbers, lists, and Python data structures.'),
            ('Functions and Loops', 'https://www.youtube.com/watch?v=9Os0o3wzS_I', '10:05', 'Create reusable logic with functions and loops.')
        ],
        'AI Foundations': [
            ('AI Introduction', 'https://www.youtube.com/watch?v=2ePf9rue1Ao', '07:45', 'Understand what AI is and its applications.'),
            ('Machine Learning Basics', 'https://www.youtube.com/watch?v=Gv9_4yMHFmA', '11:00', 'Learn supervised learning and model training concepts.'),
            ('AI in Practice', 'https://www.youtube.com/watch?v=Kx0pRShH9rA', '08:25', 'Use AI tools to solve real problems.')
        ],
        'Web Development Bootcamp': [
            ('HTML Essentials', 'https://www.youtube.com/watch?v=G3e-cpL7ofc', '06:55', 'Build the structure of a webpage.'),
            ('CSS Modern Layouts', 'https://www.youtube.com/watch?v=J35jug1uHzE', '09:30', 'Design beautiful, responsive layouts.'),
            ('JavaScript Interactivity', 'https://www.youtube.com/watch?v=PkZNo7MGyTo', '12:10', 'Add behavior and interaction to pages.')
        ],
        'Data Analytics Essentials': [
            ('Data Cleaning', 'https://www.youtube.com/watch?v=Q4K0Ubd5Tms', '08:15', 'Clean and normalize messy data.'),
            ('Visualization Basics', 'https://www.youtube.com/watch?v=0fKg7e37bms', '09:45', 'Create charts and dashboards for analysis.'),
            ('Insights and Reporting', 'https://www.youtube.com/watch?v=Rq9a_52ezjI', '10:25', 'Turn data into actionable conclusions.')
        ]
    }

    for course in courses:
        for title, video_url, duration, content in lesson_map.get(course['title'], []):
            conn.execute(
                'INSERT INTO lessons (course_id, title, video_url, duration, content) VALUES (?, ?, ?, ?, ?)',
                (course['id'], title, video_url, duration, content)
            )
        conn.execute(
            'INSERT INTO assignments (course_id, title, description, due_date, max_score, created_by) VALUES (?, ?, ?, ?, ?, ?)',
            (
                course['id'],
                f'{course["title"]} Capstone Task',
                f'Complete a practical project for {course["title"]} and provide a short report.',
                '2026-12-31',
                100,
                teacher_id
            )
        )
        conn.execute(
            'INSERT INTO quizzes (course_id, title, questions, created_by) VALUES (?, ?, ?, ?)',
            (
                course['id'],
                f'{course["title"]} Quiz',
                json.dumps([
                    {'question': 'Which of the following is a core part of a learning system?', 'options': ['Course', 'Student', 'Dashboard', 'All of the above'], 'answer': 'All of the above'},
                    {'question': 'What is the main goal of a course progress bar?', 'options': ['Decorate the page', 'Track learning progress', 'Delete lessons', 'Fix login issues'], 'answer': 'Track learning progress'},
                    {'question': 'Which of these best describes a certificate?', 'options': ['Payment receipt', 'Completion proof', 'Login form', 'Database table'], 'answer': 'Completion proof'}
                ]),
                teacher_id
            )
        )

    student_id = conn.execute('SELECT id FROM users WHERE email = ?', ('student@lms.com',)).fetchone()[0]
    python_course_id = conn.execute('SELECT id FROM courses WHERE title = ?', ('Python for Beginners',)).fetchone()[0]
    web_course_id = conn.execute('SELECT id FROM courses WHERE title = ?', ('Web Development Bootcamp',)).fetchone()[0]
    conn.execute('INSERT OR IGNORE INTO enrollments (user_id, course_id, progress) VALUES (?, ?, ?)', (student_id, python_course_id, 65))
    conn.execute('INSERT OR IGNORE INTO enrollments (user_id, course_id, progress) VALUES (?, ?, ?)', (student_id, web_course_id, 40))
    conn.execute('INSERT OR IGNORE INTO progress (user_id, course_id, completed_lessons, total_lessons, percent) VALUES (?, ?, ?, ?, ?)', (student_id, python_course_id, 2, 3, 65))
    conn.execute('INSERT OR IGNORE INTO progress (user_id, course_id, completed_lessons, total_lessons, percent) VALUES (?, ?, ?, ?, ?)', (student_id, web_course_id, 1, 3, 40))
    conn.execute('INSERT OR IGNORE INTO certificates (user_id, course_id, certificate_name) VALUES (?, ?, ?)', (student_id, python_course_id, 'Python for Beginners Certificate'))
    conn.execute('INSERT INTO chatbot_messages (user_id, message, reply) VALUES (?, ?, ?)', (student_id, 'Which courses are available?', 'Python, AI, Web Development and Data Analytics courses are available.'))
    conn.commit()
    conn.close()


@app.before_request
def ensure_db_ready():
    init_db()
    seed_data()


@app.get('/')
def home():
    return render_template('home.html')


@app.get('/login')
def login_page():
    return render_template('login.html')


@app.get('/student')
def student_dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('student_dashboard.html')


@app.get('/teacher')
def teacher_dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('teacher_dashboard.html')


@app.get('/admin')
def admin_dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('admin_dashboard.html')


@app.get('/courses')
def course_catalog():
    return render_template('course_catalog.html')


@app.get('/courses/<int:course_id>')
def course_detail(course_id):
    return render_template('course_detail.html', course_id=course_id)


@app.get('/profile')
def profile_page():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('profile.html')


@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    role = (data.get('role') or 'student').strip().lower()

    if not name or not email or not password:
        return jsonify({'success': False, 'message': 'Name, email, and password are required.'}), 400

    if role not in {'student', 'teacher', 'admin'}:
        role = 'student'

    conn = get_db_connection()
    existing = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
    if existing:
        conn.close()
        return jsonify({'success': False, 'message': 'Email already registered.'}), 400

    hashed = generate_password_hash(password)
    cursor = conn.execute(
        'INSERT INTO users (name, email, password, role, bio) VALUES (?, ?, ?, ?, ?)',
        (name, email, hashed, role, 'New member')
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    session['user_id'] = user_id
    session['role'] = role
    return jsonify({'success': True, 'message': 'Registration successful.', 'user': {'id': user_id, 'name': name, 'role': role}})


@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()

    if not user or not check_password_hash(user['password'], password):
        return jsonify({'success': False, 'message': 'Invalid email or password.'}), 401

    session['user_id'] = user['id']
    session['role'] = user['role']
    return jsonify({'success': True, 'message': 'Login successful.', 'user': {'id': user['id'], 'name': user['name'], 'role': user['role']}})


@app.route('/api/logout', methods=['POST'])
def logout_user():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out.'})


@app.route('/api/me')
def current_user():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in.'}), 401
    user = get_user_by_id(user_id)
    if not user:
        session.clear()
        return jsonify({'success': False, 'message': 'Unauthorized.'}), 401
    return jsonify({'success': True, 'user': {'id': user['id'], 'name': user['name'], 'email': user['email'], 'role': user['role'], 'bio': user['bio']}})


@app.route('/api/courses')
def list_courses():
    conn = get_db_connection()
    courses = conn.execute(
        '''
        SELECT c.*, u.name as instructor_name
        FROM courses c
        JOIN users u ON u.id = c.instructor_id
        ORDER BY c.id DESC
        '''
    ).fetchall()
    conn.close()
    return jsonify({'success': True, 'courses': [dict(course) for course in courses]})


@app.route('/api/courses/<int:course_id>')
def get_course(course_id):
    conn = get_db_connection()
    course = conn.execute('SELECT c.*, u.name as instructor_name FROM courses c JOIN users u ON u.id = c.instructor_id WHERE c.id = ?', (course_id,)).fetchone()
    if not course:
        conn.close()
        return jsonify({'success': False, 'message': 'Course not found.'}), 404

    lessons = conn.execute('SELECT * FROM lessons WHERE course_id = ? ORDER BY id', (course_id,)).fetchall()
    assignments = conn.execute('SELECT * FROM assignments WHERE course_id = ? ORDER BY id', (course_id,)).fetchall()
    quizzes = conn.execute('SELECT * FROM quizzes WHERE course_id = ? ORDER BY id', (course_id,)).fetchall()
    enrollment_count = conn.execute('SELECT COUNT(*) FROM enrollments WHERE course_id = ?', (course_id,)).fetchone()[0]
    conn.close()

    return jsonify({
        'success': True,
        'course': dict(course),
        'lessons': [dict(lesson) for lesson in lessons],
        'assignments': [dict(item) for item in assignments],
        'quizzes': [dict(item) for item in quizzes],
        'enrollment_count': enrollment_count
    })


@app.route('/api/my-courses')
def my_courses():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Login required.'}), 401

    conn = get_db_connection()
    user = conn.execute('SELECT role FROM users WHERE id = ?', (user_id,)).fetchone()
    if user['role'] == 'student':
        rows = conn.execute(
            '''
            SELECT e.*, c.title, c.category, c.description, u.name as instructor_name,
                   p.percent AS progress_percent
            FROM enrollments e
            JOIN courses c ON c.id = e.course_id
            JOIN users u ON u.id = c.instructor_id
            LEFT JOIN progress p ON p.user_id = e.user_id AND p.course_id = e.course_id
            WHERE e.user_id = ?
            ORDER BY e.enrolled_at DESC
            ''',
            (user_id,)
        ).fetchall()
    elif user['role'] == 'teacher':
        rows = conn.execute(
            '''
            SELECT c.*, COUNT(e.id) AS student_count
            FROM courses c
            LEFT JOIN enrollments e ON e.course_id = c.id
            WHERE c.instructor_id = ?
            GROUP BY c.id
            ORDER BY c.id DESC
            ''',
            (user_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            '''
            SELECT c.*, COUNT(e.id) AS student_count
            FROM courses c
            LEFT JOIN enrollments e ON e.course_id = c.id
            GROUP BY c.id
            ORDER BY c.id DESC
            '''
        ).fetchall()
    conn.close()
    return jsonify({'success': True, 'courses': [dict(row) for row in rows]})


@app.route('/api/courses/<int:course_id>/enroll', methods=['POST'])
def enroll_course(course_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Login required.'}), 401

    conn = get_db_connection()
    existing = conn.execute('SELECT id FROM enrollments WHERE user_id = ? AND course_id = ?', (user_id, course_id)).fetchone()
    if existing:
        conn.close()
        return jsonify({'success': False, 'message': 'You are already enrolled in this course.'})

    conn.execute('INSERT INTO enrollments (user_id, course_id, progress) VALUES (?, ?, 0)', (user_id, course_id))
    conn.execute('INSERT INTO progress (user_id, course_id, completed_lessons, total_lessons, percent) VALUES (?, ?, 0, 0, 0)', (user_id, course_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Course enrolled successfully.'})


@app.route('/api/courses/<int:course_id>/progress', methods=['POST'])
def update_course_progress(course_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Login required.'}), 401

    data = request.get_json(silent=True) or {}
    completed = int(data.get('completed', 0) or 0)
    total = int(data.get('total', 0) or 0)
    if total <= 0:
        total = 1
    percent = max(0, min(100, round((completed / total) * 100)))

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO progress (user_id, course_id, completed_lessons, total_lessons, percent, updated_at) VALUES (?, ?, ?, ?, ?, ?) '
        'ON CONFLICT(user_id, course_id) DO UPDATE SET completed_lessons = excluded.completed_lessons, '
        'total_lessons = excluded.total_lessons, percent = excluded.percent, updated_at = excluded.updated_at',
        (user_id, course_id, completed, total, percent, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )
    conn.execute(
        'UPDATE enrollments SET progress = ? WHERE user_id = ? AND course_id = ?',
        (percent, user_id, course_id)
    )
    if percent >= 80:
        conn.execute(
            'INSERT OR IGNORE INTO certificates (user_id, course_id, certificate_name) VALUES (?, ?, ?)',
            (user_id, course_id, f'Certificate for Course {course_id}')
        )
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'percent': percent})


@app.route('/api/assignments/<int:assignment_id>/submit', methods=['POST'])
def submit_assignment(assignment_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Login required.'}), 401

    data = request.get_json(silent=True) or {}
    text = (data.get('submission_text') or '').strip()
    if not text:
        return jsonify({'success': False, 'message': 'Submission text is required.'}), 400

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO assignment_submissions (assignment_id, student_id, submission_text, grade, feedback) VALUES (?, ?, ?, ?, ?)',
        (assignment_id, user_id, text, 95, 'Submitted successfully and awaiting review.')
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Assignment submitted successfully.'})


@app.route('/api/assignments/<int:assignment_id>')
def get_assignment(assignment_id):
    conn = get_db_connection()
    assignment = conn.execute('SELECT * FROM assignments WHERE id = ?', (assignment_id,)).fetchone()
    conn.close()
    if not assignment:
        return jsonify({'success': False, 'message': 'Assignment not found.'}), 404
    return jsonify({'success': True, 'assignment': dict(assignment)})


@app.route('/api/quizzes/<int:quiz_id>/submit', methods=['POST'])
def submit_quiz(quiz_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Login required.'}), 401

    data = request.get_json(silent=True) or {}
    answers = data.get('answers') or {}
    conn = get_db_connection()
    quiz = conn.execute('SELECT * FROM quizzes WHERE id = ?', (quiz_id,)).fetchone()
    if not quiz:
        conn.close()
        return jsonify({'success': False, 'message': 'Quiz not found.'}), 404

    questions = json.loads(quiz['questions'])
    score = 0
    total = len(questions)
    for i, question in enumerate(questions):
        selected = str(answers.get(str(i), '')).strip()
        if selected.lower() == str(question.get('answer', '')).lower():
            score += 1

    conn.execute(
        'INSERT INTO quiz_results (quiz_id, user_id, score, total) VALUES (?, ?, ?, ?)',
        (quiz_id, user_id, score, total)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'score': score, 'total': total, 'percentage': round((score / total) * 100) if total else 0})


@app.route('/api/certificates')
def list_certificates():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Login required.'}), 401

    conn = get_db_connection()
    rows = conn.execute(
        '''
        SELECT c.*, cr.title AS course_title
        FROM certificates cert
        JOIN courses cr ON cr.id = cert.course_id
        WHERE cert.user_id = ?
        ORDER BY cert.issued_at DESC
        '''
        , (user_id,)).fetchall()
    conn.close()
    return jsonify({'success': True, 'certificates': [dict(row) for row in rows]})


@app.route('/api/profile')
def profile_info():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Login required.'}), 401

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    course_count = conn.execute('SELECT COUNT(*) FROM enrollments WHERE user_id = ?', (user_id,)).fetchone()[0]
    cert_count = conn.execute('SELECT COUNT(*) FROM certificates WHERE user_id = ?', (user_id,)).fetchone()[0]
    conn.close()
    return jsonify({
        'success': True,
        'profile': {
            'name': user['name'],
            'email': user['email'],
            'role': user['role'],
            'bio': user['bio'],
            'courses_enrolled': course_count,
            'certificates_earned': cert_count
        }
    })


@app.route('/api/dashboard-stats')
def dashboard_stats():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Login required.'}), 401

    conn = get_db_connection()
    user = conn.execute('SELECT role FROM users WHERE id = ?', (user_id,)).fetchone()
    role = user['role']
    if role == 'student':
        total_courses = conn.execute('SELECT COUNT(*) FROM enrollments WHERE user_id = ?', (user_id,)).fetchone()[0]
        completed = conn.execute('SELECT COUNT(*) FROM certificates WHERE user_id = ?', (user_id,)).fetchone()[0]
        average = conn.execute('SELECT AVG(percent) FROM progress WHERE user_id = ?', (user_id,)).fetchone()[0] or 0
        data = {'courses': total_courses, 'certificates': completed, 'average_progress': round(average)}
    elif role == 'teacher':
        total_courses = conn.execute('SELECT COUNT(*) FROM courses WHERE instructor_id = ?', (user_id,)).fetchone()[0]
        student_count = conn.execute('SELECT COUNT(DISTINCT user_id) FROM enrollments e JOIN courses c ON c.id = e.course_id WHERE c.instructor_id = ?', (user_id,)).fetchone()[0]
        assignments = conn.execute('SELECT COUNT(*) FROM assignments WHERE created_by = ?', (user_id,)).fetchone()[0]
        data = {'courses': total_courses, 'students': student_count, 'assignments': assignments}
    else:
        total_courses = conn.execute('SELECT COUNT(*) FROM courses').fetchone()[0]
        total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        total_enrollments = conn.execute('SELECT COUNT(*) FROM enrollments').fetchone()[0]
        data = {'courses': total_courses, 'users': total_users, 'enrollments': total_enrollments}

    conn.close()
    return jsonify({'success': True, 'stats': data})


@app.route('/api/chatbot', methods=['POST'])
def chatbot_api():
    user_id = session.get('user_id')
    data = request.get_json(silent=True) or {}
    user_message = (data.get('message') or '').strip()
    if not user_message:
        return jsonify({'success': False, 'message': 'Message is required.'}), 400

    conn = get_db_connection()
    courses = conn.execute('SELECT title FROM courses ORDER BY id').fetchall()
    available = ', '.join(course['title'] for course in courses)
    user = None
    if user_id:
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    lower = user_message.lower()
    if 'course' in lower and ('available' in lower or 'list' in lower or 'what' in lower):
        reply = f'Available courses: {available}.'
    elif 'progress' in lower:
        if user_id:
            progress = conn.execute('SELECT AVG(percent) AS avg_progress FROM progress WHERE user_id = ?', (user_id,)).fetchone()['avg_progress'] or 0
            reply = f'You have completed {round(progress)}% of your enrolled learning path.'
        else:
            reply = 'Please log in to check your personal progress.'
    elif 'lesson' in lower:
        reply = 'You can open any course and watch the lesson videos from the Course Details page.'
    elif 'assignment' in lower:
        reply = 'Assignments are available in each course and can be submitted from the course details area.'
    elif 'quiz' in lower:
        reply = 'Take the quizzes from the course page to test your understanding and improve your results.'
    elif 'hello' in lower or 'hi' in lower:
        reply = 'Hello! I am your LMS assistant. Ask me about courses, progress, assignments, or quizzes.'
    else:
        reply = 'I can help with course search, progress, lessons, assignments, quizzes, and navigation.'

    conn.execute('INSERT INTO chatbot_messages (user_id, message, reply) VALUES (?, ?, ?)', (user_id, user_message, reply))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'reply': reply})


@app.route('/api/chatbot/history')
def chatbot_history():
    user_id = session.get('user_id')
    conn = get_db_connection()
    rows = conn.execute(
        'SELECT message, reply, created_at FROM chatbot_messages WHERE user_id = ? ORDER BY id DESC LIMIT 10',
        (user_id,) if user_id else (0,)
    ).fetchall()
    conn.close()
    return jsonify({'success': True, 'messages': [dict(row) for row in rows]})


if __name__ == '__main__':
    init_db()
    seed_data()
    app.run(debug=True, host='0.0.0.0', port=5000)
