import streamlit as st
import sqlite3
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

# Set the page config at the very start
st.set_page_config(page_title="Knowledge Based Recommender System", layout="wide", page_icon="logo.jpg")

st.sidebar.image("logo.jpg", width=300)
st.sidebar.markdown("""
    <h1 style='text-align: center; font-size: 28px; font-weight: bold; color: #007BFF; font-family: "Helvetica", sans-serif;'>Welcome to Saveetha Engineering College</h1>
""", unsafe_allow_html=True)

# CSS Styling
st.markdown(""" 
    <style>
        body {
            background-color: #f0f2f5;  /* Light grey background */
        }
        .title {
            font-size: 36px;
            font-weight: bold;
            color: #007BFF;  /* Primary blue color */
            text-align: center;
            margin-bottom: 20px;
            font-family: 'Helvetica', sans-serif;
        }
        .quote {
            font-size: 20px;
            font-style: italic;
            color: #888;  /* Grey text for quote */
            text-align: center;
            margin: 10px 0;
            font-family: 'Helvetica', serif;
        }
    </style>
""", unsafe_allow_html=True)

# Title and Quote
st.markdown('<div class="title">Knowledge Based Recommender System</div>', unsafe_allow_html=True)
st.markdown('<div class="quote">Networking is not just about connecting people; it\'s about connecting people with ideas, and opportunities</div>', unsafe_allow_html=True)
# Display the centered subheader
st.markdown('<h2 style="text-align: center;color: #007BFF">Login as Student or Admin</h2>', unsafe_allow_html=True)

# Connect to SQLite database
def create_connection():
    conn = sqlite3.connect('students.db')
    return conn

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

def verify_user(user_id, password):
    conn = create_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM students WHERE user_id = ? AND password = ?', (user_id, password))
    user_found = c.fetchone() is not None
    conn.close()
    return user_found

