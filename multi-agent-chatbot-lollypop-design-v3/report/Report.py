from flask import Blueprint,Flask, request, jsonify, render_template,redirect,session, abort
from flask_cors import CORS # Ensure `graph.py` includes the `LollypopDesignGraph` class
import sys,os,sqlite3,json
from datetime import datetime, timedelta
import time
import shutil
from langchain_openai import ChatOpenAI

from werkzeug.security import generate_password_hash, check_password_hash
from flask import session, flash, redirect, url_for, render_template, request, Response
import sqlite3
import threading
from src.tools.SF_store import send_project_enquiry_to_salesforce

#from conv_summarizer import *
sys.path.append(os.getcwd())
from src.graphs.graph_lollypop_v3 import *
import report.conv_summarizer as conv_summarizer
import utils.helper as helper
from utils.Log_sql import *
from src.tools.mail_sender import send_project_enquiry_email

report_bp = Blueprint("report", __name__)

# load application properties at the load of the report.py
application_properties = helper.load_application_properties()
report_app_db_path = application_properties["REPORT_APP_DB_PATH"]
report_db_path = os.path.join(report_app_db_path, "report_db")
state_db_path = application_properties["STATE_DB_PATH"]
log_db_path = application_properties["LOG_DB_PATH"]
log_db_file = os.path.join(log_db_path, "Log.db")

# conversation summarizer requires llm, report app provides it.
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def ensure_schema_upgrade(client_id):
    """
    Upgrade old client DBs to have the latest columns.
    Runs only if table already exists and missing columns.
    """
    db_name = os.path.join(report_db_path, f"{client_id}.db")
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()

        # Get existing columns in table
        cursor.execute("PRAGMA table_info(client_sessions_data)")
        existing_columns = [col[1] for col in cursor.fetchall()]

        # Add missing columns with safe defaults
        if "conversation_category" not in existing_columns:
            cursor.execute("""
                ALTER TABLE client_sessions_data 
                ADD COLUMN conversation_category TEXT DEFAULT 'Uncategorized'
            """)
            cursor.execute("""
                UPDATE client_sessions_data 
                SET conversation_category = 'Uncategorized' 
                WHERE conversation_category IS NULL
            """)

        if "Email_Sent" not in existing_columns:
            cursor.execute("""
                ALTER TABLE client_sessions_data 
                ADD COLUMN Email_Sent INTEGER DEFAULT 0
            """)
            cursor.execute("""
                UPDATE client_sessions_data 
                SET Email_Sent = 0 
                WHERE Email_Sent IS NULL
            """)

        conn.commit()


def create_db_report(client_id):
    # create report_db folder if it doesn't exist
    os.makedirs(report_db_path, exist_ok=True)
    report_db_name = os.path.join(report_db_path, f"{client_id}.db")

    # Check if the database exists, create and initialize it if it doesn't
    if not os.path.exists(report_db_name):
        conn = sqlite3.connect(report_db_name)
        cursor = conn.cursor()
        # Create the client_sessions_data table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS client_sessions_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id TEXT NOT NULL,
            client_id TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            user_questions JSON,
            user_answers JSON,
            conversation_summary TEXT,
            company_information TEXT,
            conversation JSON,
            conversation_category TEXT,
            time TEXT,
            date TEXT,
            Email_Sent INTEGER DEFAULT 0
        )
        """)
        # Create the user_cred table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_cred (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unique_number TEXT NOT NULL UNIQUE,
            user_name TEXT NOT NULL,
            password TEXT NOT NULL,
            user_token TEXT NOT NULL
        )
        """)
        conn.commit()
        conn.close()
        logger.info("Report.py: report DB did not exist. Created now")
    else:
        logger.info("Report.py: report DB already exists.")
    
    # Insert data into the client_sessions_data table. Loads any unprocessed conversations when the function is called (application load)
    insert_summary_into_report_db(client_id=client_id)
    logger.info("Report.py: processed all unprocessed conversations on application start.")
    

