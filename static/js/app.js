document.addEventListener('DOMContentLoaded', () => {
    initializeAuthForms();
    initializeChatbot();
    initializeNavigation();

    const path = window.location.pathname;
    if (path === '/') {
        loadHomeCourses();
    }

    if (path === '/courses') {
        loadCourseCatalog();
    }

    if (path === '/student') {
        loadStudentDashboard();
    }

    if (path === '/teacher') {
        loadTeacherDashboard();
    }

    if (path === '/admin') {
        loadAdminDashboard();
    }

    if (path === '/profile') {
        loadProfile();
    }

    if (path.startsWith('/courses/')) {
        const id = Number(path.split('/').filter(Boolean).pop());
        loadCourseDetail(id);
    }

    loadSessionUser();
});

function initializeNavigation() {
    const path = window.location.pathname;
    const loginBtn = document.getElementById('loginPromptBtn');
    const logoutBtn = document.getElementById('logoutBtn');

    const loginLink = document.querySelector('.main-nav a[href="/login"]');

    if (loginBtn) {
        loginBtn.addEventListener('click', () => {
            window.location.href = '/login';
        });
    }

    if (logoutBtn) {
        logoutBtn.addEventListener('click', async () => {
            await fetch('/api/logout', { method: 'POST' });
            window.location.href = '/';
        });
    }

    if (loginLink) {
        loginLink.textContent = path === '/login' ? 'Dashboard' : 'Login';
        loginLink.setAttribute('href', path === '/login' ? '/student' : '/login');
    }
}

async function loadSessionUser() {
    try {
        const response = await fetch('/api/me');
        if (!response.ok) {
            return;
        }
        const data = await response.json();
        if (data.success) {
            const user = data.user;
            const logoutBtn = document.getElementById('logoutBtn');
            const loginBtn = document.getElementById('loginPromptBtn');
            if (logoutBtn) logoutBtn.style.display = 'inline-flex';
            if (loginBtn) {
                loginBtn.textContent = user.role === 'student' ? 'Dashboard' : user.role === 'teacher' ? 'Teacher Panel' : 'Admin Panel';
                loginBtn.onclick = () => {
                    if (user.role === 'student') window.location.href = '/student';
                    else if (user.role === 'teacher') window.location.href = '/teacher';
                    else window.location.href = '/admin';
                };
            }
        }
    } catch (error) {
        console.warn('No active session', error);
    }
}

function initializeAuthForms() {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const toggleButtons = document.querySelectorAll('.toggle-btn');

    if (toggleButtons.length) {
        toggleButtons.forEach((button) => {
            button.addEventListener('click', () => {
                toggleButtons.forEach((btn) => btn.classList.toggle('active', btn === button));
                const mode = button.dataset.mode;
                loginForm?.classList.toggle('active-form', mode === 'login');
                registerForm?.classList.toggle('active-form', mode === 'register');
            });
        });
    }

    if (loginForm) {
        loginForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const email = document.getElementById('loginEmail').value.trim();
            const password = document.getElementById('loginPassword').value;

            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            const result = await response.json();

            if (!response.ok) {
                alert(result.message || 'Login failed');
                return;
            }

            const user = result.user;
            if (user.role === 'student') window.location.href = '/student';
            else if (user.role === 'teacher') window.location.href = '/teacher';
            else window.location.href = '/admin';
        });
    }

    if (registerForm) {
        registerForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const name = document.getElementById('registerName').value.trim();
            const email = document.getElementById('registerEmail').value.trim();
            const password = document.getElementById('registerPassword').value;
            const role = document.getElementById('registerRole').value;

            const response = await fetch('/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, password, role })
            });
            const result = await response.json();

            if (!response.ok) {
                alert(result.message || 'Registration failed');
                return;
            }

            alert('Registration successful!');
            if (role === 'student') window.location.href = '/student';
            else if (role === 'teacher') window.location.href = '/teacher';
            else window.location.href = '/admin';
        });
    }
}

