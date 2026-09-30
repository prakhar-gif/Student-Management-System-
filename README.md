# Student Management System Pro

A full-stack Student Management System built with Flask, SQLite/MySQL, HTML, CSS and JavaScript.

## Features

- Admin and Student authentication
- Student registration
- Password hashing
- Role-based access control
- Admin dashboard
- Student dashboard
- Add/edit/delete students
- Add/delete courses
- Course enrollment
- Marks management
- Automatic grades
- SGPA/CGPA calculation
- Attendance management
- Attendance warning below 75%
- Student profile
- PDF marksheet generation
- SQLite by default
- Optional MySQL configuration
- ER diagram and DFD documentation

## Run on Windows

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

Default admin:
- Username: admin
- Password: admin123

A sample student:
- Username: STU001
- Password: student123

## MySQL

Set these environment variables before running:

```powershell
$env:DB_TYPE="mysql"
$env:MYSQL_HOST="localhost"
$env:MYSQL_PORT="3306"
$env:MYSQL_USER="root"
$env:MYSQL_PASSWORD="your_password"
$env:MYSQL_DATABASE="student_management"
python app.py
```

Create the database first:

```sql
CREATE DATABASE student_management;
```

The application creates its tables automatically.

## Project Structure

```text
Student-Management-System-Pro/
├── app.py
├── database.py
├── requirements.txt
├── README.md
├── templates/
├── static/
└── docs/
```

## Security note

Change the Flask secret key and default passwords before deployment. This project is intended as an academic/project foundation; production deployment should add CSRF protection, stronger account policies, HTTPS, environment-based secrets, and audit logging.
