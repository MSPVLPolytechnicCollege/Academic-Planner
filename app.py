from flask import Flask, render_template, request, redirect, flash, session, url_for
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


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['uname']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        dob = request.form['dob']
        email = request.form['email']
        password = request.form['pwd']

        if insert_user(username, firstname, lastname, dob, email, password):
            flash("Signup successful!", "success")
            return redirect('/')
        else:
            flash("Username already exists!", "error")

    return render_template('signUp.html')


@app.route('/login', methods=['GET', 'POST'])
def login_check():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = sqlite3.connect("db_AcademicPlannerAdvisor.db")
        cursor = conn.cursor()

        # Query to fetch user details
        cursor.execute("SELECT * FROM tbl_login WHERE user_name = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user:
            session["username"] = user["user_name"]  # Store username in session
            flash("Login successful!", "success")
            return redirect(url_for("update"))  # Redirect to next page
        else:
            flash("Invalid username or password.", "error")

        return render_template("login.html")


def insert_user(username, firstname, lastname, dob, email, password):
    try:
        conn = sqlite3.connect("db_AcademicPlannerAdvisor.db")
        cursor = conn.cursor()
        query = "INSERT INTO tbl_signup(user_name,first_name,last_name,dob,email,passwd) VALUES (?,?,?,?,?,?)"
        cursor.execute(query, (username, firstname, lastname, dob, email, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


# Route to render the password update form
@app.route('/update_password', methods=['GET', 'POST'])
def update_password():
    if request.method == 'POST':
        # Get form data
        username = request.form['uname']
        old_password = request.form['passwd_old']
        new_password = request.form['passwd_new']
        confirm_password = request.form['passwd_confirm']

        # Check if the new passwords match
        if new_password != confirm_password:
            return "New passwords do not match!"

        # Connect to the database
        conn = sqlite3.connect('db_AcademicPlannerAdvisor.db')
        cursor = conn.cursor()

        # Check if the username and old password match
        cursor.execute("SELECT passwd FROM tbl_login WHERE user_name = ?", (username,))
        row = cursor.fetchone()

        if row is None or not check_password_hash(row[0], old_password):
            conn.close()
            return "Invalid username or old password."

        # Hash the new password using werkzeug
        hashed_new_password = generate_password_hash(new_password)

        # Update password in the database (login table)
        cursor.execute("UPDATE tbl_login SET passwd = ? WHERE user_name = ?", (hashed_new_password, username))
        cursor.execute("UPDATE tbl_signup SET passwd = ? WHERE user_name = ?", (hashed_new_password, username))

        conn.commit()
        conn.close()

        return redirect(url_for('login'))

    return render_template('update.html')


if __name__ == '__main__':
    app.run(debug=True)
