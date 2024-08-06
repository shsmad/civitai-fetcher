import fnmatch
import os


def recursively_find_all_files_by_extension_in_folder(folder: str, extension: str) -> dict[str, str]:
    matches: dict[str, str] = {}
    for root, dirnames, filenames in os.walk(folder):
        matches.update(
            {filename: os.path.join(root, filename) for filename in fnmatch.filter(filenames, f"*.{extension}")},
        )
    return matches
