import json
import clickhouse_driver
from schemas.registry import get_schema

SCHEMA_REGISTRY_PATH = './schemas/registry.json'
DB_CONFIG_PATH = '../config/development.json'
RESERVED_WORDS = ['format']


class Clickhouse:
    __connection = None
    __schema = None

    def __init__(self, reconnect=False):
        config = json.load(open(DB_CONFIG_PATH))['clickhouse']
        self.db_name = config['dbName']
        self.host = config['host']
        self.port = config['port']

        if reconnect or Clickhouse.__connection is None:
            Clickhouse.__connection = clickhouse_driver.Client(
                host=self.host,
                port=self.port,
                database=self.db_name,
                user=config['auth']['username'],
                password=config['auth']['password']
            )

        if Clickhouse.__schema is None:
            Clickhouse.__schema = Clickhouse.load_schema()

    @staticmethod
    def get_sql_properties(properties):
        sql_properties = {}
        for key, value in properties.items():
            if key == '_from' or key == '_to':
                continue
            property_type = value['type']
            sql_properties[key] = property_type
        return sql_properties

    @staticmethod
    def load_schema():
        clickhouse_schema = {}
        with open(SCHEMA_REGISTRY_PATH, 'r') as registry:
            registry_data = json.load(registry)
            for table_name in registry_data['nodes']:
                # Iterate over all adapters for this collection
                for adapter_name in registry_data['nodes'][table_name]:
                    schema = get_schema('nodes', table_name, adapter_name)
                    properties = Clickhouse.get_sql_properties(
                        schema['properties'])
                    if table_name in clickhouse_schema:
                        clickhouse_schema[table_name]['properties'].update(
                            properties)
                    else:
                        clickhouse_schema[table_name] = {
                            'properties': properties}
            for table_name in registry_data['edges']:
                # Iterate over all adapters for this collection
                for adapter_name in registry_data['edges'][table_name]:
                    schema = get_schema('edges', table_name, adapter_name)
                    from_nodes = schema['properties']['_from']['collections']
                    to_nodes = schema['properties']['_to']['collections']
                    properties = Clickhouse.get_sql_properties(
                        schema['properties'])
                    if table_name in clickhouse_schema:
                        clickhouse_schema[table_name]['properties'].update(
                            properties)
                        clickhouse_schema[table_name]['relationship']['from'].update(
                            from_nodes)
                        clickhouse_schema[table_name]['relationship']['to'].update(
                            to_nodes)
                    else:
                        clickhouse_schema[table_name] = {
                            'properties': properties,
                            'relationship': {
                                'from': from_nodes,
                                'to': to_nodes
                            }
                        }
                # After processing all adapters for this edge collection, normalize the relationship IDs
                froms = set(
                    clickhouse_schema[table_name]['relationship']['from'])
                tos = set(clickhouse_schema[table_name]['relationship']['to'])

                clickhouse_schema[table_name]['relationship']['from'] = [
                    f + '_id' if (f not in tos) else f + '_1_id' for f in froms]
                clickhouse_schema[table_name]['relationship']['to'] = [
                    f + '_id' if (f not in froms) else f + '_2_id' for f in tos]

        return clickhouse_schema

    def get_connection():
        return Clickhouse.__connection

    def get_schema():
        return Clickhouse.__schema

    def process_json_line(self, json_line, properties):
        data = json.loads(json_line)
        processed_data = []

        for key in properties:
            # biocypher heritage for number cases
            if key not in data:
                key += ':long'

            # certain properties might not exist in all records, setting them to None
            value = data.get(key)

            # clickhouse discourages the use of NULL, using '' instead
            if value == None or value == []:
                value = ''
            processed_data.append(value)

        processed_data.append(data['_key'])
        if data.get('_from') is not None and data.get('_to') is not None:
            # removing collection prefix from _from and _to. E.g. genes/ENSG00000148584 => ENSG00000148584
            processed_data.append(data['_from'].split('/')[-1])
            processed_data.append(data['_to'].split('/')[-1])

        return processed_data

    def import_jsonl_file(self, original_jsonl_filepath, collection):
        client = Clickhouse.__connection

        schema = Clickhouse.get_schema().get(collection)
        if schema is None:
            raise ValueError('Collection not defined in schema_config.yaml')

        properties = schema.get('properties')

        sql_properties = ','.join(properties) + ',id'
        if schema.get('relationship'):
            sql_properties += ',' + \
                schema['relationship'].get['from'].join(',')
            sql_properties += ',' + schema['relationship'].get['to'].join(',')

        print('Loading data...')

        bulk = []
        for json_line in open(original_jsonl_filepath, 'r'):
            bulk.append(tuple(self.process_json_line(json_line, properties)))

            if len(bulk) == 10000:
                try:
                    client.execute('INSERT INTO ' + collection +
                                   ' (' + sql_properties + ') VALUES', bulk)
                    bulk.clear()
                except:
                    # every collection has particular edge cases
                    # this is needed until we have all collections loaded
                    import pdb
                    pdb.set_trace()

        if len(bulk) > 0:
            client.execute('INSERT INTO ' + collection +
                           ' (' + sql_properties + ') VALUES', bulk)

    def generate_json_import_statement(self, processed_filepath, collection):
        return f'clickhouse-client --host {self.host} --port {self.port} --database {self.db_name} --query="INSERT INTO {collection} FORMAT JSONEachRow" < {processed_filepath}'

    def generate_sql_schema(self, output_filepath):
        schema = Clickhouse.get_schema()

        with open(output_filepath, 'w') as clickhouse_schema:
            clickhouse_schema.write(
                '-- autogenerated from schema_config.yaml\n\n')
            clickhouse_schema.write(
                'SET allow_experimental_json_type = 1;\n\n')
            clickhouse_schema.write(f'USE {self.db_name};\n\n')

            for table in schema:
                sql_table = []
                properties = schema[table]['properties']
                for prop in properties.keys():
                    clickhouse_type = properties[prop]

                    if clickhouse_type == 'string':
                        clickhouse_type = 'String'
                    if clickhouse_type in ['integer', 'number']:
                        clickhouse_type = 'Float64'
                    elif clickhouse_type == 'array':
                        clickhouse_type = 'Array(String)'
                    elif clickhouse_type == 'object':
                        clickhouse_type = 'String'

                    if prop in RESERVED_WORDS:
                        prop += '_'

                    sql_table.append(prop + ' ' + clickhouse_type)

                sql_table.append('id String PRIMARY KEY')
                if schema[table].get('relationship'):
                    for f in schema[table]['relationship']['from'] + schema[table]['relationship']['to']:
                        sql_table.append(f + ' String')

                clickhouse_schema.write(
                    '\nCREATE TABLE IF NOT EXISTS ' + table + ' (\n\t')
                clickhouse_schema.write(',\n\t'.join(sql_table))
                clickhouse_schema.write('\n);\n')


if __name__ == '__main__':
    Clickhouse().generate_sql_schema('./db/schema/clickhouse_schema.sql')
