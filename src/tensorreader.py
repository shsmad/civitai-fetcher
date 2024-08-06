import json
import struct


def parse_safetensor_header(f):
    f.seek(0)
    header = f.read(8)
    # Interpret the bytes as a little-endian unsigned 64-bit integer
    length_of_header = struct.unpack("<Q", header)[0]
    # read bytes from 8 to 7+length_of_header
    f.seek(8)
    metadata = f.read(length_of_header)
    # Interpret the response as a JSON object
    json.loads(metadata.decode("utf-8"))
    return True


def can_read_safetensor_metadata(filename: str):
    try:
        with open(filename, "rb") as f:
            return parse_safetensor_header(f)
    except UnicodeDecodeError:
        return False
