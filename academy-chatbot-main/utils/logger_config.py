import os
import sys
sys.path.append(os.getcwd())
import logging

from utils.helper import load_application_properties

app_properties = load_application_properties()
app_log_dir = app_properties['APP_LOG_PATH']
app_log_name = app_properties['APP_LOG_NAME']

os.makedirs(app_log_dir, exist_ok=True)

# Configure the logger
logging.basicConfig(
    level=logging.INFO,  # Capture all log levels >= INFO
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=os.path.join(app_log_dir, app_log_name),  # Save logs in this file
    filemode="a"  # Append mode
)

# Create a logger instance for modules to use
logger = logging.getLogger("ChatBot-AppLogger")