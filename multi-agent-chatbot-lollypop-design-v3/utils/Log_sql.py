import sys, os, sqlite3, json
from datetime import datetime
import utils.helper as helper
from utils.logger_config import logger

# load application properties at the load of the lof_sql.py file
application_properties = helper.load_application_properties()
log_db_path = application_properties["LOG_DB_PATH"]
log_db_file = os.path.join(log_db_path, "Log.db")

def create_user_log_db():
    os.makedirs(log_db_path, exist_ok=True)
    
    # log.db file is created only if it doesnt exist.
    if not os.path.exists(log_db_file):
        conn = sqlite3.connect(log_db_file)
        cursor = conn.cursor()
        # Create a table for storing client session data with a summary column
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS client_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            conversation JSON,
            time TEXT,
            date TEXT,
            summary BOOLEAN DEFAULT 0
        )
        """)
        conn.commit()
        conn.close()
        logger.info("log_sql.py: log DB did not exist. Created now")
    else:
        logger.info("log_sql.py: log DB already exists.")

# Insert data into the client_sessions table
def insert_data(client_id, session_id, conversation_dict, summary=False, timestamp=None):
    conn = sqlite3.connect(log_db_file)
    cursor = conn.cursor()

    if timestamp is None:
        timestamp = datetime.now()

    time_str = timestamp.strftime("%H:%M:%S")
    date_str = timestamp.strftime("%Y-%m-%d")

    try:
        cursor.execute("""
        INSERT INTO client_sessions (client_id, session_id, conversation, time, date, summary)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (client_id, session_id, json.dumps(conversation_dict), time_str, date_str, int(summary)))

        conn.commit()
        print(f"Inserted new record for session_id {session_id}.")
    except Exception as e:
        print(f"Error inserting data: {e}")
    finally:
        conn.close()

# Function to update the JSON column with a new dictionary
def update_activity_for_session(client_id, session_id, new_dict):
    conn = sqlite3.connect(log_db_file)
    cursor = conn.cursor()
    try:
        # Fetch existing conversation JSON
        cursor.execute("SELECT conversation FROM client_sessions WHERE session_id = ?", (session_id,))
        result = cursor.fetchone()

        if result:
            # Existing session: merge the new dictionary
            existing_json = json.loads(result[0])
            for key, value in new_dict.items():
                if key in existing_json and isinstance(existing_json[key], dict) and isinstance(value, dict):
                    existing_json[key].update(value)  # Merge nested dicts
                else:
                    existing_json[key] = value  # Add or overwrite

            # Update the database with the new JSON
            cursor.execute("""
            UPDATE client_sessions
            SET conversation = ?
            WHERE session_id = ?
            """, (json.dumps(existing_json), session_id))
            conn.commit()
            # print(f"Updated JSON for session_id {session_id}: {existing_json}")
        else:
            # No session found, insert a new record
            insert_data(client_id, session_id, new_dict)
    except Exception as e:
        print(f"Error updating or inserting data: {e}")
    finally:
        conn.close()

# Function to update the summary column
def update_session_summary(session_id, summary):
    conn = sqlite3.connect(log_db_file)
    cursor = conn.cursor()
    try:
        cursor.execute("""
        UPDATE client_sessions
        SET summary = ?
        WHERE session_id = ?
        """, (int(summary), session_id))
        conn.commit()
        # print(f"Updated summary for session_id {session_id} to {summary}.")
    except Exception as e:
        print(f"Error updating summary: {e}")
    finally:
        conn.close()
