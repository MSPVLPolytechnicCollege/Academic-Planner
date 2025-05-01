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
            department = "Basic"

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

        if not department or not hours_per_day:
            return jsonify({"error": "Missing required fields"}), 400

        conn = sqlite3.connect("db_AcademicPlannerAdvisor.db")
        cursor = conn.cursor()

        basic_engg_departments = {
            "Basic_Engg_CE_IT", "Basic_Engg_ECE", "Basic_Engg_EEE",
            "Basic_Engg_CIVIL", "Basic_Engg_MECH", "Basic_Engg_AUTO"
        }

        if department in basic_engg_departments:
            department = "Basic"

        table_name = f"staff_{department}"

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

        # Extract the department, semester, and year from the first staff member (assuming all staff in a request are from the same department, semester, and year)
        target_department = staff_data[0][1]
        target_semester = staff_data[0][2]
        target_year = staff_data[0][3]

        timetable = generate_staff_timetable_with_continuous_labs(staff_data, days, periods, hours_per_day, target_department,
                                                  target_semester, target_year)
        save_timetable_to_db(department, timetable)
        fetch_staff_timetable_from_db(department)



        return jsonify({"message": "Timetable generated Successfully !", "timetable": timetable})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def generate_staff_timetable_with_continuous_labs(staff_data, days, periods, hours_per_day, target_department,
                                                  target_semester, target_year):
    timetable = {}
    global_schedule = {d: {p: None for p in range(periods)} for d in days}

    for staff in staff_data:
        staff_name = staff[0]
        timetable[staff_name] = {d: ["-" for _ in range(periods)] for d in days}

    print("\n=== Generating Timetable ===")

    for staff in staff_data:
        if len(staff) < 9:
            continue

        staff_name, department, semester, year, _, subject_names, subject_types, hours_per_week, _ = staff

        print(f"\n--- Allocating for Staff: {staff_name} ---")

        current_sem = semester
        current_year = year
        current_dept = department

        subjects_list = [s.strip() for s in str(subject_names).split(",")]
        subject_types_list = [s.strip() for s in str(subject_types).split(",")] if subject_types else ["Theory"] * len(subjects_list)
        hours_list = extract_hours(hours_per_week)

        if len(hours_list) != len(subjects_list):
            hours_list = [1] * len(subjects_list)

        subject_info = list(zip(subjects_list, subject_types_list, hours_list))
        random.shuffle(subject_info)

        theory_subjects = []
        practical_subjects = []
        pd_pt_subjects = []

        for subject, sub_type, hours in subject_info:
            if sub_type.lower() in ["pt", "pd", "pt/pd"]:
                pd_pt_subjects.append((subject, sub_type, hours))
            elif "Practical" in sub_type or "Practicum" in sub_type:
                practical_subjects.append((subject, sub_type, hours))
            else:
                theory_subjects.append((subject, sub_type, hours))

        print("Theory Subjects:", theory_subjects)
        print("Practical/Practicum Subjects:", practical_subjects)
        print("PD/PT Subjects:", pd_pt_subjects)

        for subject, sub_type, hours in practical_subjects:
            label = f"{subject} (Lab)"
            splits = get_practical_splits(hours, hours_per_day)
            print(f"Allocating {label} ({hours} hrs/week)")
            print(f"Lab Splits: {splits}")
            success = allocate_lab_periods(
                timetable[staff_name], global_schedule, label, days, periods, splits,
                current_sem, current_year, current_dept
            )
            if not success:
                print(f"  Warning: Could not fully allocate lab {label} for {staff_name}")
            else:
                print(f" Successfully allocated lab {label}.")

        combined_subjects = theory_subjects + pd_pt_subjects
        allocate_subjects(
            timetable[staff_name], global_schedule, combined_subjects,
            days, periods, current_sem, current_year, current_dept
        )

    print("\n=== Timetable Generation Complete ===")
    return timetable


def extract_hours(hours_str):
    if isinstance(hours_str, int):
        return [hours_str]
    if isinstance(hours_str, str):
        return [int(h.strip()) for h in hours_str.split(",") if h.strip().isdigit()]
    return [0]


