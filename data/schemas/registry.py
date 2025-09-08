import json
import os

# Load the registry from JSON file


def load_registry():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    registry_path = os.path.join(current_dir, 'registry.json')

    with open(registry_path, 'r') as f:
        return json.load(f)


# Export the registry
registry = load_registry()


def get_schema(collection_type, collection_name, adapter_name):
    schema_file = registry[collection_type][collection_name][adapter_name]
    current_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(current_dir, '..', schema_file)
    with open(schema_path, 'r') as f:
        return json.load(f)
