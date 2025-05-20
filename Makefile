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
RUN_FILENAME = run.sh
TEAR_DOWN_FILENAME = tear_down.sh

TARGET_CONFIG_MAP_PATH = $(TARGET_DIR)/$(CONFIG_MAP_FILENAME)
TARGET_RULES_PATH = $(TARGET_DIR)/$(RULES_FILENAME)

# targets that aren't annotated with ## are not supposed to be run on their own

help: ## show Makefile contents
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

run: ## run scenario <SCENARIO_NAME>
	@echo "Running scenario $(SCENARIO_NAME)"
	make upload-rules
	$(SCENARIO_DIR)/$(RUN_FILENAME)
	make tear-down

upload-rules: ## upload rules of <SCENARIO_NAME>
	@mkdir -p target
	@echo "Creating a ConfigMap file: $(TARGET_CONFIG_MAP_PATH)"
	@echo "$$CONFIG_MAP_HEADER" > $(TARGET_CONFIG_MAP_PATH)
	cp $(SCENARIO_DIR)/$(RULES_FILENAME) $(TARGET_RULES_PATH)
	sed -i 's/^/    /' $(TARGET_RULES_PATH) # assuming tab = 4 spaces
	cat $(TARGET_RULES_PATH) >> $(TARGET_CONFIG_MAP_PATH)
	@echo "Uploading rules"
	kubectl replace -f $(TARGET_CONFIG_MAP_PATH)

tear-down: ## run tear_down script of scenario <SCENARIO_NAME>
	@echo "Running tear_down script of scenario $(SCENARIO_NAME)"
	$(SCENARIO_DIR)/$(TEAR_DOWN_FILENAME)

crossplane-wrap-kubernetes: ## wrap manifests with Kubernetes provider for Crossplane
	python3 scripts/crossplane_wrap_kubernetes.py $(DIR) -pc $(PROVIDER_CONFIG)

.DEFAULT_GOAL := help
