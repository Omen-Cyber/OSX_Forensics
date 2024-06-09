import sys
import biplist
import base64
from datetime import datetime

class plistError(Exception):
    pass

def extract_readable_text(value):
    # Regular expression to match readable text
    readable_pattern = {
        '\ufffd', '\u0000', '\u0001', '\u0002', '\u0003', '\u0004', '\u0005',
        '\u000b', '\u000e', '\u000f', '\u0010', '\u0011', '\u0012', '\u0013',
        '\u0014', '\u0017', '\u0018', '\u001a'
    }  # Matches ASCII printable characters (space to tilde)

    prev_char = '\n'
    modified_value = ''
    for pattern in readable_pattern:
        if pattern == '\u0000':
            value = value.replace(pattern, '')
        elif pattern == '\u0018':
            value = value.replace(pattern, '')
        elif pattern == '\u001a':
            value = value.replace(pattern, '')
        else:
            for char in value:
                if char == '\n' and prev_char == '\n':
                    continue  # Skip consecutive line breaks
                modified_value += char
                prev_char = char
    return modified_value


def parse_plist(data):
    """
    Parses and decodes binary property list files.
    Takes a plist file as an argument and returns
    A data structure representing the data in the
    Property list

    """
    if isinstance(data, bytes) and data.startswith(b"bplist00"):
        plist = biplist.readPlistFromString(data)
        return parse_plist(plist)
    elif isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, biplist.Uid):
                data[key] = int(value)
            elif key == "bytes" and isinstance(value, bytes):
                try:
                    plist2 = biplist.readPlistFromString(value)
                    data[key] = parse_plist(plist2)
                except Exception:
                    data[key] = value.decode('utf-8', errors='replace')
                    data[key] = extract_readable_text(data[key])
            else:
                data[key] = parse_plist(value)
    elif isinstance(data, list):
        for index, item in enumerate(data):
            if isinstance(item, biplist.Uid):
                data[index] = int(item)
            elif isinstance(item, bytes):
                try:
                    plist2 = biplist.readPlistFromString(item)
                    data[index] = parse_plist(plist2)
                except Exception:
                    data[index] = item.decode('utf-8', errors='replace')
            else:
                data[index] = parse_plist(item)
    return data

def custom_pretty_print(data, indent=0):
    # A custom script to format the output in pretty print
    if isinstance(data, dict):
        print("{")
        for i, (key, value) in enumerate(data.items()):
            print(" " * (indent + 2) + f'"{key}" =>', end="")
            custom_pretty_print(value, indent + 2)
            if i < len(data) - 1:
                print(",")
            else:
                print("")
        print(" " * indent + "}", end="")
    elif isinstance(data, list):
        print("[")
        for i, item in enumerate(data):
            print(" " * (indent + 2), end="")
            custom_pretty_print(item, indent + 2)
            if i < len(data) - 1:
                print(",")
            else:
                print("")
        print(" " * indent + "]", end="")
    elif isinstance(data, datetime):
        print(f'{data.strftime("%Y-%m-%d %H:%M:%S.%f")} {data.microsecond//1000}/2097152 -0400', end="")
    elif isinstance(data, str):
        print(f'"{data}"', end="")
    else:
        print(data, end="")

def main(file_path):
    try:
        with open(file_path, 'rb') as f:
            # Checking magic number
            if f.read(8) != b"bplist00":
                raise plistError("Bad file header")

            f.seek(0) # Starting back at the top of the file
            plist = biplist.readPlist(f)

        parsed_data = parse_plist(plist)
        custom_pretty_print(parsed_data)
        print()
    except biplist.InvalidPlistException as e:
        print(f"Error reading plist file: {e}")
    except plistError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python plist_parse.py [file containing bplist to parse]")
        sys.exit(1)

    file_path = sys.argv[1]
    main(file_path)
