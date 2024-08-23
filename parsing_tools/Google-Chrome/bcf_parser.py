import argparse
import os
import pathlib
import sys
import json
import struct
from io import BytesIO
from time import strftime, gmtime
import io
from typing import Union, BinaryIO


__description__ = "Extracts and parses data from Google Chrome Cookies.binarycookies files"
__organization__ = "Omen-Cyber"
__contact__ = "DaKota LaFeber"


def parse_arguments():
    parser = argparse.ArgumentParser(description="A tool to extract and parse data from Google Chrome Cookies.binarycookies files")
    parser.add_argument('-i', type=str, required=True, help='Path to Cookies.binarycookies file')
    parser.add_argument('-o', type=str, required=True, help='Path to save output file')
    parser.add_argument('-f', choices=['json'], required=False, help='Output format: json')
    return parser.parse_args()


class Magic:
    _Magic = 0x6b6f6f63  # 'cook'


class BinaryReader:
    def __init__(self, stream: Union[BinaryIO, bytes]):
        """
        Initializes a new instance of the BinaryReader class.

        Args:
            stream (Union[BinaryIO, bytes]): The input stream to read from, which can be either a BinaryIO object or a bytes object.

        Returns:
            None
        """
        self.b_stream = io.BytesIO(stream) if isinstance(stream, bytes) else stream

    def seek(self, offset, whence=io.SEEK_SET):
        """
        Seeks the binary stream to the specified offset.

        Args:
            offset (int): The offset to seek to.
            whence (int, optional): The reference point for the offset. Defaults to io.SEEK_SET.

        Returns:
            int: The new position of the stream.
        """
        return self.b_stream.seek(offset, whence)

    def tell(self):
        """
        Returns the current position of the binary stream.

        Returns:
            int: The current position of the binary stream.
        """
        return self.b_stream.tell()

    def read_raw(self, count):
        """
        Reads raw binary data from the underlying stream.

        Args:
            count (int): The number of bytes to read from the stream.

        Returns:
            bytes: The raw binary data read from the stream.

        Raises:
            ValueError: If the number of bytes read does not match the expected count.
        """
        result = self.b_stream.read(count)
        if len(result) != count:
            raise ValueError(f"Could not read expected bytes: {count}, got {len(result)} for {result}")
        return result

    def read_int32(self) -> int:
        """
        Reads a signed 32-bit integer from the binary stream.

        Returns:
            int: The signed 32-bit integer read from the stream.
        """
        return struct.unpack(">i", self.read_raw(4))[0]
    
    def read2_int32(self) -> int:
        """
        Reads a signed 32-bit integer from the binary stream.

        Args:
            None

        Returns:
            int: The signed 32-bit integer read from the stream.
        """
        raw = self.read_raw(4)
        return struct.unpack("<i", raw)[0]

    def read_uint32(self) -> int:
        """
        Reads an unsigned 32-bit integer from the binary stream.
        
        Returns:
            int: The unsigned 32-bit integer read from the stream.
        """
        return struct.unpack("<I", self.read_raw(4))[0] 

    def read_uint64(self) -> int:
        """
        Reads an unsigned 64-bit integer from the binary stream.

        Returns:
            int: The unsigned 64-bit integer read from the stream.
        """
        return struct.unpack("<Q", self.read_raw(8))[0]

    def read_datetime(self) -> str:
        """Reads and converts binary cookie date."""
        epoch = struct.unpack('<d', self.read_raw(8))[0] + 978307200
        return strftime("%a, %d %b %Y", gmtime(epoch))

    def read_offsets(self) -> tuple:
        """Reads the offsets for URL, name, path, and value."""
        return struct.unpack('<iiii', self.read_raw(16))


