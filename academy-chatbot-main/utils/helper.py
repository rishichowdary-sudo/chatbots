import os
import sys
sys.path.append(os.getcwd())
import yaml
import configparser

client_properties_file_path = "client_properties.yaml"
app_properties_file_path = "application_properties.yaml"

def load_client_properties(client):
    with open(client_properties_file_path) as file:
        client_properties = yaml.safe_load(file)
        client_properties = client_properties[client]
        return client_properties
    
def load_application_properties():
    with open(app_properties_file_path) as file:
        app_properties = yaml.safe_load(file)
        return app_properties
    
def load_prompts(client_properties):
    prompts_config = configparser.ConfigParser()
    prompts_file_path = os.path.join(client_properties["ROOT_DIR"], client_properties["CLIENT_NAME"], client_properties["SYSTEM_PROMPTS_FILE"])
    prompts_config.read(prompts_file_path)
    all_prompts = prompts_config["prompts"]
    return all_prompts