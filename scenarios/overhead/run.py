from enum import Enum
import requests
import os
import time
import random
from datetime import datetime, timedelta


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{ts} {msg}")


def log_and_sleep(seconds):
    log(f"Sleeping for {seconds} seconds...")
    time.sleep(seconds)


class ActionType(Enum):
    CREATE = ("create", 3)
    UPDATE = ("update", 5)
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


def build_delete_payload(entity_name=None):
    if entity_name:
        query = f"select * from entity where definition->'$.metadata.name' = '{entity_name}'"
    else:
        query = "select * from entity"
    return {
        "collectionName": "moam.statemanager",
        "actionName": "DeleteEntityAction",
        "params": {
            "query": query
        }
    }


def send_post_request(payload, url):
    headers = {'Content-Type': 'application/json'}
    log(f"Sending payload: {payload}")
    response = requests.post(url, headers=headers, json=payload)
    log(f"Status Code: {response.status_code}")
    log(f"Response Text: {response.text}")


# ---------------------------
# PHASES
# ---------------------------

def phase1(url):
    log("Phase 1 - delete all entities")

    payload = build_delete_payload()
    send_post_request(payload, url)


def phase2(url, template_dir, n_infra, n_ctr, n_app, existing_entities, entity_counter):
    log("Phase 2 - create specified amounts of entities of each type")

    def create_entities(entity_type, count, counter):
        for _ in range(count):
            entity_name = f"{entity_type.prefix}-{counter}"
            key = f"key-{counter}"
            content = f"content {counter}"
            payload = build_create_payload(entity_type, entity_name, key, content, template_dir)
            send_post_request(payload, url)
            existing_entities[entity_name] = {
                "type": entity_type,
                "created_at": datetime.now()
            }
            counter += 1
        return counter

    entity_counter = create_entities(EntityType.INFRASTRUCTURE, n_infra, entity_counter)
    entity_counter = create_entities(EntityType.CONTAINERIZATION, n_ctr, entity_counter)
    entity_counter = create_entities(EntityType.APPLICATION, n_app, entity_counter)

    return entity_counter


def phase3(url, template_dir, existing_entities, entity_counter, N=10):
    log("Phase 3 - random create/update/delete loop")

    executed_actions = 0
    while executed_actions < N:
        if existing_entities:
            possible_actions = list(ActionType)
        else:
            possible_actions = [ActionType.CREATE]

        action_weights = [a.weight for a in possible_actions]
        action = random.choices(possible_actions, weights=action_weights, k=1)[0]

        action_performed = False

        if action == ActionType.CREATE:
            entity_type = random.choices(list(EntityType), weights=[et.weight for et in EntityType], k=1)[0]
            entity_name = f"{entity_type.prefix}-{entity_counter}"
            key = f"key-{entity_counter}"
            content = f"content {entity_counter}"
            payload = build_create_payload(entity_type, entity_name, key, content, template_dir)
            send_post_request(payload, url)
            existing_entities[entity_name] = {
                "type": entity_type,
                "created_at": datetime.now()
            }
            entity_counter += 1
            action_performed = True

        elif action == ActionType.UPDATE:
            entity_name = random.choice(list(existing_entities.keys()))
            entity_type = existing_entities[entity_name]["type"]
            payload = build_update_payload(entity_type, entity_name, template_dir)
            send_post_request(payload, url)
            action_performed = True

        elif action == ActionType.DELETE:
            now = datetime.now()
            deletable_entities = [
                name for name, data in existing_entities.items()
                if now - data["created_at"] >= timedelta(seconds=90)
            ]
            if deletable_entities:
                entity_name = random.choice(deletable_entities)
                payload = build_delete_payload(entity_name)
                send_post_request(payload, url)
                del existing_entities[entity_name]
                action_performed = True
            else:
                log("No entities old enough to delete yet, skipping delete")

        if action_performed:
            executed_actions += 1

        wait_between_actions_s = random.uniform(2, 15)
        log(f"Sleeping for {wait_between_actions_s:.2f} seconds...")
        time.sleep(wait_between_actions_s)


def main():
    template_dir = 'templates'
    url = 'http://localhost:31420/execute'

    existing_entities = {}
    entity_counter = 1

    phase1(url)
    log_and_sleep(180)

    entity_counter = phase2(url, template_dir, n_infra=1, n_ctr=2, n_app=3,
                            existing_entities=existing_entities,
                            entity_counter=entity_counter)
    log_and_sleep(300)

    phase3(url, template_dir, existing_entities, entity_counter, N=10)
    log_and_sleep(300)


if __name__ == "__main__":
    main()
