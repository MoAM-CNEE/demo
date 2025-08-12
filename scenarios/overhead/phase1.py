import requests
import json
import os

def read_file(file_path):
    with open(file_path, 'r') as f:
        return f.read().strip()

def apply_substitutions(template, substitutions):
    for key, value in substitutions.items():
        template = template.replace(key, value)
    return template

def build_create_payload(definition_file, entity_name, key, content):
    definition = read_file(definition_file)
    substitutions = {
        "<ENTITY_NAME>": entity_name,
        "<KEY>": key,
        "<CONTENT>": content
    }
    definition = apply_substitutions(definition, substitutions)

    return {
        "collectionName": "moam.statemanager",
        "actionName": "CreateEntityAction",
        "params": {
            "definition": definition
        }
    }

def build_delete_payload(entity_name):
    query_template = "select * from entity where definition->'$.metadata.name' = '<ENTITY_NAME>'"
    query = query_template.replace("<ENTITY_NAME>", entity_name)

    return {
        "collectionName": "moam.statemanager",
        "actionName": "DeleteEntityAction",
        "params": {
            "query": query
        }
    }

def build_update_payload(definition_file, entity_name, lambdas_file):
    query_template = "select * from entity where definition->'$.metadata.name' = '<ENTITY_NAME>'"
    query = query_template.replace("<ENTITY_NAME>", entity_name)
    lambdas = read_file(lambdas_file)

    return {
        "collectionName": "moam.statemanager",
        "actionName": "UpdateEntityAction",
        "params": {
            "query": query,
            "lambdas": lambdas
        }
    }

def send_post_request(payload, url):
    headers = {'Content-Type': 'application/json'}

    print(payload)

    response = requests.post(url, headers=headers, json=payload)

    print(f"Status Code: {response.status_code}")
    print(f"Response Text: {response.text}")

def main():
    template_dir = 'templates'

    definition_file = os.path.join(template_dir, 'application_definition.txt')
    lambdas_file = os.path.join(template_dir, 'application_lambdas.txt')

    entity_name = "cnee-crud-operations-message"
    key = "key123"
    content = "sample content for the message"
    url = 'http://localhost:31420/execute'

    create_payload = build_create_payload(definition_file, entity_name, key, content)
    send_post_request(create_payload, url)

    delete_payload = build_delete_payload(entity_name)
    send_post_request(delete_payload, url)

    update_payload = build_update_payload(definition_file, entity_name, lambdas_file)
    send_post_request(update_payload, url)

if __name__ == "__main__":
    main()
