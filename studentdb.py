import streamlit as st
import sqlite3
import pandas as pd

# Admin credentials (hardcoded for simplicity)
ADMIN_USER = "admin"
ADMIN_PASSWORD = "password123"

# Connect to SQLite database
def create_connection():
    conn = sqlite3.connect('students.db')
    return conn

# Create table if it doesn't exist
def create_table():
    conn = create_connection()
    with conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                year INTEGER NOT NULL,
                interests TEXT NOT NULL,
                linkedin_id TEXT,
                phone_number TEXT,
                email TEXT UNIQUE NOT NULL,
                user_id TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
    conn.close()

# Add a new student to the database
def add_student(name, department, year, interests, linkedin_id, phone_number, email, user_id, password):
    conn = create_connection()
    try:
        with conn:
            conn.execute('''
                INSERT INTO students (name, department, year, interests, linkedin_id, phone_number, email, user_id, password)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, department, year, interests, linkedin_id, phone_number, email, user_id, password))
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# Update student by ID
def update_student(student_id, name, department, year, interests, linkedin_id, phone_number, email, user_id, password):
    conn = create_connection()
    with conn:
        conn.execute('''
            UPDATE students
            SET name = ?, department = ?, year = ?, interests = ?, linkedin_id = ?, phone_number = ?, email = ?, user_id = ?, password = ?
            WHERE id = ?
        ''', (name, department, year, interests, linkedin_id, phone_number, email, user_id, password, student_id))
    conn.close()

# Delete a student by ID
def delete_student(student_id):
    conn = create_connection()
    with conn:
        conn.execute('DELETE FROM students WHERE id = ?', (student_id,))
    conn.close()

# Get all students from the database
def get_students():
    conn = create_connection()
    df = pd.read_sql_query('SELECT * FROM students', conn)
    conn.close()
    return df

# Streamlit UI
def main():
    st.title("Student Database Management")
    create_table()

    # Admin login
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        login_form()
    else:
        st.success(f"Logged in as: {st.session_state['username']}")
        manage_students()

def login_form():
    st.subheader("Admin Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    
    if st.button("Login"):
        if username == ADMIN_USER and password == ADMIN_PASSWORD:
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.success("Login successful!")
            st.experimental_rerun()  # Refresh UI after login
        else:
            st.error("Invalid username or password")

def manage_students():
    # Display current students
    st.subheader("Current Students")
    students = get_students()

    if students.empty:
        st.write("No students in the database.")
    else:
        st.dataframe(students)

    # Create three tabs for Add, Edit, and Delete
    tab1, tab2, tab3 = st.tabs(["Add Student", "Edit Student", "Delete Student"])

    # Add student tab
    with tab1:
        st.subheader("Add New Student")
        name = st.text_input("Name (Add)", key="name_add")
        department = st.text_input("Department (Add)", key="department_add")
        year = st.number_input("Year (Add)", min_value=1, max_value=4, key="year_add")
        interests = st.text_input("Interests (Add)", key="interests_add")
        linkedin_id = st.text_input("LinkedIn ID (Add)", key="linkedin_add")
        phone_number = st.text_input("Phone Number (Add)", key="phone_add")
        email = st.text_input("Email (Add)", key="email_add")
        user_id = st.text_input("User ID (Add)", key="user_id_add")
        password = st.text_input("Password (Add)", type='password', key="password_add")

        if st.button("Add Student", key="add_btn"):
            if add_student(name, department, year, interests, linkedin_id, phone_number, email, user_id, password):
                st.success("Student added successfully!")
                st.experimental_rerun()  # Refresh page to reflect the new student
            else:
                st.error("Email or User ID already exists!")

    # Edit student tab
    with tab2:
        st.subheader("Edit Existing Student")
        student_id = st.number_input("Student ID to edit", min_value=1, step=1, key="edit_id")

        if student_id in students['id'].values:
            student = students[students['id'] == student_id].iloc[0]

            # Display current details in the form
            name = st.text_input("Name (Edit)", value=student['name'], key="name_edit")
            department = st.text_input("Department (Edit)", value=student['department'], key="department_edit")
            year = st.number_input("Year (Edit)", min_value=1, max_value=4, value=student['year'], key="year_edit")
            interests = st.text_input("Interests (Edit)", value=student['interests'], key="interests_edit")
            linkedin_id = st.text_input("LinkedIn ID (Edit)", value=student['linkedin_id'], key="linkedin_edit")
            phone_number = st.text_input("Phone Number (Edit)", value=student['phone_number'], key="phone_edit")
            email = st.text_input("Email (Edit)", value=student['email'], key="email_edit")
            user_id = st.text_input("User ID (Edit)", value=student['user_id'], key="user_id_edit")
            password = st.text_input("Password (Edit)", value=student['password'], type='password', key="password_edit")

            if st.button("Update Student", key="update_btn"):
                update_student(student_id, name, department, year, interests, linkedin_id, phone_number, email, user_id, password)
                st.success("Student updated successfully!")
                st.experimental_rerun()  # Refresh page to reflect updates

    # Delete student tab
    with tab3:
        st.subheader("Delete Student")
        student_id = st.number_input("Student ID to delete", min_value=1, step=1, key="delete_id")

        if st.button("Delete Student", key="delete_btn"):
            delete_student(student_id)
            st.success("Student deleted successfully!")
            st.experimental_rerun()  # Refresh page to reflect deletion

if __name__ == "__main__":
    main()
