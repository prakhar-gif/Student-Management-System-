# Student-Management-System-
A full-stack Student Management System built with Python Flask, SQLite, HTML, CSS, and JavaScript for managing students, courses, marks, attendance, grades, SGPA/CGPA, and PDF marksheets.

## 📌 Project Overview

The Student Management System is designed to simplify and digitize common academic management tasks.

Instead of maintaining student information manually, administrators can manage student records, courses, marks, attendance, and enrollments from a web-based dashboard.

Students can log in to their own portal and view their academic information such as marks, grades, attendance, SGPA, and CGPA.

---

## ✨ Features

### 👨‍💼 Admin Module

The administrator can:

- 🔐 Secure admin login
- 👨‍🎓 Add new students
- ✏️ Edit student information
- 🗑️ Delete student records
- 🔎 Search and manage students
- 📚 Add and manage courses
- 📝 Manage course enrollments
- 📊 Enter and manage student marks
- 📈 Calculate grades automatically
- 🎯 Calculate SGPA and CGPA
- 🕐 Manage student attendance
- ⚠️ Identify students with attendance below 75%
- 📄 Generate student marksheets in PDF
- 👤 Manage student accounts

---

### 👨‍🎓 Student Module

Students can:

- 🔐 Login securely
- 📊 View personal dashboard
- 👤 View profile information
- 📚 View enrolled courses
- 📝 View marks
- 🎓 View grades
- 📈 View SGPA
- 🏆 View CGPA
- 🕐 View attendance
- ⚠️ Check attendance warnings
- 📄 Download marksheet

---

## 🛠️ Technologies Used

### Frontend

- HTML5
- CSS3
- JavaScript
- Responsive Web Design

### Backend

- Python
- Flask

### Database

- SQLite

### PDF Generation

- ReportLab

### Security

- Werkzeug Password Hashing

---

## 🏗️ System Architecture

```text
                    ┌─────────────────────┐
                    │       User          │
                    │ Admin / Student     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    Web Browser      │
                    │ HTML / CSS / JS     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    Flask Backend    │
                    │      Python         │
                    └──────────┬──────────┘
                               │
                 ┌─────────────┴─────────────┐
                 │                           │
                 ▼                           ▼
       ┌─────────────────┐          ┌─────────────────┐
       │ Authentication   │          │ Business Logic  │
       └─────────────────┘          └────────┬────────┘
                                             │
                                             ▼
                                  ┌────────────────────┐
                                  │   SQLite Database  │
                                  └────────────────────┘
