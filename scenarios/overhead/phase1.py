from enum import Enum
import requests
import os
import time
import random


class ActionType(Enum):
    CREATE = ("create", 3)
    UPDATE = ("update", 2)
    DELETE = ("delete", 2)

    def __init__(self, value, weight):
        self._value_ = value
        self.weight = weight


class EntityType(Enum):
    APPLICATION = ("application", "app", 6)
    CONTAINERIZATION = ("containerization", "ctr", 3)
    INFRASTRUCTURE = ("infrastructure", "infra", 1)

    def __init__(self, name, prefix, weight):
        self._value_ = name
        self.prefix = prefix
        self.weight = weight


def read_file(file_path):
    with open(file_path, 'r') as f:
        return f.read().strip()


def apply_substitutions(template, substitutions):
    for key, value in substitutions.items():
        template = template.replace(key, value)
    return template


def build_create_payload(entity_type: EntityType, entity_name, key, content, template_dir):
    definition_file = os.path.join(template_dir, f"{entity_type.value}_definition.json")
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


def build_update_payload(entity_type: EntityType, entity_name, template_dir):
    lambdas_file = os.path.join(template_dir, f"{entity_type.value}_lambdas.json")
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


def build_delete_payload(entity_name):
    query = f"select * from entity where definition->'$.metadata.name' = '{entity_name}'"
    return {
        "collectionName": "moam.statemanager",
        "actionName": "DeleteEntityAction",
        "params": {
            "query": query
        }
    }


def send_post_request(payload, url):
    headers = {'Content-Type': 'application/json'}
    print(f"Sending payload: {payload}")
    response = requests.post(url, headers=headers, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response Text: {response.text}")


def main():
    template_dir = 'templates'
    url = 'http://localhost:31420/execute'

    N = 10
    existing_entities = {}  # entity_name -> EntityType
    entity_counter = 1

    for i in range(N):
        if existing_entities:
            possible_actions = list(ActionType)
        else:
            possible_actions = [ActionType.CREATE]

        action_weights = [a.weight for a in possible_actions]
        action = random.choices(possible_actions, weights=action_weights, k=1)[0]

        if action == ActionType.CREATE:
            entity_type = random.choices(list(EntityType), weights=[et.weight for et in EntityType], k=1)[0]
            entity_name = f"{entity_type.prefix}-{entity_counter}"
            key = f"key-{entity_counter}"
            content = f"content {entity_counter}"
            payload = build_create_payload(entity_type, entity_name, key, content, template_dir)
            send_post_request(payload, url)
            existing_entities[entity_name] = entity_type
            entity_counter += 1

        elif action == ActionType.UPDATE:
            entity_name = random.choice(list(existing_entities.keys()))
            entity_type = existing_entities[entity_name]
            payload = build_update_payload(entity_type, entity_name, template_dir)
            send_post_request(payload, url)

        elif action == ActionType.DELETE:
            entity_name = random.choice(list(existing_entities.keys()))
            payload = build_delete_payload(entity_name)
            send_post_request(payload, url)
            del existing_entities[entity_name]

        wait_between_actions_s = random.uniform(2, 15)
        print(f"Sleeping for {wait_between_actions_s:.2f} seconds...")
        time.sleep(wait_between_actions_s)


if __name__ == "__main__":
    main()
