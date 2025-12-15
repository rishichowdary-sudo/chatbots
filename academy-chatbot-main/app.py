from flask import Flask, request, jsonify, render_template, abort
from flask_cors import CORS  # Ensure `graph.py` includes the `LollypopDesignGraph` class
import sys
import os
import sqlite3
import json
from datetime import datetime
import bleach
from functools import wraps
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.schedulers.background import BackgroundScheduler
import yaml

from src.graphs.graph_multi_tenant import *
from utils.Log_sql import *
from utils.logger_config import logger
import utils.data_backup_runner as data_backup_runner
from shared_admin_api import (
    API_PROVIDER_ENV_MAP,
    apply_client_api_keys,
    get_active_provider_for_client,
    register_admin_endpoints,
    save_conversation_to_json,
    save_to_report_db,
)

app = Flask(__name__)
# Configure CORS for all routes without authentication (no credentials)
CORS(
    app,
    resources={
        r"/*": {
            "origins": [
                "https://lollypop.academy",
                "https://terralogic.academy",
                "http://127.0.0.1:5002",
                "http://localhost:9000",
            ],
            "methods": ["GET", "POST"],
            "allow_headers": ["Content-Type"],
        }
    },
)

# Load chatbot configurations for Admin Portal integration
with open("client_properties.yaml", "r") as config_file:
    client_configs = yaml.safe_load(config_file)

# Global variable for client_id
create_db()

for configured_client in client_configs.keys():
    apply_client_api_keys(configured_client, client_configs, logger)

# Initialize graphs on startup to avoid lazy-loading issues
try:
    logger.info("Initializing Lollypop Academy graph...")
    lollypop_academy_graph = MultiTenantGraph(client="lollypop_academy", state_in_memory=False)
    lollypop_academy_graph.build_graph()
    logger.info("Lollypop Academy graph initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Lollypop Academy graph: {e}")
    lollypop_academy_graph = None

try:
    logger.info("Initializing Terralogic Academy graph...")
    terralogic_academy_graph = MultiTenantGraph(client="terralogic_academy", state_in_memory=False)
    terralogic_academy_graph.build_graph()
    logger.info("Terralogic Academy graph initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Terralogic Academy graph: {e}")
    terralogic_academy_graph = None

# Define the allowed domain for iframe embedding
ALLOWED_IP = os.getenv("ALLOWED_IP")
ALLOWED_DOMAIN = os.getenv("ALLOWED_DOMAIN")
chatbot_csp_mapping = json.loads(os.getenv("CHATBOT_CSP_MAPPING", "{}"))


def sanitize_input(input_value):
    if input_value is None:
        return None
    # Allow only safe HTML tags and attributes (if needed)
    allowed_tags = []  # Empty list means no HTML tags are allowed
    allowed_attributes = {}  # Empty dict means no attributes are allowed
    return bleach.clean(input_value, tags=allowed_tags, attributes=allowed_attributes)

