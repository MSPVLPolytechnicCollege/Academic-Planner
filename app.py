from flask import Flask, render_template,redirect, flash, session, url_for,request,jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database setup
def init_db():
    """Initialize the database and ensure tbl_subjects table exists."""
    conn = sqlite3.connect('db_AcademicPlannerAdvisor.db')  # Ensure correct DB name
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tbl_subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department TEXT,
            semester TEXT,
            year TEXT,
            subject TEXT
        )
    ''')
    conn.commit()



@app.route('/save_subjects', methods=['POST'])  # Only allow POST requests
def save_subjects():
    init_db()  # Ensure the table exists before inserting data

    # Debugging: Print request data for troubleshooting
    print("🔍 Raw Request Data:", request.data)
    print("🔍 Headers:", request.headers)

    # Attempt to parse JSON
    data = request.get_json(silent=True)

    print("🔍 Parsed JSON:", data)  # Debugging

    # If JSON is not received correctly
    if not data:
        return jsonify({
            "error": "Invalid JSON format. Ensure Content-Type is application/json.",
            "received_raw": request.data.decode('utf-8')  # Decode raw data for debugging
        }), 400

    # Determine the correct key
    key_name = "tbl_subjects" if "tbl_subjects" in data else "subjects"

    if key_name not in data:
        return jsonify({
            "error": "Missing subjects key in JSON.",
            "received_keys": list(data.keys())
        }), 400

    subjects = data[key_name]

    # Ensure subjects is a list
    if not isinstance(subjects, list):
        return jsonify({
            "error": "Subjects must be a list.",
            "received_type": type(subjects).__name__
        }), 400

    # Validate that each subject has the required fields
    required_keys = {"department", "semester", "year", "subject"}
    for i, subject in enumerate(subjects):
        if not isinstance(subject, dict):
            return jsonify({
                "error": f"Each subject must be a dictionary. Found {type(subject).__name__}.",
                "subject_index": i
            }), 400
        missing_keys = required_keys - subject.keys()
        if missing_keys:
            return jsonify({
                "error": f"Missing required fields in subject at index {i}.",
                "missing_keys": list(missing_keys),
                "subject_data": subject
            }), 400

    # Insert subjects into database
    conn = sqlite3.connect('db_AcademicPlannerAdvisor.db')
    cursor = conn.cursor()

    for subject in subjects:
        cursor.execute('''
            INSERT INTO tbl_subjects (department, semester, year, subject)
            VALUES (?, ?, ?, ?)
        ''', (subject['department'], subject['semester'], subject['year'], subject['subject']))

    conn.commit()
    conn.close()

    return jsonify({"message": "Subjects saved successfully!"}), 201  # 201 Created status


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


if __name__ == '__main__':
    app.run(debug=True)
