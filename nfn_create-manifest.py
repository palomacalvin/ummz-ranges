import os
import csv
import re
from collections import defaultdict
import pickle
import pandas as pd
import time
import csv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

###### VARIABLES ######

# Set Google Drive folder using the string after "/folders/"
FOLDER_ID = "15VHDiTnDUUE-V3I4H8msTp3TH0UefTM2"

# If modifying this scope, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]



###### FUNCTIONS ######
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
    """ Given a Google Drive folder, create list of all files stored in the folder.
        Handles pagination for batches of files exceeding 100 files. """

    query = f"'{folder_id}' in parents"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    page_token = None

    while True:
        try:
            # Fetch a batch of files using the page_token for pagination
            results = service.files().list(
                q=query,
                fields="files(id, name), nextPageToken",  # nextPageToken handles pagination
                pageToken=page_token  # Pass the current pageToken to retrieve the next set of files
            ).execute()

            # Extend the files list with the newly fetched files
            files.extend(results.get("files", []))

            # Check if there are more files, and if so, update the page_token
            page_token = results.get("nextPageToken")

            # If no more files to fetch, break the loop
            if not page_token:
                break
        except Exception as e:
            print(f"Error retrieving files: {e}")
            print("Retrying in 5 seconds...")
            time.sleep(5)  # Retry after a short delay (5 seconds)
            continue

    # Remove duplicate files by using a set based on file ID
    seen_file_ids = set()
    unique_files = []
    for file in files:
        if file['id'] not in seen_file_ids:
            unique_files.append(file)
            seen_file_ids.add(file['id'])

    if not unique_files:
        print("No files found.")
    else:
        print("Files in folder:")
        for file in unique_files:
            print(f"Name: {file['name']}, ID: {file['id']}")

    # Final count of files accessed
    total_files_accessed = len(unique_files)

    print(f"Total files accessed: {total_files_accessed}")

    if not unique_files:
        print("No files found.")
    else:
        print(f"Found {len(unique_files)} unique files in the folder.")
        for file in unique_files:
            print(f"File: {file['name']}")


    return unique_files, total_files_accessed

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
        the file name format is standardized. """

    sorted_files = {}
    unique_numbers = defaultdict(int)
    seen_files = set()  # To track and prevent duplicates by file name

    for file in files:
        filename = file["name"]

        # UNCOMMENT FOR DEBUGGING.
        # print(f"Processing file: {filename}")

        file_parts = filename.split("-")

        # Add check for the number of parts in the filename to ensure
        # that the filename is compatible.
        if len(file_parts) < 3:
            print(f"Skipping invalid filename: {filename}")
            continue

        file_num = file_parts[2].strip()  # Strip any leading/trailing spaces

        # UNCOMMENT FOR DEBUGGING.
        #print(f"Filename: {filename} --> Catalog Number: {file_parts[2]}")

        if file_num not in sorted_files:
            sorted_files[file_num] = [filename]
        else:
            sorted_files[file_num].append(filename)

        unique_numbers[file_num] += 1

        # UNCOMMENT FOR DEBBUGING.
        # print("\nSorted Files:")
        # for number, files in sorted_files.items():
        #     print(f"Catalog Number: {number}, Files: {files}")


    return sorted_files, unique_numbers


def create_csv_from_sort(filename, data):
    """ Creates an output CSV file based on the sorted filenames. """

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        # Find the maximum number of filenames in any group to define the number of columns
        max_files_per_group = max(len(files) for files in data.values())

        #Define the header columns: "ID", "Image_1", "Image_2", ..., "Image_N"
        header = ["ID"] + [f'Image_{i+1}' for i in range(max_files_per_group)]
        writer.writerow(header)

        # Write the data: for each group, write the group number followed by filenames
        for number, filenames in sorted(data.items()):
            # Pad the filenames list with empty strings if there are fewer than max_files_per_group
            row = [number] + filenames + [""] * (max_files_per_group - len(filenames))
            writer.writerow(row)


def display_unique_numbers(unique_numbers):
    """ Display the unique numbers and their counts.
        Use to validate items accessed from the Google Drive folder. """

    print("\nUnique numbers count:")
    for number, count in unique_numbers.items():
        print(f"Number: {number}, Count: {count}")


def export_files_to_csv(files, output_filename="google_drive_files.csv"):
    """Export file names and catalog numbers from Google Drive to a CSV file."""

    with open(output_filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["File Name", "Catalog Number"])

        for file_info in files:
            filename = file_info["name"]
            file_parts = filename.split("-")

            # Extract the catalog number (3rd part of the filename)
            if len(file_parts) >= 3:
                file_num = file_parts[2]
                writer.writerow([filename, file_num])
            else:
                print(f"Skipping invalid filename: {filename}")
    print(f"Exported files to {output_filename}")


def compare_unique_numbers_with_drive_files(csv_filename="google_drive_files.csv", unique_numbers=None):
    """Compare the catalog numbers in the CSV file with the unique numbers in the script."""
    drive_catalog_numbers = defaultdict(int)

    # Read the exported CSV file with Google Drive file names and catalog numbers
    with open(csv_filename, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        header = next(reader)  # Skip header row

        for row in reader:
            filename = row[0]
            catalog_number = row[1]
            drive_catalog_numbers[catalog_number] += 1

    # Compare the unique numbers with the ones from Google Drive
    print("\nComparison of Catalog Numbers and Counts:")
    for number, count in drive_catalog_numbers.items():
        if number in unique_numbers:
            if unique_numbers[number] == count:
                print(f"Match: {number} - {count} files")
            else:
                print(f"Mismatch: {number} - Expected {unique_numbers[number]}, Found {count}")
        else:
            print(f"Not found in unique numbers: {number} - {count} files")

    # Check for any catalog numbers in unique_numbers that aren't in the Google Drive files
    for number, count in unique_numbers.items():
        if number not in drive_catalog_numbers:
            print(f"Missing in Drive: {number} - Expected {count} files")




def main():

    creds = authenticate_google_drive()

    # Build the Google Drive service
    service = build('drive', 'v3', credentials=creds)

    files, total_files_accessed = list_files_in_folder(service, FOLDER_ID)

    if files:

        file_names = [file['name'] for file in files]

        # Print the list format
        print("\nList of File Names:")
        print(file_names)



    sorted_files, unique_numbers = sort_filenames(files)

    display_unique_numbers(unique_numbers)

    create_csv_from_sort("output_file.csv", sorted_files)

    export_files_to_csv(files)

    # Compare the total files accessed with the images processed in the CSV
    total_files_in_csv = sum(len(filenames) for filenames in sorted_files.values())
    print(f"\nTotal images processed in CSV: {total_files_in_csv}")

    # Compare counts
    print(f"\nComparison of File Counts:")
    print(f"Files accessed from Google Drive: {total_files_accessed}")
    print(f"Files written to CSV: {total_files_in_csv}")

    compare_unique_numbers_with_drive_files(csv_filename="google_drive_files.csv", unique_numbers=unique_numbers)






if __name__ == '__main__':
    main()










