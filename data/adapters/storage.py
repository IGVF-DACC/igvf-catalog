import yaml
import os

from db.arango_db import ArangoDB
from db.clickhouse import Clickhouse

CONFIG_PATH = './schema-config.yaml'
OUTPUT_PATH = './parsed-data/'

AVAILABLE_DBS = ['arangodb', 'clickhouse']


class Storage:
    def __init__(self, collection, db='arangodb', dry_run=True):
        if db not in AVAILABLE_DBS:
            raise ValueError(
                'Supported database engines: [arangodb, clickhouse]')

        self.collection = collection
        self.dry_run = dry_run
        self.db = db

        with open(CONFIG_PATH, 'r') as config:
            schema_configs = yaml.safe_load(config)

            for c in schema_configs:
                if schema_configs[c].get('db_collection_name') == collection:
                    self.schema_config_name = c
                    self.schema_config = schema_configs[c]
                    break

        if not hasattr(self, 'schema_config'):
            raise ValueError('Collection: ' + self.collection +
                             ' not defined in schema-config.yaml')

        if self.schema_config['represented_as'] == 'edge':
            self.element_type = 'edge'
        else:
            self.element_type = 'node'

    def save(self, filepath, keep_file=False):
        if self.db == 'arangodb':
            self.save_to_arango(filepath, keep_file)
        elif self.db == 'clickhouse':
            self.save_to_clickhouse(filepath, keep_file)

    def save_to_arango(self, filepath, keep_file=False):
        arango_imp = ArangoDB().generate_json_import_statement(
            filepath, self.collection, type=self.element_type)

        if self.dry_run:
            print(arango_imp[0])
        else:
            os.system(arango_imp[0])
        if not keep_file:
            os.remove(filepath)

    def save_to_clickhouse(self, filepath, keep_file=False):
        if self.dry_run:
            cmd = Clickhouse().generate_json_import_statement(filepath, self.collection)
            print(cmd)
        else:
            Clickhouse().import_jsonl_file(filepath, self.collection)
        if not keep_file:
            os.remove(filepath)

    def all_collections():
        collections = []

        with open(CONFIG_PATH, 'r') as config:
            schema_configs = yaml.safe_load(config)
            for schema in schema_configs:
                collections.append(
                    schema_configs[schema]['db_collection_name'])

        return list(set(collections))

    def create_indexes(self):
        if 'db_indexes' not in self.schema_config:
            print('No indexes registered in {} config'.format(self.collection))
            return

        indexes = self.schema_config['db_indexes']

        for index in indexes:
            if indexes[index]['type'] == 'inverted':
                continue  # it's already handled by aliases

            fields_list = indexes[index]['fields']

            for fields in fields_list:
                fields = [f.strip() for f in fields.split(',')]
                if self.db == 'arangodb':
                    ArangoDB().create_index(
                        self.collection,
                        indexes[index]['type'],
                        fields
                    )

    def create_aliases(self):
        if self.schema_config.get('accessible_via', {}).get('fuzzy_text_search'):
            fields_list = self.schema_config['accessible_via']['fuzzy_text_search']
            index_name = '{}_fuzzy_search'.format(self.collection)
            view_name = '{}_fuzzy_search_alias'.format(self.collection)
            analyzer = 'text_en_no_stem'
            if self.db == 'arangodb':
                self.create_aliases_arango(
                    fields_list, index_name, analyzer, view_name)

        if self.schema_config.get('accessible_via', {}).get('delimiter_text_search'):
            fields_list = self.schema_config['accessible_via']['delimiter_text_search']
            index_name = '{}_delimiter_search'.format(self.collection)
            view_name = '{}_delimiter_search_alias'.format(self.collection)
            analyzer = 'text_delimiter'
            if self.db == 'arangodb':
                self.create_aliases_arango(
                    fields_list, index_name, analyzer, view_name)

    def create_aliases_arango(self, fields_list, index_name, analyzer, view_name):
        fields = [f.strip() for f in fields_list.split(',')]

        ArangoDB().create_index(
            self.collection,
            'inverted',
            fields,
            name=index_name,
            opts={'analyzer': analyzer}
        )

        ArangoDB().create_view(
            view_name,
            'search-alias',
            self.collection,
            index_name
        )
