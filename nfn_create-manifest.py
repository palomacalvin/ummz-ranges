import os
import csv
import re
from collections import defaultdict

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

def sort_filenames(files):
    sorted_files = {}
    for filename in files:
        file = filename.split("-")
        print(filename)
        file_num = file[2]
        if file_num not in sorted_files.keys():
            sorted_files[file_num] = [filename]
        elif file_num in sorted_files.keys():
            sorted_files[file_num].append(filename)

    return sorted_files


def create_csv_from_sort(filename, data):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        # Find the maximum number of filenames in any group to define the number of columns
        max_files_per_group = max(len(files) for files in data.values())

        # Write the header: "Number", "File 1", "File 2", ..., "File N"
        header = ['Number'] + [f'File {i+1}' for i in range(max_files_per_group)]
        writer.writerow(header)

        # Write the data: for each group, write the group number followed by filenames
        for number, filenames in sorted(data.items()):
            # Pad the filenames list with empty strings if there are fewer than max_files_per_group
            row = [number] + filenames + [''] * (max_files_per_group - len(filenames))
            writer.writerow(row)



def main():
    directory = input("Enter the directory path: ")  # Path to the directory

    files = access_filenames(directory)

    sorted_files = sort_filenames(files)

    create_csv_from_sort("output_file.csv", sorted_files)






if __name__ == '__main__':
    main()










# def group_files_by_number(directory):
#     # Dictionary to store the grouped files
#     grouped_files = defaultdict(list)

#     try:
#         for filename in os.listdir(directory):
#             # Ensure we're working with only files (not directories)
#             file_path = os.path.join(directory, filename)
#             if os.path.isfile(file_path):
#                 # Split the filename by '-'
#                 parts = filename.split('-')
#                 if len(parts) >= 4:  # Ensure that there are at least 4 parts
#                     try:
#                         # Extract the number, which is in the third position
#                         number = parts[2]
#                         grouped_files[number].append(filename)
#                     except IndexError:
#                         print(f"Skipping file (incorrect format): {filename}")
#                 else:
#                     print(f"Skipping file (doesn't have expected format): {filename}")
#     except FileNotFoundError:
#         print(f"Error: The directory '{directory}' does not exist.")
#         return None

#     # Sort the groups by the number and also sort the filenames within each group
#     sorted_groups = sorted(grouped_files.items(), key=lambda x: int(x[0]))

#     return sorted_groups

# def write_to_csv(sorted_groups, output_file):
#     # Create or overwrite a CSV file
#     with open(output_file, mode='w', newline='') as file:
#         writer = csv.writer(file)

#         # Write each group of files in the same row
#         for group in sorted_groups:
#             row = group[1]  # Extract the filenames in the group
#             writer.writerow(row)

# def main():
#     directory = input("Enter the directory path: ")  # Path to the directory
#     output_file = input("Enter the output CSV filename: ")  # Path for the output CSV file

#     sorted_groups = group_files_by_number(directory)
#     write_to_csv(sorted_groups, output_file)

#     print(f"CSV file has been created: {output_file}")

# if __name__ == '__main__':
#     main()
