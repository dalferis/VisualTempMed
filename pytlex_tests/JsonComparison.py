"""
Standalone script that digests JSON data and reports if they
are equivalent in content.
"""

import json
from typing import Any
from pathlib import Path


def compare_json_string_data(json_str_a: str, json_str_b: str) -> bool:
    """
    Deserializes the JSON input and returns the result of a deep comparison.
    """
    process_json_str = lambda x: sort_and_process_json(json.loads(x))
    json_dict_a = process_json_str(json_str_a)
    json_dict_b = process_json_str(json_str_b)

    return json_dict_a == json_dict_b


def sort_and_process_json(json_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Since the JSON is an unordered set, this function normalizes the data
    so the comparison can be correct, and returns it.
    """
    id_sorting_fn = lambda x: x["id"]

    # first sort the array of nodes by id
    json_dict["nodes"].sort(key=id_sorting_fn)

    # then sort the links by id
    json_dict["links"].sort(key=id_sorting_fn)

    # finally, we sort every single nested element in a partition
    for partition in json_dict["partitions"]:
        partition["nodeIDs"].sort()
        partition["linkIDs"].sort()
        partition["Timeline"].sort(key=id_sorting_fn)
    # then we use the hash of the sorted nodeIDs (as tuple) to sort the array
    json_dict["partitions"].sort(key=lambda x: hash(tuple(x["nodeIDs"])))

    return json_dict


def _compare_json_from_files(json_path_a: Path, json_path_b: Path) -> bool:
    """
    Helper method that takes care of the JSON value unwrapping from a file
    instead of from raw strings.
    """
    def read_file_data(path: Path) -> str:
        with open(path, 'r') as f:
            return f.read()

    json_str_a = read_file_data(json_path_a)
    json_str_b = read_file_data(json_path_b)

    return compare_json_string_data(json_str_a, json_str_b)


if __name__ == "__main__":
    # sample of how to use this script
    filename_a = Path("test_json_a.json")
    filename_b = Path("test_json_b.json")

    compare_result = _compare_json_from_files(filename_a, filename_b)
    print("files match?: ", compare_result)