def fetch(client_id):
    """
    Function to fetch conversation information from state_db and write into report database.

    1. Gathers client_id.db, client_id.db-wal from state_db folder. .db-shm file has transient locking and state data, not the actual data
    2. Copies them over to report_db folder, flushes write-ahead log into the client_id.db
    3. Runs conversation summary function. This gathers last day's data from log_sql database and conversation is summarised for them.
    4. return result dictionary. It has conversation_summary, company_details and other fields. 
    """

    state_db_load_path = os.path.join(report_app_db_path, "load")
    os.makedirs(state_db_load_path, exist_ok=True)

    state_db_file = os.path.join(state_db_path, f"{client_id}.db")
    # make a copy of the state_db file into the load folder. This copy is used for fetching all the conversations for summarization.
    shutil.copy(state_db_file, state_db_load_path)  
    state_db_load_file = os.path.join(state_db_load_path, f"{client_id}.db")
    try:
        state_db_wal_file = os.path.join(state_db_path, f"{client_id}.db-wal")

        # if write ahead log file exists, copy and flush it to the main database
        if os.path.exists(state_db_wal_file):
            shutil.copy(state_db_wal_file, state_db_load_path)
            logger.info(f"Copied WAL file: {state_db_wal_file} to {state_db_load_path}")

            conn = sqlite3.connect(state_db_load_file)
            # Flushes all pages from the WAL to the main DB file.
            conn.execute("PRAGMA wal_checkpoint(FULL);")
            conn.close()

        # summarize all the unprocessed 
        start = time.perf_counter()
        result, total_conversations, rejected_conversations = conv_summarizer.conversation_summary_from_db(llm, state_db_load_file, log_db_file)
        summary_duration = time.perf_counter() - start
        logger.info(f"Summarizer Completed: Total - {total_conversations}, Rejected - {rejected_conversations}, Summary Duration - {summary_duration:.4f}")
        # result = jsonify(result)
    except Exception as e:
        logger.exception(f"report.py: error in fetch call function {e}")

    return result


# function to insert conversation summary into report database
def insert_summary_into_report_db(client_id):
    """
    Fetch data directly from the fetch function, process it, 
    and insert it into a SQLite database for the given client_id.
    """
    try:
        # Fetch data directly from the fetch function
        conversations = fetch(client_id)

        # Check if the response is a dict object
        if not isinstance(conversations, dict):
            print("Invalid 'result_json' structure or missing data.")
            return {"status": 400, "reason": "Invalid or missing 'result_json' in API response"}

    except Exception as e:
        logger.exception(f"error in primary fetch button function {e}")
        print(f"Error while fetching data: {e}")
        return {"status": 400, "reason": "Error processing fetched data"}

    # Database setup
    db_name = os.path.join(report_db_path, f"{client_id}.db")
    try:
        project_enquiries = []
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()

            # Iterate through each conversation and insert into the database
            for thread_id, data in conversations.items():
                if not isinstance(data, dict):
                    print(f"Skipping invalid data for thread_id {thread_id}: {data}")
                    continue

                # Extract fields with default values for missing data
                name = data.get('name', '')
                email = data.get('email', '')
                user_questions = data.get('user_questions', [])
                chatbot_answers = data.get('chatbot_answers', [])
                conversation_summary = data.get('conversation_summary', '')
                conversation_category = data.get('conversation_category', '')
                company_information = data.get('company_information', {})
                time_stamp = data.get('time_stamp', '')

                # Ensure that user_questions and chatbot_answers have matching lengths
                conversation = [{"question": q, "answer": a} for q, a in zip(user_questions, chatbot_answers)]

                # Get current date and time
            

                # Convert the timestamp to a datetime object
                dt = datetime.fromisoformat(time_stamp)
                # adding 5.5 hours to UTC to show time in IST
                dt = dt + timedelta(hours=5, minutes=30)

                # Extract time in "HH:MM:SS" format
                time = dt.strftime("%H:%M:%S")

                # Extract date in "YYYY-MM-DD" format
                date = dt.strftime("%Y-%m-%d")

                #print("Time:", time)
                #print("Date:", date)

                # Prepare data for insertion
                insert_data = (
                    thread_id, client_id, name, email,
                    json.dumps(user_questions), json.dumps(chatbot_answers),
                    conversation_summary, company_information,
                    conversation_category, json.dumps(conversation), time, date
                )
                # Insert into database
                cursor.execute("""
                    INSERT INTO client_sessions_data (
                        thread_id, client_id, name, email,
                        user_questions, user_answers,
                        conversation_summary, company_information,conversation_category,
                        conversation, time, date
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, insert_data)

                if conversation_category.lower() == "project enquiry":
                    project_enquiries.append({
                        "thread_id": thread_id,
                        "name": name,
                        "email": email,
                        "summary": conversation_summary,
                        "company_info": company_information,
                        "category": conversation_category
                    })

            # Commit transaction
            conn.commit()
        for enquiry in project_enquiries:
                try:
                    # Start email sending in a separate thread
                    email_thread = threading.Thread(
                        target=lambda e=enquiry: send_project_enquiry_email(e)
                    )
                    email_thread.start()

                    # Start Salesforce push in a separate thread
                    sf_thread = threading.Thread(
                        target=lambda e=enquiry: send_project_enquiry_to_salesforce(e)
                    )
                    sf_thread.start()

                    # Optional: wait for both to finish before moving to next enquiry
                    email_thread.join()
                    sf_thread.join()

                    # After both succeed, mark Email_Sent in DB
                    with sqlite3.connect(db_name) as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE client_sessions_data
                            SET Email_Sent = 1
                            WHERE thread_id = ? AND client_id = ?
                        """, (enquiry.get("thread_id"), client_id))
                        conn.commit()

                except Exception as e:
                    logger.exception(f"Failed to process project enquiry: {e}")

        return redirect(f"/report/{client_id}")
    except sqlite3.Error as e:
        logger.exception(f"Report Database operation failed error {e}")
        print(f"Database error: {e}")
        return {"status": 500, "reason": "Database operation failed"}
    except Exception as e:
        logger.exception(f"Unexpected error in primary fetch button function {e}")
        print(f"Unexpected error: {e}")
        return {"status": 500, "reason": "An unexpected error occurred"}