async function loadHomeCourses() {
    const container = document.getElementById('homeCourseGrid');
    if (!container) return;

    try {
        const response = await fetch('/api/courses');
        const data = await response.json();
        const courses = data.courses || [];
        container.innerHTML = courses.slice(0, 4).map(course => `
            <article class="course-card">
                <div class="course-top">
                    <span class="category-pill">${course.category}</span>
                    <span>${course.instructor_name}</span>
                </div>
                <h4>${course.title}</h4>
                <p>${course.description.slice(0, 100)}...</p>
                <div class="meta">
                    <span>Lessons</span>
                    <span>Progress</span>
                </div>
                <div class="course-footer">
                    <strong>Enroll</strong>
                    <button onclick="location.href='/courses/${course.id}'">View</button>
                </div>
            </article>
        `).join('');
    } catch (error) {
        console.error(error);
    }
}

async function loadCourseCatalog() {
    const container = document.getElementById('courseCatalogGrid');
    if (!container) return;

    try {
        const response = await fetch('/api/courses');
        const data = await response.json();
        const courses = data.courses || [];
        const input = document.getElementById('courseSearch');

        const render = (list) => {
            container.innerHTML = list.map(course => `
                <article class="course-card">
                    <div class="course-top">
                        <span class="category-pill">${course.category}</span>
                        <span>${course.instructor_name}</span>
                    </div>
                    <h4>${course.title}</h4>
                    <p>${course.description}</p>
                    <div class="meta">
                        <span>Course</span>
                        <span>${course.status}</span>
                    </div>
                    <div class="course-footer">
                        <strong>New</strong>
                        <button onclick="location.href='/courses/${course.id}'">Open</button>
                    </div>
                </article>
            `).join('');
        };

        render(courses);

        if (input) {
            input.addEventListener('input', (event) => {
                const searchTerm = event.target.value.toLowerCase();
                const filtered = courses.filter(course =>
                    course.title.toLowerCase().includes(searchTerm) ||
                    course.category.toLowerCase().includes(searchTerm) ||
                    course.description.toLowerCase().includes(searchTerm)
                );
                render(filtered);
            });
        }
    } catch (error) {
        console.error(error);
    }
}

async function loadCourseDetail(courseId) {
    const container = document.getElementById('courseDetailContent');
    if (!container) return;

    try {
        const response = await fetch(`/api/courses/${courseId}`);
        const data = await response.json();
        const course = data.course;
        const lessons = data.lessons || [];
        const assignments = data.assignments || [];
        const quizzes = data.quizzes || [];

        const summary = `
            <div class="course-detail-hero">
                <div>
                    <span class="eyebrow">${course.category}</span>
                    <h2>${course.title}</h2>
                    <p>${course.description}</p>
                    <div class="course-badges">
                        <span>Instructor: ${course.instructor_name}</span>
                        <span>${data.enrollment_count} learners</span>
                        <span>${lessons.length} lessons</span>
                    </div>
                </div>
                <div class="course-side-card">
                    <h3>Course Overview</h3>
                    <p>${course.description}</p>
                    <button class="primary-btn" id="enrollCourseButton">Enroll Course</button>
                </div>
            </div>
            <div class="course-detail-body">
                <div>
                    <h3>Lessons</h3>
                    <div class="lesson-list">
                        ${lessons.map(lesson => `
                            <div class="lesson-item">
                                <h4>${lesson.title}</h4>
                                <p>${lesson.content}</p>
                                <a href="${lesson.video_url}" target="_blank">Watch video (${lesson.duration})</a>
                            </div>
                        `).join('') || '<p>No lessons yet.</p>'}
                    </div>

                    <h3 style="margin-top:24px;">Assignments</h3>
                    <div class="assignment-list">
                        ${assignments.map(item => `
                            <div class="assignment-item">
                                <h4>${item.title}</h4>
                                <p>${item.description}</p>
                                <small>Due: ${item.due_date || 'No due date'} </small>
                            </div>
                        `).join('') || '<p>No assignments yet.</p>'}
                    </div>

                    <h3 style="margin-top:24px;">Quizzes</h3>
                    <div class="quiz-list">
                        ${quizzes.map(item => `
                            <div class="quiz-item">
                                <h4>${item.title}</h4>
                                <p>Quiz available in the course.</p>
                            </div>
                        `).join('') || '<p>No quizzes yet.</p>'}
                    </div>
                </div>
                <div class="course-side-card">
                    <h3>Progress</h3>
                    <div class="progress-meter">
                        <div class="progress-fill" style="width: 65%"></div>
                    </div>
                    <p>Current progress: 65%</p>
                    <button class="secondary-btn" id="markProgressButton">Mark Lesson Complete</button>
                </div>
            </div>
        `;

        container.innerHTML = summary;

        const enrollButton = document.getElementById('enrollCourseButton');
        if (enrollButton) {
            enrollButton.addEventListener('click', async () => {
                const response = await fetch(`/api/courses/${courseId}/enroll`, { method: 'POST' });
                const result = await response.json();
                alert(result.message || 'Enrolled');
            });
        }

        const progressButton = document.getElementById('markProgressButton');
        if (progressButton) {
            progressButton.addEventListener('click', async () => {
                const response = await fetch(`/api/courses/${courseId}/progress`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ completed: 2, total: 3 })
                });
                const result = await response.json();
                alert(`Progress updated: ${result.percent}%`);
            });
        }
    } catch (error) {
        console.error('Course detail failed:', error);
        container.innerHTML = '<p>Unable to load the course.</p>';
    }
}

