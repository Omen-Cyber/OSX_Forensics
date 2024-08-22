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
        self.b_stream = io.BytesIO(stream) if isinstance(stream, bytes) else stream

    def seek(self, offset, whence=io.SEEK_SET):
        return self.b_stream.seek(offset, whence)

    def tell(self):
        return self.b_stream.tell()

    def read_raw(self, count):
        result = self.b_stream.read(count)
        if len(result) != count:
            raise ValueError(f"Could not read expected bytes: {count}, got {len(result)} for {result}")
        return result

    def read_int32(self) -> int:
        return struct.unpack(">i", self.read_raw(4))[0]
    
    def read2_int32(self) -> int:
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
        with open(self.file_path, 'rb') as file:
            self.br = BinaryReader(file)
            self._read_file()

    def _read_file(self):
        # Read magic number
        self._Magic = self.br.read_uint32()
        if self._Magic != Magic._Magic:
            raise ValueError("Not a valid Cookies.binarycookies file")
        print(f"Magic number: {self._Magic}")

        # Read number of pages
        num_pages = self.br.read_int32()
        print(f"Number of pages: {num_pages}")

        # Read page sizes
        total_page_size = 0
        for i in range(num_pages):
            page_size = self.br.read_int32()
            self.page_sizes.append(page_size)
            total_page_size += page_size

        print(f"Total size of pages: {total_page_size}")

        # Read each page            
        pages = [self.br.read_raw(page_size) for page_size in self.page_sizes]
        for page_num, page_data in enumerate(pages, 1):
            self._process_page(page_data, page_num)

        print(f"Total Cookies: {self.total_cookies}")
        self._print_values()
        self.json_format()

    def _process_page(self, page_data, page_num):
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
        cookie.seek(offset - 4)
        result = b""
        while True:
            byte = cookie.read(1)
            if byte == b'\x00':
                break
            result += byte
        return result.decode('utf-8')


    # Print a summary of the parsed data
    def _print_values(self):
        page_len = len(self.all_pages)
        for page in self.all_pages:
            print(f"\nPage: {page['Page Num']} of {page_len}")
            print(f"Size: {page['Size']}")
            print(f"Cookies: {page['# of Cookies']}")
    
    
    def json_format(self):
        # Ensure the output directory exists
        if not self.output_file.parent.exists():
            os.makedirs(self.output_file.parent)

        # Export the parsed data to a JSON file
        if self.format == 'json':
            self.output_file = self.output_file.with_suffix('.json')
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
                        
    def __str__(self):
        
        str_output = (
        f"\nMagic number: {self._Magic}"
        f"\nNumber of pages: {len(self.page_sizes)}"
        f"\nTotal size of pages: {sum(self.page_sizes)}"
        f"\nTotal Cookies: {self.total_cookies}"
        f"\nInput file: {self.file_path}"
        f"\nOutput file: {self.output_file}"
        )
        return str_output

def main(args):
    input_path = pathlib.Path(args.i)
    output_path = pathlib.Path(args.o)
    
    # Ensure the directory exists before creating the file
    if not output_path.parent.exists():
        os.makedirs(output_path.parent)
    
    Cookies(input_path, output_path, args.f)
    
    """ print(f"\n\nInput file: {input_path}")
    print(f"Output directory: {output_path.resolve()}") """

if __name__ == "__main__":
    try:
        args = parse_arguments()
        main(args)
    except Exception as e:
        print("An error occurred: ", e)
        sys.exit(1) 