from flask import Flask, render_template, redirect, flash, session, url_for, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from collections import defaultdict
import sqlite3
import re
import random
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your_secret_key'


# Function to insert user data into the database
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/register')
def register():
    return render_template('signUp.html')


@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')


@app.route('/update_password')
def forget_password():
    return render_template('update.html')


@app.route('/dashboard')
def main_page():
    return render_template('generate.html')


@app.route('/add_subjects')
def add_subjects():
    return render_template('add_subject.html')


@app.route('/add_staffs')
def add_staffs():
    return render_template('add_staff.html')


@app.route('/add_classes')
def add_classes():
    return render_template('add_class.html')


@app.route('/staff_timetable')
def staff_timetable():
    return render_template('staff_timetable.html')


@app.route('/lab_timetable')
def lab_timetable():
    return render_template('lab_timetable.html')


@app.route('/class_timetable')
def class_timetable():
    return render_template('class_timetable.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['uname']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        password = request.form['pwd']

        conn = sqlite3.connect("db_AcademicPlannerAdvisor.db", check_same_thread=False, timeout=10)
        cursor = conn.cursor()

        # Check if username already exists
        cursor.execute("SELECT * FROM signUp_tbl WHERE user_name = ?", (username,))
        existing_user = cursor.fetchone()

        # Check if email already exists
        cursor.execute("SELECT * FROM signUp_tbl WHERE email = ?", (email,))
        existing_email = cursor.fetchone()

        # Check if password already exists
        cursor.execute("SELECT passwd FROM signUp_tbl")
        all_passwords = cursor.fetchall()

        password_exists = any(check_password_hash(row[0], password) for row in all_passwords)

        if existing_user:
            session['username_error'] = "Username already exists! Please choose a different one."

        if existing_email:
            session['email_error'] = "Email already registered!"

        if password_exists:
            session['password_error'] = "Password already exists! Choose a different password."

        if existing_user or existing_email:
            conn.close()
            return redirect(url_for('signup'))  # Reload with errors

        # Hash the password for security
        hashed_password = generate_password_hash(password)

        # Insert new user
        query = "INSERT INTO signUp_tbl(user_name, first_name, last_name, email, passwd) VALUES (?, ?, ?, ?, ?)"
        cursor.execute(query, (username, firstname, lastname, email, hashed_password))
        conn.commit()
        conn.close()

        flash("Signup successful! Please log in.", "success")
        return redirect(url_for('login'))  # Redirect to login page

    return render_template('signUp.html')


@app.route('/login', methods=['GET', 'POST'])
def login_check():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = sqlite3.connect("db_AcademicPlannerAdvisor.db")
        cursor = conn.cursor()

        # Fetch user details from tbl_login
        cursor.execute("SELECT user_name, passwd FROM tbl_login WHERE user_name = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):  # Check hashed password
            session["username"] = user[0]  # Store username in session
            flash("Login successful!", "success")
            return redirect(url_for("main_page"))  # Redirect to dashboard
        else:
            flash("Username or password does not match.", "error")

    return render_template("login.html")


# Route to render the password update form
@app.route('/update_password', methods=['GET', 'POST'])
def update_password():
    if request.method == 'POST':
        username = request.form['uname']
        e_mail = request.form['email']
        new_password = request.form['passwd_new']
        confirm_password = request.form['passwd_confirm']

        # Connect to database
        conn = sqlite3.connect("db_AcademicPlannerAdvisor.db")
        cursor = conn.cursor()

        # Fetch user details from database
        cursor.execute("SELECT email FROM signUp_tbl WHERE user_name = ?", (username,))
        user = cursor.fetchone()

        if user:
            db_email = user[0]

            # Check if old password matches
            if db_email == e_mail :
                # Check if new password and confirm password match
                if new_password == confirm_password:
                    new_hashed_password = generate_password_hash(new_password)

                    # Update password in the database
                    cursor.execute("UPDATE tbl_login SET passwd = ? WHERE user_name = ?",
                                   (new_hashed_password, username))
                    conn.commit()
                    flash("Password updated successfully!", "success")
                    conn.close()
                    return redirect(url_for('login'))  # Redirect to login page

                else:
                    flash("New password and confirm password do not match.", "error")
            else:
                flash("Username and Email doesn't matches.", "error")
        else:
            flash("Username not found.", "error")

        conn.close()

    return render_template('update.html')  # Render update password page


@app.route("/save_subjects", methods=["POST"])
def save_subjects():
    try:
        data = request.json
        subjects = data.get("subjects", [])
        if not subjects:
            return jsonify({"error": "No subjects provided"}), 400

        conn = sqlite3.connect("db_AcademicPlannerAdvisor.db")
        cursor = conn.cursor()

        for subject in subjects:
            department = subject["department"]
            department = re.sub(r"[^a-zA-Z0-9_]", "_", department)  # Replace special characters with "_"
            semester = subject["semester"]
            year = subject["year"]
            year = re.sub(r"[^a-zA-Z0-9_]", "_", year)  # Replace special characters with "_"

            # Dynamically create a table name
            table_name = f"{year}_sem_{semester}_{department}"

            # Create the table if it doesn't exist
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject_code TEXT ,
                    department TEXT,
                    semester TEXT,
                    year TEXT,
                    subject_name TEXT,
                    subject_type TEXT,
                    no_of_hours INTEGER
                )
            """)

            try:
                # Check if record already exists
                cursor.execute(f"""
                               SELECT * FROM {table_name}
                               WHERE subject_code=? AND department=? AND semester=? AND year=? 
                                 AND subject_name= ? AND subject_type=? AND no_of_hours=?
                               """, (subject["subject_code"], subject["department"], subject["semester"],
                                     subject["year"], subject["subject_name"], subject["subject_type"],
                                     subject["no_of_hours"]))

                existing_record = cursor.fetchone()

                if existing_record:
                    conn.close()
                    return jsonify({"error": "Duplicate entry! This subject details already exists."}), 400

                #  Insert data into the dynamic table
                cursor.execute(f"""
                    INSERT INTO {table_name} 
                    (subject_code, department, semester, year, subject_name, subject_type, no_of_hours)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    subject["subject_code"], subject["department"], subject["semester"],
                    subject["year"], subject["subject_name"], subject["subject_type"],
                    subject["no_of_hours"]
                ))

            except sqlite3.IntegrityError:
                return jsonify({"error": f"Subject code {subject['subject_code']} already exists in {table_name}"}), 400

        conn.commit()
        conn.close()
        return jsonify({"message": f"Subjects saved successfully in {table_name}!"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# API to save staff details
@app.route("/save_staff", methods=["POST"])
def save_staff():
    try:
        # Receive JSON data from request
        data = request.json
        staff_name = data.get("staff_name")
        department = data.get("department")
        department = re.sub(r"[^a-zA-Z0-9_]", "_", department)  # Replace special characters with "_"
        semester = data.get("semester")
        year = data.get("year")
        total_students = data.get("total_students", 0)
        no_of_subjects = data.get("no_of_subjects", 0)

        subject_names = data.get("subject_names", [])  # Expecting a list
        subject_types = data.get("subject_types", [])  # Expecting a list
        subject_hours = data.get("subject_hours", [])  # Expecting a list
        students_per_batch = data.get("students_per_batch", [])  # Expecting a list

        # Ensure all required fields are provided
        if not (staff_name and department and semester and year and total_students and no_of_subjects and subject_hours):
            return jsonify({"error": "All fields are required"}), 400

        if not subject_names or not all(subject_names) or not subject_types or not all(subject_types) or not students_per_batch:
            return jsonify({"error": "Subject names,types,hours and student counts cannot be empty"}), 400

        # Convert list to comma-separated string
        subject_names_str = ",".join((map(str,subject_names)))
        subject_types_str = ",".join((map(str,subject_types)))
        subject_hours_str = ",".join(map(str, subject_hours))
        students_per_batch_str = ",".join(map(str, students_per_batch))

        # Ensure all required fields are provided
        if not all([staff_name, department, semester, year, total_students, no_of_subjects, subject_names_str, subject_types_str,
                    subject_hours_str,students_per_batch_str]):
            return jsonify({"error": "All fields are required"}), 400

        # Connect to SQLite database
        conn = sqlite3.connect("db_AcademicPlannerAdvisor.db")
        cursor = conn.cursor()

        basic_engg_departments = {"Basic_Engg_CE_IT", "Basic_Engg_ECE", "Basic_Engg_EEE", "Basic_Engg_CIVIL",
                                  "Basic_Engg_MECH", "Basic_Engg_AUTO"}
        if department in basic_engg_departments:
            table_name = f"staff_Basic"
        elif department  in {"CE","IT"}:
            table_name = f"staff_CE_IT"
        else:
            table_name = f"staff_{department}"

        # Create table if it doesn't exist
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                staff_name TEXT,
                department TEXT NOT NULL,
                semester TEXT NOT NULL,
                year TEXT NOT NULL,
                no_of_subjects INTEGER NOT NULL,
                subject_names TEXT NOT NULL,   
                subject_types TEXT NOT NULL,
                hours_per_week INTEGER NOT NULL,
                students_per_batch INTEGER NOT NULL,
                total_students INTEGER NOT NULL
            )
        """)

        # Check if record already exists
        cursor.execute(f"""
               SELECT * FROM {table_name}
               WHERE staff_name=? AND department=? AND semester=? AND year=?  AND no_of_subjects=?
                 AND subject_names= ? AND subject_types=? AND hours_per_week=? AND students_per_batch=? AND total_students=?
           """, (staff_name, department, semester, year, no_of_subjects, subject_names_str, subject_types_str, subject_hours_str,students_per_batch_str,total_students))

        existing_record = cursor.fetchone()

        if existing_record:
            conn.close()
            return jsonify({"error": "Duplicate entry! This staff data already exists."}), 400

        # Insert staff details into the table
        cursor.execute(f"""
            INSERT INTO {table_name} (staff_name, department, semester, year, no_of_subjects, subject_names, 
            subject_types,hours_per_week, students_per_batch, total_students) VALUES (?, ?, ?, ?, ?, ?, ?,?,?,?)
             """, (staff_name, department, semester, year, no_of_subjects, subject_names_str,
                   subject_types_str, subject_hours_str, students_per_batch_str, total_students))

        # Commit and close connection
        conn.commit()
        conn.close()

        return jsonify({"message": f"Staff details saved successfully in {table_name}!"})

    except sqlite3.IntegrityError:
        return jsonify({"error": f"Duplicate entry. Staff already exists in {table_name}."}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/save_classroom", methods=["POST"])
def save_classroom():
    try:
        data = request.json
        department = data.get("department", "").strip()
        department = re.sub(r"[^a-zA-Z0-9_]", "_", department)  # Normalize department name
        no_of_classroom = data.get("no_of_classroom", 0)
        no_of_lab = data.get("no_of_lab", 0)
        classroom_names = data.get("classroom_names", [])
        lab_details = data.get("lab_details", [])

        if not department or no_of_classroom <= 0 or not classroom_names or not all(classroom_names) \
                or no_of_lab <= 0 or not lab_details or not all(ld.get("lab_name") and ld.get("subjects") for ld in lab_details):
            return jsonify({"error": "All fields are required"}), 400

        classroom_names_str = ",".join(classroom_names)
        lab_names = [ld["lab_name"] for ld in lab_details]
        lab_names_str = ",".join(lab_names)

        conn = sqlite3.connect("db_AcademicPlannerAdvisor.db")
        cursor = conn.cursor()

        # Main class list table
        table_classlist = f"ClassList_{department}"
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_classlist} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                department TEXT NOT NULL,
                no_of_classroom INTEGER NOT NULL,
                classroom_names TEXT NOT NULL,
                no_of_lab INTEGER NOT NULL,
                lab_names TEXT NOT NULL
            )
        """)

        # Lab details table (lab name, subject count, each subject name)
        table_labdetails = f"LabDetails_{department}"
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_labdetails} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lab_name TEXT NOT NULL,
                subject_count INTEGER NOT NULL,
                subject_name TEXT NOT NULL
            )
        """)

        # Check for duplicate class list
        cursor.execute(f"""
            SELECT * FROM {table_classlist}
            WHERE department = ? AND no_of_classroom = ? AND classroom_names = ? AND
                  no_of_lab = ? AND lab_names = ?
        """, (department, no_of_classroom, classroom_names_str, no_of_lab, lab_names_str))
        if cursor.fetchone():
            conn.close()
            return jsonify({"error": "Duplicate entry! This ClassList data already exists."}), 400

        # Insert into class list
        cursor.execute(f"""
            INSERT INTO {table_classlist} (department, no_of_classroom, classroom_names, no_of_lab, lab_names)
            VALUES (?, ?, ?, ?, ?)
        """, (department, no_of_classroom, classroom_names_str, no_of_lab, lab_names_str))

        # Insert into lab details table
        for lab in lab_details:
            lab_name = lab["lab_name"]
            subject_count = lab["subject_count"]
            for subject in lab["subjects"]:
                cursor.execute(f"""
                    INSERT INTO {table_labdetails} (lab_name, subject_count, subject_name)
                    VALUES (?, ?, ?)
                """, (lab_name, subject_count, subject))

        conn.commit()
        conn.close()

        return jsonify({"message": f"All details saved successfully in {table_classlist} and {table_labdetails}"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/timetable_staff", methods=["POST"])
def timetable_staff():
    try:
        data = request.json
        department = data.get("department", "").strip()
        hours_per_day = int(data.get("hours_per_day", 0))
        total_students = int(data.get("total_students", 0))
        time_slots = data.get("time_slot", [])
        days = ["MON", "TUE", "WED", "THU", "FRI"]

        if not department or not hours_per_day or not time_slots:
            return jsonify({"error": "Missing required fields"}), 400

        conn = sqlite3.connect("db_AcademicPlannerAdvisor.db")
        cursor = conn.cursor()
        staff_data = fetch_staff_data(cursor, department)
        conn.close()

        if not staff_data:
            return jsonify({"error": "No staff data found"}), 404

        timetable = {
            staff["staff_name"]: {
                day: ["-" for _ in range(hours_per_day)]
                for day in days
            } for staff in staff_data
        }

        theory_subjects = []
        pdpt_subjects = []
        lab_subjects_by_sem = defaultdict(list)

        for staff in staff_data:
            staff["hours"] = staff["hours_per_week"]
            staff["subject"] = staff["subject_names"].strip().title()
            staff["subject_type"] = staff["subject_types"].strip().lower()
            staff["students_per_batch"] = int(staff.get("students_per_batch", total_students))

            if staff["subject_type"] in ["practical", "practicum"]:
                lab_subjects_by_sem[(staff["semester"], staff["year"])].append(staff)
            elif staff["subject_type"] in ["pd", "pt"]:
                pdpt_subjects.append(staff)
            else:
                theory_subjects.append(staff)

        # Allocate paired lab sessions
        for key, staff_list in lab_subjects_by_sem.items():
            paired = list(zip(staff_list[::2], staff_list[1::2]))
            for staff1, staff2 in paired:
                split_parts = determine_split(staff1["hours"], hours_per_day)
                for part in split_parts:
                    assigned = False
                    for _ in range(100):
                        day = random.choice(days)
                        start = random.randint(0, hours_per_day - part)
                        if all(timetable[staff1["staff_name"]][day][start+i] == "-" for i in range(part)) and \
                           all(timetable[staff2["staff_name"]][day][start+i] == "-" for i in range(part)):
                            for i in range(part):
                                timetable[staff1["staff_name"]][day][start+i] = f"{staff1['subject']} Lab - Batch 1"
                                timetable[staff2["staff_name"]][day][start+i] = f"{staff2['subject']} Lab - Batch 2"
                            assigned = True
                            break
                    if not assigned:
                        print(f"❌ Could not allocate paired lab for {staff1['staff_name']} and {staff2['staff_name']}")

        # Allocate unpaired labs (odd one out)
        for key, staff_list in lab_subjects_by_sem.items():
            if len(staff_list) % 2 != 0:
                leftover = staff_list[-1]
                split_parts = determine_split(leftover["hours"], hours_per_day)
                for part in split_parts:
                    day, start = find_slot(timetable[leftover["staff_name"]], hours_per_day, part, days)
                    if day:
                        for i in range(part):
                            timetable[leftover["staff_name"]][day][start+i] = f"{leftover['subject']} Lab"

        # Allocate theory
        for staff in theory_subjects:
            label = f"{staff['subject']} (Theory)"
            slots_assigned = 0
            trials = 0
            while slots_assigned < staff["hours"] and trials < 300:
                trials += 1
                day = random.choice(days)
                slot = random.randint(0, hours_per_day - 1)
                if timetable[staff["staff_name"]][day][slot] == "-":
                    timetable[staff["staff_name"]][day][slot] = label
                    slots_assigned += 1

        # Allocate PD/PT
        for staff in pdpt_subjects:
            label = f"{staff['subject']} (Theory)"
            slots_assigned = 0
            trials = 0
            while slots_assigned < staff["hours"] and trials < 300:
                trials += 1
                day = random.choice(days)
                slot = random.randint(0, hours_per_day - 1)
                if timetable[staff["staff_name"]][day][slot] == "-":
                    timetable[staff["staff_name"]][day][slot] = label
                    slots_assigned += 1

        return jsonify({"timetable": timetable, "time_slot": time_slots})

    except Exception as e:
        print("❌ Error:", str(e))
        return jsonify({"error": "Internal server error"}), 500


def fetch_staff_data(cursor, department):
    table_name = f"staff_{department}"
    try:
        cursor.execute(
            f"SELECT staff_name, semester, year, subject_names, subject_types, hours_per_week, students_per_batch FROM {table_name}"
        )
        rows = cursor.fetchall()
    except sqlite3.Error as e:
        print("DB Error:", e)
        return []

    col_names = [desc[0] for desc in cursor.description]
    data = [dict(zip(col_names, row)) for row in rows]

    for row in data:
        row["hours_per_week"] = extract_hours(row["hours_per_week"])[0]
        row["students_per_batch"] = safe_int(row["students_per_batch"])
    return data


def find_slot(staff_day_slots, hours_per_day, duration, days):
    for _ in range(100):
        day = random.choice(days)
        start = random.randint(0, hours_per_day - duration)
        if all(staff_day_slots[day][start+i] == "-" for i in range(duration)):
            return day, start
    return None, None


def extract_hours(hours_str):
    if not hours_str:
        return [0]
    if not isinstance(hours_str, str):
        hours_str = str(hours_str)
    hours_list = re.findall(r'\d+', hours_str)
    return [int(hour) for hour in hours_list] if hours_list else [0]


def determine_split(total_hours, hours_per_day):
    if total_hours == 6:
        return random.choice([[2, 2, 2], [2, 4]]) if hours_per_day == 8 else [3, 3]
    elif total_hours == 4:
        return [2, 2]
    elif total_hours == 8:
        return [4, 4]
    elif total_hours == 9:
        return [3, 3, 3]
    elif total_hours == 7:
        return [3, 3, 1]
    else:
        return [total_hours]


def safe_int(value, default=0):
    try:
        return int(value) if value else default
    except ValueError:
        return default



if __name__ == '__main__':
    app.run(debug=True)
