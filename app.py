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
        department = data.get("department")
        department = re.sub(r"[^a-zA-Z0-9_]", "_", department)
        hours_per_day = int(data.get("hours_per_day", 0))
        time_slots = data.get("time_slot", [])

        if not department or not hours_per_day or not time_slots:
            return jsonify({"error": "Missing required fields"}), 400

        conn = sqlite3.connect("db_AcademicPlannerAdvisor.db")
        cursor = conn.cursor()

        basic_engg_departments = {
            "Basic_Engg_CE_IT", "Basic_Engg_ECE", "Basic_Engg_EEE",
            "Basic_Engg_CIVIL", "Basic_Engg_MECH", "Basic_Engg_AUTO"
        }
        table_name = "staff_Basic" if department in basic_engg_departments else f"staff_{department}"

        cursor.execute(f"""
            SELECT staff_name, department, semester, year, total_students, subject_names,
                   subject_types, hours_per_week, students_per_batch
            FROM {table_name}
        """)
        staff_data = cursor.fetchall()
        conn.close()

        if not staff_data:
            return jsonify({"error": "No data found for the selected department"}), 404

        days = ["MON", "TUE", "WED", "THU", "FRI"]
        periods = hours_per_day
        timetable = generate_timetable(staff_data, days, periods)
        save_timetable_to_db(department, timetable, time_slots)

        return jsonify({"message": "Timetable generated successfully", "timetable": timetable})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def generate_timetable(staff_data, days, periods):
    timetable = {}
    global_schedule = {d: {p: {} for p in range(periods)} for d in days}
    practical_pairs = {}

    # Initialize empty timetable
    for staff in staff_data:
        staff_name = staff[0]
        timetable[staff_name] = {d: ["-" for _ in range(periods)] for d in days}

    print("\n=== Parsing Staff Data ===")
    for staff in staff_data:
        if len(staff) < 9:
            print(f"Skipping invalid staff data: {staff}")
            continue

        staff_name, department, semester, year, total_students, subject_names, subject_types, hours_per_week, students_per_batch_raw = staff
        total_students = int(total_students)

        subjects_list = str(subject_names).split(",")
        subject_types_list = str(subject_types).split(",") if subject_types else ["Theory"] * len(subjects_list)
        hours_list = extract_hours(hours_per_week)
        students_per_batch_list = [int(x.strip()) for x in str(students_per_batch_raw).split(",") if x.strip().isdigit()]

        if len(hours_list) != len(subjects_list):
            print(f"Warning: Mismatched hours for {staff_name}. Defaulting to 1 hour per subject.")
            hours_list = [1] * len(subjects_list)
        if len(students_per_batch_list) != len(subjects_list):
            students_per_batch_list = [students_per_batch_list[0]] * len(subjects_list)

        subject_info = list(zip(subjects_list, subject_types_list, hours_list, students_per_batch_list))
        print(f"\n{staff_name} - Subjects:")
        for subject, sub_type, hours, students_per_batch in subject_info:
            print(f"   Subject: {subject.strip()}, Type: {sub_type}, Hours: {hours}, Students/Batch: {students_per_batch}")

        for subject, sub_type, hours, students_per_batch in subject_info:
            if "practical" in sub_type.lower() or "practicum" in sub_type.lower():
                key = (semester, year, department)
                practical_pairs.setdefault(key, []).append({
                    "staff_name": staff_name,
                    "subject": subject.strip(),
                    "hours": int(hours),
                    "total_students": total_students,
                    "students_per_batch": students_per_batch
                })

    print("\n=== Allocating Practical/Practicum Subjects ===")
    for key, pairs in practical_pairs.items():
        random.shuffle(pairs)
        while len(pairs) >= 2:
            p1 = pairs.pop()
            p2 = pairs.pop()
            print(f"\nPairing: {p1['staff_name']} ({p1['subject']}) <--> {p2['staff_name']} ({p2['subject']})")

            if p1["staff_name"] not in timetable or p2["staff_name"] not in timetable:
                print("Skipping invalid pairing (staff not found in timetable).")
                continue

            split_pattern = determine_split(p1["hours"] * 2, periods, p1["total_students"], p1["students_per_batch"])
            print(f"   Split pattern: {split_pattern}")

            for chunk in split_pattern:
                allocated = False
                for d in days:
                    for p in range(1, periods - chunk + 2):
                        if any(global_schedule[d][p - 1 + j] for j in range(chunk)) or \
                           any(timetable[p1["staff_name"]][d][p - 1 + j] != "-" for j in range(chunk)) or \
                           any(timetable[p2["staff_name"]][d][p - 1 + j] != "-" for j in range(chunk)):
                            continue

                        for j in range(chunk):
                            timetable[p1["staff_name"]][d][p - 1 + j] = f"{p1['subject']} Lab (Batch 1)"
                            timetable[p2["staff_name"]][d][p - 1 + j] = f"{p2['subject']} Lab (Batch 2)"
                            global_schedule[d][p - 1 + j][key] = True

                        print(f"   Allocated {chunk} periods on {d}, period {p}")
                        allocated = True
                        break
                    if allocated:
                        break
                if not allocated:
                    print(f"Could not allocate {chunk} periods for {p1['subject']} and {p2['subject']}")

        # Solo labs
        if len(pairs) == 1:
            p = pairs.pop()
            print(f"\nSolo Practical: {p['staff_name']} - {p['subject']}")
            if p["staff_name"] not in timetable:
                print("Skipping invalid solo lab staff.")
                continue

            hours = p["hours"]
            label = "Lab" if p["total_students"] == p["students_per_batch"] else "Lab (Batch 1)"
            hours_to_allocate = hours if label == "Lab" else hours * 2
            split_pattern = determine_split(hours_to_allocate, periods, p["total_students"], p["students_per_batch"])
            print(f"   Split pattern: {split_pattern}")

            for chunk in split_pattern:
                allocated = False
                for d in days:
                    for i in range(1, periods - chunk + 2):
                        if any(global_schedule[d][i - 1 + j] for j in range(chunk)) or \
                           any(timetable[p["staff_name"]][d][i - 1 + j] != "-" for j in range(chunk)):
                            continue

                        for j in range(chunk):
                            timetable[p["staff_name"]][d][i - 1 + j] = f"{p['subject']} {label}"
                            global_schedule[d][i - 1 + j][key] = True

                        print(f"   Allocated {chunk} periods for {p['subject']} ({label}) on {d}, starting at period {i}")
                        allocated = True
                        break
                    if allocated:
                        break
                if not allocated:
                    print(f"Could not allocate {chunk} periods for solo lab {p['subject']}")

    print("\n=== Allocating Theory and PD/PT Subjects ===")
    for staff in staff_data:
        if len(staff) < 9:
            continue

        staff_name, _, semester, year, _, subject_names, subject_types, hours_per_week, _ = staff
        subjects_list = str(subject_names).split(",")
        subject_types_list = str(subject_types).split(",") if subject_types else ["Theory"] * len(subjects_list)
        hours_list = extract_hours(hours_per_week)

        if len(hours_list) != len(subjects_list):
            print(f"Warning: Mismatched hours for {staff_name}. Defaulting to 1 hour per subject.")
            hours_list = [1] * len(subjects_list)

        theory_subjects = list(zip(subjects_list, subject_types_list, hours_list))
        random.shuffle(theory_subjects)  # Randomize subject order

        for subject, sub_type, hours in theory_subjects:
            if "practical" in sub_type.lower() or "practicum" in sub_type.lower():
                continue

            subject = subject.strip()
            label = f"{subject} (PD/PT)" if "pd" in subject.lower() or "pt" in subject.lower() else f"{subject} (Theory)"
            allocated = 0
            attempts = 0
            max_attempts = 1000

            print(f"\nAllocating {label} for {staff_name}, Hours/Week: {hours}")

            while allocated < int(hours) and attempts < max_attempts:
                day_shuffled = random.sample(days, len(days))
                progress = False

                for day in day_shuffled:
                    # Avoid placing the same subject multiple times on same day
                    if timetable[staff_name][day].count(label) >= 1:
                        continue

                    periods_shuffled = list(range(1, periods + 1))
                    random.shuffle(periods_shuffled)

                    for p in periods_shuffled:
                        idx = p - 1
                        if timetable[staff_name][day][idx] != "-":
                            continue
                        if (semester, year, staff_name) in global_schedule[day][idx]:
                            continue

                        # Avoid consecutive same-subject slots
                        prev_slot = timetable[staff_name][day][idx - 1] if p > 1 else None
                        next_slot = timetable[staff_name][day][idx + 1] if p < periods else None
                        if prev_slot == label or next_slot == label:
                            continue

                        # Assign slot
                        timetable[staff_name][day][idx] = label
                        global_schedule[day][idx][(semester, year, staff_name)] = label
                        allocated += 1
                        print(f"   Assigned to {day}, period {p}")
                        progress = True
                        break

                    if progress:
                        break

                if not progress:
                    print(f"Could not find available slot for {label} for {staff_name}. Allocated {allocated}/{hours}")
                    break

                attempts += 1

    print("\n=== Timetable Generation Complete ===")
    return timetable


