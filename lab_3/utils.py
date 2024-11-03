import json
import re
import csv


def read_csv(path: str) -> list[list[str]]:
    """
        Reads the csv file and takes the necessary lines
    Args:
        path (str): the path to the file

    Returns:
        list: csv file lines except column names
    """
    try:
        with open(path, "r", encoding="utf-16") as file:
            info_file = csv.reader(file, delimiter=";")
            first_line = next(info_file, None)
            return [line for line in info_file] if first_line else []
    except Exception as e:
        print(f"Exception in read_csv: {e}")


def read_json(path: str) -> dict[str, str]:
    """
        Reads the json file
    Args:
        path (str): the path to the file

    Returns:
        dict[str, str]: patterns for text processing
    """
    try:
        with open(path, "r") as file:
            return json.load(file)
    except Exception as e:
        print(f"Exception read_json: {e}")


def write_json(path: str, data: dict) -> None:
    """
        Writing data to a json file
    Args:
        path (str): the path to the file
        data (dict): information to write to the file
    """
    try:
        with open(path, mode="w", encoding="utf-16") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Exception write_json: {e}")


def is_invalid(pattern: dict, data: list) -> bool:
    """
        Searches for invalid lines in a csv file
    Args:
        pattern (dict): patterns for text processing
        data (list): a string from a csv file

    Returns:
        bool: invalid or valid
    """
    return not all(re.match(pattern[key], value) for key, value in zip(pattern, data))


def get_data(pattern: dict, data: list) -> list[int]:
    """
        Returns indexes of all invalid rows

    Args:
        pattern (dict):  patterns for text processing
        data (list): csv file

    Returns:
        list[int]: indexes of all invalid rows
    """
    return [index for index, value in enumerate(data) if is_invalid(pattern, value)]
