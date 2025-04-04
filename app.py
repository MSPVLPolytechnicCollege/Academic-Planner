from flask import Flask, render_template, redirect, flash, session, url_for, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
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
        no_of_subjects = data.get("no_of_subjects", 0)

        subject_names = data.get("subject_names", [])  # Expecting a list
        subject_types = data.get("subject_types", [])  # Expecting a list
        subject_hours = data.get("subject_hours", [])  # Expecting a list
        students_per_batch = data.get("students_per_batch", [])  # Expecting a list

        # Ensure all required fields are provided
        if not (staff_name and department and semester and year and no_of_subjects and subject_hours):
            return jsonify({"error": "All fields are required"}), 400

        if not subject_names or not all(subject_names) or not subject_types or not all(subject_types) or not students_per_batch:
            return jsonify({"error": "Subject names,types,hours and student counts cannot be empty"}), 400

        # Convert list to comma-separated string
        subject_names_str = ",".join(subject_names)
        subject_types_str = ",".join(subject_types)
        subject_hours_str = ",".join(subject_hours)
        students_per_batch_str = ",".join(students_per_batch)

        # Ensure all required fields are provided
        if not all([staff_name, department, semester, year, no_of_subjects, subject_names_str, subject_types_str,
                    subject_hours_str,students_per_batch_str]):
            return jsonify({"error": "All fields are required"}), 400

        # Connect to SQLite database
        conn = sqlite3.connect("db_AcademicPlannerAdvisor.db")
        cursor = conn.cursor()

        # Table name based on department
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
                students_per_batch INTEGER NOT NULL
            )
        """)

        # Check if record already exists
        cursor.execute(f"""
               SELECT * FROM {table_name}
               WHERE staff_name=? AND department=? AND semester=? AND year=? 
                 AND subject_names= ? AND subject_types=? AND hours_per_week=? AND students_per_batch=?
           """, (staff_name, department, semester, year, subject_names_str, subject_types_str, subject_hours_str,students_per_batch_str))

        existing_record = cursor.fetchone()

        if existing_record:
            conn.close()
            return jsonify({"error": "Duplicate entry! This staff data already exists."}), 400

        # Insert staff details into the table
        cursor.execute(f"""
            INSERT INTO {table_name} (staff_name, department, semester, year, no_of_subjects, subject_names, 
            subject_types,hours_per_week, students_per_batch) VALUES (?, ?, ?, ?, ?, ?, ?,?,?)
             """, (staff_name, department, semester, year, no_of_subjects, subject_names_str,
                   subject_types_str, subject_hours_str, students_per_batch_str))

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
        # Receive JSON data from request
        data = request.json
        department = data.get("department").strip()
        department = re.sub(r"[^a-zA-Z0-9_]", "_", department)  # Replace special characters with "_"
        no_of_classroom = data.get("no_of_classroom", 0)
        no_of_lab = data.get("no_of_lab", 0)
        classroom_names = data.get("classroom_names", [])  # Comma-separated string
        lab_names = data.get("lab_names", [])  # Comma-separated string

        # Ensure all required fields are provided
        if (not department or no_of_classroom <= 0 or not classroom_names or not all(classroom_names)
                or no_of_lab <= 0 or not lab_names or not all(lab_names)):
            return jsonify({"error": "All fields are required"}), 400

        # Convert list to comma-separated string
        classroom_names_str = ",".join(classroom_names)
        lab_names_str = ",".join(lab_names)

        conn = sqlite3.connect("db_AcademicPlannerAdvisor.db")
        cursor = conn.cursor()

        # table name based on department
        table_name = f"ClassList_{department}"

        cursor.execute(f"""
         CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                department TEXT NOT NULL,
                no_of_classroom INTEGER NOT NULL,
                classroom_names TEXT NOT NULL,  
                no_of_lab INTEGER NOT NULL,
                lab_names TEXT NOT NULL )
        """)

        # Check if record already exists
        cursor.execute(f"""
                      SELECT * FROM {table_name}
                      WHERE department = ? AND no_of_classroom = ? AND classroom_names LIKE ? AND
                      no_of_lab = ? AND lab_names LIKE ?
                  """, (department, no_of_classroom, f"%{classroom_names_str}%", no_of_lab, f"%{lab_names_str}%"))

        existing_record = cursor.fetchone()

        if existing_record:
            conn.close()
            return jsonify({"error": "Duplicate entry! This ClassList data already exists."}), 400

        cursor.execute(f'''
            INSERT INTO {table_name} (department, no_of_classroom, classroom_names, no_of_lab, lab_names)
            VALUES (?, ?, ?, ?, ?)
        ''', (department, no_of_classroom, classroom_names_str, no_of_lab, lab_names_str))

        conn.commit()
        conn.close()

        return jsonify({"message": f"All details saved successfully in {table_name}"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/timetable_staff", methods=["POST"])
def timetable_staff():
    try:
        data = request.json
        print("Received data:", data)  # Debugging

        department = data.get("department", "").strip()
        hours_per_day = int(data.get("hours_per_day", 0))
        total_students = int(data.get("total_students" , 0))
        time_slots = data.get("time_slot", [])

        if not department or hours_per_day <= 0:
            return jsonify({"error": "Invalid department or hours per day"}), 400

        if not time_slots or not isinstance(time_slots, list):
            return jsonify({"error": "Invalid or missing time slot data"}), 400

        conn = sqlite3.connect("db_AcademicPlannerAdvisor.db")
        cursor = conn.cursor()
        staff_data = fetch_staff_data(cursor, department)
        conn.close()

        if not staff_data:
            return jsonify({"error": "No data found for the selected department"}), 404

        timetable = generate_timetable_structure(staff_data, hours_per_day,time_slots)
        timetable = allocate_classes(timetable, staff_data, hours_per_day)

        return jsonify({"timetable": timetable, "time_slot": time_slots})
    except Exception as e:
        print(f"Error: {str(e)}")  # Logs the error
        return jsonify({"error": "An error occurred while generating the timetable"}), 500



def extract_hours(hours_str):
    """Extracts hours from a given string."""
    if not hours_str:
        return [0]
    if not isinstance(hours_str, str):
        hours_str = str(hours_str)
    hours_list = re.findall(r'\d+', hours_str)
    return [int(hour) for hour in hours_list] if hours_list else [0]

def determine_split(total_hours, hours_per_day):
    """Determines how lab hours should be split across multiple days."""
    if total_hours == 6:
        return [2, 2, 2] if hours_per_day == 8 else [3, 3]
    elif total_hours == 4:
        return [2, 2]
    elif total_hours == 8:
        return [4, 4]
    elif total_hours == 9:
        return [3, 3, 3]
    elif total_hours == 7:
        return [3, 3]
    else:
        return [total_hours]

def generate_timetable_structure(staff_data, hours_per_day, time_slots):
    """Creates an empty timetable structure for all staff members."""
    days = ["MON", "TUE", "WED", "THU", "FRI"]

    return {
        staff["staff_name"]: {
            day: [{"slot": time_slots[i], "subject": "-"} for i in range(hours_per_day)]
            for day in days
        }
        for staff in staff_data
    }

def is_slot_available(timetable, staff_name, day, start_slot, duration):
    """Checks if the required time slots are free for allocation."""
    try:
        return all(
            timetable[staff_name][day][slot]["subject"] == "-"
            for slot in range(start_slot, start_slot + duration)
        )
    except IndexError:
        return False

def allocate_classes(timetable, staff_data, hours_per_day):
    """Allocates theory and practical classes into the timetable."""
    days = ["MON", "TUE", "WED", "THU", "FRI"]
    day_index = 0

    for staff in staff_data:
        staff_name = staff["staff_name"]
        subject = staff["subject_names"]
        subject_type = staff["subject_types"].lower()
        total_hours = sum(extract_hours(staff.get("hours_per_week", "0")))

        for _ in range(total_hours):
            assigned = False
            for _ in range(50):  # Retry mechanism
                day = days[day_index % len(days)]
                start_slot = random.randint(0, hours_per_day - 1)

                if is_slot_available(timetable, staff_name, day, start_slot, 1):
                    timetable[staff_name][day][start_slot]["subject"] = f"{subject} ({subject_type.capitalize()})"
                    assigned = True
                    break

            if not assigned:
                print(f"❌ Could not assign all hours for {staff_name} - {subject}")

            day_index += 1

    return timetable


def mutate(timetable):
    """Randomly swaps two slots for a staff member to create a mutation."""
    staff_name = random.choice(list(timetable.keys()))
    day = random.choice(list(timetable[staff_name].keys()))

    slots = [i for i, period in enumerate(timetable[staff_name][day]) if period["subject"] != "-"]

    if len(slots) >= 2:
        slot1, slot2 = random.sample(slots, 2)
        period1, period2 = timetable[staff_name][day][slot1]["subject"], timetable[staff_name][day][slot2]["subject"]

        if ("Lab" in period1 and "Theory" in period2) or ("Lab" in period2 and "Theory" in period1):
            print("Mutation skipped: Swapping between Lab and Theory is not allowed.")
            return timetable  # Skip mutation if it violates constraints

        timetable[staff_name][day][slot1]["subject"], timetable[staff_name][day][slot2]["subject"] = period2, period1
        print(f" Mutation: Swapped {period1} and {period2} for {staff_name} on {day}")

    return timetable


def fetch_staff_data(cursor, department):
    table_name = f"staff_{department}"

    try:
        cursor.execute(
            f"SELECT staff_name, semester, year, subject_names, subject_types, hours_per_week, students_per_batch FROM {table_name}"
        )
        staff_data = cursor.fetchall()
        print("Raw Data Fetched from DB:", staff_data)  # ✅ Debugging: Print raw fetched data
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []

    if not staff_data:
        print("No staff data retrieved")
        return []

    column_names = [desc[0] for desc in cursor.description]
    staff_data_dict = [dict(zip(column_names, row)) for row in staff_data]

    # ✅ Debugging: Print formatted data
    print("\nFormatted Staff Data (Before Extracting Hours):")
    for staff in staff_data_dict:
        print(staff)

    # Convert `hours_per_week` to a list of integers
    for staff in staff_data_dict:
        staff['hours_per_week'] = extract_hours(staff['hours_per_week'])

    print("\nFormatted Staff Data (After Extracting Hours):")
    for staff in staff_data_dict:
        staff['students_per_batch'] = safe_int(staff['students_per_batch'])
        print(staff)

    return staff_data_dict

def safe_int(value, default=0):
    try:
        return int(value) if value else default
    except ValueError:
        return default

    
if __name__ == '__main__':
    app.run(debug=True)
