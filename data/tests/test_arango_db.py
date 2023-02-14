from unittest.mock import patch, mock_open, Mock

from db.arango_db import ArangoDB


MOCK_CONFIG_FILE = '''
{  
  "environment": "development",
  "host": {
    "protocol": "http",
    "hostname": "localhost",
    "port": 2023
  },
  "database": {
    "connectionUri": "http://example.org:8529",
    "dbName": "igvf",
    "auth": {
        "username": "test",
        "password": "test"
    }
  }
}'''


@patch('db.arango_db.ArangoClient')
@patch("builtins.open", new_callable=mock_open, read_data=MOCK_CONFIG_FILE)
def test_arangodb_ingests_config_file(mock_op, mock_client):
  db = ArangoDB()

  assert db.connection_uri == 'http://example.org:8529'
  assert db.dbName == 'igvf'
  assert db.username == 'test'
  assert db.password == 'test'

  mock_client.assert_called_with(hosts='http://example.org:8529')


@patch('db.arango_db.ArangoClient')
@patch("builtins.open", new_callable=mock_open, read_data=MOCK_CONFIG_FILE)
def test_arangodb_setup_dev_creates_db_if_inexistent(mock_op, mock_client):
  db = ArangoDB()

  mock_client = db.get_connection()
  
  db_mock = Mock()
  mock_client.db.return_value = db_mock

  db_mock.has_database.return_value = False

  db.setup_dev()
  
  db_mock.has_database.assert_called_with('igvf')
  db_mock.create_database.assert_called_with(name='igvf')


@patch('db.arango_db.ArangoClient')
@patch("builtins.open", new_callable=mock_open, read_data=MOCK_CONFIG_FILE)
def test_arangodb_setup_dev_doesnt_create_db_if_it_exists(mock_op, mock_client):
  db = ArangoDB()

  mock_client = db.get_connection()
  
  db_mock = Mock()
  mock_client.db.return_value = db_mock

  db_mock.has_database.return_value = True

  db.setup_dev()
  
  db_mock.has_database.assert_called_with('igvf')
  db_mock.create_database.assert_not_called()


@patch('db.arango_db.ArangoClient')
@patch("builtins.open", new_callable=mock_open, read_data=MOCK_CONFIG_FILE)
def test_arangodb_setup_dev_creates_user_if_inexistent(mock_op, mock_client):
  db = ArangoDB()

  mock_client = db.get_connection()
  
  db_mock = Mock()
  mock_client.db.return_value = db_mock

  db_mock.has_database.return_value = True
  db_mock.has_user.return_value = False

  db.setup_dev()
  
  db_mock.has_user.assert_called_with('test')
  db_mock.create_user.assert_called_with(username='test', password='test', active=True)


@patch('db.arango_db.ArangoClient')
@patch("builtins.open", new_callable=mock_open, read_data=MOCK_CONFIG_FILE)
def test_arangodb_setup_dev_doesnt_create_user_if_existent(mock_op, mock_client):
  db = ArangoDB()

  mock_client = db.get_connection()
  
  db_mock = Mock()
  mock_client.db.return_value = db_mock

  db_mock.has_database.return_value = True
  db_mock.has_user.return_value = True

  db.setup_dev()
  
  db_mock.has_user.assert_called_with('test')
  db_mock.create_user.assert_not_called()


@patch('db.arango_db.ArangoClient')
@patch("builtins.open", new_callable=mock_open, read_data=MOCK_CONFIG_FILE)
def test_arangodb_setup_dev_adds_correct_permissions(mock_op, mock_client):
  db = ArangoDB()

  mock_client = db.get_connection()
  
  db_mock = Mock()
  mock_client.db.return_value = db_mock

  db_mock.has_database.return_value = True
  db_mock.has_user.return_value = True

  db.setup_dev()
  
  db_mock.update_permission.assert_called_with(username='test', permission='rw', database='igvf')


@patch('db.arango_db.ArangoClient')
@patch('db.arango_db.path')
def test_arangodb_setup_dev_writes_arangoimp_conf_if_inexistent(mock_os, mock_client):
  with patch("builtins.open", new_callable=mock_open, read_data=MOCK_CONFIG_FILE) as mock_op:
    db = ArangoDB()

  mock_os.exists.return_value = False
  
  with patch('builtins.open') as mock_op:
    file_handle = mock_op.return_value.__enter__.return_value

    db.setup_dev()

    mock_os.exists.assert_called_with('arangoimp.conf')
    file_handle.write.assert_called_with('server.endpoint = http+tcp://example.org:8529 \n server.database = igvf \n server.username = test \n server.password = test')


