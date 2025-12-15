import os,sqlite3,json
from datetime import datetime
import sys
sys.path.append(os.getcwd())
from utils.helper import load_application_properties

app_properties = load_application_properties()    
log_db_dir = app_properties['LOG_DB_PATH']              # db parent directory
log_db_name = "Log.db"     
log_db_file = os.path.join(log_db_dir, log_db_name)    

def create_db():

    os.makedirs(log_db_dir, exist_ok=True)
    conn = sqlite3.connect(log_db_file)
    cursor = conn.cursor()
    # Create a table for storing client session data
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS client_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT NOT NULL,
        session_id TEXT NOT NULL,
        conversation JSON,
        time TEXT,
        date TEXT
    )
    """)
    conn.commit()

# Insert data into the client_sessions table
def insert_data(client_id, session_id, conversation_dict, timestamp=None):
    
    conn = sqlite3.connect(log_db_file)
    cursor = conn.cursor()
    
    if timestamp is None:
        timestamp = datetime.now()
    
    time_str = timestamp.strftime("%H:%M:%S")
    date_str = timestamp.strftime("%Y-%m-%d")
    
    try:
        cursor.execute("""
        INSERT INTO client_sessions (client_id, session_id, conversation, time, date)
        VALUES (?, ?, ?, ?, ?)
        """, (client_id, session_id, json.dumps(conversation_dict), time_str, date_str))

        conn.commit()
        print(f"Inserted new record for session_id {session_id}.")
    except Exception as e:
        print(f"Error inserting data: {e}")
    finally:
        conn.close()

# Function to update the JSON column with a new dictionary
def add_new_dict_to_json(client_id,session_id, new_dict):
    # Fetch the existing JSON for the given session_id
    conn = sqlite3.connect(log_db_file)
    cursor = conn.cursor()
    try:
    # Fetch existing conversation JSON
        cursor.execute("SELECT conversation FROM client_sessions WHERE session_id = ?", (session_id,))
        result = cursor.fetchone()

        if result:
            # Existing session: merge the new dictionary
            existing_json = json.loads(result[0])
            # Merge new_dict into the existing JSON structure
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
            print(f"Updated JSON for session_id {session_id}: {existing_json}")
        else:
            # No session found, insert a new record
            insert_data(client_id, session_id, new_dict)
    except Exception as e:
        print(f"Error updating or inserting data: {e}")
    finally:
        conn.close()