import io
import os
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from database import get_db, init_db

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret-key-before-deployment")
init_db()

def q(sql, params=(), one=False):
    db = get_db()
    cur = db.cursor()
    cur.execute(sql, params)
    result = cur.fetchone() if one else cur.fetchall()
    db.close()
    return result

def execute(sql, params=()):
    db = get_db()
    cur = db.cursor()
    cur.execute(sql, params)
    db.commit()
    last = getattr(cur, "lastrowid", None)
    db.close()
    return last

def role_required(role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if session.get("role") != role:
                flash("You do not have permission to access that page.", "error")
                return redirect(url_for("login"))
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def grade(mark):
    mark = float(mark)
    if mark >= 90: return "A+"
    if mark >= 80: return "A"
    if mark >= 70: return "B+"
    if mark >= 60: return "B"
    if mark >= 50: return "C"
    if mark >= 40: return "D"
    return "F"

def grade_point(mark):
    m = float(mark)
    if m >= 90: return 10
    if m >= 80: return 9
    if m >= 70: return 8
    if m >= 60: return 7
    if m >= 50: return 6
    if m >= 40: return 5
    return 0

def academic_rows(student_db_id):
    rows = q("""SELECT c.code,c.name,c.credits,
                       COALESCE(m.marks,0) marks,
                       COALESCE(a.total_classes,0) total_classes,
                       COALESCE(a.attended_classes,0) attended_classes
                FROM enrollments e
                JOIN courses c ON c.id=e.course_id
                LEFT JOIN marks m ON m.student_id=e.student_id AND m.course_id=e.course_id
                LEFT JOIN attendance a ON a.student_id=e.student_id AND a.course_id=e.course_id
                WHERE e.student_id=?
                ORDER BY c.code""", (student_db_id,))
    return rows

def academic_summary(student_db_id):
    rows = academic_rows(student_db_id)
    credits = sum(int(r["credits"]) for r in rows)
    weighted = sum(grade_point(r["marks"]) * int(r["credits"]) for r in rows)
    cgpa = round(weighted / credits, 2) if credits else 0
    percentage = round(sum(float(r["marks"]) for r in rows) / len(rows), 2) if rows else 0
    attendance_values = []
    for r in rows:
        if int(r["total_classes"]) > 0:
            attendance_values.append(100 * int(r["attended_classes"]) / int(r["total_classes"]))
    attendance = round(sum(attendance_values) / len(attendance_values), 2) if attendance_values else 0
    return {"cgpa": cgpa, "percentage": percentage, "attendance": attendance, "courses": len(rows)}

@app.context_processor
def inject_helpers():
    return {"grade": grade, "grade_point": grade_point}

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        user = q("SELECT * FROM users WHERE username=?", (username,), one=True)
        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect(url_for("admin_dashboard" if user["role"] == "admin" else "student_dashboard"))
        flash("Invalid username or password.", "error")
    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        student_id = request.form["student_id"].strip().upper()
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        department = request.form["department"]
        semester = int(request.form["semester"])
        try:
            db = get_db()
            cur = db.cursor()
            cur.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                        (student_id, generate_password_hash(password), "student"))
            cur.execute("""INSERT INTO students
                (student_id,name,email,department,semester)
                VALUES (?,?,?,?,?)""",
                (student_id,name,email,department,semester))
            db.commit()
            db.close()
            flash("Registration successful. You can now log in.", "success")
            return redirect(url_for("login"))
        except Exception:
            try: db.rollback(); db.close()
            except Exception: pass
            flash("Student ID or email may already exist.", "error")
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/admin/dashboard")
@role_required("admin")
def admin_dashboard():
    total_students = q("SELECT COUNT(*) n FROM students", one=True)["n"]
    total_courses = q("SELECT COUNT(*) n FROM courses", one=True)["n"]
    avg = q("SELECT AVG(marks) n FROM marks", one=True)["n"] or 0
    total_marks = q("SELECT COUNT(*) n FROM marks", one=True)["n"]
    passed = q("SELECT COUNT(*) n FROM marks WHERE marks>=40", one=True)["n"]
    pass_rate = round(100*passed/total_marks,2) if total_marks else 0
    recent = q("SELECT * FROM students ORDER BY id DESC LIMIT 8")
    return render_template("admin_dashboard.html", total_students=total_students,
                           total_courses=total_courses, average=round(avg,2),
                           pass_rate=pass_rate, recent_students=recent)