@patch('db.arango_db.ArangoClient')
@patch('db.arango_db.path')
def test_arangodb_setup_dev_doesnt_write_arangoimp_conf_if_existent(mock_os, mock_client):
  with patch("builtins.open", new_callable=mock_open, read_data=MOCK_CONFIG_FILE) as mock_op:
    db = ArangoDB()

  mock_os.exists.return_value = True
  
  with patch('builtins.open') as mock_op:
    file_handle = mock_op.return_value.__enter__.return_value

    db.setup_dev()

    mock_os.exists.assert_called_with('arangoimp.conf')
    file_handle.write.assert_not_called()


@patch('db.arango_db.ArangoClient')
def test_arangodb_generates_import_statements_for_nodes(mock_client):
  with patch("builtins.open", new_callable=mock_open, read_data=MOCK_CONFIG_FILE) as mock_op:
    db = ArangoDB()

    cmds = db.generate_import_statement('header-test.csv', ['data1.csv', 'data2.csv'], 'test_collection', 'node')

    import_st_1 = 'arangoimp --headers-file header-test.csv --file data1.csv --type csv --collection test_collection --create-collection --remove-attribute ":TYPE" --translate ":ID=_key" --remove-attribute "preferred_id" --remove-attribute "id" --remove-attribute ":LABEL"'
    import_st_2 = 'arangoimp --headers-file header-test.csv --file data2.csv --type csv --collection test_collection --create-collection --remove-attribute ":TYPE" --translate ":ID=_key" --remove-attribute "preferred_id" --remove-attribute "id" --remove-attribute ":LABEL"'

    assert cmds == [import_st_1, import_st_2]
  

@patch('db.arango_db.ArangoClient')
def test_arangodb_generates_import_statements_for_edges(mock_client):
  with patch("builtins.open", new_callable=mock_open, read_data=MOCK_CONFIG_FILE) as mock_op:
    db = ArangoDB()

    cmds = db.generate_import_statement('header-test.csv', ['data1.csv', 'data2.csv'], 'test_collection', 'edge')

    import_st_1 = 'arangoimp --headers-file header-test.csv --file data1.csv --type csv --collection test_collection --create-collection --remove-attribute ":TYPE" --create-collection-type edge --translate ":START_ID=_from" --translate ":END_ID=_to"'
    import_st_2 = 'arangoimp --headers-file header-test.csv --file data2.csv --type csv --collection test_collection --create-collection --remove-attribute ":TYPE" --create-collection-type edge --translate ":START_ID=_from" --translate ":END_ID=_to"'

    assert cmds == [import_st_1, import_st_2]


@patch('db.arango_db.ArangoClient')
@patch("builtins.open", new_callable=mock_open, read_data=MOCK_CONFIG_FILE)
def test_arangodb_creates_index(mock_op, mock_client):
  db = ArangoDB()

  mock_client = db.get_connection()

  db_mock = Mock()
  mock_client.db.return_value = db_mock

  collection_mock = Mock()
  db_mock.collection.return_value = collection_mock

  collection_name = 'myCollection'
  index_name = 'myIndex'
  index_type = 'persistent'
  fields = 'chr'

  db.create_index(collection_name, index_name, index_type, fields)

  db_mock.collection.assert_called_with(collection_name)
  collection_mock.add_persistent_index.assert_called_with(name=index_name, fields=fields, in_background=True)


@patch('db.arango_db.ArangoClient')
@patch("builtins.open", new_callable=mock_open, read_data=MOCK_CONFIG_FILE)
def test_arangodb_doesnt_create_index_for_unsupported_type(mock_op, mock_client):
  db = ArangoDB()

  mock_client = db.get_connection()

  db_mock = Mock()
  mock_client.db.return_value = db_mock

  collection_mock = Mock()
  db_mock.collection.return_value = collection_mock

  collection_name = 'myCollection'
  index_name = 'myIndex'
  index_type = 'TYPE_NOT_IMPLEMENTED'
  fields = 'chr'

  db.create_index(collection_name, index_name, index_type, fields)

  db_mock.collection.assert_called_with(collection_name)
  collection_mock.add_persistent_index.assert_not_called()
