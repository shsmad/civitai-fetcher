import json
import struct

from safetensors import safe_open

from src.utils import recursively_find_all_files_by_extension_in_folder


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


def can_read_safetensor_metadata(filename: str, quick=True):
    if not quick:
        tf = safe_open(filename, framework="tf", device="cpu")
        return len(tf.keys()) > 0

    try:
        with open(filename, "rb") as f:
            return parse_safetensor_header(f)
    except UnicodeDecodeError:
        return False


def get_corrupted_files(base_path: str) -> list[str]:
    files = recursively_find_all_files_by_extension_in_folder(
        folder=base_path,
        extension="safetensors",
    ).values()

    res = [file for file in files if not can_read_safetensor_metadata(file, quick=True)]
    res.extend([file for file in files if not can_read_safetensor_metadata(file, quick=False)])

    return list(set(res))
