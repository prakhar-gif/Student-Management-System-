import os
import sqlite3
from werkzeug.security import generate_password_hash

DB_TYPE = os.getenv("DB_TYPE", "sqlite").lower()

SQLITE_DB = os.getenv("SQLITE_DB", "student_management.db")
MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "student_management"),
}

SCHEMA = [
"""CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)""",
"""CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    phone VARCHAR(30),
    department VARCHAR(100) NOT NULL,
    semester INTEGER NOT NULL,
    address TEXT,
    date_of_birth DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)""",
"""CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(30) UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL,
    credits INTEGER NOT NULL
)""",
"""CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    UNIQUE(student_id, course_id),
    FOREIGN KEY(student_id) REFERENCES students(id),
    FOREIGN KEY(course_id) REFERENCES courses(id)
)""",
"""CREATE TABLE IF NOT EXISTS marks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    marks REAL NOT NULL,
    UNIQUE(student_id, course_id),
    FOREIGN KEY(student_id) REFERENCES students(id),
    FOREIGN KEY(course_id) REFERENCES courses(id)
)""",
"""CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    total_classes INTEGER NOT NULL DEFAULT 0,
    attended_classes INTEGER NOT NULL DEFAULT 0,
    UNIQUE(student_id, course_id),
    FOREIGN KEY(student_id) REFERENCES students(id),
    FOREIGN KEY(course_id) REFERENCES courses(id)
)"""
]

def get_db():
    if DB_TYPE == "mysql":
        import pymysql
        return pymysql.connect(
            host=MYSQL_CONFIG["host"],
            port=MYSQL_CONFIG["port"],
            user=MYSQL_CONFIG["user"],
            password=MYSQL_CONFIG["password"],
            database=MYSQL_CONFIG["database"],
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False
        )
    
    db = sqlite3.connect(SQLITE_DB)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    cur = db.cursor()
    for statement in SCHEMA:
        if DB_TYPE == "mysql":
            statement = statement.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "INT PRIMARY KEY AUTO_INCREMENT")
            statement = statement.replace("VARCHAR(255)", "VARCHAR(255)")
            statement = statement.replace("TIMESTAMP DEFAULT CURRENT_TIMESTAMP", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        cur.execute(statement)
    db.commit()

    def fetchone(query, params=()):
        cur.execute(query, params)
        return cur.fetchone()

    admin = fetchone("SELECT id FROM users WHERE username=?", ("admin",))
    if not admin:
        cur.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                    ("admin", generate_password_hash("admin123"), "admin"))

    student_user = fetchone("SELECT id FROM users WHERE username=?", ("STU001",))
    if not student_user:
        cur.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                    ("STU001", generate_password_hash("student123"), "student"))

    student = fetchone("SELECT id FROM students WHERE student_id=?", ("STU001",))
    if not student:
        cur.execute("""INSERT INTO students
        (student_id,name,email,phone,department,semester,address,date_of_birth)
        VALUES (?,?,?,?,?,?,?,?)""",
        ("STU001","Prakhar Dubey","prakhar@example.com","9876543210",
         "Computer Science",5,"India","2004-01-15"))
        student = fetchone("SELECT id FROM students WHERE student_id=?", ("STU001",))

    courses = [
        ("CS101","Data Structures",4),
        ("CS102","Database Management Systems",4),
        ("CS103","Operating Systems",3),
        ("CS104","Computer Networks",3),
        ("CS105","Web Development",3),
        ("CS106","Software Engineering",3)
    ]
    for c in courses:
        try:
            cur.execute("INSERT INTO courses (code,name,credits) VALUES (?,?,?)", c)
        except Exception:
            pass

    if student:
        for code in ["CS101","CS102","CS103","CS104","CS105"]:
            course = fetchone("SELECT id FROM courses WHERE code=?", (code,))
            if course:
                try:
                    cur.execute("INSERT INTO enrollments (student_id,course_id) VALUES (?,?)",
                                (student["id"], course["id"]))
                except Exception:
                    pass

    sample = {"CS101":85,"CS102":78,"CS103":91,"CS104":74,"CS105":88}
    for code, value in sample.items():
        course = fetchone("SELECT id FROM courses WHERE code=?", (code,))
        if course:
            try:
                cur.execute("INSERT INTO marks (student_id,course_id,marks) VALUES (?,?,?)",
                            (student["id"], course["id"], value))
            except Exception:
                pass
            try:
                cur.execute("""INSERT INTO attendance
                    (student_id,course_id,total_classes,attended_classes)
                    VALUES (?,?,?,?)""", (student["id"], course["id"], 40, 36))
            except Exception:
                pass

    db.commit()
    db.close()
