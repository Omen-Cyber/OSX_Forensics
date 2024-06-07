import os
import os.path
from argparse import ArgumentParser

__description__ = "Recursively searches through a directory and extracts all files with a specified extension"
__organization__ = "Omen-Cyber"
__contact__ = "DaKota LaFeber"

def parse_arguments():
    parser = ArgumentParser(description="A tool to extract files in a directory")
    parser.add_argument("-d", "--directory", dest="starting_directory", required=True, help="Starting directory for the search")
    parser.add_argument("-t", "--file-type", dest="file_type", required=True, choices=['db', 'plist', 'ips'], help="Type of files to search for (db, plist, ips)")
    parser.add_argument("-o", "--output-file", dest="output_file", help="Path to the output file")
    return parser.parse_args()

'''
Searches for files with specified extension
In the directory and its subdirectories
Then outputs them to a specified file
'''
def find_files(starting_directory, file_extension, output_file=None):
    # using stack for recursive file traversal
    stack = [os.path.expanduser(starting_directory)]
    found_files = []

    # looking for files and adding them to the array
    while stack:
        current_directory = stack.pop()
        for item in os.listdir(current_directory):
            full_path = os.path.join(current_directory, item)
            if os.path.isfile(full_path) and item.endswith("." + file_extension):
                found_files.append(full_path)
            elif os.path.isdir(full_path):
                stack.append(full_path)

    if output_file:
        with open(output_file, "w") as f:
            for file_path in found_files:
                f.write(file_path + "\n")
    else:
        for file_path in found_files:
            print(file_path)

if __name__ == "__main__":
    args = parse_arguments()
    starting_directory = args.starting_directory
    file_type = args.file_type
    output_file = args.output_file

    if output_file:
        find_files(starting_directory, file_type, output_file)
    else:
        if file_type == 'db':
            find_files(starting_directory, 'db')
        elif file_type == 'plist':
            find_files(starting_directory, 'plist')
        elif file_type == 'ips':
            find_files(starting_directory, 'ips')