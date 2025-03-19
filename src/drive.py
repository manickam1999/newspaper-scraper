from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from utils.logger import logger


def handle_drive_upload(config, file_path, file_name, is_star=False, date=None):
    drive_config = config.get("google_drive", {})
    service_account_file = drive_config.get("service_account_file")

    folder_name = drive_config.get("star_folder" if is_star else "edge_folder")

    drive_service = get_google_drive_service(service_account_file)
    root_folder_id = find_or_create_folder(drive_service, folder_name)
    
    if is_star and date:
        folder_id = find_or_create_folder(drive_service, date, root_folder_id)
    else:
        folder_id = root_folder_id
        
    file_id, drive_link = upload_to_drive(
        drive_service, file_path, file_name, folder_id
    )

    # Return folder_id for Star files to set permissions on the folder
    return drive_service, file_id, drive_link, folder_id if is_star else None


def get_google_drive_service(service_account_file):
    SCOPES = ["https://www.googleapis.com/auth/drive"]
    credentials = service_account.Credentials.from_service_account_file(
        service_account_file, scopes=SCOPES
    )
    return build("drive", "v3", credentials=credentials)


def find_or_create_folder(service, folder_name, parent_id="root"):
    logger.info(f"Finding or creating folder: {folder_name}")
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id != "root":
        query += f" and '{parent_id}' in parents"

    results = (
        service.files()
        .list(q=query, spaces="drive", fields="files(id, name)")
        .execute()
    )
    folders = results.get("files", [])

    if not folders:
        logger.info(f"Folder not found. Creating a new folder: {folder_name}")
        folder_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        }
        folder = service.files().create(body=folder_metadata, fields="id").execute()
        return folder.get("id")

    logger.info(f"Folder found: {folder_name}")
    return folders[0]["id"]


def upload_to_drive(service, file_path, file_name, folder_id):
    logger.info(f"Uploading file: {file_name}")
    file_metadata = {"name": file_name, "parents": [folder_id]}
    media = MediaFileUpload(file_path, resumable=True)
    file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id, webViewLink")
        .execute()
    )
    logger.info(f"File uploaded: {file_name}")
    return file.get("id"), file.get("webViewLink")


def set_file_permissions(service, file_id, email_list):
    logger.info(f"Setting permissions for file: {file_id}")
    for email in email_list:
        logger.info(f"Setting permission for email: {email}")
        permission = {"type": "user", "role": "reader", "emailAddress": email}
        service.permissions().create(fileId=file_id, body=permission).execute()
