from arango.client import ArangoClient
from os import path
import json

DB_CONFIG_PATH = '../config/development.json'


class ArangoDB:
    __connection = None

    CUSTOM_ANALYZERS = ['text_en_no_stem']

    def __init__(self):
        config = json.load(open(DB_CONFIG_PATH))['database']
        self.connection_uri = config['connectionUri']
        self.dbName = config['dbName']
        self.username = config['auth']['username']
        self.password = config['auth']['password']

        if ArangoDB.__connection is None:
            ArangoDB.__connection = ArangoClient(hosts=self.connection_uri)

    def get_connection(self):
        return ArangoDB.__connection

    def setup_dev(self):
        sys_db = ArangoDB.__connection.db(
            '_system', username='root', password=self.password)

        if not sys_db.has_database(self.dbName):
            sys_db.create_database(name=self.dbName)

        if not sys_db.has_user(self.username):
            sys_db.create_user(
                username=self.username,
                password=self.password,
                active=True
            )

        sys_db.update_permission(
            username=self.username,
            permission='rw',
            database=self.dbName
        )

        if not path.exists('arangoimp.conf'):
            auth_parameters = ('server.endpoint = {} \n server.database = {} \n server.username = {} \n server.password = {}').format(
                self.connection_uri.replace('://', '+tcp://'),
                self.dbName,
                self.username,
                self.password
            )

            with open('arangoimp.conf', 'w') as conf_file:
                conf_file.write(auth_parameters)

    def generate_import_statement(self, header_path, data_filenames, collection, element_type):
        cmds = []

        for data_filepath in data_filenames:
            cmd = 'arangoimp --headers-file {} --file {} --type csv --collection {} --create-collection --remove-attribute ":TYPE" '.format(
                header_path,
                data_filepath,
                collection
            )

            if element_type == 'node':
                cmd += '--translate ":ID=_key" --remove-attribute "preferred_id" --remove-attribute "id" --remove-attribute ":LABEL"'

            if element_type == 'edge':
                cmd += '--create-collection-type edge --translate ":START_ID=_from" --translate ":END_ID=_to"'

            cmds.append(cmd)

        return cmds

    def create_custom_analyzer(self, db, analyzer):
        if analyzer == 'text_en_no_stem':
            db.create_analyzer(
                name='text_en_no_stem',
                analyzer_type='text',
                properties={'locale': 'en', 'accent': False,
                            'case': 'lower', 'stemming': False, 'stopwords': []},
                features=['position', 'frequency', 'norm']
            )

    def index_exists(self, collection_db, index_name):
        return (index_name in [i['name'] for i in collection_db.indexes()])

    def view_exists(self, db, view_name):
        return (view_name in [v['name'] for v in db.views()])

    def create_index(self, collection, name, index_type, fields, opts={}):
        db = ArangoDB.__connection.db(
            self.dbName, username=self.username, password=self.password)

        collection_db = db.collection(collection)

        if index_type == 'persistent':
            collection_db.add_persistent_index(
                name=name, fields=fields, in_background=True)
        elif index_type == 'zkd':
            data = {
                'type': 'zkd',
                'fields': fields,
                'name': name,
                'inBackground': True,
                'fieldValueTypes': 'double'
            }
            collection_db._add_index(data)
        elif index_type == 'inverted':
            if self.index_exists(collection_db, name):
                return

            if opts['analyzer'] in ArangoDB.CUSTOM_ANALYZERS:
                self.create_custom_analyzer(db, opts['analyzer'])
            collection_db.add_inverted_index(
                name=name, fields=fields, analyzer=opts['analyzer'], inBackground=True)

    def create_view(self, view_name, view_type, collection_name, index_name):
        db = ArangoDB.__connection.db(
            self.dbName, username=self.username, password=self.password)

        if self.view_exists(db, view_name):
            return

        db.create_view(name=view_name, view_type=view_type, properties={
            'indexes': [{'collection': collection_name, 'index': index_name}]
        })
