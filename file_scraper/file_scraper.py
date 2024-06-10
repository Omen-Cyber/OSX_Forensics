import os
import os.path
import pathlib
import struct
from argparse import ArgumentParser

__description__ = "Recursively searches through a directory and extracts all files with a specified extension"
__organization__ = "Omen-Cyber"
__contact__ = "DaKota LaFeber"

HEADER_LENGTH = 32
MAGIC = b"SEGB"

def parse_arguments():
    parser = ArgumentParser(description="A tool to extract files in a directory")
    parser.add_argument("-d", "--directory", dest="starting_directory", required=True, help="Starting directory for the search")
    parser.add_argument("-t", "--file-type", dest="file_type", required=True, choices=['db', 'plist', 'ips', 'segb'], help="Type of files to search for (db, plist, ips, segb)")
    parser.add_argument("-o", "--output-file", dest="output_file", help="Path to the output file")
    return parser.parse_args()

'''
Searches for files by file type
In the directory and its subdirectories
Then outputs them to a specified file
'''

def stream_matches_segb_signature(stream):
    reset_offset = stream.tell()
    file_header = stream.read(HEADER_LENGTH)
    stream.seek(reset_offset, os.SEEK_SET)

    if len(file_header) != HEADER_LENGTH or file_header[0:4] != MAGIC:
        return False

    return True


def file_matches_segb_signature(file_path):
    try:
        with open(file_path, "rb") as f:
            return stream_matches_segb_signature(f)
    except Exception as e:
        print(f"Error checking file {file_path}: {e}")
        return False


def find_segb_files(directory):
    segb_files = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if file_matches_segb_signature(file_path):
                segb_files.append(file_path)

    return segb_files


def find_files(starting_directory, file_extension):
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

    return found_files


def main():
    args = parse_arguments()
    starting_directory = args.starting_directory
    file_type = args.file_type
    output_file = args.output_file

    if not os.path.isdir(starting_directory):
        print("Invalid directory path.")
        return

    if file_type == 'segb':
        found_files = find_segb_files(starting_directory)
    else:
        found_files = find_files(starting_directory, file_type)

    if output_file:
        with open(output_file, "w") as f:
            for file_path in found_files:
                f.write(file_path + "\n")
                

if __name__ == "__main__":
    main()