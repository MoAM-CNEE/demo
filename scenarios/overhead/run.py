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
    CREATE = ("create", 1)
    UPDATE = ("update", 4)
    DELETE = ("delete", 6)

    def __init__(self, value, weight):
        self._value_ = value
        self.weight = weight


class EntityType(Enum):
    APPLICATION = ("application", "app", 6, 362, 10)
    CONTAINERIZATION = ("containerization", "ctr", 3, 248, 45)
    INFRASTRUCTURE = ("infrastructure", "infra", 1, 15, 120)

    def __init__(self, name, prefix, weight, max_count, cooldown_seconds):
        self._value_ = name
        self.prefix = prefix
        self.weight = weight
        self.max_count = max_count
        self.cooldown_seconds = cooldown_seconds


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
    query = f"select * from entity where definition->'$.metadata.name' = '{entity_name}'" if entity_name else "select * from entity"
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


def phase2(url, template_dir, existing_entities, entity_counter):
    log("Phase 2 - create entities up to max count per type")

    def create_entities(entity_type, counter):
        current_count = sum(1 for e in existing_entities.values() if e["type"] == entity_type)
        to_create = entity_type.max_count - current_count
        for _ in range(to_create):
            entity_name = f"{entity_type.prefix}-{counter}"
            key = f"key-{counter}"
            content = f"content {counter}"
            payload = build_create_payload(entity_type, entity_name, key, content, template_dir)
            send_post_request(payload, url)
            now = datetime.now()
            existing_entities[entity_name] = {
                "type": entity_type,
                "created_at": now,
                "last_action_at": now
            }
            counter += 1
        return counter

    entity_counter = create_entities(EntityType.INFRASTRUCTURE, entity_counter)
    entity_counter = create_entities(EntityType.CONTAINERIZATION, entity_counter)
    entity_counter = create_entities(EntityType.APPLICATION, entity_counter)

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
        now = datetime.now()

        if action == ActionType.CREATE:
            entity_type = random.choices(list(EntityType), weights=[et.weight for et in EntityType], k=1)[0]
            current_count = sum(1 for e in existing_entities.values() if e["type"] == entity_type)
            if current_count >= entity_type.max_count:
                log(f"CREATE skipped: {entity_type.value} limit ({entity_type.max_count}) reached")
            else:
                entity_name = f"{entity_type.prefix}-{entity_counter}"
                key = f"key-{entity_counter}"
                content = f"content {entity_counter}"
                payload = build_create_payload(entity_type, entity_name, key, content, template_dir)
                send_post_request(payload, url)
                now = datetime.now()
                existing_entities[entity_name] = {
                    "type": entity_type,
                    "created_at": now,
                    "last_action_at": now
                }
                entity_counter += 1
                action_performed = True

        elif action == ActionType.UPDATE:
            updatable_entities = [
                (name, data) for name, data in existing_entities.items()
                if now - data["last_action_at"] >= timedelta(seconds=data["type"].cooldown_seconds)
            ]
            if updatable_entities:
                entity_name, entity_data = random.choice(updatable_entities)
                payload = build_update_payload(entity_data["type"], entity_name, template_dir)
                send_post_request(payload, url)
                existing_entities[entity_name]["last_action_at"] = datetime.now()
                action_performed = True
            else:
                log("No entities eligible for update (cooldown not met)")

        elif action == ActionType.DELETE:
            deletable_entities = [
                (name, data) for name, data in existing_entities.items()
                if now - data["last_action_at"] >= timedelta(seconds=data["type"].cooldown_seconds)
            ]
            if deletable_entities:
                entity_name, _ = random.choice(deletable_entities)
                payload = build_delete_payload(entity_name)
                send_post_request(payload, url)
                del existing_entities[entity_name]
                action_performed = True
            else:
                log("No entities eligible for deletion (cooldown not met)")

        if action_performed:
            executed_actions += 1
            print(f"Executed {executed_actions} actions")

        wait_between_actions_s = random.uniform(2, 7)
        log(f"Sleeping for {wait_between_actions_s:.2f} seconds...")
        time.sleep(wait_between_actions_s)


def main():
    template_dir = 'templates'
    url = 'http://localhost:31420/execute'

    existing_entities = {}
    entity_counter = 1

    phase1(url)
    log_and_sleep(180)

    entity_counter = phase2(url, template_dir, existing_entities, entity_counter)
    log_and_sleep(300)

    phase3(url, template_dir, existing_entities, entity_counter, N=200)
    log_and_sleep(300)


if __name__ == "__main__":
    main()
