import csv
from venv import create

from flask import Flask, request, render_template, redirect, url_for, flash, session, send_file
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

@app.route('/admin/add_student', methods=['GET', 'POST'])
def add_student():
    if 'admin_username' not in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        roll_number = request.form['roll_number']
        username = request.form['username']
        group_number = request.form['group_number']
        cgpa = request.form['cgpa']

        connection = create_connection()
        cursor = connection.cursor()

        # Insert new student into the database
        student_query = "INSERT INTO student (roll_number, username, group_number, cgpa) VALUES (%s, %s, %s, %s)"
        try:
            cursor.execute(student_query, (roll_number, username, group_number, cgpa))
            connection.commit()

            # Compute the average CGPA for the group
            average_query = """
                SELECT AVG(cgpa) AS average_cgpa 
                FROM student 
                WHERE group_number = %s
            """
            cursor.execute(average_query, (group_number,))
            result = cursor.fetchone()
            average_cgpa = result[0] if result else 0

            # Update the group_average_cgpa table
            update_query = """
                INSERT INTO group_average_cgpa (group_number, average_cgpa)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE average_cgpa = VALUES(average_cgpa)
            """
            cursor.execute(update_query, (group_number, average_cgpa))
            connection.commit()

            flash('Student added successfully and group average CGPA updated!', 'success')
            return redirect(url_for('admin_dashboard'))
        except Error as e:
            flash(f'Error: {e}', 'danger')
        finally:
            cursor.close()
            connection.close()

    return render_template('add_student.html')



def get_group_entries():
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT group_number, average_cgpa FROM group_average_cgpa")
    group_entries = cursor.fetchall()
    cursor.close()
    conn.close()
    return group_entries

def get_faculty_entries():
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT fac_id FROM Faculty")
    faculty_entries = cursor.fetchall()
    cursor.close()
    conn.close()
    return faculty_entries

@app.route('/preferences', methods=['GET', 'POST'])
def preferences():
    if request.method == 'POST':
        preferences_data = {}
        group_entries = get_group_entries()
        faculty_entries = get_faculty_entries()

        for group in group_entries:
            group_number = group['group_number']
            average_cgpa = group['average_cgpa']
            # Initialize a list for preferences for this group
            preferences_data[group_number] = {
                'average_cgpa': average_cgpa,
                'preferences': []
            }

            for faculty in faculty_entries:
                preference = request.form.get(f"{faculty['fac_id']}_preference_{group_number}")
                if preference:
                    preferences_data[group_number]['preferences'].append(preference)

        # Write data to CSV
        with open('preferences.csv', 'w', newline='') as csvfile:
            fieldnames = ['group_number', 'average_cgpa', 'preferences']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for group_number, data in preferences_data.items():
                # Join the preferences into a single string
                preferences_string = ', '.join(data['preferences'])
                writer.writerow({
                    'group_number': group_number,
                    'average_cgpa': data['average_cgpa'],
                    'preferences': preferences_string
                })

        return redirect(url_for('preferences'))

    group_entries = get_group_entries()
    faculty_entries = get_faculty_entries()
    return render_template('preferences.html', entries=group_entries, faculties=faculty_entries)

# actual algorithm
from flask import Flask, render_template
import pandas as pd
import math as Math
import os

def get_faculty_entries_with_name():
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT fac_id, name FROM Faculty")
    faculty_entries = cursor.fetchall()
    cursor.close()
    conn.close()
    return faculty_entries

@app.route('/export_faculties', methods=['GET'])
def export_faculties():
    faculty_entries = get_faculty_entries_with_name()
    csv_file_path = os.path.join(os.getcwd(), 'faculties.csv')

    with open(csv_file_path, 'w', newline='') as csvfile:
        fieldnames = ['fac_id', 'name']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for entry in faculty_entries:
            print("Entry:", entry)  # Debugging line to see the content of each entry
            writer.writerow(entry)

    return send_file(csv_file_path, as_attachment=True)

#set capacity by admin
@app.route('/set_capacity', methods=['GET'])
def set_capacity():
    return render_template('set_capacity.html')

