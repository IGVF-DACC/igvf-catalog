from biocypher import BioCypher
import yaml
import glob

from db.arango_db import ArangoDB

BIOCYPHER_CONFIG_PATH = './schema-config.yaml'
BIOCYPHER_OUTPUT_PATH = './parsed-data/'


class Adapter:
    def __init__(self):
        with open(BIOCYPHER_CONFIG_PATH, 'r') as config:
            schema_configs = yaml.safe_load(config)

            for c in schema_configs:
                if schema_configs[c].get('label_in_input') == self.dataset:
                    self.schema_config_name = c
                    self.schema_config = schema_configs[c]
                    break
        self.has_edge_id = self.schema_config.get('use_id', True)
        if self.schema_config['represented_as'] == 'edge':
            self.file_prefix = self.schema_config['label_as_edge']
            self.element_type = 'edge'

            if 'relationship' in self.schema_config:
                self.collection_from = schema_configs[self.schema_config['relationship']
                                                      ['from']]['db_collection_name']
                self.collection_to = schema_configs[self.schema_config['relationship']
                                                    ['to']]['db_collection_name']
        else:
            self.file_prefix = ''.join(
                x for x in self.schema_config_name.title() if not x.isspace())
            self.element_type = 'node'

        self.collection = self.schema_config['db_collection_name']

    @classmethod
    def get_biocypher(cls):
        return BioCypher(
            schema_config_path=BIOCYPHER_CONFIG_PATH,
            output_directory=BIOCYPHER_OUTPUT_PATH
        )

    def print_ontology(self):
        Adapter.get_biocypher().show_ontology_structure()

    def write_file(self):
        if getattr(self, 'SKIP_BIOCYPHER', None):
            self.process_file()
            return

        if self.element_type == 'edge':
            Adapter.get_biocypher().write_edges(self.process_file())
        elif self.element_type == 'node':
            Adapter.get_biocypher().write_nodes(self.process_file())
        else:
            print('Unsuported element type')

    def has_indexes(self):
        return 'db_indexes' in self.schema_config

    def requires_fuzzy_search_alias(self):
        return self.schema_config.get('accessible_via', {}).get('fuzzy_text_search')

    def create_indexes(self):
        if not self.has_indexes():
            print('No indexes registered in {} config'.format(self.collection))
            return

        indexes = self.schema_config['db_indexes']

        for index in indexes:
            if indexes[index]['type'] == 'inverted':
                continue  # it's already handled by aliases

            fields_list = indexes[index]['fields']

            for fields in fields_list:
                fields = [f.strip() for f in fields.split(',')]
                ArangoDB().create_index(
                    self.collection,
                    indexes[index]['type'],
                    fields
                )

    def create_aliases(self):
        if not self.requires_fuzzy_search_alias():
            return

        field = self.schema_config['accessible_via']['fuzzy_text_search']

        index_name = '{}_fuzzy_search'.format(self.collection)
        view_name = '{}_fuzzy_search_alias'.format(self.collection)

        ArangoDB().create_index(
            self.collection,
            'inverted',
            [field],
            name=index_name,
            opts={'analyzer': 'text_en_no_stem'}
        )

        ArangoDB().create_view(
            view_name,
            'search-alias',
            self.collection,
            index_name
        )

    def arangodb(self):
        # header filename format: {label_as_edge}-header.csv
        header = self.file_prefix + '-header.csv'
        header_path = BIOCYPHER_OUTPUT_PATH + header

        # data filename format: {label_as_edge}_part{000 - *}.csv
        data_filenames = sorted(
            glob.glob(BIOCYPHER_OUTPUT_PATH + self.file_prefix + '-part*'))

        if self.schema_config.get('db_collection_per_chromosome'):
            self.collection += '_' + self.chr

        return ArangoDB().generate_import_statement(
            header_path,
            data_filenames,
            self.collection,
            self.element_type,
            self.has_edge_id
        )