def get_practical_splits(hours_per_week, hours_per_day):
    if hours_per_day == 8:
        if hours_per_week == 6:
            return [[2, 2, 2], [4, 2], [3,3]]
        elif hours_per_week == 4:
            return [[2, 2], [4]]
        else:
            return [[hours_per_week]]
    elif hours_per_day == 7:
        if hours_per_week == 6:
            return [[3, 3], [4, 2], [2, 2, 2]]
        elif hours_per_week == 4:
            return [[2, 2]]
        else:
            return [[hours_per_week]]
    else:
        if hours_per_week % hours_per_day == 0:
            splits = [[hours_per_week // hours_per_day] * hours_per_day]
        else:
            split_block = hours_per_week // hours_per_day
            remainder = hours_per_week % hours_per_day
            splits = [[split_block] * (hours_per_day - remainder)] + [[split_block + 1] * remainder]
        return splits


def can_allocate_slot(day, slot, global_schedule, current_sem, current_year, current_dept):
    existing = global_schedule[day][slot]
    if existing is None:
        return True
    return not (
        existing['sem'] == current_sem and
        existing['year'] == current_year and
        existing['dept'] == current_dept
    )


def allocate_lab_periods(timetable_staff, global_schedule, label, days, periods, splits,
                         current_sem, current_year, current_dept):
    for split in splits:
        print(f"Trying to allocate {label} with split {split}")
        random_days = days.copy()
        random.shuffle(random_days)

        used_days = set()
        day_slot_allocations = []

        for part_len in split:
            allocated = False
            for day in random_days:
                if day in used_days:
                    continue
                for i in range(periods - part_len + 1):
                    if all(
                        timetable_staff[day][i + j] == "-" and
                        can_allocate_slot(day, i + j, global_schedule, current_sem, current_year, current_dept)
                        for j in range(part_len)
                    ):
                        day_slot_allocations.append((day, list(range(i, i + part_len))))
                        used_days.add(day)
                        allocated = True
                        break
                if allocated:
                    break

        if len(day_slot_allocations) == len(split):
            for day, slots in day_slot_allocations:
                for j in slots:
                    timetable_staff[day][j] = label
                    global_schedule[day][j] = {
                        "label": label,
                        "sem": current_sem,
                        "year": current_year,
                        "dept": current_dept
                    }
                print(f"Allocated {label} on {day} from slot {slots[0]} to {slots[-1]}")
            print(f"Successfully allocated {label} with split {split}.")
            return True
        else:
            print(f"Failed to allocate {label} with split {split}.")
    return False


def allocate_subjects(timetable_staff, global_schedule, subjects, days, periods,
                      current_sem, current_year, current_dept):
    for subject, sub_type, hours in subjects:
        label = f"{subject} ({sub_type})"
        allocated = 0
        print(f"\nAllocating {label} ({hours} hrs/week)")

        day_indices = list(range(len(days)))
        random.shuffle(day_indices)
        attempt_limit = 100

        while allocated < hours and attempt_limit > 0:
            for i in day_indices:
                if allocated >= hours:
                    break
                day = days[i]
                available_slots = [s for s in range(periods)
                                   if timetable_staff[day][s] == "-" and
                                   can_allocate_slot(day, s, global_schedule, current_sem, current_year, current_dept)]

                max_today = min(2, hours - allocated)
                if len(available_slots) >= max_today:
                    chosen_slots = random.sample(available_slots, max_today)
                else:
                    chosen_slots = available_slots[:hours - allocated]

                for slot in chosen_slots:
                    timetable_staff[day][slot] = label
                    global_schedule[day][slot] = {
                        "label": label,
                        "sem": current_sem,
                        "year": current_year,
                        "dept": current_dept
                    }
                    allocated += 1
                    print(f"Allocated {label} on {day}, slot {slot + 1}")

                if allocated >= hours:
                    break
            attempt_limit -= 1

        if allocated < hours:
            print(f" Warning: Could not fully allocate {label}. Allocated {allocated}/{hours}")

def save_timetable_to_db(department, timetable):
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
        print("Formatted Timetable:", timetable)
        return render_template('staff_timetable.html', timetable=timetable)

    except Exception as e:
        return f"Error loading timetable: {str(e)}", 500


@app.route("/timetable_lab", methods=["POST"])
def timetable_lab():
    try:
        data = request.json
        department = data.get("department")
        department = re.sub(r"[^a-zA-Z0-9_]", "_", department)
        lab_hours_per_day = int(data.get("hours_per_day", 0))

        if not department or not lab_hours_per_day:
            return jsonify({"error": "Missing required fields"}), 400

        print(f"[INFO] Request received for department: {department}, lab_hours_per_day: {lab_hours_per_day}")

        conn = sqlite3.connect("db_AcademicPlannerAdvisor.db")
        cursor = conn.cursor()

        # First check staff timetable hours configuration
        cursor.execute(f"""
                SELECT DISTINCT period 
                FROM staff_timetable_{department}
                ORDER BY period DESC
                LIMIT 1
            """)
        max_staff_period = cursor.fetchone()

        if max_staff_period:
            max_staff_period = max_staff_period[0]
            if lab_hours_per_day < max_staff_period:
                return jsonify({
                    "error": f"Incorrect hours per day input. Staff timetable has periods up to {max_staff_period} but lab timetable requested for {lab_hours_per_day} hours."
                }), 400

        # Rest of your existing code for lab timetable generation...
        basic_engg_departments = {
            "Basic_Engg_CE_IT", "Basic_Engg_ECE", "Basic_Engg_EEE",
            "Basic_Engg_CIVIL", "Basic_Engg_MECH", "Basic_Engg_AUTO"
        }

        table_name = f"LabDetails_{department}"
        cursor.execute(f"SELECT lab_name, subject_count, subject_name FROM {table_name}")
        lab_data = cursor.fetchall()

        if not lab_data:
            return jsonify({"error": "No lab data found for the selected department"}), 404

        print(f"[INFO] Lab data retrieved: {lab_data}")

        subject_lab_map = defaultdict(list)
        for lab_name, _, subject_name in lab_data:
            cleaned_subject = subject_name.strip().lower()
            subject_lab_map[cleaned_subject].append(lab_name)

        cursor.execute(f"""
            SELECT staff_name, day, period, subject
            FROM staff_timetable_{department}
            WHERE subject LIKE '%Lab%'
        """)
        lab_sessions = cursor.fetchall()
        print(f"[INFO] Lab sessions fetched: {len(lab_sessions)} records found")

        days = ["MON", "TUE", "WED", "THU", "FRI"]
        lab_timetable = defaultdict(lambda: defaultdict(dict))
        used_slots = defaultdict(lambda: defaultdict(set))

        for staff_name, day, period, subject in lab_sessions:
            print(f"[INFO] Processing lab session: {staff_name} | {subject} | {day} | {period}")
            assigned = False
            subject_base = re.sub(r"\s*\(.*?\)", "", subject).strip().lower()
            mapped_labs = subject_lab_map.get(subject_base, [])

            if not mapped_labs:
                print(f"[WARNING] No mapped lab found for subject: {subject} (normalized: {subject_base})")
                continue

            for lab in mapped_labs:
                if period not in used_slots[lab][day]:
                    lab_timetable[lab][day][period] = {
                        "subject": subject,
                        "staff": staff_name
                    }
                    used_slots[lab][day].add(period)
                    assigned = True
                    print(f"[INFO] Assigned {subject} to {lab} on {day} slot {period} with {staff_name}")
                    break

            if not assigned:
                print(f"[WARNING] Could not assign: {subject} on {day} slot {period} by {staff_name}")

        save_lab_timetable_to_db(department, lab_timetable)

        timetable_json = {
            lab: {
                day: {
                    period: {
                        "staff": info['staff'],
                        "subject": info['subject']
                    }
                    for period, info in day_slots.items()
                }
                for day, day_slots in day_data.items()
            }
            for lab, day_data in lab_timetable.items()
        }

        print(f"[INFO] Timetable generation successful.")
        return jsonify({
            "message": "Lab Timetable generated successfully!",
            "timetable": timetable_json
        })

    except Exception as e:
        print(f"[ERROR] An error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

def save_lab_timetable_to_db(department, timetable):
    conn = sqlite3.connect("db_AcademicPlannerAdvisor.db")
    cursor = conn.cursor()

    table_name = f"lab_timetable_{department}"

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lab_name TEXT,
            day TEXT,
            period INTEGER,
            subject TEXT,
            staff TEXT
        )
    """)

    cursor.execute(f"DELETE FROM {table_name}")

    for lab_name, schedule in timetable.items():
        for day, periods in schedule.items():
            for period, info in periods.items():
                subject = info["subject"]
                staff = info["staff"]
                cursor.execute(f"""
                    INSERT INTO {table_name} (lab_name, day, period, subject, staff) 
                    VALUES (?, ?, ?, ?, ?)
                """, (lab_name, day, int(period), subject, staff))

    conn.commit()
    conn.close()

def fetch_lab_timetable_from_db(department):
    conn = sqlite3.connect("db_AcademicPlannerAdvisor.db")
    query = f"""
        SELECT lab_name, day, period, subject, staff 
        FROM lab_timetable_{department} 
        ORDER BY lab_name, day, period
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def format_lab_timetable(df):
    timetable = {}
    for _, row in df.iterrows():
        lab_name = row["lab_name"]
        day = row["day"]
        period = row["period"]
        subject = row["subject"]
        staff = row["staff"]

        if lab_name not in timetable:
            timetable[lab_name] = {d: ["-" for _ in range(8)] for d in ["MON", "TUE", "WED", "THU", "FRI"]}

        timetable[lab_name][day][period - 1] = f"{subject} ({staff})"
    return timetable

@app.route('/lab_timetable/<department>')
def display_lab_timetable(department):
    try:
        df = fetch_lab_timetable_from_db(department)

        if df.empty:
            return "No lab timetable found for this department.", 404

        timetable = format_lab_timetable(df)
        return render_template('lab_timetable.html', timetable=timetable)

    except Exception as e:
        return f"Error loading lab timetable: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
