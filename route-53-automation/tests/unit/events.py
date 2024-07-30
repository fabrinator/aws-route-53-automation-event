import os, json

file_path = os.path.realpath(__file__)
json_sns = os.path.abspath(os.path.join(file_path, "../../../", "events/sns.json"))

def sns_json_file():
    with open(json_sns) as file:
        data = json.load(file)
    return data