import os
import shutil
import datetime
import sqlite3
import yaml
import requests
import boto3
import sys
sys.path.append(os.getcwd())
from dotenv import load_dotenv
from google.cloud import storage

from utils.helper import load_client_properties, load_application_properties
load_dotenv()

def fetch_required_database_files(client_id, data_backup_parent_folder, needStateDB, needReportDB, needLogDB):
    """
    function to fetch state_db, log_db as well as report database as requested by the provided flag arguments

    client_id: client_id for whom data backup is requested.
    data_backup_parent_folder: parent folder of the data backup
    needStateDB: boolean flag to indicate if state_db backup is required
    needReportDB: boolean flag to indicate if report database backup is required
    needLogDB: boolean flag to indicate if log_db backup is required
    """
    # list that contains tuple of path and file name to copy
    files_to_process_list = []
    # temporary folder of the form- /data_backup/temp
    temp_destination_path = os.path.join(data_backup_parent_folder, "temp")
    zipped_folder_name = []
    today_date = datetime.datetime.today().strftime('%Y-%m-%d')

    app_properties = load_application_properties()
    state_db_dir = app_properties['STATE_DB_PATH']              # state_db parent folder
    log_db_dir = app_properties['LOG_DB_PATH']                  # log_db parent folder
    log_db_name = "Log.db"

    # tuple of flag, path, filename, type_of_db
    db_checks = [
    (needStateDB, state_db_dir, f"{client_id}.db", "state"),
    (needReportDB, "report/report_db", f"{client_id}.db", "report"),
    (needLogDB, log_db_dir, log_db_name, "log"),
    ]
    
    # check if state_db file is required
    for need_db, path, file_name, zip_name in db_checks:
        if need_db and os.path.exists(os.path.join(path, file_name)):
            files_to_process_list.append((path, file_name, zip_name))
            zipped_folder_name.append(zip_name)
    
    # create a folder name of the format: state-report-log_date. 
    # example- state-report-log_2025-03-21
    destination_folder_name = "-".join(zipped_folder_name) + "_" + today_date
    # example destination_path- data_backup/state-report-log_2025-03-21 
    destination_path = os.path.join(data_backup_parent_folder, destination_folder_name)

    os.mkdir(destination_path)

    # write all required sqlite files into 
    for path, file_name, zip_name in files_to_process_list:
        # temp folders are created and deleted for each database. Temp folders is to keep db and db-wal and then merge them.
        os.mkdir(temp_destination_path)
        destination_file_name = zip_name + "_" + file_name
        # copy the required db file to temp folder
        shutil.copy(os.path.join(path, file_name), os.path.join(temp_destination_path, destination_file_name))
        
        # if uncommitted writes exist, copy that too and merge these changes into main db file
        if os.path.exists(os.path.join(path, file_name+"-wal")):
            print(file_name+"-wal" + " exists")
            shutil.copy(os.path.join(path, file_name+"-wal"), temp_destination_path)

            with sqlite3.connect(os.path.join(path, file_name)) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA wal_checkpoint(FULL);")
        
        shutil.copy(os.path.join(temp_destination_path, destination_file_name), destination_path)
        shutil.rmtree(temp_destination_path)
    
    return destination_path


