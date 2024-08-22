import yaml
import glob
import os

from db.arango_db import ArangoDB
from .writer import S3Writer, LocalWriter

CONFIG_PATH = './schema-config.yaml'
OUTPUT_PATH = './parsed-data/'


class Adapter:
    def __init__(self):
        with open(CONFIG_PATH, 'r') as config:
            schema_configs = yaml.safe_load(config)

            for c in schema_configs:
                if schema_configs[c].get('label_in_input') == self.label:
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

    def write_file(self, s3_bucket='', session=None):
        self.s3_bucket = s3_bucket

        self.output_filepath = '{}/{}.json'.format(
            OUTPUT_PATH,
            self.dataset
        )

        if (s3_bucket):
            s3_filepath = self.collection + '/' + \
                self.output_filepath.split('/')[-1]
            self.writer = S3Writer(self.s3_bucket, s3_filepath, session)
        else:
            self.writer = LocalWriter(self.output_filepath)

        self.writer.open()

        self.process_file()

        self.writer.close()

    def has_indexes(self):
        return 'db_indexes' in self.schema_config

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
        if self.schema_config.get('accessible_via', {}).get('fuzzy_text_search'):
            fields_list = self.schema_config['accessible_via']['fuzzy_text_search']
            index_name = '{}_fuzzy_search'.format(self.collection)
            view_name = '{}_fuzzy_search_alias'.format(self.collection)
            analyzer = 'text_en_no_stem'
            self.create_aliases_arango(
                fields_list, index_name, analyzer, view_name)

        if self.schema_config.get('accessible_via', {}).get('delimiter_text_search'):
            fields_list = self.schema_config['accessible_via']['delimiter_text_search']
            index_name = '{}_delimiter_search'.format(self.collection)
            view_name = '{}_delimiter_search_alias'.format(self.collection)
            analyzer = 'text_delimiter'
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

    def arangodb(self):
        # header filename format: {label_as_edge}-header.csv
        header = self.file_prefix + '-header.csv'
        header_path = OUTPUT_PATH + header

        # data filename format: {label_as_edge}_part{000 - *}.csv
        data_filenames = sorted(
            glob.glob(OUTPUT_PATH + self.file_prefix + '-part*'))

        if self.schema_config.get('db_collection_per_chromosome'):
            self.collection += '_' + self.chr

        return ArangoDB().generate_import_statement(
            header_path,
            data_filenames,
            self.collection,
            self.element_type,
            self.has_edge_id
        )

    def save_to_arango(self):
        arango_imp = ArangoDB().generate_json_import_statement(
            self.output_filepath, self.collection, type=self.type)

        if self.dry_run:
            print(arango_imp[0])
        else:
            os.system(arango_imp[0])

    # TODO: does the smart_open lib need any last flush?
    def save_to_s3(self):
        pass

    def save(self):
        if self.s3_bucket == 's3':
            self.save_to_s3()
        else:
            self.save_to_arango()