async function loadStudentDashboard() {
    try {
        const userResponse = await fetch('/api/me');
        const userData = await userResponse.json();
        if (userData.success && userData.user) {
            document.getElementById('studentName').textContent = userData.user.name;
        }

        const response = await fetch('/api/dashboard-stats');
        const data = await response.json();
        const stats = data.stats || {};
        document.getElementById('studentStats').innerHTML = `
            <div class="stat-card"><div class="stat-label">Enrolled Courses</div><div class="stat-value">${stats.courses || 0}</div></div>
            <div class="stat-card"><div class="stat-label">Certificates</div><div class="stat-value">${stats.certificates || 0}</div></div>
            <div class="stat-card"><div class="stat-label">Avg. Progress</div><div class="stat-value">${stats.average_progress || 0}%</div></div>
        `;

        const coursesResponse = await fetch('/api/my-courses');
        const coursesData = await coursesResponse.json();
        const courseList = coursesData.courses || [];
        const studentCourses = document.getElementById('studentCourses');
        studentCourses.innerHTML = courseList.map(course => `
            <div class="course-card">
                <div class="course-top">
                    <span class="category-pill">${course.category}</span>
                    <span>${course.instructor_name || 'Instructor'}</span>
                </div>
                <h4>${course.title}</h4>
                <p>${course.description}</p>
                <div class="meta">
                    <span>Progress</span>
                    <span>${course.progress_percent || 0}%</span>
                </div>
                <div class="progress-bar"><div style="width:${course.progress_percent || 0}%"></div></div>
                <div class="course-footer">
                    <strong>${course.progress_percent || 0}%</strong>
                    <button onclick="location.href='/courses/${course.id}'">Continue</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error(error);
    }
}

async function loadTeacherDashboard() {
    try {
        const userResponse = await fetch('/api/me');
        const userData = await userResponse.json();
        if (userData.success && userData.user) {
            document.getElementById('teacherName').textContent = userData.user.name;
        }

        const statsResponse = await fetch('/api/dashboard-stats');
        const statsData = await statsResponse.json();
        const stats = statsData.stats || {};
        document.getElementById('teacherStats').innerHTML = `
            <div class="stat-card"><div class="stat-label">Courses</div><div class="stat-value">${stats.courses || 0}</div></div>
            <div class="stat-card"><div class="stat-label">Students</div><div class="stat-value">${stats.students || 0}</div></div>
            <div class="stat-card"><div class="stat-label">Assignments</div><div class="stat-value">${stats.assignments || 0}</div></div>
        `;

        const coursesResponse = await fetch('/api/my-courses');
        const coursesData = await coursesResponse.json();
        const courseList = coursesData.courses || [];
        const teacherCourses = document.getElementById('teacherCourses');
        teacherCourses.innerHTML = courseList.map(course => `
            <div class="course-card">
                <div class="course-top"><span class="category-pill">${course.category}</span><span>${course.student_count || 0} students</span></div>
                <h4>${course.title}</h4>
                <p>${course.description}</p>
                <div class="course-footer"><strong>Manage</strong><button onclick="location.href='/courses/${course.id}'">Open</button></div>
            </div>
        `).join('');
    } catch (error) {
        console.error(error);
    }
}

async function loadAdminDashboard() {
    try {
        const statsResponse = await fetch('/api/dashboard-stats');
        const statsData = await statsResponse.json();
        const stats = statsData.stats || {};
        document.getElementById('adminStats').innerHTML = `
            <div class="stat-card"><div class="stat-label">Total Courses</div><div class="stat-value">${stats.courses || 0}</div></div>
            <div class="stat-card"><div class="stat-label">Total Users</div><div class="stat-value">${stats.users || 0}</div></div>
            <div class="stat-card"><div class="stat-label">Enrollments</div><div class="stat-value">${stats.enrollments || 0}</div></div>
        `;

        const coursesResponse = await fetch('/api/my-courses');
        const coursesData = await coursesResponse.json();
        const courseList = coursesData.courses || [];
        const adminCourses = document.getElementById('adminCourses');
        adminCourses.innerHTML = courseList.map(course => `
            <div class="course-card">
                <div class="course-top"><span class="category-pill">${course.category}</span><span>${course.student_count || 0} learners</span></div>
                <h4>${course.title}</h4>
                <p>${course.description}</p>
                <div class="course-footer"><strong>Admin</strong><button onclick="location.href='/courses/${course.id}'">Review</button></div>
            </div>
        `).join('');
    } catch (error) {
        console.error(error);
    }
}

async function loadProfile() {
    try {
        const response = await fetch('/api/profile');
        const data = await response.json();
        if (!data.success) {
            window.location.href = '/login';
            return;
        }
        const profile = data.profile;
        document.getElementById('profileName').textContent = profile.name;
        document.getElementById('profileEmail').textContent = profile.email;
        document.getElementById('profileRole').textContent = profile.role;
        document.getElementById('profileCourses').textContent = profile.courses_enrolled;
        document.getElementById('profileCertificates').textContent = profile.certificates_earned;
        document.getElementById('profileBio').textContent = profile.bio || 'No bio yet.';
    } catch (error) {
        console.error(error);
    }
}

function initializeChatbot() {
    const toggle = document.getElementById('chatbotToggle');
    const panel = document.getElementById('chatbotPanel');
    const closeBtn = document.getElementById('chatbotClose');
    const sendBtn = document.getElementById('chatbotSend');
    const input = document.getElementById('chatbotInput');
    const messagesContainer = document.getElementById('chatbotMessages');

    if (!toggle || !panel || !messagesContainer) return;

    toggle.addEventListener('click', () => {
        panel.classList.toggle('hidden');
    });

    closeBtn?.addEventListener('click', () => panel.classList.add('hidden'));

    const addMessage = (text, role = 'bot') => {
        const div = document.createElement('div');
        div.className = `message ${role}`;
        div.textContent = text;
        messagesContainer.appendChild(div);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    };

    const sendMessage = async () => {
        const message = input.value.trim();
        if (!message) return;

        addMessage(message, 'user');
        input.value = '';

        try {
            const response = await fetch('/api/chatbot', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });
            const result = await response.json();
            addMessage(result.reply || 'I can help with that.', 'bot');
        } catch (error) {
            addMessage('Connection failed. Please try again.', 'bot');
        }
    };

    sendBtn?.addEventListener('click', sendMessage);
    input?.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') sendMessage();
    });

    addMessage('Hi! I can help you find courses, track progress, and answer classroom questions.', 'bot');
}
