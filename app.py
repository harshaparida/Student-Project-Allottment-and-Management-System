# from flask import Flask, request, render_template, redirect, url_for, flash, session
# import mysql.connector
# from mysql.connector import Error
# from werkzeug.security import generate_password_hash, check_password_hash
#
# app = Flask(__name__)
# app.secret_key = 'your_secret_key'
#
# # MySQL configuration
# db_config = {
#     'host': 'localhost',
#     'user': 'root',
#     'password': 'rootroot',
#     'database': 'resourceDb'
# }
#
#
# # Function to create a database connection
# def create_connection():
#     connection = None
#     try:
#         connection = mysql.connector.connect(**db_config)
#         if connection.is_connected():
#             print("Connection to MySQL DB successful")
#     except Error as e:
#         print(f"The error '{e}' occurred")
#     return connection
#
#
# # Home route
# @app.route('/')
# def home():
#     return render_template('admin_login.html')
#
#
# # Signup route
# @app.route('/signup', methods=['GET', 'POST'])
# def signup():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']
#         email = request.form['email']
#
#         # Hash the password
#         hashed_password = generate_password_hash(password)
#
#         connection = create_connection()
#         cursor = connection.cursor()
#
#         # Insert new user into the database
#         query = "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)"
#         try:
#             cursor.execute(query, (username, hashed_password, email))
#             connection.commit()
#             flash('Account created successfully! You can now log in.', 'success')
#             return redirect(url_for('home'))
#         except Error as e:
#             flash(f'Error: {e}', 'danger')
#         finally:
#             cursor.close()
#             connection.close()
#
#     return render_template('add_student.html')
#
#
# # Login route
# @app.route('/login', methods=['POST'])
# def login():
#     username = request.form['username']
#     password = request.form['password']
#
#     connection = create_connection()
#     cursor = connection.cursor(dictionary=True)
#
#     query = "SELECT * FROM users WHERE username = %s"
#     cursor.execute(query, (username,))
#     user = cursor.fetchone()
#
#     if user and check_password_hash(user['password'], password):
#         session['username'] = user['username']
#         return redirect(url_for('welcome'))
#     else:
#         flash('Invalid credentials, please try again.', 'danger')
#         return redirect(url_for('home'))
#
#
# # Welcome route
# @app.route('/welcome')
# def welcome():
#     if 'username' in session:
#         return render_template('admin_dashboard.html', username=session['username'])
#     return redirect(url_for('home'))
#
#
# # Logout route
# @app.route('/logout')
# def logout():
#     session.pop('username', None)
#     return redirect(url_for('home'))
#
#
# if __name__ == '__main__':
#     app.run(debug=True)


from flask import Flask, request, render_template, redirect, url_for, flash, session
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'rootroot',
    'database': 'resourceDb'
}

# Function to create a database connection
def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            print("Connection to MySQL DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection

# Home route
@app.route('/')
def home():
    return render_template('admin_login.html')

# Admin Login route
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        connection = create_connection()
        cursor = connection.cursor(dictionary=True)

        query = "SELECT * FROM admin WHERE username = %s"
        cursor.execute(query, (username,))
        admin = cursor.fetchone()

        if admin and check_password_hash(admin['password'], password):
            session['admin_username'] = admin['username']
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials, please try again.', 'danger')
            return redirect(url_for('home'))

    return render_template('admin_login.html')

# Admin Dashboard route
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_username' in session:
        return render_template('admin_dashboard.html', username=session['admin_username'])
    return redirect(url_for('home'))

@app.route('/admin/add_student', methods=['GET', 'POST'])
def add_student():
    if 'admin_username' not in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        roll_number = request.form['roll_number']
        username = request.form['username']
        email = request.form['email']
        cgpa = request.form['cgpa']

        connection = create_connection()
        cursor = connection.cursor()

        # Insert new student into the database
        query = "INSERT INTO student (roll_number, username, email, cgpa) VALUES (%s, %s, %s, %s)"
        try:
            cursor.execute(query, (roll_number, username, email, cgpa))
            connection.commit()
            flash('Student added successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        except Error as e:
            flash(f'Error: {e}', 'danger')
        finally:
            cursor.close()
            connection.close()

    return render_template('add_student.html')

def add_admin(username, password):
    # Hash the password
    hashed_password = generate_password_hash(password)

    connection = create_connection()
    cursor = connection.cursor()

    # Insert new admin into the database
    query = "INSERT INTO admin (username, password) VALUES (%s, %s)"
    try:
        cursor.execute(query, (username, hashed_password))
        connection.commit()
        print("Admin added successfully!")
    except Error as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        connection.close()

# Example usage
add_admin('admin', 'admin_password')  # Use a strong password in production

@app.route('/admin/show_students')
def show_students():
    if 'admin_username' not in session:
        return redirect(url_for('home'))

    connection = create_connection()
    cursor = connection.cursor(dictionary=True)

    # Fetch all students from the database
    query = "SELECT * FROM student"
    cursor.execute(query)
    students = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('show_students.html', username=session['admin_username'], students=students)
@app.route('/admin/assign', methods=['GET', 'POST'])
def assign():
    if 'admin_username' not in session:
        return redirect(url_for('home'))

    connection = create_connection()
    cursor = connection.cursor(dictionary=True)

    students = []
    groups = []
    message = None  # To store success or error messages

    if request.method == 'POST':
        try:
            # Get the group size from the form
            group_size = int(request.form.get('group_size', 0))

            # Fetch all students from the database
            query = "SELECT id, roll_number, username FROM student"
            cursor.execute(query)
            students = cursor.fetchall()

            if students and group_size > 0:
                total_students = len(students)
                num_groups = -(-total_students // group_size)  # Ceiling division

                # Assign group numbers and update the database
                group_number = 1
                for idx, student in enumerate(students):
                    if idx % group_size == 0 and idx != 0:
                        group_number += 1

                    update_query = "UPDATE student SET group_number = %s WHERE id = %s"
                    cursor.execute(update_query, (group_number, student['id']))

                connection.commit()

                # Generate the list of group numbers
                groups = list(range(1, num_groups + 1))

                message = f"Successfully assigned {num_groups} groups with a maximum size of {group_size} students each."
            else:
                message = "Group size must be greater than 0 and students must be available."
        except Exception as e:
            connection.rollback()
            message = f"An error occurred: {str(e)}"

    # Fetch updated student data
    query = "SELECT roll_number, username, group_number FROM student ORDER BY group_number, roll_number"
    cursor.execute(query)
    students = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        'assign.html',
        username=session['admin_username'],
        students=students,
        groups=groups,
        message=message
    )

# Route to display the form
@app.route('/faculty_update', methods=['GET', 'POST'])
def faculty_update():
    if request.method == 'POST':
        name = request.form['name']
        faculty_id = request.form['id']

        if name.strip():  # Validate input
            try:
                conn = create_connection()
                cursor = conn.cursor()
                # Insert the data into Faculty table
                cursor.execute("INSERT INTO Faculty (id, name) VALUES (%s, %s)", (faculty_id, name))
                conn.commit()
                flash("Faculty added successfully!", "success")
            except mysql.connector.Error as err:
                flash(f"Error: {err}", "danger")
            finally:
                cursor.close()
                conn.close()
        else:
            flash("Name cannot be empty!", "danger")

        return redirect('/faculty_update')

    return render_template('faculty_update.html')
# Logout route
@app.route('/logout')
def logout():
    session.pop('admin_username', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)