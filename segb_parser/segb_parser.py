import os
import pathlib
import struct
import dataclasses
import typing
import datetime
import zlib
import pytz 
import json
from argparse import ArgumentParser

__description__ = "A Python script to read and parse SEGB files"
__organozation__ = "Omen-Cyber"
__contact__ = "DaKota LaFeber"


def parse_arguments():
    parser = ArgumentParser(description="A tool that extracts parses data from SEGB files.")
    parser.add_argument("-f", "--file", dest="input_dir", required=True, help="Path to the SEGB file")
    parser.add_argument("-o", "--output", dest="output_dir", help="Path to the output directory")
    return parser.parse_args()

# Defining magic bytes 
HEADER_LENGTH = 32
ENTRY_HEADER_LENGTH = 8
TRAILER_ENTRY_LENGTH = 16
MAGIC = b"SEGB"
# SEGB files use Cocoa timestamps, using pytz for timezone handling
APPLE_EPOCH = datetime.datetime(2001, 1, 1, tzinfo=pytz.UTC)


# storing metadata (offsets, state, and creation time)
@dataclasses.dataclass(frozen=True)
class EntryMetadata:
    metadata_offset: int
    end_offset: int
    state: int
    creation: datetime.datetime


# SEGB entry values
@dataclasses.dataclass(frozen=True)
class SegbEntry:
    metadata: EntryMetadata
    data_start_offset: int
    metadata_crc: int
    actual_crc: int
    data: bytes
    _unknown_value: int = dataclasses.field(kw_only=True, compare=False)

    # getting the creation timestamp
    @property
    def timestamp1(self) -> datetime.datetime:
        return self.metadata.creation

    # check if crc is passed
    @property
    def crc_passed(self):
        return self.metadata_crc == self.actual_crc

    # getting the state
    @property
    def state(self):
        return self.metadata.state


# checks magic bytes in a stream
def stream_matches_segb_signature(stream: typing.BinaryIO) -> bool:
    reset_offset = stream.tell()
    file_header = stream.read(HEADER_LENGTH)
    stream.seek(reset_offset, os.SEEK_SET)

    return len(file_header) == HEADER_LENGTH and file_header[0:4] == MAGIC


# checks if file matches SEGB signature by calling stream_matches_segb_signature 
def file_matches_segb_signature(path: pathlib.Path | os.PathLike | str) -> bool:
    path = pathlib.Path(path)
    with path.open("rb") as f:
        return stream_matches_segb_signature(f)


# converting cocoa time to utc struct adjusted to the local timezone
def decode_cocoa_time(cocoa_time: float) -> datetime.datetime:
    return (APPLE_EPOCH + datetime.timedelta(seconds=cocoa_time)).astimezone()


# reads the SEGB file streams and extracts 'SegbEntry' objects
def read_segb_stream(stream: typing.BinaryIO) -> typing.Iterable[SegbEntry]:
    trailer_list: list[EntryMetadata] = []

    # reads header to get magic bytes, entries count, and creation timestamp
    header_raw = stream.read(HEADER_LENGTH) 
    magic_number, entries_count, creation_timestamp_raw, unknown_padding = struct.unpack("<4sid16s", header_raw)
    if magic_number != MAGIC:
        raise ValueError(f"Unexpected file magic. Expected: {MAGIC.hex()}; got: {magic_number.hex()}")

    creation_date = decode_cocoa_time(creation_timestamp_raw)

    # reads trailer entries in reverse
    trailer_reverse_offset = TRAILER_ENTRY_LENGTH * entries_count
    stream.seek(-trailer_reverse_offset, os.SEEK_END)

    # gets metadata for each entry
    for _ in range(entries_count):
        meta_offset = stream.tell()
        trailer_entry_raw = stream.read(TRAILER_ENTRY_LENGTH)
        entry_end_offset, entry_state_raw, entry_timestamp_raw = struct.unpack("<2id", trailer_entry_raw)
        entry_creation_date = decode_cocoa_time(entry_timestamp_raw)
        trailer_list.append(
            EntryMetadata(
                meta_offset, entry_end_offset, entry_state_raw, entry_creation_date))

    stream.seek(HEADER_LENGTH, os.SEEK_SET)

    trailer_list.sort(key=lambda x: x.end_offset)
    for trailer_entry in trailer_list:
        entry_offset = stream.tell()

        if trailer_entry.state == 4:
            continue

        # calculates the CRC
        entry_length = trailer_entry.end_offset - stream.tell() + HEADER_LENGTH
        entry_raw = stream.read(entry_length)
        data = entry_raw[ENTRY_HEADER_LENGTH:]
        crc32_stored, unknown_raw = struct.unpack("Ii", entry_raw[:ENTRY_HEADER_LENGTH])
        crc32_calculated = zlib.crc32(data)

        if (remainder := trailer_entry.end_offset % 4) != 0:
            stream.seek(4 - remainder, os.SEEK_CUR)

        yield SegbEntry(trailer_entry, entry_offset, crc32_stored, crc32_calculated, data, _unknown_value=unknown_raw)


# opens file and reads contents
def read_segb_file(path: pathlib.Path | os.PathLike | str) -> typing.Iterable[SegbEntry]:
    path = pathlib.Path(path)
    with path.open("rb") as f:
        yield from read_segb_stream(f)

def run_command(file_path: pathlib.Path | os.PathLike | str, output_dir):
    try:
        records = []
        for record in read_segb_file(file_path):
            if record.crc_passed == True: # when false, returns null values for Data
                decoded_data = record.data.decode('utf-8', errors='replace')
                clean_data = ''.join(char for char in decoded_data if char.isprintable()) # removing extra bytes
                entry = {
                    "Offset": record.data_start_offset,
                    "Creation Timestamp": record.metadata.creation.strftime('%Y-%m-%d %H:%M:%S %Z'),
                    "State": record.metadata.state,
                    "CRC Passed": record.crc_passed,
                    "Data": clean_data 
                }
                records.append(entry)
    except Exception as e:
        print(f"An error occurred: {e}")

    # Save records to JSON file
    output_file = pathlib.Path(file_path).stem + "_output.json"
    if output_dir:
        output_file = output_dir
    with open(output_file, 'w') as f:
        json.dump(records, f, indent=4)
    print(f"Output saved to {output_file}")


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print(f"USAGE: {pathlib.Path(sys.argv[0]).name} <SEGB file>")
        print()
        exit(1)

    args = parse_arguments()
    run_command(args.input_dir, args.output_dir)
    print()
