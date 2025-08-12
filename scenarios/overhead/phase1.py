from enum import Enum
import requests
import os
import time
import random

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
    query = f"select * from entity where definition->'$.metadata.name' = '{entity_name}'"
    return {
        "collectionName": "moam.statemanager",
        "actionName": "DeleteEntityAction",
        "params": {
            "query": query
        }
    }

def build_update_payload(entity_name, lambdas_file):
    query = f"select * from entity where definition->'$.metadata.name' = '{entity_name}'"
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
    print(f"Sending payload: '{payload}'")
    response = requests.post(url, headers=headers, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response Text: '{response.text}'")

class ActionType(Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"

def main():
    template_dir = 'templates'
    definition_file = os.path.join(template_dir, 'application_definition.json')
    lambdas_file = os.path.join(template_dir, 'application_lambdas.json')
    url = 'http://localhost:31420/execute'

    N = 15
    existing_entities = set()

    entity_counter = 1

    for i in range(N):
        actions = [ActionType.CREATE]
        weights = [4]  # 4/7 for create

        if existing_entities:
            actions.extend([ActionType.UPDATE, ActionType.DELETE])
            weights.extend([2, 1])

        action = random.choices(actions, weights=weights, k=1)[0]

        if action == ActionType.CREATE:
            entity_name = f"entity-{entity_counter}"
            key = f"key-{entity_counter}"
            content = f"content {entity_counter}"
            payload = build_create_payload(definition_file, entity_name, key, content)
            send_post_request(payload, url)
            existing_entities.add(entity_name)
            entity_counter += 1

        elif action == ActionType.UPDATE:
            entity_name = random.choice(list(existing_entities))
            payload = build_update_payload(entity_name, lambdas_file)
            send_post_request(payload, url)

        elif action == ActionType.DELETE:
            entity_name = random.choice(list(existing_entities))
            payload = build_delete_payload(entity_name)
            send_post_request(payload, url)
            existing_entities.remove(entity_name)

        wait_between_actions_s = random.uniform(2, 15)
        time.sleep(f"Sleeping for {wait_between_actions_s}")

if __name__ == "__main__":
    main()
