import os
import json

from db.arango_db import ArangoDB
from db.clickhouse import Clickhouse

CONFIG_PATH = './schemas/registry.json'

AVAILABLE_DBS = ['arangodb', 'clickhouse']


class Storage:
    def __init__(self, collection_name, db='arangodb', dry_run=True):
        if db not in AVAILABLE_DBS:
            raise ValueError(
                'Supported database engines: [arangodb, clickhouse]')

        self.collection_name = collection_name
        self.dry_run = dry_run
        self.db = db

        # read node and edge collection names from data/schemas/registry.json
        with open(CONFIG_PATH, 'r') as registry:
            registry_data = json.load(registry)
            self.node_collection_names = registry_data['nodes']
            self.edge_collection_names = registry_data['edges']

        if self.collection_name in self.node_collection_names:
            self.element_type = 'node'
        elif self.collection_name in self.edge_collection_names:
            self.element_type = 'edge'
        else:
            raise ValueError('Collection: ' + self.collection_name +
                             ' not defined in registry.json')

    def save(self, filepath, keep_file=False):
        if self.db == 'arangodb':
            self.save_to_arango(filepath, keep_file)
        elif self.db == 'clickhouse':
            self.save_to_clickhouse(filepath, keep_file)

    def save_to_arango(self, filepath, keep_file=False):
        arango_imp = ArangoDB().generate_json_import_statement(
            filepath, self.collection_name, type=self.element_type)

        if self.dry_run:
            print(arango_imp[0])
        else:
            os.system(arango_imp[0])
        if not keep_file:
            os.remove(filepath)

    def save_to_clickhouse(self, filepath, keep_file=False):
        if self.dry_run:
            cmd = Clickhouse().generate_json_import_statement(filepath, self.collection_name)
            print(cmd)
        else:
            Clickhouse().import_jsonl_file(filepath, self.collection_name)
        if not keep_file:
            os.remove(filepath)

    def all_collections():
        with open(CONFIG_PATH, 'r') as registry:
            registry_data = json.load(registry)
            collections = list(registry_data['nodes'].keys(
            )) + list(registry_data['edges'].keys())
            return collections