def upload_to_gcs(bucket_name, client_id, source_file_path):
    """
    Uploads a file to a Google Cloud Storage bucket.

    bucket_name: name of the bucket to store data
    client_id: client_id for the data backup. Will serve as the folder name in GCP bucket.
    source_file_path: path of the compressed file
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        
        # Construct destination path: bucket_name/client_id/destination_file_path
        destination_file_path = os.path.basename(source_file_path)
        destination_blob_name = f"{client_id}/{destination_file_path}"
        blob = bucket.blob(destination_blob_name)

        # Optional: Ensure the object is created only if it doesn't exist
        generation_match_precondition = 0     
        blob.upload_from_filename(source_file_path, if_generation_match=generation_match_precondition)

        return True
    except FileNotFoundError:
        print(f"Error: The file {source_file_path} was not found.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False        
            
def take_backup_to_gcp_bucket(client_id, needStateDB = True, needReportDB = True, needLogDB = True):
    """
    function to create compressed file of all required databases and then push it to GCP bucket.
    
    client_id: client_id for whom data backup is requested.
    needStateDB: boolean flag to indicate if state_db backup is required
    needReportDB: boolean flag to indicate if report database backup is required
    needLogDB: boolean flag to indicate if log_db backup is required
    """
    # create data_backup folder. This is a temp folder for backup preparation
    data_backup_parent_folder = "data_backup"
    if os.path.exists(data_backup_parent_folder):
        shutil.rmtree(data_backup_parent_folder)
    os.mkdir(data_backup_parent_folder)

    # prepare folder with all the necessary sqlite databases
    backup_file_path = fetch_required_database_files(client_id, data_backup_parent_folder, needStateDB, needReportDB, needLogDB)
    print(f"backup file created at {backup_file_path}")
    
    # archive and gzip compress
    gzipped_file = shutil.make_archive(backup_file_path, 'gztar', backup_file_path)
    print(f"backup file compression completed {gzipped_file}")

    # transfer compressed file to required bucket
    bucket_name = load_client_properties(client_id)["GCP_BUCKET_NAME"]
    upload_status = upload_to_gcs(bucket_name, client_id, gzipped_file)

    # delete data_backup folder after completion
    shutil.rmtree(data_backup_parent_folder)

# def create_akamai_bucket():

#     url = "https://api.linode.com/v4/object-storage/buckets"

#     payload = {
#         "label": "academy-chatbot-data-backup",  
#         "region": "us-east",
#         "acl": "private",
#         "s3_endpoint": "us-east-12.linodeobjects.com",
#         "cors_enabled": False,
#         "endpoint_type": "E1",
#     }

#     # Set headers
#     headers = {
#         "Authorization": f"Bearer {os.getenv("LINODE_API_TOKEN")}",
#         "accept": "application/json",
#         "content-type": "application/json"
#     }

#     # Make the request
#     response = requests.post(url, json=payload, headers=headers)

#     # Print the response
#     if response.status_code == 200:
#         print("Bucket created successfully:", response.json())
#     else:
#         print("Error:", response.status_code, response.text)

def upload_to_akamai(bucket_name, client_id, source_file_path):
    """Uploads files to specified Akamai Bucket"""

    LINODE_ACCESS_KEY = os.getenv("LINODE_ACCESS_KEY")
    LINODE_SECRET_KEY = os.getenv("LINODE_SECRET_KEY")
    REGION = "us-east-1"  
    destination_file_path = os.path.basename(source_file_path)
    destination_blob_name = f"{client_id}/{destination_file_path}"

    # Create an S3 client for Linode
    s3_client = boto3.client(
        "s3",
        endpoint_url=f"https://{REGION}.linodeobjects.com",  # Linode's S3-compatible endpoint
        aws_access_key_id=LINODE_ACCESS_KEY,
        aws_secret_access_key=LINODE_SECRET_KEY
    )

    # Upload file
    try:
        s3_client.upload_file(source_file_path, bucket_name, destination_blob_name)
        print(f"File '{source_file_path}' uploaded successfully to '{bucket_name}/{destination_blob_name}'")
    except Exception as e:
        print(f"Error uploading file: {e}")

def take_backup_to_akamai_bucket(client_id, needStateDB = True, needReportDB = True, needLogDB = True):
    """
    function to create compressed file of all required databases and then push it to Akamai bucket.
    
    client_id: client_id for whom data backup is requested.
    needStateDB: boolean flag to indicate if state_db backup is required
    needReportDB: boolean flag to indicate if report database backup is required
    needLogDB: boolean flag to indicate if log_db backup is required
    """
    # create data_backup folder. This is a temp folder for backup preparation
    data_backup_parent_folder = f"data_backup_{client_id}"
    if os.path.exists(data_backup_parent_folder):
        shutil.rmtree(data_backup_parent_folder)
    os.mkdir(data_backup_parent_folder)

    # prepare folder with all the necessary sqlite databases
    backup_file_path = fetch_required_database_files(client_id, data_backup_parent_folder, needStateDB, needReportDB, needLogDB)
    print(f"backup file created at {backup_file_path}")
    
    # archive and gzip compress
    gzipped_file = shutil.make_archive(backup_file_path, 'gztar', backup_file_path)
    print(f"backup file compression completed {gzipped_file}")

    # transfer compressed file to required bucket
    bucket_name = load_client_properties(client_id)["AKAMAI_BUCKET_NAME"]
    upload_status = upload_to_akamai(bucket_name, client_id, gzipped_file)

    # delete data_backup folder after completion
    shutil.rmtree(data_backup_parent_folder)

        
if __name__ == "__main__":
    # take_backup_to_gcp_bucket("terralogic_academy", needStateDB = True, needReportDB = False, needLogDB = True)
    take_backup_to_akamai_bucket("terralogic_academy", needStateDB = True, needReportDB = False, needLogDB = True)
