from arango import ArangoClient
import json

DB_CONFIG_PATH = '../config/development.json'


class ArangoDB:
  __connection = None

  def __init__(self):
    config = json.load(open(DB_CONFIG_PATH))['database']
    self.connection_uri = config['connectionUri']
    self.dbName = config['dbName']
    self.username = config['auth']['username']
    self.password = config['auth']['password']

    if ArangoDB.__connection is None:
      ArangoDB.__connection = ArangoClient(hosts=self.connection_uri)


  def setup_dev(self):
    sys_db = ArangoDB.__connection.db('_system', username='root', password=self.password)

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


  def generate_import_statement(self, header_path, data_filenames, collection, element_type):
    cmds = []

    auth_parameters = (' --server.endpoint {} --server.database {} --server.username {} --server.password {}').format(
      self.connection_uri,
      self.dbName,
      self.username,
      self.password
    )

    for data_filepath in data_filenames:
      cmd = 'arangoimp --headers-file {} --file {} --type csv --collection {} --create-collection --remove-attribute ":TYPE" '.format(
        header_path,
        data_filepath,
        collection
      )

      if element_type == 'edge':
        cmd += '--create-collection-type edge --translate ":START_ID=_from" --translate ":END_ID=_to"'

      cmds.append(cmd + auth_parameters)

    return cmds