@app.route("/admin/students")
@role_required("admin")
def students():
    rows = q("SELECT * FROM students ORDER BY id DESC")
    return render_template("students.html", students=rows)

@app.route("/admin/students/add", methods=["POST"])
@role_required("admin")
def add_student():
    data = request.form
    try:
        db = get_db(); cur = db.cursor()
        cur.execute("""INSERT INTO students
            (student_id,name,email,phone,department,semester,address,date_of_birth)
            VALUES (?,?,?,?,?,?,?,?)""",
            (data["student_id"].strip().upper(),data["name"].strip(),data["email"].strip(),
             data.get("phone",""),data["department"],int(data["semester"]),
             data.get("address",""),data.get("date_of_birth") or None))
        cur.execute("""INSERT INTO users(username,password,role) VALUES(?,?,?)""",
                    (data["student_id"].strip().upper(), generate_password_hash(data.get("password","student123")), "student"))
        db.commit(); db.close()
        flash("Student created successfully.", "success")
    except Exception as e:
        try: db.rollback(); db.close()
        except Exception: pass
        flash(f"Could not create student: {e}", "error")
    return redirect(url_for("students"))

@app.route("/admin/students/edit/<int:student_db_id>", methods=["GET","POST"])
@role_required("admin")
def edit_student(student_db_id):
    student = q("SELECT * FROM students WHERE id=?", (student_db_id,), one=True)
    if not student:
        return redirect(url_for("students"))
    if request.method == "POST":
        d = request.form
        try:
            execute("""UPDATE students SET name=?,email=?,phone=?,department=?,
                       semester=?,address=?,date_of_birth=? WHERE id=?""",
                    (d["name"],d["email"],d.get("phone",""),d["department"],
                     int(d["semester"]),d.get("address",""),d.get("date_of_birth") or None,student_db_id))
            if d.get("password"):
                execute("UPDATE users SET password=? WHERE username=?",
                        (generate_password_hash(d["password"]), student["student_id"]))
            flash("Student updated successfully.", "success")
            return redirect(url_for("students"))
        except Exception as e:
            flash(f"Update failed: {e}", "error")
    return render_template("edit_student.html", student=student)

@app.route("/admin/students/delete/<int:student_db_id>")
@role_required("admin")
def delete_student(student_db_id):
    student = q("SELECT student_id FROM students WHERE id=?", (student_db_id,), one=True)
    if student:
        db=get_db(); cur=db.cursor()
        for table in ["marks","attendance","enrollments"]:
            cur.execute(f"DELETE FROM {table} WHERE student_id=?", (student_db_id,))
        cur.execute("DELETE FROM students WHERE id=?", (student_db_id,))
        cur.execute("DELETE FROM users WHERE username=?", (student["student_id"],))
        db.commit(); db.close()
    return redirect(url_for("students"))

@app.route("/admin/courses")
@role_required("admin")
def courses():
    rows=q("SELECT * FROM courses ORDER BY code")
    return render_template("courses.html", courses=rows)

@app.route("/admin/courses/add", methods=["POST"])
@role_required("admin")
def add_course():
    try:
        execute("INSERT INTO courses(code,name,credits) VALUES(?,?,?)",
                (request.form["code"].strip().upper(),request.form["name"].strip(),int(request.form["credits"])))
        flash("Course added.", "success")
    except Exception as e:
        flash(f"Could not add course: {e}", "error")
    return redirect(url_for("courses"))

