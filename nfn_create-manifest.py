import os
import csv
import re
from collections import defaultdict
import pickle
import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

###### VARIABLES

# Set Google Drive folder using the string after "/folders/"
FOLDER_ID = "10l9Jk9uLJ6_DFTMJOjN0mgJkY1in8Z8c"

# If modifying this scope, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]



###### FUNCTIONS
def authenticate_google_drive():
    """Handles the authentication process."""

    creds = None

    # The file token.pickle stores the user's access and refresh tokens.
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run.
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds

def list_files_in_folder(service, folder_id):
    """Given a GDrive folder, create list of all files stored in the folder."""

    query = f"'{folder_id}' in parents"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])

    if not files:
        print("No files found.")
    else:
        print("Files in folder:")
        for file in files:
            print(f"Name: {file['name']}, ID: {file['id']}")

    return files

"""
# Uncomment this function and make edits in main to access filenames from a local directory.
def access_filenames(directory_path):
    try:
        # List all files in the specified directory
        filenames = os.listdir(directory_path)

        # Filter out only files (not directories)
        files = [file for file in filenames if os.path.isfile(os.path.join(directory_path, file))]
        return files
    except FileNotFoundError:
        print(f"The directory {directory_path} does not exist.")
        return []
    except PermissionError:
        print(f"Permission denied to access the directory {directory_path}.")
        return []
"""

def sort_filenames(files):
    """ Sorts files into rows and columns based on their catalog number when
        the file name format is standardized."""
    sorted_files = {}

    for file in files:
        filename = file["name"]
        file_parts = filename.split("-")
        print(filename)
        file_num = file_parts[2]
        if file_num not in sorted_files:
            sorted_files[file_num] = [filename]
        elif file_num in sorted_files.keys():
            sorted_files[file_num].append(filename)

    return sorted_files


def create_csv_from_sort(filename, data):
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        # Find the maximum number of filenames in any group to define the number of columns
        max_files_per_group = max(len(files) for files in data.values())

        # Write the header: "Number", "Image 1", "Image 2", ..., "Image N"
        header = ["Number"] + [f'Image {i+1}' for i in range(max_files_per_group)]
        writer.writerow(header)

        # Write the data: for each group, write the group number followed by filenames
        for number, filenames in sorted(data.items()):
            # Pad the filenames list with empty strings if there are fewer than max_files_per_group
            row = [number] + filenames + [""] * (max_files_per_group - len(filenames))
            writer.writerow(row)



def main():

    creds = authenticate_google_drive()

    # Build the Google Drive service
    service = build('drive', 'v3', credentials=creds)

    files = list_files_in_folder(service, FOLDER_ID)

    if files:
        file_names = [file['name'] for file in files]

        # Print the list format
        print("\nList of File Names:")
        print(file_names)

    sorted_files = sort_filenames(files)

    create_csv_from_sort("output_file.csv", sorted_files)






if __name__ == '__main__':
    main()










