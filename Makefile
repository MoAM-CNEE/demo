.PHONY: help

PROVIDER_CONFIG=provider-config-kubernetes

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

crossplane-wrap-kubernetes: ## wrap manifests with Kubernetes provider for Crossplane
	python3 scripts/crossplane_wrap_kubernetes.py $(DIR) -pc $(PROVIDER_CONFIG)