def restrict_if_file_not_exists(file_path_template):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            file_path = file_path_template.format(**kwargs)
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                abort(403)  # Not Found
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Custom decorator to restrict access by IP (if needed)
def restrict_domain(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Allow everything if ALLOWED_IP not configured or wildcard
        if not ALLOWED_IP or ALLOWED_IP == "*":
            return func(*args, **kwargs)

        client_domain = request.host
        logger.info("client_domain - %s", client_domain)

        if client_domain != ALLOWED_IP:
            abort(403)  # Forbidden access

        return func(*args, **kwargs)

    return wrapper

@app.after_request
def add_security_headers(response):
    # Allow embedding only from the specified domain
    # response.headers['Content-Security-Policy'] = f"frame-ancestors {ALLOWED_DOMAIN};"

    path = request.path.lower().strip("/")

    # Extract the first part of the path (e.g. 'chatbot1' from '/chatbot1/...')
    chatbot_key = path.split('/')[0] if path else None

    allowed_ancestor = chatbot_csp_mapping.get(chatbot_key, "'none'")
    response.headers['Content-Security-Policy'] = f"frame-ancestors {allowed_ancestor};"
    return response

@app.route('/getresponses', methods=['POST'])
@restrict_domain  # Apply IP restriction if needed
def get_responses():
    try:
        global lollypop_academy_graph, terralogic_academy_graph

        client_id = request.json.get('client_id')
        user_input = request.json.get('user_input')
        session_id = request.json.get('session_id')

        # Apply only the active provider key (and clear others)
        apply_client_api_keys(client_id, client_configs, logger)

        # Validate active provider has an env var set; otherwise fail fast
        active_provider = get_active_provider_for_client(client_id, client_configs)
        if active_provider:
            env_var = API_PROVIDER_ENV_MAP.get(active_provider.lower())
            if env_var:
                # Ensure other provider env vars are cleared to prevent fallback
                for prov, env_name in API_PROVIDER_ENV_MAP.items():
                    if prov != active_provider.lower():
                        os.environ.pop(env_name, None)
                if not os.environ.get(env_var):
                    return jsonify(error=f"Active provider '{active_provider}' has no API key set"), 500

        # Use pre-loaded graphs or lazy-load if initialization failed
        if client_id=="lollypop_academy":
            if lollypop_academy_graph is None:
                lollypop_academy_graph = MultiTenantGraph(client="lollypop_academy", state_in_memory=False)
                lollypop_academy_graph.build_graph()
            output = lollypop_academy_graph.run_graph(user_input,session_id=session_id)
        elif client_id=="terralogic_academy":
            if terralogic_academy_graph is None:
                terralogic_academy_graph = MultiTenantGraph(client="terralogic_academy", state_in_memory=False)
                terralogic_academy_graph.build_graph()
            output = terralogic_academy_graph.run_graph(user_input,session_id=session_id)
        else:
            raise ValueError(f"Unknown client_id: {client_id}")

        record={
             user_input.lower(): {
                    "response": output['chatbot_answer'],
                    'options': output.get('llm_free_options', [])}
        }

        # Save to database (old system - keep for compatibility)
        add_new_dict_to_json(client_id=client_id,session_id=session_id,new_dict=record)

        # Save to JSON (new system for Admin Portal audit)
        save_conversation_to_json(client_id, session_id, record, client_configs, logger)

        # Save to report database (for real-time reporting in Admin Portal)
        save_to_report_db(client_id, session_id, record, client_configs, logger)

        return jsonify(record)  # Return the response directly

    except Exception as e:
        print(f"Error: {e}")  # Log error for debugging
        return jsonify(error=str(e)), 500

@app.route('/<client_id>')
@restrict_domain  # Apply IP restriction if needed
def main(client_id):
    """Serve the main HTML interface."""
    img=""
    if client_id=="lollypop_academy":
        img="https://lollypop.academy/wp-content/themes/lollypop-academy/assets/images/academy.svg"
    elif client_id =="terralogic_academy":
        img="https://terralogic.academy/_next/static/media/Logo.a806a3cd.svg"
    else:
        abort(403)

    return render_template("index.html", client_id=client_id,img=img)

# Register shared admin API endpoints (PDF upload/indexing)
register_admin_endpoints(app, client_configs, logger)

# Cron job for data backup
def start_scheduler():
    scheduler = BackgroundScheduler()
    # data backup scheduler
    logger.info("Data backup scheduler started")
    # # Define a trigger to run every week
    data_backup_trigger = IntervalTrigger(days=1)  
    # # Add the job to the scheduler
    scheduler.add_job(lambda: data_backup_runner.take_backup_to_akamai_bucket(client_id="lollypop_academy", needStateDB=True, needReportDB=False, needLogDB=True), data_backup_trigger)
    scheduler.add_job(lambda: data_backup_runner.take_backup_to_akamai_bucket(client_id="terralogic_academy", needStateDB=True, needReportDB=False, needLogDB=True), data_backup_trigger)
    # # Start the scheduler
    # logger.info("Data backup scheduler is scheduled")
    scheduler.start()
    logger.info("Scheduler is running")

start_scheduler()

if __name__ == "__main__":
    app.run(debug=True, port=5002)
