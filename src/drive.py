from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from datetime import datetime

from utils.logger import logger


def handle_drive_upload(config, file_path, file_name):

    drive_config = config.get("google_drive", {})
    service_account_file = drive_config.get("service_account_file")
    folder_name = drive_config.get("edge_folder")

    drive_service = get_google_drive_service(service_account_file)
    folder_id = find_or_create_folder(drive_service, folder_name)
    file_id, drive_link = upload_to_drive(
        drive_service, file_path, file_name, folder_id
    )

    return drive_service, file_id, drive_link


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
        service.permissions().create(fileId=file_id, body=permission, sendNotificationEmail=False).execute()

def list_trash_files(service):
    """List all files in the trash."""
    logger.info("Checking for files in trash")
    query = "trashed=true"
    results = (
        service.files()
        .list(q=query, spaces="drive", fields="files(id, name)")
        .execute()
    )
    return results.get("files", [])

def empty_drive_trash(service):
    """Permanently delete all files in the trash."""
    trash_files = list_trash_files(service)
    if trash_files:
        logger.info(f"Found {len(trash_files)} files in trash. Emptying trash...")
        for file in trash_files:
            logger.info(f"Permanently deleting file: {file['name']}")
            service.files().delete(fileId=file['id']).execute()
        logger.info("Trash emptied successfully")
    else:
        logger.info("No files found in trash")

def list_all_files(service):
    """List all files in drive with their metadata."""
    logger.info("Listing all files in drive")
    query = "trashed=false"
    fields = "files(id, name, mimeType, size, createdTime, owners, md5Checksum)"
    
    files = []
    page_token = None
    
    while True:
        try:
            response = service.files().list(
                q=query,
                spaces='drive',
                fields=f"nextPageToken, {fields}",
                pageToken=page_token,
                pageSize=1000
            ).execute()
            
            files.extend(response.get('files', []))
            page_token = response.get('nextPageToken')
            
            if not page_token:
                break
                
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            break
    
    return files

def analyze_storage(service):
    """Analyze drive storage usage."""
    files = list_all_files(service)
    
    # Initialize storage analysis
    total_size = 0
    mime_type_stats = {}
    large_files = []
    
    for file in files:
        size = int(file.get('size', 0))
        mime_type = file.get('mimeType', 'unknown')
        owners = file.get('owners', [])
        owner_email = owners[0].get('emailAddress') if owners else 'unknown'
        
        # Update total size
        total_size += size
        
        # Update mime type statistics
        if mime_type not in mime_type_stats:
            mime_type_stats[mime_type] = {
                'count': 0,
                'total_size': 0,
                'files': []
            }
        mime_type_stats[mime_type]['count'] += 1
        mime_type_stats[mime_type]['total_size'] += size
        
        # Track files larger than 10MB
        if size > 10 * 1024 * 1024:  # 10MB
            large_files.append({
                'name': file.get('name'),
                'size': size,
                'mime_type': mime_type,
                'owner': owner_email,
                'created': file.get('createdTime')
            })
    
    # Sort large files by size
    large_files.sort(key=lambda x: x['size'], reverse=True)
    
    return {
        'total_size': total_size,
        'mime_type_stats': mime_type_stats,
        'large_files': large_files,
        'total_files': len(files)
    }

def format_size(size_bytes):
    """Convert bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"

def delete_pdf_files(service):
    """Permanently delete all PDF files."""
    logger.info("Searching for PDF files...")
    query = "mimeType='application/pdf' and trashed=false"
    fields = "files(id, name, size, createdTime, owners)"
    
    files = []
    page_token = None
    total_size = 0
    
    # Get all PDF files
    while True:
        try:
            response = service.files().list(
                q=query,
                spaces='drive',
                fields=f"nextPageToken, {fields}",
                pageToken=page_token
            ).execute()
            
            batch = response.get('files', [])
            files.extend(batch)
            page_token = response.get('nextPageToken')
            
            if not page_token:
                break
                
        except Exception as e:
            logger.error(f"Error listing PDF files: {e}")
            break
    
    if not files:
        logger.info("No PDF files found")
        return
    
    # Create deletion log file
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f"pdf_deletion_log_{current_time}.txt"
    
    logger.info(f"Found {len(files)} PDF files. Starting deletion...")
    
    with open(log_file, 'w') as f:
        f.write("=== PDF Files Deletion Log ===\n\n")
        
        for i, file in enumerate(files, 1):
            try:
                # Get file details
                name = file.get('name', 'Unknown')
                size = int(file.get('size', 0))
                created = file.get('createdTime', 'Unknown')
                owners = file.get('owners', [])
                owner = owners[0].get('emailAddress') if owners else 'Unknown'
                
                # Log file details before deletion
                f.write(f"File {i}/{len(files)}:\n")
                f.write(f"Name: {name}\n")
                f.write(f"Size: {format_size(size)}\n")
                f.write(f"Created: {created}\n")
                f.write(f"Owner: {owner}\n")
                
                # Permanently delete the file
                service.files().delete(fileId=file['id']).execute()
                
                f.write("Status: Deleted successfully\n\n")
                total_size += size
                
                # Print progress
                print(f"\rDeleting files... {i}/{len(files)} ({format_size(total_size)} freed)", end='')
                
            except Exception as e:
                f.write(f"Status: Error - {str(e)}\n\n")
                logger.error(f"Error deleting file {name}: {e}")
    
    print("\nDeletion complete!")
    logger.info(f"Deletion log saved to {log_file}")
    logger.info(f"Total space freed: {format_size(total_size)}")
    return log_file