# Runs before every request, that is before the view function is called.
@report_bp.before_request
def check_client_db_exists():
    # view_args of the form- {'client_id': 'lollypop_design'}
    view_args = request.view_args
    if not view_args:
        return
    client_id = view_args.get("client_id")
    if client_id is None:
        return   
    # the proposed path of the report db file for the given client_id (depends if the db for this client was created during start)
    report_db_file = os.path.join(report_db_path, f"{client_id}.db")
    if not os.path.exists(report_db_file):
        logger.error(f"Report App: DB file for {client_id} not found. Path accessed- {request.path}")
        abort(403)
    ensure_schema_upgrade(client_id)


#primary fetch button fuction
@report_bp.route("/report/fetchdata/<client_id>")
def insert_data_from_json(client_id):
    result = insert_summary_into_report_db(client_id)
    return result
    


#Authentication module:
#Login
@report_bp.route("/login/<client_id>", methods=["GET", "POST"])
def login(client_id):
    db_name = os.path.join(report_db_path, f"{client_id}.db")
    #print(db_name)
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    if request.method == "POST":
        user_name = request.form.get("user_name")
        password = request.form.get("password")
        cursor.execute("SELECT * FROM user_cred WHERE user_name = ?", (user_name,))
        user = cursor.fetchone()
        if user and check_password_hash(user[3], password):  # Check if the entered password matches the stored hash
            session["user_token"] = user[4]  # Store user_token in session
            session["user_id"] = user[0]  # Store user_id in session
            #print("Login successful, redirecting to the report page.")
            return redirect(f"/report/{client_id}") # Redirect to report/dashboard after login
        else:
            error="Login failed. Incorrect username or password."
            logger.exception(error)
            return render_template("error.html",client_id=client_id,error=error) # Redirect to login page again

    # Check if the table has any rows; if not, redirect to signup
    cursor.execute("SELECT COUNT(*) AS count FROM user_cred")
    user_count = int(cursor.fetchone()[0])
    
    if user_count == 0:
        #print("No users in the database. Redirecting to signup.")
        return redirect(url_for("report.signup", client_id=client_id))  # Redirect to signup if no users exist
    # If users exist, directly render the login page
    conn.close()
    return render_template("login.html", client_id=client_id)


#signup page
@report_bp.route("/signup/<client_id>", methods=["GET", "POST"])
def signup(client_id):
    db_name = os.path.join(report_db_path, f"{client_id}.db")
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    # Check the count of users in the 'user_cred' table
    cursor.execute("SELECT COUNT(*) AS count FROM user_cred")
    user_count = cursor.fetchone()[0]
    if user_count == 0:
        #print("No users in the database. Signup is allowed.")
        pass
    else:
        # If users already exist, restrict signup unless the user is logged in
        if "user_token" not in session:  # Check if the user is logged in
            #print("Signup is restricted to existing users only. Please log in.")
            conn.close()
            return redirect(url_for("report.login", client_id=client_id))

    if request.method == "POST":
        # Ensure that only logged-in users can sign up new users when users already exist
        if user_count > 0 and "user_token" not in session:
            #print("You need to be logged in to add new users.")
            return redirect(url_for("report.login", client_id=client_id))

        unique_number = str(uuid.uuid4())  # Generate unique user number
        user_name = request.form.get("user_name")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Check if passwords match
        if password != confirm_password:
            #flash("Passwords do not match.", "danger")
            #print("Passwords do not match.")
            return redirect(url_for("report.signup", client_id=client_id))  # Redirect back to signup page if passwords don't match

        # Hash the password before storing
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
        user_token = user_name + password
        user_token = generate_password_hash(user_token, method="pbkdf2:sha256")

        try:
            # Insert new user data into the database
            cursor.execute("""
                INSERT INTO user_cred (unique_number, user_name, password, user_token)
                VALUES (?, ?, ?, ?)
            """, (unique_number, user_name, hashed_password, user_token))
            conn.commit()

            #flash("User created successfully. Please log in.", "success")
            #print("User created successfully. Redirecting to login.")
            return redirect(url_for("report.login", client_id=client_id))  # Redirect to login after successful signup
        except sqlite3.IntegrityError:
            #flash("Unique number or username already exists.", "danger")
            logger.exception(f"Unique number or username already exists - Login function")
            #print("Unique number or username already exists.")

    conn.close()
    return render_template("signup.html", client_id=client_id)


