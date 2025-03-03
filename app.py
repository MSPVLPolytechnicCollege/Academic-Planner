from flask import Flask, render_template,redirect, flash, session, url_for,request,jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

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

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['uname']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        password = request.form['pwd']

        conn = sqlite3.connect("db_AcademicPlannerAdvisor.db", check_same_thread=False,timeout=10)
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
        cursor.execute(query, (username, firstname, lastname, email, hashed_password) )
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
        old_password = request.form['passwd_old']
        new_password = request.form['passwd_new']
        confirm_password = request.form['passwd_confirm']

        # Connect to database
        conn = sqlite3.connect("db_AcademicPlannerAdvisor.db")
        cursor = conn.cursor()

        # Fetch user details from database
        cursor.execute("SELECT passwd FROM tbl_login WHERE user_name = ?", (username,))
        user = cursor.fetchone()

        if user:
            db_password_hash = user[0]

            # Check if old password matches
            if check_password_hash(db_password_hash, old_password):

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
                flash("Old password is incorrect.", "error")
        else:
            flash("Username not found.", "error")

        conn.close()

    return render_template('update.html')  # Render update password page


def init_db():
    conn = sqlite3.connect("db_AcademicPlannerAdvisor.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_code TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            semester TEXT NOT NULL,
            year TEXT NOT NULL,
            subject_name TEXT NOT NULL,
            subject_type TEXT NOT NULL,
            no_of_hours INTEGER NOT NULL
        )
    ''')
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                staff_name TEXT NOT NULL,
                department TEXT NOT NULL,
                semester TEXT NOT NULL,
                year TEXT NOT NULL,
                no_of_subjects INTEGER NOT NULL,
                subject_names TEXT NOT NULL
            )
        ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS classrooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department TEXT NOT NULL,
            no_of_classroom INTEGER NOT NULL,
            classroom_names TEXT NOT NULL,
            no_of_lab INTEGER NOT NULL,
            lab_names TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()


# Run this at the start of the application
init_db()

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
            try:
                cursor.execute('''
                    INSERT INTO subjects (subject_code, department, semester, year, subject_name, subject_type, no_of_hours)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    subject["subject_code"], subject["department"], subject["semester"],
                    subject["year"], subject["subject_name"], subject["subject_type"],
                    subject["no_of_hours"]
                ))
            except sqlite3.IntegrityError:
                return jsonify({"error": f"Subject code {subject['subject_code']} already exists"}), 400

        conn.commit()
        conn.close()
        return jsonify({"message": "Subjects saved successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# API to save staff details
@app.route("/save_staff", methods=["POST"])
def save_staff():
    try:
        data = request.json  # Receive JSON data from request
        staff_name = data.get("staff_name")
        department = data.get("department")
        semester = data.get("semester")
        year = data.get("year")
        no_of_subjects = data.get("no_of_subjects")
        subject_names = data.get("subject_names")

        # Check if all fields are provided
        if not all([staff_name, department, semester, year, no_of_subjects, subject_names]):
            return jsonify({"error": "All fields are required"}), 400

        #  Insert data into SQLite database
        conn = sqlite3.connect("db_AcademicPlannerAdvisor.db")
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO staff (staff_name, department, semester, year, no_of_subjects, subject_names)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (staff_name, department, semester, year, no_of_subjects, subject_names))

        conn.commit()
        conn.close()
        return jsonify({"message": "Staff details saved successfully!"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 🔹 API to retrieve all staff details
@app.route("/get_staff", methods=["GET"])
def get_staff():
    try:
        conn = sqlite3.connect("db_AcademicPlannerAdvisor.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM staff")
        staff_list = cursor.fetchall()
        conn.close()

        staff_data = []
        for staff in staff_list:
            staff_data.append({
                "id": staff[0],
                "staff_name": staff[1],
                "department": staff[2],
                "semester": staff[3],
                "year": staff[4],
                "no_of_subjects": staff[5],
                "subject_names": staff[6]
            })

        return jsonify(staff_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/save_classroom", methods=["POST"])
def save_classroom():
    try:
        data = request.json  # Get JSON data from frontend

        # Extract form values
        department = data.get("department")
        no_of_classroom = data.get("no_of_classroom")
        classroom_names = data.get("classroom_names")
        no_of_lab = data.get("no_of_lab")
        lab_names = data.get("lab_names")

        if not (department and classroom_names and lab_names):
            return jsonify({"error": "Missing required fields"}), 400

        conn = sqlite3.connect("db_AcademicPlannerAdvisor.db")
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO classrooms (department, no_of_classroom, classroom_names, no_of_lab, lab_names)
            VALUES (?, ?, ?, ?, ?)
        ''', (department, no_of_classroom, classroom_names, no_of_lab, lab_names))

        conn.commit()
        conn.close()

        return jsonify({"message": "Classroom details saved successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