class Cookies:
    def __init__(self, file_path, output_file, format):
        self.file_path = pathlib.Path(file_path) if isinstance(file_path, str) else file_path
        self.output_file = pathlib.Path(output_file) if isinstance(output_file, str) else output_file
        self.format = format
        self.page_sizes = []
        self.total_cookies = 0
        self.all_pages = []  # To store detailed info about each page
        self._strings = []
        with open(self.file_path, 'rb') as file:
            self.br = BinaryReader(file)
            self._read_file()

    def _read_file(self):
        """
        Reads a binary cookies file and extracts relevant information.

        This function reads the magic number, number of pages, page sizes, and each page's data.
        It then processes each page, extracts the total number of cookies, and appends various strings to the _strings list.
        Finally, it prints the values, formats the output as JSON, and prints the joined strings.

        Parameters:
            None

        Returns:
            None
        """
        # Read magic number
        self._Magic = self.br.read_uint32()
        if self._Magic != Magic._Magic:
            raise ValueError("Not a valid Cookies.binarycookies file")
        
        str = ""
        
        str = f"\nMagic number: {self._Magic}"
        self._strings.append(str)

        # Read number of pages
        num_pages = self.br.read_int32()
        str = f"Number of pages: {num_pages}"
        self._strings.append(str)

        # Read page sizes
        total_page_size = 0
        for i in range(num_pages):
            page_size = self.br.read_int32()
            self.page_sizes.append(page_size)
            total_page_size += page_size

        str = f"Total size of pages: {total_page_size}"
        self._strings.append(str)

        # Read each page            
        pages = [self.br.read_raw(page_size) for page_size in self.page_sizes]
        for page_num, page_data in enumerate(pages, 1):
            self._process_page(page_data, page_num)

        str = f"Total Cookies: {self.total_cookies}"
        self._strings.append(str)
        str = f"Input file: {self.file_path}"
        self._strings.append(str)
        str = f"Output file: {self.output_file}\n"
        self._strings.append(str)
        self._print_values()
        self.json_format()
        print("\n".join(self._strings))
        
        

    def _process_page(self, page_data, page_num):
        """
        Process a single page of cookie data.

        Parameters:
            page_data (bytes): The raw page data.
            page_num (int): The page number.

        Returns:
            None
        """
        page = BytesIO(page_data)
        br_page = BinaryReader(page)
        br_page.read2_int32()  # Skip page header
        num_cookies = br_page.read2_int32()
        self.total_cookies += num_cookies
        cookie_offsets = [br_page.read2_int32() for _ in range(num_cookies)]
        br_page.read2_int32()  # Skip footer

        cookies_data = []
        for offset in cookie_offsets:
            cookies_data.append(self._process_cookie(page_data, offset))

        # Collect page data
        page_info = {
            "Page Num": page_num,
            "Size": self.page_sizes[page_num - 1],
            "# of Cookies": num_cookies,
            "Cookie Data": cookies_data
        }
        self.all_pages.append(page_info)

    def _process_cookie(self, page_data: bytes, offset: int) -> dict:
        """Process a single cookie from a binarycookies file."""

        cookie_stream = BytesIO(page_data)
        cookie_stream.seek(offset)

        cookie_size = BinaryReader(cookie_stream).read2_int32()
        cookie_data = cookie_stream.read(cookie_size)

        cookie = BytesIO(cookie_data)
        br_cookie = BinaryReader(cookie)

        br_cookie.read_raw(4)  # skipping bytes

        flags = br_cookie.read2_int32()
        cookie_flags = {
            0: '',
            1: 'Secure',
            4: 'HttpOnly',
            5: 'Secure; HttpOnly'
        }.get(flags, 'Unknown')

        br_cookie.read_raw(4)  # skipping bytes

        urloffset, nameoffset, pathoffset, valueoffset = br_cookie.read_offsets()

        br_cookie.read_raw(8)  # skipping bytes

        # Convert date values
        expiry_date = br_cookie.read_datetime()
        create_date = br_cookie.read_datetime()

        # Read string values
        domain = self._read_string(cookie, urloffset)
        name = self._read_string(cookie, nameoffset)
        path = self._read_string(cookie, pathoffset)
        value = self._read_string(cookie, valueoffset)

        return {
            'domain': domain,
            'name': name,
            'path': path,
            'value': value,
            'created': create_date,
            'expires': expiry_date,
            'flags': cookie_flags
        }


    # Function to read string values from the binarycookies file
    def _read_string(self, cookie, offset):
        """
        Reads a string value from a binarycookies file at the specified offset.

        Args:
            cookie (BytesIO): The binarycookies file to read from.
            offset (int): The offset at which to start reading the string.

        Returns:
            str: The decoded string value.
        """
        cookie.seek(offset - 4)
        result = b""
        while True:
            byte = cookie.read(1)
            if byte == b'\x00':
                break
            result += byte
        return result.decode('utf-8')


    def _print_values(self):
        """
        Prints a summary of the parsed data, including page numbers, sizes, and cookie counts.

        Parameters:
            None

        Returns:
            None
        """
        page_len = len(self.all_pages)
        for page in self.all_pages:
            print(f"\nPage: {page['Page Num']} of {page_len}")
            print(f"Size: {page['Size']}")
            print(f"Cookies: {page['# of Cookies']}")
    
    
    def json_format(self):
        """
        Exports the parsed data to a JSON or text file based on the specified format.

        Parameters:
            None

        Returns:
            None
        """
        # Ensure the output directory exists
        if not self.output_file.exists():
            os.makedirs(self.output_file)

        # Export the parsed data to a JSON file
        if self.format == 'json':
            self.output_file = self.output_file / 'parsed_cookies.json'
            with open(self.output_file, 'w') as json_file:
                json.dump(self.all_pages, json_file, indent=4)
        else:
            self.output_file = self.output_file.with_suffix('.txt')
            with open(self.output_file, 'w') as txt_file:
                page_len = len(self.all_pages)
                for page in self.all_pages:
                    txt_file.write(f"\nPage: {page['Page Num']} of {page_len}")
                    txt_file.write(f"Size: {page['Size']}")
                    txt_file.write(f"Cookies: {page['# of Cookies']}")
                    for cookie in page['Cookie Data']:
                        txt_file.write(f"\nDomain: {cookie['domain']}")
                        txt_file.write(f"Name: {cookie['name']}")
                        txt_file.write(f"Path: {cookie['path']}")
                        txt_file.write(f"Value: {cookie['value']}")
                        txt_file.write(f"Created: {cookie['created']}")
                        txt_file.write(f"Expires: {cookie['expires']}")
                        txt_file.write(f"Flags: {cookie['flags']}")
    
    
    

def main(args):
    """
    The main entry point of the program. It takes in command line arguments, 
    constructs input and output file paths, ensures the output directory exists, 
    and calls the Cookies function to perform the main task.

    Parameters:
        args (object): Command line arguments containing input file path, output file path, and format.

    Returns:
        None
    """
    input_path = pathlib.Path(args.i)
    output_path = pathlib.Path(args.o)
    
    # Ensure the directory exists before creating the file
    if not output_path.parent.exists():
        os.makedirs(output_path.parent)
    
    Cookies(input_path, output_path, args.f)
    

if __name__ == "__main__":
    try:
        args = parse_arguments()
        main(args)
    except Exception as e:
        print("An error occurred: ", e)
        sys.exit(1) 