#Logout
@report_bp.route("/logout/<client_id>", methods=["GET"])
def logout(client_id):
    """
    Logs out the current user by clearing their session data.
    Redirects to the login page or home page after logout.
    """
    if "user_id" in session or "user_token" in session:
        # Clear the session data
        session.pop("user_id", None)
        session.pop("user_token", None)

        # Flash a logout success message (optional)
        #flash("You have been successfully logged out.", "success")
        #print("User successfully logged out.")
    else:
        #print("No active user session found.")
        pass

    # Redirect to the login page
    return redirect(url_for("report.login", client_id=client_id))  # Replace `your_client_id` with the appropriate value




#Report page Api
@report_bp.route("/report/<client_id>")
def display_table(client_id):
    # Check if the user is logged in
    if "user_id" not in session or "user_token" not in session:
        flash("You must be logged in to access this page.", "danger")
        return redirect(url_for("report.login", client_id=client_id))

    user_id = session.get("user_id")
    session_user_token = session.get("user_token")

    # Authentication check (same as before)
    try:
        conn = sqlite3.connect(os.path.join(report_db_path, f"{client_id}.db"))
        cursor = conn.cursor()
        cursor.execute("SELECT user_token FROM user_cred WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        if result is None:
            error = "User not found in the database."
            return render_template("error.html", client_id=client_id, error=error)
        db_user_token = result[0]
        if db_user_token != session_user_token:
            error = "Authentication failed. Token mismatch detected."
            return render_template("error.html", client_id=client_id, error=error)
    finally:
        conn.close()

    # 🔹 Get category filter from query params
    category_filter = request.args.get("category", "").strip()

    try:
        conn = sqlite3.connect(os.path.join(report_db_path, f"{client_id}.db"))
        cursor = conn.cursor()

        if category_filter:
            cursor.execute("""
                SELECT * FROM client_sessions_data
                WHERE conversation_category = ?
                ORDER BY date DESC, time DESC
            """, (category_filter,))
        else:
            cursor.execute("""
                SELECT * FROM client_sessions_data
                ORDER BY date DESC, time DESC
            """)

        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
    finally:
        conn.close()

    # Serialize JSON fields
    serialized_rows = []
    for row in rows:
        row = list(row)
        if len(row) > 9 and isinstance(row[9], str):
            try:
                json.loads(row[9])
            except json.JSONDecodeError:
                row[9] = json.dumps(row[9])
        serialized_rows.append(row)

    unique_rows = remove_duplicates(serialized_rows, key_index=1)

    # 🔹 Fetch all categories for dropdown
    all_categories = []
    try:
        conn = sqlite3.connect(os.path.join(report_db_path, f"{client_id}.db"))
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT conversation_category FROM client_sessions_data")
        all_categories = [row[0] for row in cursor.fetchall() if row[0]]
    finally:
        conn.close()

    return render_template(
        "report.html",
        rows=unique_rows,
        columns=columns,
        client_id=client_id,
        categories=all_categories,  # pass categories to template
        selected_category=category_filter
    )


def remove_duplicates(rows, key_index):
    """
    Remove duplicate rows based on a unique key (e.g., thread_id).
    Args:
        rows (list): List of rows from the database.
        key_index (int): Index of the column to use as the unique key.
    Returns:
        list: List of unique rows.
    """
    seen = set()
    unique_rows = []
    for row in rows:
        key = row[key_index]  # Use the unique key (e.g., thread_id)
        if key not in seen:
            seen.add(key)
            unique_rows.append(row)
    return unique_rows