@app.route('/allotment', methods=['GET', 'POST'])
def allotment():
    if request.method == 'POST':  # Get the capacity from the form
        capacity = int(request.form['capacity'])
        # Read students and faculties data from CSV
        groups_df = pd.read_csv('preferences.csv')
        faculties_df = pd.read_csv('faculties.csv')

        groups = {}
        for _, row in groups_df.iterrows():
            # Use the correct column names from your CSV
            groups[row['group_number']] = {
                'average_cgpa': row['average_cgpa'],  # Use the correct column name
                'preferences': list(map(int, row['preferences'].strip('"').split(', ')))
                # Convert preferences to a list of integers
            }

        # Convert faculties DataFrame to dictionary
        faculties = {}
        for _, row in faculties_df.iterrows():
            faculties[row['fac_id']] = {
                'name': row['name']
            }

        # Dictionary to hold allocations
        Initial_choices = {faculties[faculty_id]['name']: [] for faculty_id in faculties}

        # Populate the dictionary based on the first choice of each student group
        for group_id, group_info in groups.items():
            id = group_info['preferences'][0]  # Get the first choice
            name = faculties[id]['name']
            group_name = group_id  # Get the group name
            Initial_choices[name].append(group_name)  # Add the group name to the corresponding faculty list

        group_list = {}
        i = 1
        for f_name, f_group in Initial_choices.items():
            # Simulate faculty choices (replace with actual input)
            m = 1  # Assume the faculty chooses the first group
            if m == 0 or m > len(f_group):
                group_list.update({i: {f_name: []}})
                i += 1
            else:
                value = Initial_choices[f_name][m - 1]
                group_list.update({i: {f_name: [value]}})
                i += 1
                Initial_choices[f_name].remove(value)

        unallotted_list = []
        for f_name, f_group in Initial_choices.items():
            for i in range(len(f_group)):
                unallotted_list.append(f_group[i])

        # cgpa_sort = {}
        # for name in unallotted_list:
        #     for group in groups.values():
        #         if group['name'] == name:  # Check if the group name matches
        #             cgpa_sort.update({name: group['CGPA']})
        #             break  # Move to the next unallocated group once
        # cgpa_sort = dict(sorted(cgpa_sort.items(), key=lambda item: item[1], reverse=True))
        # unallotted_list.clear()
        # for key in cgpa_sort.keys():
        #     unallotted_list.append(key)




        # Initialize a dictionary to store CGPA sorted results
        cgpa_sort = {}

        # Fill cgpa_sort with group names and their corresponding average CGPA
        for name in unallotted_list:
            for group_id, group_info in groups.items():
                if group_id == name:  # Check if the group ID matches
                    cgpa_sort.update({name: group_info['average_cgpa']})  # Use average_cgpa here
                    break  # Move to the next unallocated group once found

        # Sort the cgpa_sort dictionary by CGPA in descending order
        cgpa_sort = dict(sorted(cgpa_sort.items(), key=lambda item: item[1], reverse=True))

        # Clear the unallotted_list and append sorted group names
        unallotted_list.clear()
        for key in cgpa_sort.keys():
            unallotted_list.append(key)



        # group_choices = {}
        # for name in unallotted_list:
        #     for group in groups.values():
        #         if group['name'] == name:  # Check if the group name matches
        #             group_choices.update({name: [group['choices']]})
        #             break  # Move to the next unallocated group once
        #
        # capacity = Math.ceil(len(groups) / len(faculties))


        group_choices = {}

        # Fill group_choices with group IDs and their corresponding preferences
        for name in unallotted_list:
            for group_id, group_info in groups.items():
                if group_id == name:  # Check if the group ID matches
                    group_choices.update({name: group_info['preferences']})  # Use preferences here
                    break  # Move to the next unallocated group once found


        # for group, preferences in group_choices.items():
        #     for preferred_faculty in preferences[0]:
        #         professor_name = list(group_list[preferred_faculty].keys())[0]
        #         if len(group_list[preferred_faculty][professor_name]) < capacity:
        #             group_list[preferred_faculty][professor_name].append(group)
        #             break  # Once the group is assigned, move to the next group



        for group, preferences in group_choices.items():
            for preferred_faculty in preferences:
                # Get the professor's name from the faculty list
                professor_name = list(group_list[preferred_faculty].keys())[0]

                # Check if the professor can take more groups
                if len(group_list[preferred_faculty][professor_name]) < capacity:
                    group_list[preferred_faculty][professor_name].append(group)  # Assign the group to the professor
                    break  # Once the group is assigned, move to the next group
        return render_template('allotment.html', group_list=group_list)
    return render_template('set_capacity.html')







# Logout route
@app.route('/logout')
def logout():
    session.pop('admin_username', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)