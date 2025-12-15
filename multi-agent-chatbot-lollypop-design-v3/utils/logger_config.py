import os
import logging
import utils.helper as helper

application_properties = helper.load_application_properties()
application_log_path = application_properties["APPLICATION_LOG_PATH"]
os.makedirs(application_log_path, exist_ok=True)

# Configure the logger
logging.basicConfig(
    level=logging.INFO,  # Capture all log levels >= INFO
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename= os.path.join(application_log_path, "chatbotapp.log"),  # Save logs in this file
    filemode="a"  # Append mode
)

# Create a logger instance for modules to use
logger = logging.getLogger("ChatBot-AppLogger")