@app.route("/admin/courses/delete/<int:course_id>")
@role_required("admin")
def delete_course(course_id):
    db=get_db(); cur=db.cursor()
    for table in ["marks","attendance","enrollments"]:
        cur.execute(f"DELETE FROM {table} WHERE course_id=?", (course_id,))
    cur.execute("DELETE FROM courses WHERE id=?", (course_id,))
    db.commit(); db.close()
    return redirect(url_for("courses"))

@app.route("/admin/enrollments")
@role_required("admin")
def enrollments():
    students=q("SELECT * FROM students ORDER BY name")
    courses=q("SELECT * FROM courses ORDER BY code")
    rows=q("""SELECT e.id,s.student_id,s.name,c.code,c.name course_name
              FROM enrollments e JOIN students s ON s.id=e.student_id
              JOIN courses c ON c.id=e.course_id ORDER BY s.name,c.code""")
    return render_template("enrollments.html", students=students, courses=courses, rows=rows)

@app.route("/admin/enrollments/add", methods=["POST"])
@role_required("admin")
def add_enrollment():
    try:
        execute("INSERT INTO enrollments(student_id,course_id) VALUES(?,?)",
                (int(request.form["student_id"]),int(request.form["course_id"])))
        flash("Course enrolled successfully.", "success")
    except Exception:
        flash("Student is already enrolled in this course.", "error")
    return redirect(url_for("enrollments"))

@app.route("/admin/enrollments/delete/<int:enrollment_id>")
@role_required("admin")
def delete_enrollment(enrollment_id):
    execute("DELETE FROM enrollments WHERE id=?", (enrollment_id,))
    return redirect(url_for("enrollments"))

@app.route("/admin/marks")
@role_required("admin")
def marks():
    records=q("""SELECT m.id,s.student_id,s.name,c.code,c.name course_name,
                        c.credits,m.marks
                 FROM marks m JOIN students s ON s.id=m.student_id
                 JOIN courses c ON c.id=m.course_id ORDER BY s.name,c.code""")
    students=q("SELECT * FROM students ORDER BY name")
    courses=q("SELECT * FROM courses ORDER BY code")
    return render_template("marks.html", records=records, students=students, courses=courses)

@app.route("/admin/marks/save", methods=["POST"])
@role_required("admin")
def save_marks():
    sid=int(request.form["student_id"]); cid=int(request.form["course_id"]); value=float(request.form["marks"])
    if not 0 <= value <= 100:
        flash("Marks must be between 0 and 100.", "error")
        return redirect(url_for("marks"))
    db=get_db(); cur=db.cursor()
    try:
        cur.execute("UPDATE marks SET marks=? WHERE student_id=? AND course_id=?", (value,sid,cid))
        if getattr(cur,"rowcount",0)==0:
            cur.execute("INSERT INTO marks(student_id,course_id,marks) VALUES(?,?,?)",(sid,cid,value))
        db.commit(); db.close()
        flash("Marks saved.", "success")
    except Exception as e:
        db.rollback(); db.close(); flash(str(e),"error")
    return redirect(url_for("marks"))

@app.route("/admin/attendance")
@role_required("admin")
def attendance():
    records=q("""SELECT a.id,s.student_id,s.name,c.code,c.name course_name,
                        a.total_classes,a.attended_classes
                 FROM attendance a JOIN students s ON s.id=a.student_id
                 JOIN courses c ON c.id=a.course_id ORDER BY s.name,c.code""")
    students=q("SELECT * FROM students ORDER BY name")
    courses=q("SELECT * FROM courses ORDER BY code")
    return render_template("attendance.html", records=records, students=students, courses=courses)

