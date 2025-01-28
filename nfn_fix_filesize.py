import os
import csv
import re
import io
from collections import defaultdict
import pickle
import pandas as pd
import time
import csv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from PIL import Image
from io import BytesIO
from googleapiclient.http import MediaIoBaseUpload


###### VARIABLES ######
FOLDER_ID = "10l9Jk9uLJ6_DFTMJOjN0mgJkY1in8Z8c"

SCOPES = ["https://www.googleapis.com/auth/drive"]

def authenticate_google_drive():
    """Handles the authentication process."""
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

def list_files_in_folder(service, folder_id):
    """Given a Google Drive folder, create a list of all files stored in the folder, ensuring no duplicates."""
    query = f"'{folder_id}' in parents"
    print(f"Query: {query}")

    files = []
    page_token = None
    while True:
        results = service.files().list(
            q=query,
            fields="files(id, name), nextPageToken",
            pageToken=page_token
        ).execute()

        # Avoid duplicates by storing seen file IDs
        seen_file_ids = set()
        for file in results.get("files", []):
            if file['id'] not in seen_file_ids:
                files.append(file)
                seen_file_ids.add(file['id'])

        page_token = results.get("nextPageToken")
        if not page_token:
            break

    print(f"Found {len(files)} unique files in the folder.")
    return files


def download_image(service, file_id):
    """Download an image from Google Drive by file ID."""
    request = service.files().get_media(fileId=file_id)
    file_content = BytesIO(request.execute())
    image = Image.open(file_content)
    return image

def compress_image(image, max_size_kb=999):
    """Compress image to ensure size is < max_size_kb."""
    quality = 95  # Start with high quality
    while True:
        # Create a BytesIO buffer to store the compressed image
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=quality)
        size_kb = len(buffer.getvalue()) / 1024  # Size in KB
        if size_kb <= max_size_kb:
            break
        quality -= 5  # Reduce quality if the image is too large
        if quality < 10:  # Avoid extremely low quality
            break
    buffer.seek(0)  # Reset the buffer pointer
    return buffer

def create_folder(service, folder_name, parent_folder_id):
    """Create a new folder inside the specified parent folder."""
    folder_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_folder_id]  # Specify the parent folder ID
    }
    folder = service.files().create(body=folder_metadata, fields="id").execute()
    print(f"Folder '{folder_name}' created with ID: {folder['id']} inside parent folder ID: {parent_folder_id}")
    return folder['id']

def check_existing_image(service, folder_id, filename):
    """Check if the image already exists in the target folder."""
    query = f"'{folder_id}' in parents and name = '{filename}'"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    return len(files) > 0  # Returns True if file already exists, False otherwise

def upload_image(service, file_id, buffer, new_folder_id, original_filename):
    """Upload the compressed image with the original filename to the specified folder, only if not already uploaded."""

    # Check if the image already exists in the new folder
    if check_existing_image(service, new_folder_id, original_filename):
        print(f"Image '{original_filename}' already exists in the folder. Skipping upload.")
        return None

    media_body = MediaIoBaseUpload(buffer, mimetype="image/jpeg")
    file_metadata = {
        "name": original_filename,  # Keep the original filename
        "parents": [new_folder_id]   # Upload to the specified folder
    }

    updated_file = service.files().create(
        body=file_metadata,
        media_body=media_body,
        fields="id"
    ).execute()
    print(f"Uploaded image '{original_filename}' to folder with ID: {new_folder_id}")
    return updated_file


def process_and_compress_images(service, files):
    """Download, compress, and optionally upload images."""
    for file in files:
        file_id = file["id"]
        filename = file["name"]
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            print(f"Processing file: {filename}")
            image = download_image(service, file_id)
            compressed_image_buffer = compress_image(image)
            # Optionally upload the compressed image back to Google Drive
            # upload_image(service, file_id, compressed_image_buffer)
            print(f"Compressed and processed image: {filename}")


def get_filenames_from_folder(service, folder_id):
    """Helper function to list filenames in a folder on Google Drive."""
    query = f"'{folder_id}' in parents"
    results = service.files().list(q=query, fields="files(name)").execute()
    files = results.get("files", [])
    filenames = [file['name'] for file in files]
    return filenames

def compare_filenames_in_folders(service, original_folder_id, new_folder_id):
    """Compares filenames between the original folder and the new folder."""

    # Get filenames from both folders
    original_filenames = get_filenames_from_folder(service, original_folder_id)
    new_filenames = get_filenames_from_folder(service, new_folder_id)

    # Ensure no duplicates in the new folder
    new_filenames_set = set(new_filenames)
    if len(new_filenames_set) != len(new_filenames):
        print("Warning: Duplicates detected in the new folder!")

    # Check for missing files
    missing_files = [filename for filename in original_filenames if filename not in new_filenames_set]
    extra_files = [filename for filename in new_filenames if filename not in original_filenames]

    # Display results
    if not missing_files and not extra_files:
        print("All files are present and there are no duplicates.")
    else:
        if missing_files:
            print(f"Missing files from the new folder: {', '.join(missing_files)}")
        if extra_files:
            print(f"Extra files in the new folder (not in the original): {', '.join(extra_files)}")


def main():
    creds = authenticate_google_drive()
    service = build("drive", "v3", credentials=creds)

    # The ID of the original folder (replace with actual folder ID)
    original_folder_id = FOLDER_ID
    parent_folder_id = original_folder_id  # Ensure the new folder is in the same parent folder as the original folder

    # List files in the original folder, ensuring no duplicates
    files = list_files_in_folder(service, original_folder_id)
    print(f"Found {len(files)} files in the original folder.")

    # Create a new folder inside the same parent folder
    new_folder_name = "Compressed Images Folder"
    new_folder_id = create_folder(service, new_folder_name, parent_folder_id)

    # Process each file: download, compress, and upload
    for file in files:
        file_id = file['id']
        original_filename = file['name']

        # Download and compress the image
        if original_filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            print(f"Processing file: {original_filename}")
            image = download_image(service, file_id)
            compressed_image_buffer = compress_image(image)

            # Upload the compressed image only if not already uploaded
            upload_image(service, file_id, compressed_image_buffer, new_folder_id, original_filename)

            print(f"Uploaded compressed image: {original_filename}")
        else:
            print(f"Skipping non-image file: {original_filename}")

    compare_filenames_in_folders(service, original_folder_id, new_folder_id)

if __name__ == '__main__':
    main()
