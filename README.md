# LMS Auto Machine

A modern Learning Management System built with Python Flask, SQLite database, responsive HTML/CSS/JavaScript frontend, and an AI chatbot.

## Features

- Student, teacher, and admin dashboards
- Course catalog and detail pages
- Enrollment, lessons, assignments, and quizzes
- Progress tracking and certificate generation
- AI chatbot for student support
- SQLite database with seeded demo data

## Local Setup

1. Open a terminal in the project root.
2. Create a virtual environment and install dependencies:

   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt

3. Run the app:

   python app.py

4. Open:

   http://127.0.0.1:5000/

## Demo Accounts

- Admin: admin@lms.com / admin123
- Teacher: teacher@lms.com / teacher123
- Student: student@lms.com / student123

## Project Structure

- app.py - Flask backend and API
- static/css/style.css - App styling
- static/js/app.js - Frontend logic
- templates/ - HTML pages
- lms.db - SQLite database
