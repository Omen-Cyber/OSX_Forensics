import sys
import biplist
import base64
import json
from datetime import datetime
import re

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
            elif isinstance(value, bytes):
                try:
                    plist2 = biplist.readPlistFromString(value)
                    data[key] = parse_plist(plist2)
                except (biplist.InvalidPlistException, ValueError):
                    #data[key] = base64.b64encode(value).decode('utf-8')
                    data[key] = data[key].decode('utf-8', errors='replace')
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
                except (biplist.InvalidPlistException, ValueError):
                    #data[index] = base64.b64encode(item).decode('utf-8')
                    data[index] = data[index].decode('utf-8', errors='replace')
            else:
                data[index] = parse_plist(item)
    elif isinstance(data, datetime):
        data = data.isoformat()  # Convert datetime to ISO format
    elif isinstance(data, biplist.Data):
        #data = base64.b64encode(data).decode('utf-8')  # Convert Data to base64 string
        data = data.decode('utf-8', errors='replace')
    return data

def extract_readable_text(input_str):
    # Regular expression to match readable text
    text = r'[\x20-\x7E]'
    # Find all matches of readable text
    matches = re.findall(text, input_str)
    # Join the matches into a single string
    readable_text = ''.join(matches)
    return readable_text

def clean_data(data, indent=0):
    """
    Recursively replaces unwanted control characters in the data with descriptive strings.
    """
    control_chars = {
        '\ufffd': '<REPLACEMENT CHARACTER>',
        '\u0000': '<NULL>',
        '\u0001': '<SUM>',
        '\u0002': '<START OF TEXT>',
        '\u0003': '<END OF TEXT>',
        '\u0004': '<END OF TRANSMISSION>',
        '\u0005': '<ENQUIRY>',
        '\u000b': '<VERTICAL TAB>',
        '\u000e': '<SHIFT OUT>',
        '\u000f': '<SHIFT IN>',
        '\u0010': '<DATA LINK ESCAPE>',
        '\u0011': '<DEVICE CONTROL 1>',
        '\u0012': '<DEVICE CONTROL 2>',
        '\u0013': '<DEVICE CONTROL 3>',
        '\u0014': '<DEVICE CONTROL 4>',
        '\u0017': '<END OF TRANSMISSION BLOCK>',
        '\u0018': '<CANCEL>',
        '\u001a': '<SUBSTITUTE>'
    }

    if isinstance(data, dict):
        cleaned_data = {}
        for key, value in data.items():
            cleaned_data[key] = clean_data(value)  # Recursively clean each value
        return cleaned_data
    elif isinstance(data, list):
        return [clean_data(item) for item in data]  # Recursively clean each item in the list
    elif isinstance(data, str):
        # Replace control characters in the string
        for char, description in control_chars.items():
            if description == '<SUM>':
                data = data.replace(description, "My  man")
        return data
    else:
        return data  # Return as is if not a string, list, or dictionary




def main(file_path):
    try:
        with open(file_path, 'rb') as f:
            if f.read(8) != b"bplist00":
                raise biplist.InvalidPlistException("Bad file header")
            f.seek(0)
            plist = biplist.readPlist(f)
        parsed_data = parse_plist(plist)
        cleaned_data = clean_data(parsed_data)
        with open("outputMan.json", 'w') as json_file:
            json.dump(cleaned_data, json_file, indent=4)
        print("Output saved to output.json")
    except biplist.InvalidPlistException as e:
        print(f"Error reading plist file: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python plist_parse.py [file containing bplist to parse]")
        sys.exit(1)
    file_path = sys.argv[1]
    main(file_path)
