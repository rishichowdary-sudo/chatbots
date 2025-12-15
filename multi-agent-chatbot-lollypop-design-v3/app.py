from flask import Flask, request, jsonify, render_template, redirect, session, abort
from flask_cors import CORS
import sys
import os
import yaml
from threading import Lock

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

sys.path.append(os.getcwd())
sys.path.insert(0, 'C:\\Users\\Rishichowdary-3925\\Downloads')  # shared_admin_api path

import utils.Log_sql as user_activity_log
from utils.logger_config import logger
import utils.helper as helper
import utils.decorators as decorator
from src.graphs.graph_lollypop_v3 import *
import utils.data_backup_runner as data_backup_runner
import report.Report as report
from shared_admin_api import register_admin_endpoints, apply_client_api_keys, save_conversation_to_json, save_to_report_db

# Load client configurations from YAML
with open('client_properties.yaml', 'r') as f:
    client_configs = yaml.safe_load(f)

# Load stored BYOK secrets for every client once on startup
for configured_client in client_configs.keys():
    apply_client_api_keys(configured_client, client_configs, logger)

# Pre-load graphs at startup to avoid lazy-loading delays and errors
client_graphs = {}
graph_locks = {}

# Initialize all graphs at startup
for client_id in client_configs.keys():
    try:
        logger.info(f"Initializing graph for client: {client_id}")
        client_graphs[client_id] = MultiTenantGraph(client=client_id, state_in_memory=False)
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
        if client_graphs.get(client_id) is None:
            logger.info(f"Lazy-loading graph for client: {client_id}")
            client_graphs[client_id] = MultiTenantGraph(client=client_id, state_in_memory=False)
            client_graphs[client_id].build_graph()
            logger.info(f"Graph lazy-loaded successfully for: {client_id}")

    return client_graphs[client_id]

ALLOWED_IP = os.getenv('ALLOWED_IP')
ALLOWED_DOMAIN = os.getenv('ALLOWED_DOMAIN')

app = Flask(__name__)
app.secret_key = os.getenv('App_SCREAT_KEY')
app.register_blueprint(report.report_bp)
CORS(app)

user_activity_log.create_user_log_db()
report.create_db_report(client_id="lollypop_design")

@app.after_request
def add_security_headers(response):
    response.headers['Content-Security-Policy'] = f"frame-ancestors {ALLOWED_DOMAIN};"
    return response

@app.route('/getresponses', methods=['POST'])
def get_responses():
    try:
        client_id = helper.sanitize_input(request.json.get('client_id'))
        user_input = helper.sanitize_input(request.json.get('user_input'))
        session_id = helper.sanitize_input(request.json.get('session_id'))

        apply_client_api_keys(client_id, client_configs, logger)

        try:
            graph = get_or_create_graph(client_id)
        except ValueError as e:
            return jsonify({"error": str(e)}), 404

        output = graph.run_graph(user_input, session_id=session_id)

        record = {
            user_input.lower(): {
                "response": output['chatbot_answer'],
                'options': output.get('llm_free_options', []),
                'chatMessageOptions': output.get('chatMessageOptions', []),
                'jobs': output.get('jobs', [])
            }
        }
        # Save to database (old system - keep for compatibility)
        user_activity_log.update_activity_for_session(client_id=client_id, session_id=session_id, new_dict=record)

        # Save to JSON (new system for Admin Portal audit)
        save_conversation_to_json(client_id, session_id, record, client_configs, logger)

        # Save to report database (for real-time reporting in Admin Portal)
        save_to_report_db(client_id, session_id, record, client_configs, logger)

        return jsonify(record)

    except Exception as e:
        logger.exception(f"Error getresponses function {e}")
        return jsonify(error=str(e)), 500

@app.route('/<client_id>')
def main(client_id):
    if client_id not in client_configs:
        logger.warning(f"Access attempt to unconfigured client: {client_id}")
        return abort(404)

    client_config = client_configs.get(client_id, {})
    img = client_config.get('FAVICON_URL', "https://lollypop.design/wp-content/uploads/2023/01/Web-favicon.png")
    return render_template("index.html", client_id=client_id, img=img)

# Register admin upload/indexing APIs
register_admin_endpoints(app, client_configs, logger)

def start_scheduler():
    scheduler = BackgroundScheduler()
    report_trigger = IntervalTrigger(hours=3)
    scheduler.add_job(lambda: report.insert_data_from_json(client_id="lollypop_design"), report_trigger)

    data_backup_trigger = IntervalTrigger(days=1)
    scheduler.add_job(lambda: data_backup_runner.take_backup_to_provider_bucket(
        "akamai", client_id="lollypop_design", need_state_db=True, need_report_db=True, need_log_db=True
    ), data_backup_trigger)

    scheduler.start()

start_scheduler()

if __name__ == "__main__":
    app.run(debug=True)