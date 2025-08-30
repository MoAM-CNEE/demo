from enum import Enum
import requests
import os
import time
import random
import json
from datetime import datetime, timedelta


# ---------------------------
# Logging
# ---------------------------
def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{ts} {msg}")


def log_and_sleep(seconds):
    log(f"Sleeping for {seconds} seconds...")
    time.sleep(seconds)


# ---------------------------
# Enums
# ---------------------------
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


# ---------------------------
# File & Template Utils
# ---------------------------
def read_file(file_path):
    with open(file_path, 'r') as f:
        return f.read().strip()


def apply_substitutions(template, substitutions):
    for key, value in substitutions.items():
        template = template.replace(key, value)
    return template


def load_template(entity_type: EntityType, action: ActionType, template_dir):
    file_name = f"{entity_type.value}_{action.value}.json"
    file_path = os.path.join(template_dir, file_name)
    return read_file(file_path)


def build_payload(entity_type: EntityType, action: ActionType, substitutions, template_dir):
    template = load_template(entity_type, action, template_dir)
    payload_str = apply_substitutions(template, substitutions)
    # Convert JSON string to dict
    return json.loads(payload_str)


# ---------------------------
# HTTP Request
# ---------------------------
def send_post_request(payload, url, dry_run=False):
    headers = {'Content-Type': 'application/json'}
    log(f"Sending payload: {payload}")
    if not dry_run:
        response = requests.post(url, headers=headers, json=payload)
        log(f"Status Code: {response.status_code}")
        log(f"Response Text: {response.text}")


# ---------------------------
# PHASES
# ---------------------------
def get_substitutions(entity_name):
    counter = entity_name.split('-')[1]
    return {
        "<ENTITY_NAME>": entity_name,

        "<KEY>": f"key-{counter}",
        "<CONTENT>": f"content {counter}",

        "<RESOURCE_NAME>": entity_name,
        "<LIMITS_CPU>": "50m",
        "<LIMITS_MEMORY>": "64Mi",

        "<INSTANCE_NAME_PATTERN>": f"^{entity_name}-",
        "<FLAVOR_ID>": "13a343c9-1fc5-4dae-9a74-203d290d736b"
    }


def phase1():
    log("Phase 1 - idle run")


def phase2(url, template_dir, existing_entities, entity_counter):
    log("Phase 2 - create entities up to max count per type")

    def create_entities(entity_type, counter):
        current_count = sum(1 for e in existing_entities.values() if e["type"] == entity_type)
        to_create = entity_type.max_count - current_count
        for _ in range(to_create):
            entity_name = f"{entity_type.prefix}-{counter}"
            substitutions = get_substitutions(entity_name)
            try:
                payload = build_payload(entity_type, ActionType.CREATE, substitutions, template_dir)
                send_post_request(payload, url)
                now = datetime.now()
                existing_entities[entity_name] = {
                    "type": entity_type,
                    "created_at": now,
                    "last_action_at": now
                }
                counter += 1
            except FileNotFoundError:
                log(f"No CREATE template found for {entity_type.value}, skipping.")
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
            possible_actions = [ActionType.CREATE, ActionType.UPDATE, ActionType.DELETE]
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
                substitutions = get_substitutions(entity_name)
                try:
                    payload = build_payload(entity_type, ActionType.CREATE, substitutions, template_dir)
                    send_post_request(payload, url)
                    existing_entities[entity_name] = {
                        "type": entity_type,
                        "created_at": now,
                        "last_action_at": now
                    }
                    entity_counter += 1
                    action_performed = True
                except FileNotFoundError:
                    log(f"No CREATE template for {entity_type.value}, skipping.")

        elif action in [ActionType.UPDATE, ActionType.DELETE]:
            candidates = [
                (name, data) for name, data in existing_entities.items()
                if now - data["last_action_at"] >= timedelta(seconds=data["type"].cooldown_seconds)
            ]
            if candidates:
                entity_name, entity_data = random.choice(candidates)
                substitutions = get_substitutions(entity_name)
                try:
                    payload = build_payload(entity_data["type"], action, substitutions, template_dir)
                    send_post_request(payload, url)
                    if action == ActionType.DELETE:
                        del existing_entities[entity_name]
                    else:
                        existing_entities[entity_name]["last_action_at"] = datetime.now()
                    action_performed = True
                except FileNotFoundError:
                    log(f"No {action.value.upper()} template for {entity_data['type'].value}, skipping.")
            else:
                log(f"No entities eligible for {action.value} (cooldown not met)")

        if action_performed:
            executed_actions += 1
            print(f"Executed {executed_actions} actions")

        wait_between_actions_s = random.uniform(2, 7)
        log(f"Sleeping for {wait_between_actions_s:.2f} seconds...")
        time.sleep(wait_between_actions_s)


# ---------------------------
# MAIN
# ---------------------------
def main():
    template_dir = 'templates'
    url = 'http://localhost:31420/execute'

    existing_entities = {}
    entity_counter = 1

    # phase1()
    # log_and_sleep(180)

    # entity_counter = phase2(url, template_dir, existing_entities, entity_counter)
    # log_and_sleep(300)

    phase3(url, template_dir, existing_entities, entity_counter, N=20)
    # log_and_sleep(300)


if __name__ == "__main__":
    main()