@app.route("/admin/attendance/save", methods=["POST"])
@role_required("admin")
def save_attendance():
    sid=int(request.form["student_id"]); cid=int(request.form["course_id"])
    total=int(request.form["total_classes"]); attended=int(request.form["attended_classes"])
    if total < 0 or attended < 0 or attended > total:
        flash("Invalid attendance values.", "error")
        return redirect(url_for("attendance"))
    db=get_db(); cur=db.cursor()
    cur.execute("UPDATE attendance SET total_classes=?,attended_classes=? WHERE student_id=? AND course_id=?",
                (total,attended,sid,cid))
    if getattr(cur,"rowcount",0)==0:
        cur.execute("""INSERT INTO attendance(student_id,course_id,total_classes,attended_classes)
                       VALUES(?,?,?,?)""",(sid,cid,total,attended))
    db.commit(); db.close()
    flash("Attendance saved.", "success")
    return redirect(url_for("attendance"))

@app.route("/student/dashboard")
@role_required("student")
def student_dashboard():
    student=q("SELECT * FROM students WHERE student_id=?", (session["username"],), one=True)
    if not student:
        flash("Student profile not found.", "error")
        return redirect(url_for("logout"))
    rows=academic_rows(student["id"])
    summary=academic_summary(student["id"])
    return render_template("student_dashboard.html", student=student, rows=rows, summary=summary)

@app.route("/student/profile", methods=["GET","POST"])
@role_required("student")
def student_profile():
    student=q("SELECT * FROM students WHERE student_id=?", (session["username"],), one=True)
    if request.method=="POST":
        d=request.form
        execute("""UPDATE students SET phone=?,address=?,date_of_birth=? WHERE id=?""",
                (d.get("phone",""),d.get("address",""),d.get("date_of_birth") or None,student["id"]))
        flash("Profile updated.", "success")
        return redirect(url_for("student_profile"))
    return render_template("student_profile.html", student=student)

@app.route("/student/marksheet")
@role_required("student")
def marksheet():
    student=q("SELECT * FROM students WHERE student_id=?", (session["username"],), one=True)
    rows=academic_rows(student["id"])
    summary=academic_summary(student["id"])
    buffer=io.BytesIO()
    pdf=canvas.Canvas(buffer,pagesize=A4)
    w,h=A4
    pdf.setTitle("Student Marksheet")
    pdf.setFont("Helvetica-Bold",18); pdf.drawCentredString(w/2,h-55,"STUDENT MARKSHEET")
    pdf.setFont("Helvetica",11)
    y=h-90
    pdf.drawString(50,y,f"Student ID: {student['student_id']}"); y-=18
    pdf.drawString(50,y,f"Name: {student['name']}"); y-=18
    pdf.drawString(50,y,f"Department: {student['department']}"); y-=18
    pdf.drawString(50,y,f"Semester: {student['semester']}"); y-=30
    pdf.setFont("Helvetica-Bold",10)
    pdf.drawString(50,y,"Course"); pdf.drawString(240,y,"Credits"); pdf.drawString(315,y,"Marks"); pdf.drawString(385,y,"Grade")
    y-=18; pdf.setFont("Helvetica",10)
    for r in rows:
        pdf.drawString(50,y,f"{r['code']} - {r['name'][:25]}")
        pdf.drawString(240,y,str(r["credits"]))
        pdf.drawString(315,y,f"{r['marks']:.1f}")
        pdf.drawString(385,y,grade(r["marks"]))
        y-=18
        if y < 80:
            pdf.showPage(); y=h-60
    y-=10
    pdf.setFont("Helvetica-Bold",11)
    pdf.drawString(50,y,f"CGPA: {summary['cgpa']}")
    pdf.drawString(170,y,f"Average: {summary['percentage']}%")
    pdf.drawString(330,y,f"Attendance: {summary['attendance']}%")
    pdf.save(); buffer.seek(0)
    return send_file(buffer,as_attachment=True,download_name=f"{student['student_id']}_marksheet.pdf",mimetype="application/pdf")

if __name__=="__main__":
    app.run(debug=True,host="127.0.0.1",port=5000)
