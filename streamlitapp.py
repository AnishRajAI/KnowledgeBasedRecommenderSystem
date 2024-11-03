import streamlit as st
import sqlite3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

# Set the page config at the very start
st.set_page_config(page_title="Knowledge Based Recommender System", layout="wide", page_icon="logo.jpg")  # Add favicon here

st.sidebar.image("logo.jpg", width=300)  # Adjust the path and width as needed
st.sidebar.markdown(""" 
    <h1 style='text-align: center; font-size: 28px; font-weight: bold; color: #007BFF; font-family: "Helvetica", sans-serif;'>Welcome to Saveetha Engineering College</h1>
""", unsafe_allow_html=True)

st.markdown(""" 
    <style>
        body {
            background-color: #f0f2f5;
        }
        .title {
            font-size: 36px;
            font-weight: bold;
            color: #007BFF;
            text-align: center;
            margin-bottom: 20px;
            font-family: 'Helvetica', sans-serif;
        }
        .quote {
            font-size: 20px;
            font-style: italic;
            color: #888;
            text-align: center;
            margin: 10px 0;
            font-family: 'Helvetica', serif;
        }
    </style>
""", unsafe_allow_html=True)

# Title and Quote
st.markdown('<div class="title">Knowledge Based Recommender System</div>', unsafe_allow_html=True)
st.markdown('<div class="quote">Networking is not just about connecting people; it\'s about connecting people with ideas, and opportunities</div>', unsafe_allow_html=True)

# Connect to SQLite database
conn = sqlite3.connect('students.db')
c = conn.cursor()

# Create table if not exists
c.execute('''
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
conn.commit()

# Create a table for active matches if it doesn't exist
c.execute('''
    CREATE TABLE IF NOT EXISTS matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student1 TEXT NOT NULL,
        student2 TEXT NOT NULL,
        UNIQUE(student1, student2)
    )
''')
conn.commit()

# Verify user function
def verify_user(user_id, password):
    c.execute('SELECT * FROM students WHERE user_id = ? AND password = ?', (user_id, password))
    return c.fetchone() is not None  # Returns True if user found, False otherwise

# Add a new student to the database
def add_student(name, department, year, interests, linkedin_id, phone_number, email, user_id, password):
    try:
        c.execute('''
            INSERT INTO students (name, department, year, interests, linkedin_id, phone_number, email, user_id, password)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, department, year, interests, linkedin_id, phone_number, email, user_id, password))
        conn.commit()  # Ensure changes are committed to the database
        return True
    except sqlite3.IntegrityError:
        return False

# Remove existing match for a student
def remove_match(student_name):
    c.execute('DELETE FROM matches WHERE student1 = ? OR student2 = ?', (student_name, student_name))
    conn.commit()

# Function to find matches based on interests
def find_matches(user_id):
    # Retrieve all students
    c.execute('SELECT name, interests FROM students')
    students = c.fetchall()

    if not students:
        return []

    # Prepare data for recommendation
    student_names = [student[0] for student in students]
    interests = [student[1] for student in students]

    # Convert interests to lowercase for similarity checking
    interests_lower = [interest.lower() for interest in interests]

    # Use TF-IDF to find similarities
    tfidf = TfidfVectorizer()
    tfidf_matrix = tfidf.fit_transform(interests_lower)
    cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)

    # Find the name of the logged-in user based on the user_id
    c.execute('SELECT name, interests FROM students WHERE user_id = ?', (user_id,))
    user_data = c.fetchone()

    if user_data is None:
        return []

    user_name, user_interests = user_data
    user_interests_lower = user_interests.lower()

    if user_name not in student_names:
        return []

    user_index = student_names.index(user_name)
    sim_scores = list(enumerate(cosine_sim[user_index]))

    # Sort by similarity scores
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    # Get the top matches excluding the user themselves
    match_indices = [i for i, score in sim_scores if i != user_index and score > 0]

    # Check for current matches in the database
    c.execute('SELECT student1, student2 FROM matches')
    current_matches = c.fetchall()

    # Create a set of currently matched students
    matched_students_set = set()
    for match in current_matches:
        matched_students_set.update(match)

    # Remove existing match for the current user before finding a new match
    remove_match(user_name) 

    # Filter matches to only include those not already matched
    available_matches = [student_names[i] for i in match_indices if student_names[i] not in matched_students_set]

    # Limit to only 2 matches
    matched_students = available_matches[:2]

    # If there are two students, create a match entry in the database
    if len(matched_students) == 2:
        c.execute('INSERT INTO matches (student1, student2) VALUES (?, ?)', (matched_students[0], matched_students[1]))
        conn.commit()

    return matched_students  # Return the matched students (up to 2)

if 'form_type' not in st.session_state:
    st.session_state.form_type = 'login'  # Default to login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False  # Track whether the user is logged in

# Function to display matched students
def display_matches(user_id):
    matched_students = find_matches(user_id)
    st.subheader("Connected Students:")
    if matched_students:
        for student in matched_students:
            st.write(f"**{student}**")
            # Retrieve and display student email for collaboration
            c.execute('SELECT email FROM students WHERE name = ?', (student,))
            email = c.fetchone()[0]
            st.write(f"Email: {email}")
    else:
        st.write("No connections found.")

# Buttons to toggle between login and registration forms
def toggle_form():
    if st.session_state.form_type == 'login':
        st.session_state.form_type = 'register'
    else:
        st.session_state.form_type = 'login'

def logout():
    st.session_state.logged_in = False
    st.session_state.form_type = 'login'
    st.success("You have been logged out successfully.")

if st.session_state.logged_in:
    st.sidebar.button("Logout", on_click=logout)
    display_matches(st.session_state.user_id)  # Display matches after login
else:
    if st.session_state.form_type == 'login':
        st.header("Login")
        user_id = st.text_input("User ID", key="login_user_id")
        password = st.text_input("Password", type='password', key="login_password")

        if st.button("Login", key="login_button"):
            if user_id and password:
                if verify_user(user_id, password):
                    st.session_state.logged_in = True
                    st.session_state.user_id = user_id
                    st.success("Login successful! 🎉")
                else:
                    st.error("Invalid User ID or Password.")
            else:
                st.error("Please enter User ID and Password!")

        st.button("Don't have an account? Register here!", on_click=toggle_form)
        st.markdown("If you forgot your password, please contact [admin@gmail.com](mailto:admin@gmail.com).")
    else:
        st.header("Register")
        with st.form(key='register_form'):
            name = st.text_input("Name")
            department = st.text_input("Department")
            year = st.number_input("Year", min_value=1, max_value=4)
            interests = st.text_input("Interests (comma separated)")
            linkedin_id = st.text_input("LinkedIn ID")
            phone_number = st.text_input("Phone Number")
            email = st.text_input("Email")
            user_id_reg = st.text_input("User ID")
            password_reg = st.text_input("Password", type='password')

            submit_button = st.form_submit_button("Register")

            if submit_button:
                if not (name and department and year and interests and email and user_id_reg and password_reg):
                    st.error("All fields are required!")
                else:
                    if add_student(name, department, year, interests, linkedin_id, phone_number, email, user_id_reg, password_reg):
                        st.success("Student registered successfully! 🎉")
                        toggle_form()  # Switch back to login form after successful registration
                    else:
                        st.error("Failed to register. User ID or Email might be already in use.")

        st.button("Already have an account? Login here!", on_click=toggle_form)

# Close the database connection
conn.close()