def find_matches(user_id):
    conn = create_connection()
    c = conn.cursor()
    c.execute('SELECT name, interests, email FROM students')
    students = c.fetchall()

    if not students:
        return []

    student_names = [student[0] for student in students]
    interests = [student[1] for student in students]
    student_emails = [student[2] for student in students]

    interests_lower = [interest.lower() for interest in interests]

    tfidf = TfidfVectorizer()
    tfidf_matrix = tfidf.fit_transform(interests_lower)
    cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)

    c.execute('SELECT name, interests, email FROM students WHERE user_id = ?', (user_id,))
    user_data = c.fetchone()
    conn.close()

    if user_data is None:
        return []

    user_name, user_interests, _ = user_data
    user_interests_lower = user_interests.lower()

    user_index = student_names.index(user_name)
    sim_scores = list(enumerate(cosine_sim[user_index]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    match_indices = [i for i, score in sim_scores if i != user_index and score > 0]
    available_matches = [(student_names[i], student_emails[i]) for i in match_indices][:2]

    return available_matches

def get_students():
    conn = create_connection()
    df = pd.read_sql_query('SELECT * FROM students', conn)
    conn.close()
    return df

# Delete a student by ID
def delete_student(student_id):
    conn = create_connection()
    try:
        with conn:
            conn.execute('DELETE FROM students WHERE id = ?', (student_id,))
        return True
    except Exception as e:
        return False
    finally:
        conn.close()

# Streamlit UI
def main():
    create_table()
    
    # Session state management
    if 'user_type' not in st.session_state:
        st.session_state['user_type'] = None
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'username' not in st.session_state:
        st.session_state['username'] = ""


    # Admin login/logout functionality
    if st.session_state['logged_in']:
        if st.session_state['user_type'] == 'admin':
            st.sidebar.button("Logout", on_click=logout)
            st.success(f"Logged in as: {st.session_state['username']}")
            manage_students()
        elif st.session_state['user_type'] == 'student':
            st.sidebar.button("Logout", on_click=logout)
            st.success(f"Logged in as: {st.session_state['username']}")
            matched_students = find_matches(st.session_state['username'])
            display_matches(matched_students)
    else:
        login_form()

def login_form():
    
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Student Login")
        user_id = st.text_input("User ID", key="login_user_id")
        password = st.text_input("Password", type='password', key="login_password")
        if st.button("Login as Student"):
            if verify_user(user_id, password):
                st.session_state['logged_in'] = True
                st.session_state['username'] = user_id
                st.session_state['user_type'] = 'student'
                st.success("Login successful! 🎉")
            else:
                st.error("Invalid User ID or Password.")
    
    with col2:
        st.markdown("### Admin Login")
        admin_user = st.text_input("Admin Username", key="admin_user")
        admin_password = st.text_input("Admin Password", type='password', key="admin_password")
        if st.button("Login as Admin"):
            if admin_user == "admin" and admin_password == "password123":
                st.session_state['logged_in'] = True
                st.session_state['username'] = admin_user
                st.session_state['user_type'] = 'admin'
                st.success("Admin Login successful! 🎉")
            else:
                st.error("Invalid Admin Username or Password.")

def logout():
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
    st.session_state['user_type'] = None

def display_matches(matched_students):
    st.subheader("Connected People: ")
    if matched_students:
        for student, email in matched_students:
            st.write(f"**{student}** -  Email: {email}")
    else:
        st.write("No connections found.")

def manage_students():
    st.subheader("Manage Students")
    students = get_students()
    st.dataframe(students)

    # Create tabs for Add, Edit, Delete
    tab1, tab2, tab3 = st.tabs(["Add Student", "Edit Student", "Delete Student"])

    with tab1:
        st.subheader("Add New Student")
        name = st.text_input("Name (Add)")
        department = st.text_input("Department (Add)")
        year = st.number_input("Year (Add)", min_value=1, max_value=4)
        interests = st.text_input("Interests (Add)")
        linkedin_id = st.text_input("LinkedIn ID (Add)")
        phone_number = st.text_input("Phone Number (Add)")
        email = st.text_input("Email (Add)")
        user_id = st.text_input("User ID (Add)")
        password = st.text_input("Password (Add)", type='password')

        if st.button("Add Student"):
            if add_student(name, department, year, interests, linkedin_id, phone_number, email, user_id, password):
                st.success("Student added successfully!")
            else:
                st.error("Email or User ID already exists!")

    with tab2:
        st.subheader("Edit Existing Student")
        student_id = st.number_input("Student ID to edit", min_value=1, step=1)
        if student_id:
            students = get_students()
            student = students[students['id'] == student_id]
            if not student.empty:
                student = student.iloc[0]
                name = st.text_input("Name (Edit)", value=student['name'])
                department = st.text_input("Department (Edit)", value=student['department'])
                year = st.number_input("Year (Edit)", min_value=1, max_value=4, value=student['year'])
                interests = st.text_input("Interests (Edit)", value=student['interests'])
                linkedin_id = st.text_input("LinkedIn ID (Edit)", value=student['linkedin_id'])
                phone_number = st.text_input("Phone Number (Edit)", value=student['phone_number'])
                email = st.text_input("Email (Edit)", value=student['email'])
                user_id = st.text_input("User ID (Edit)", value=student['user_id'])
                password = st.text_input("Password (Edit)", value=student['password'], type='password')

                if st.button("Update Student"):
                    if email != student['email'] or user_id != student['user_id']:
                        if not add_student(name, department, year, interests, linkedin_id, phone_number, email, user_id, password):
                            st.error("Update failed: Email or User ID already exists.")
                        else:
                            st.success("Student updated successfully!")
                    else:
                        with create_connection() as conn:
                            conn.execute('''
                                UPDATE students
                                SET name = ?, department = ?, year = ?, interests = ?, linkedin_id = ?, phone_number = ?, password = ?
                                WHERE id = ?
                            ''', (name, department, year, interests, linkedin_id, phone_number, password, student_id))
                            st.success("Student updated successfully!")

    with tab3:
        st.subheader("Delete Student")
        student_id = st.number_input("Student ID to delete", min_value=1, step=1)
        if st.button("Delete Student"):
            if delete_student(student_id):
                st.success("Student deleted successfully!")
            else:
                st.error("Error deleting student. Please check the ID.")

if __name__ == "__main__":
    main()
