import sys
import biplist
import base64
import json
import binascii
from datetime import datetime

def parse_plist(data):
    """
    Parses and decodes binary property list files.
    Takes a plist file as an argument and returns
    a data structure representing the data in the
    property list.
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
                    return parse_plist(plist2)
                except Exception:
                    # Base64 encode byte strings that weren't parsed
                    data[key] = data[key].decode('utf-8', errors='replace')
                    #data[key] = base64.b64encode(value).decode('utf-8')
                    #data[key] = base64.b64decode(value).decode('utf-8', errors='replace')
                    data[key] = ''.join(char for char in data[key] if char.isprintable())
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
                    data[index] = base64.b64encode(item).decode('utf-8')
            else:
                data[index] = parse_plist(item)
    elif isinstance(data, datetime):
        data = data.isoformat()  # Convert datetime to ISO format
    elif isinstance(data, biplist.Data):
        data = data.decode('utf-8', errors='replace')
        #data = base64.b64encode(data).decode('utf-8')  # Convert Data to base64 string
        #data = base64.b64decode(data).decode('utf-8', errors='replace')
        #data = ''.join(char for char in data if char.isprintable())
    return data

def main(file_path):
    try:
        with open(file_path, 'rb') as f:
            if f.read(8) != b"bplist00":
                raise plistError("Bad file header")
            f.seek(0)
            plist = biplist.readPlist(f)
        parsed_data = parse_plist(plist)
        with open("output.json", 'w') as json_file:
            json.dump(parsed_data, json_file, indent=4)
        print("Output saved to output.json")
    except biplist.InvalidPlistException as e:
        print(f"Error reading plist file: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python plist_parse.py [file containing bplist to parse]")
        sys.exit(1)
    file_path = sys.argv[1]
    main(file_path)
