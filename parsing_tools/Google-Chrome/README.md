# Chrome 'BINARYCOOKIE' File Parser

## Overview

This tool extracts and parses data from Google Chrome's `Cookies.binarycookies` file. It reads binary data from the file, processes it to extract relevant cookie information such as domain, name, path, value, creation date, expiration date, and flags, and outputs the data in JSON or plain text format. As of right now this version of the tool acurately extracts various cookie attributes and parses only the `Cookies.binarycookies` file from Google Chrome Version 128.0.6613.34 on iOS 17.5.1.

### References
- https://github.com/as0ler/BinaryCookieReader
- https://pypi.org/project/binarycookiesreader/

## Features
- Reads and parses the `Cookies.binarycookies` file from Google Chrome.
- Extracts and decodes cookie attributes such as domain, name, path, value, creation date, and expiration date.
- Supports output in JSON format for further processing or analysis.
- Handles binary data reading and parsing with custom BinaryReader class.

## Usage

To use this tool, run the following command in your terminal:

```bash
python tool.py -i <path_to_Cookies.binarycookies> -o <output_directory> [-f json]
```

### Arguments
- `-i` : The input path to the `Cookies.binarycookies` file you want to parse.
- `-o` : The output path where the parsed data will be saved.
- `-f` : (Optional) Specifies the output format. Currently, only `json` is supported.

### Example:

```bash
python tool.py -i ~/Path/To/Cookies.binarycookies -o ~/parsed_output/ -f json
```

## How It Works

1. **BinaryReader Class**:  
   The tool uses the `BinaryReader` class to handle reading raw binary data from the `Cookies.binarycookies` file. It supports reading various data types including integers, strings, and dates stored in the file.
   
2. **Cookies Class**:  
   The `Cookies` class manages the parsing of cookie data by reading pages and cookie attributes from the binary file. It decodes the cookies and stores the information in a structured format.

3. **Data Extraction**:  
   - The tool reads the magic number at the beginning of the file to validate that it is a valid `Cookies.binarycookies` file.
   - It then extracts details like the number of pages, cookie counts, and various cookie attributes (domain, path, value, expiration, etc.).
   - Dates are converted from their binary format to human-readable strings.

4. **Output**:  
   - The extracted data is saved either as a JSON file or a plain text file, depending on the chosen output format.
   - The output is saved in the `output_directory` specified by the user as `parsed_cookies.json` or `parsed_cookies.txt`.

## Example Output (JSON):
```json
{
    "Page Num": 1,
    "Size": 4096,
    "# of Cookies": 10,
    "Cookie Data": [
        {
            "domain": ".example.com",
            "name": "session_id",
            "path": "/",
            "value": "abc123",
            "created": "Tue, 01 Jun 2021",
            "expires": "Thu, 01 Jul 2021",
            "flags": "Secure; HttpOnly"
        }
    ]
}
```

## Author
**DaKota LaFeber**  
Titles: Cybersecurity Tool Developer, Digital Forensics Researcher  
Organization: Omen CyberSecurity LLC  
Contact: dl@omencyber.io
