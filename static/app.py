from flask import Flask, render_template, request, redirect, flash,session
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


@app.route('/update')
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
    # Retrieve username and password from the form
    username = request.form.get('username')
    password = request.form.get('password')

    # Open a connection to the database
    conn = sqlite3.connect("db_AcademicPlannerAdvisor.db")
    cursor = conn.cursor()

    # Query the database for the user
    cursor.execute("SELECT * FROM tbl_login WHERE user_name = ? AND passwd = ?", (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        session['username'] = user['username']
        session['password'] = user['password']
        return redirect('/update')
    else:
        flash("Invalid username or password. Please try again.")
        return render_template('login.html', message="Username and Password Mismatch.")


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


if __name__ == '__main__':
    app.run(debug=True)
