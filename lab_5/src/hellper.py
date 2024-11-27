import json


class Reader:
    @staticmethod
    def read_json(filename: str):
        with open(filename, "r") as file:
            return json.load(file)
