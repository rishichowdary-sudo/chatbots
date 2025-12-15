from flask import Flask, request, jsonify, render_template,redirect,session, abort
from flask_cors import CORS
import sys
import os
import yaml
from threading import Lock

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from functools import wraps

sys.path.append(os.getcwd())
# Add path to shared_admin_api module
sys.path.insert(0, 'C:\\Users\\Rishichowdary-3925\\Downloads')

import utils.Log_sql as user_activity_log
from utils.logger_config import logger
import utils.helper as helper
import utils.decorators as decorator
import src.graphs.graph_v3 as graph_v3
import utils.data_backup_runner as data_backup_runner
import report.Report as report
from shared_admin_api import register_admin_endpoints, apply_client_api_keys, save_conversation_to_json, save_to_report_db

# Load client configurations from YAML
with open('client_properties.yaml', 'r') as f:
    client_configs = yaml.safe_load(f)

# Preload BYOK secrets for every configured client
for configured_client in client_configs.keys():
    apply_client_api_keys(configured_client, client_configs, logger)

# Pre-load graphs at startup to avoid lazy-loading delays and errors
client_graphs = {}
graph_locks = {}

# Initialize all graphs at startup
for client_id in client_configs.keys():
    try:
        logger.info(f"Initializing graph for client: {client_id}")
        client_graphs[client_id] = graph_v3.MultiTenantGraph(client=client_id, state_in_memory=False)
        client_graphs[client_id].build_graph()
        logger.info(f"Graph initialized successfully for: {client_id}")
    except Exception as e:
        logger.error(f"Failed to initialize graph for {client_id}: {e}")
        client_graphs[client_id] = None

def get_or_create_graph(client_id):
    """Get pre-loaded graph or lazy-load if initialization failed at startup"""
    if client_id not in client_configs:
        raise ValueError(f"Client '{client_id}' not configured in client_properties.yaml")

    apply_client_api_keys(client_id, client_configs, logger)

    # If graph exists, return it
    if client_id in client_graphs and client_graphs[client_id] is not None:
        return client_graphs[client_id]

    # Otherwise, lazy-load with thread safety
    if client_id not in graph_locks:
        graph_locks[client_id] = Lock()

    with graph_locks[client_id]:
        # Double-check after acquiring lock
        if client_graphs.get(client_id) is None:
            logger.info(f"Lazy-loading graph for client: {client_id}")
            client_graphs[client_id] = graph_v3.MultiTenantGraph(client=client_id, state_in_memory=False)
            client_graphs[client_id].build_graph()
            logger.info(f"Graph lazy-loaded successfully for: {client_id}")

    return client_graphs[client_id]

# Define the allowed domain for iframe embedding
ALLOWED_IP = os.getenv('ALLOWED_IP') 
ALLOWED_DOMAIN = os.getenv('ALLOWED_DOMAIN') 

app = Flask(__name__)
app.secret_key = os.getenv('App_SCREAT_KEY') 

# register report app
app.register_blueprint(report.report_bp)

CORS(app) 
###### Log db and report db creation #####
# creating db to log user activity
user_activity_log.create_user_log_db()
# report db creation. Create for every required client_id. Also loads any unprocessed conversations.
report.create_db_report(client_id="terralogic")


@app.after_request
def add_security_headers(response):
    # Allow embedding only from the specified domain
    response.headers['Content-Security-Policy'] = f"frame-ancestors {ALLOWED_DOMAIN};"
    return response

#Chatbot engine API
@app.route('/getresponses', methods=['POST'])
@decorator.restrict_domain(ALLOWED_IP)  # Apply IP restriction if needed
def get_responses():
    try:
        client_id = helper.sanitize_input(request.json.get('client_id'))
        user_input = request.json.get('user_input')
        clean_user_input = helper.sanitize_input(user_input)
        session_id = helper.sanitize_input(request.json.get('session_id'))

        apply_client_api_keys(client_id, client_configs, logger)

        # Lazy load graph for requested client
        try:
            graph = get_or_create_graph(client_id)
        except ValueError as e:
            return jsonify({"error": str(e)}), 404

        output = graph.run_graph(clean_user_input, session_id=session_id)

        record={
             user_input.lower(): {
                    "response": output['chatbot_answer'],
                    'options': output.get('llm_free_options', []),
                    'chatMessageOptions':output.get('chatMessageOptions',[]),
                    'jobs':output.get('jobs',[])
                    }
        }
        # Save to database (old system - keep for compatibility)
        user_activity_log.update_activity_for_session(client_id=client_id,session_id=session_id,new_dict=record)

        # Save to JSON (new system for Admin Portal audit)
        save_conversation_to_json(client_id, session_id, record, client_configs, logger)

        # Save to report database (for real-time reporting in Admin Portal)
        save_to_report_db(client_id, session_id, record, client_configs, logger)

        return jsonify(record)  # Return the response directly

    except Exception as e:
        logger.exception(f"Error getresponses function {e}")
        print(f"Error: {e}")  # Log error for debugging
        return jsonify(error=str(e)), 500
    
#Chatbot Interface API
@app.route('/<client_id>')
@decorator.restrict_domain(ALLOWED_IP)
def main(client_id):
    """Serve the main HTML interface."""
    # Check if client exists in configuration
    if client_id not in client_configs:
        logger.warning(f"Access attempt to unconfigured client: {client_id}")
        return abort(404)

    # Get logo from client config or use default
    img = os.path.join("static", "assets", "icons", "logo.svg")

    return render_template("index.html", client_id=client_id, img=img)


# Register shared admin API endpoints (PDF upload/indexing)
register_admin_endpoints(app, client_configs, logger)


def start_scheduler():
    scheduler = BackgroundScheduler()
    logger.info("Report scheduler started")
    # Define a trigger to run every 3 hours
    report_trigger = IntervalTrigger(hours=3)  
    # Add the job to the scheduler
    scheduler.add_job(lambda: report.insert_data_from_json(client_id="terralogic"), report_trigger)
    # Start the scheduler
    logger.info("Report scheduler is scheduled")

    # data backup scheduler
    logger.info("Data backup scheduler started")
    # # Define a trigger to run every week
    data_backup_trigger = IntervalTrigger(days=1)  
    # # Add the job to the scheduler
    scheduler.add_job(lambda: data_backup_runner.take_backup_to_provider_bucket("akamai", client_id="terralogic", need_state_db = True, need_report_db = True, need_log_db = True), data_backup_trigger)
    # # Start the scheduler
    logger.info("Data backup scheduler is scheduled")
    scheduler.start()

start_scheduler()

if __name__ == "__main__":
    app.run(debug=True, port=5001)
