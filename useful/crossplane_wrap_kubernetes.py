import yaml
import os
import argparse
from pathlib import Path


def wrap_manifest(input_manifest, name, provider_config):
    return {
        "apiVersion": "kubernetes.crossplane.io/v1alpha2",
        "kind": "Object",
        "metadata": {
            "name": name
        },
        "spec": {
            "forProvider": {
                "manifest": input_manifest
            },
            "providerConfigRef": {
                "name": provider_config
            }
        }
    }


def process_directory(directory, provider_config):
    for file_path in Path(directory).glob("*.yaml"):
        with open(file_path, "r") as f:
            try:
                input_manifest = yaml.safe_load(f)
            except yaml.YAMLError as e:
                print(f"Failed to parse {file_path}: {e}")
                continue

        name = file_path.stem  # filename without extension
        result_manifest = input_manifest
        if input_manifest["apiVersion"] != "kubernetes.crossplane.io/v1alpha2":
            result_manifest = wrap_manifest(input_manifest, name, provider_config)

        with open(file_path, "w") as f:
            yaml.dump(result_manifest, f, sort_keys=False)

        print(f"Processed {file_path.name}")


def main():
    parser = argparse.ArgumentParser(description="Wrap all Kubernetes manifests in a directory into Crossplane Objects.")
    parser.add_argument("directory", help="Path to directory containing YAML files")
    parser.add_argument("-pc", "--provider-config", default="provider-config-kubernetes", help="Provider config name")
    args = parser.parse_args()

    process_directory(args.directory, args.provider_config)


if __name__ == "__main__":
    main()
