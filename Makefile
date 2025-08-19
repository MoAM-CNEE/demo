.PHONY: help

PROVIDER_CONFIG=provider-config-kubernetes

define CONFIG_MAP_HEADER
apiVersion: v1
kind: ConfigMap
metadata:
  name: rules
  namespace: themis-executor
data:
  rules.drl: |
endef
export CONFIG_MAP_HEADER

SCENARIO_NAME ?= "sample"

TARGET_DIR = target
SCENARIOS_DIR = scenarios
SCENARIO_DIR = $(SCENARIOS_DIR)/$(SCENARIO_NAME)

CONFIG_MAP_FILENAME = cm.yaml
RULES_FILENAME = rules.drl
INIT_FILENAME = init.sh
RUN_FILENAME = run.sh
TEAR_DOWN_FILENAME = tear_down.sh

TARGET_CONFIG_MAP_PATH = $(TARGET_DIR)/$(CONFIG_MAP_FILENAME)
TARGET_RULES_PATH = $(TARGET_DIR)/$(RULES_FILENAME)

NPD = --no-print-directory

# targets that aren't annotated with ## are not supposed to be run on their own

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

run: ## make run SCENARIO_NAME=sample | all stages of the scenario
	@make $(NPD) log-time MSG="make run $(SCENARIO_NAME)"
	@make $(NPD) upload-rules
	@make $(NPD) init
	@make $(NPD) actual-run
	@make $(NPD) tear-down

upload-rules: ## make upload-rules SCENARIO_NAME=sample
	@make $(NPD) log-time MSG="make upload rules"
	@if [ -f "$(SCENARIO_DIR)/$(RULES_FILENAME)" ]; then \
		mkdir -p target; \
		echo "Creating a ConfigMap file: $(TARGET_CONFIG_MAP_PATH)"; \
		echo "$$CONFIG_MAP_HEADER" > $(TARGET_CONFIG_MAP_PATH); \
		cp $(SCENARIO_DIR)/$(RULES_FILENAME) $(TARGET_RULES_PATH); \
		sed -i 's/^/    /' $(TARGET_RULES_PATH); \
		cat $(TARGET_RULES_PATH) >> $(TARGET_CONFIG_MAP_PATH); \
		kubectl replace -f $(TARGET_CONFIG_MAP_PATH); \
	else \
		echo "Warning: $(RULES_FILENAME) not found in $(SCENARIO_DIR). Skipping upload."; \
	fi

init: ## make init SCENARIO_NAME=sample
	@make $(NPD) log-time MSG="make init"
	$(SCENARIO_DIR)/$(INIT_FILENAME)

actual-run: ## make actual-run SCENARIO_NAME=sample | only 'run' script
	@make $(NPD) log-time MSG="make actual-run"
	$(SCENARIO_DIR)/$(RUN_FILENAME)

tear-down: ## make tear-down SCENARIO_NAME=sample
	@make $(NPD) log-time MSG="make tear-down"
	$(SCENARIO_DIR)/$(TEAR_DOWN_FILENAME)

crossplane-wrap-kubernetes: ## wrap manifests with Kubernetes provider for Crossplane
	python3 useful/crossplane_wrap_kubernetes.py $(DIR) -pc $(PROVIDER_CONFIG)

log-time:
	@echo "$$(date +'%Y-%m-%d %T') $(MSG)"

.DEFAULT_GOAL := help
