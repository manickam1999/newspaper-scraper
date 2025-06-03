from utils.config import load_config
from src.drive import (
    get_google_drive_service,
    empty_drive_trash,
    analyze_storage,
    format_size,
    delete_pdf_files
)
from utils.logger import logger
from datetime import datetime

def save_storage_analysis(analysis):
    """Save storage analysis to a text file."""
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"drive_storage_analysis_{current_time}.txt"
    
    with open(filename, 'w') as f:
        # Header
        f.write("=== Google Drive Storage Analysis ===\n\n")
        
        # Total storage usage
        total = format_size(analysis['total_size'])
        f.write(f"Total Storage Used: {total}\n")
        f.write(f"Total Files: {analysis['total_files']}\n\n")
        
        # File type breakdown
        f.write("=== Storage by File Type ===\n\n")
        for mime_type, stats in analysis['mime_type_stats'].items():
            size = format_size(stats['total_size'])
            f.write(f"{mime_type}:\n")
            f.write(f"  Files: {stats['count']}\n")
            f.write(f"  Size: {size}\n\n")
        
        # Large files
        f.write("=== Largest Files (>10MB) ===\n\n")
        for file in analysis['large_files']:
            size = format_size(file['size'])
            created = datetime.fromisoformat(file['created'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"File: {file['name']}\n")
            f.write(f"Size: {size}\n")
            f.write(f"Type: {file['mime_type']}\n")
            f.write(f"Owner: {file['owner']}\n")
            f.write(f"Created: {created}\n\n")
    
    logger.info(f"Storage analysis saved to {filename}")
    return filename

def main():
    # Load configuration
    config = load_config("config/config.yaml")
    drive_config = config.get("google_drive", {})
    service_account_file = drive_config.get("service_account_file")

    # Initialize drive service
    drive_service = get_google_drive_service(service_account_file)
    
    # First analyze current storage
    logger.info("Analyzing current storage usage...")
    initial_analysis = analyze_storage(drive_service)
    initial_filename = save_storage_analysis(initial_analysis)
    print(f"\nInitial storage analysis saved to: {initial_filename}")
    
    # Delete all PDF files
    logger.info("\nStarting PDF deletion...")
    deletion_log = delete_pdf_files(drive_service)
    print(f"\nDeletion log saved to: {deletion_log}")
    
    # Analyze storage after deletion
    logger.info("\nAnalyzing storage after deletion...")
    final_analysis = analyze_storage(drive_service)
    final_filename = save_storage_analysis(final_analysis)
    print(f"\nFinal storage analysis saved to: {final_filename}")

if __name__ == "__main__":
    main()
