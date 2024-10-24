import fnmatch
import hashlib
import io
import os

from typing import Any

import loguru

from blake3 import blake3


def recursively_find_all_files_by_extension_in_folder(folder: str, extension: str) -> dict[str, str]:
    matches: dict[str, str] = {}
    for root, dirnames, filenames in os.walk(folder):
        matches.update(
            {filename: os.path.join(root, filename) for filename in fnmatch.filter(filenames, f"*.{extension}")},
        )
    return matches


def read_chunks(file, size=io.DEFAULT_BUFFER_SIZE):
    """Yield pieces of data from a file-like object until EOF."""
    while True:
        chunk = file.read(size)
        if not chunk:
            break
        yield chunk


def __gen_file_sha256(filename):
    loguru.logger.info(f"Use Memory Optimized SHA256 for {filename}")
    blocksize = 1 << 20
    h = hashlib.sha256()
    length = 0
    with open(os.path.realpath(filename), "rb") as f:
        for block in read_chunks(f, size=blocksize):
            length += len(block)
            h.update(block)

    hash_value = h.hexdigest()
    loguru.logger.info(f"sha256: {hash_value}, length: {str(length)}")
    return hash_value


def __gen_file_blake3(filename: str) -> str:
    loguru.logger.info(f"Use Memory Optimized BLAKE3 for {filename}")
    file_hasher = blake3(max_threads=blake3.AUTO)
    file_hasher.update_mmap(filename)
    hash_value = file_hasher.hexdigest()
    loguru.logger.info(f"blake3: {hash_value}")
    return hash_value


def gen_filehash(filename: str, algorithm: str | None = "blake3") -> str:
    if algorithm == "sha256":
        return __gen_file_sha256(filename)
    elif algorithm == "blake3":
        return __gen_file_blake3(filename)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")


def find_position_by_id(array: list[Any], field_name: str, target_id: Any) -> int:
    return next(
        (index for index, element in enumerate(array) if getattr(element, field_name) == target_id),
        -1,
    )


def aggregate_min_max(elements, keys: list[str] | None = None) -> dict[str, list[int | float]]:
    if keys is None:
        keys = ["cfgScale", "steps"]

    data = {}
    for key in keys:
        vals = [e[key] for e in elements]
        data[key] = [min(vals), max(vals)]
    return data