def determine_split(hours, periods_per_day, total_students, students_per_batch):
    if total_students == students_per_batch:
        return [hours]
    if hours == 6:
        if periods_per_day == 8:
            return [2, 4]
        elif periods_per_day == 7:
            return [3, 3]
        else:
            return [2, 2, 2]
    elif hours == 4:
        return [2, 2]
    else:
        return [hours]


def extract_hours(hours_str):
    if isinstance(hours_str, int):
        return [hours_str]
    if isinstance(hours_str, str):
        return [int(h.strip()) for h in hours_str.split(",") if h.strip().isdigit()]
    return [0]


def save_timetable_to_db(department, timetable, time_slots):
    """Store the generated timetable into SQLite database."""
    conn = sqlite3.connect("db_AcademicPlannerAdvisor.db")
    cursor = conn.cursor()

    table_name = f"staff_timetable_{department}"

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_name TEXT,
            day TEXT,
            period INTEGER,
            subject TEXT
        )
    """)

    cursor.execute(f"DELETE FROM {table_name}")

    for staff_name, schedule in timetable.items():
        for day, periods in schedule.items():
            for period_index, subject in enumerate(periods):
                cursor.execute(f"""
                    INSERT INTO {table_name} (staff_name, day, period, subject) 
                    VALUES (?, ?, ?, ?)
                """, (staff_name, day, period_index + 1, subject))

    conn.commit()
    conn.close()

def fetch_staff_timetable_from_db(department):
    """Fetch the timetable from the database."""
    conn = sqlite3.connect("db_AcademicPlannerAdvisor.db")
    query = f"SELECT staff_name, day, period, subject FROM staff_timetable_{department} ORDER BY staff_name, day, period"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def format_staff_timetable(df):
    """Format the timetable into a structure for display."""
    timetable = {}
    for _, row in df.iterrows():
        staff = row["staff_name"]
        day = row["day"]
        period = row["period"]
        subject = row["subject"]

        if staff not in timetable:
            timetable[staff] = {d: ["-" for _ in range(8)] for d in ["MON", "TUE", "WED", "THU", "FRI"]}

        timetable[staff][day][period - 1] = subject
    return timetable

@app.route('/timetable/<department>')
def display_timetable(department):
    try:
        df = fetch_staff_timetable_from_db(department)

        if df.empty:
            return "No timetable found for this department.", 404  # Handle empty timetable case

        timetable = format_staff_timetable(df)
        return render_template('staff_timetable.html', timetable=timetable)

    except Exception as e:
        return f"Error loading timetable: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
