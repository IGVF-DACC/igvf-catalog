import argparse
import yaml

from db.arango_db import ArangoDB

CONFIG_PATH = './index-config.yaml'
index_config = yaml.safe_load(open(CONFIG_PATH, 'r'))
collections_in_config = list(index_config.keys())

parser = argparse.ArgumentParser(
    prog='IGVF Catalog DB Index Setup',
    description='Creates indexes in the development.json IGVF Catalog ArangoDB collections'
)

parser.add_argument('-c', '--collection', nargs='*',
                    help='Creates collection indexes in the development.json DB', choices=collections_in_config)

args = parser.parse_args()
collections_to_index = args.collection or collections_in_config


def create_indexes(indexes, collection):
    for index in indexes:
        if indexes[index]['type'] == 'inverted':
            continue  # it's already handled by aliases

        fields_list = indexes[index]['fields']

        for fields in fields_list:
            fields = [f.strip() for f in fields.split(',')]
            ArangoDB().create_index(
                collection,
                indexes[index]['type'],
                fields
            )


def create_aliases_arango(fields_list, index_name, analyzer, view_name):
    fields = [f.strip() for f in fields_list.split(',')]

    ArangoDB().create_index(
        collection,
        'inverted',
        fields,
        name=index_name,
        opts={'analyzer': analyzer}
    )

    ArangoDB().create_view(
        view_name,
        'search-alias',
        collection,
        index_name
    )


def create_aliases(indexes, collection):
    if indexes.get('fuzzy_text_search'):
        fields_list = indexes['fuzzy_text_search']
        index_name = '{}_fuzzy_search'.format(collection)
        view_name = '{}_fuzzy_search_alias'.format(collection)
        analyzer = 'text_en_no_stem'
        create_aliases_arango(
            fields_list, index_name, analyzer, view_name)

    if indexes.get('delimiter_text_search'):
        fields_list = indexes['delimiter_text_search']
        index_name = '{}_delimiter_search'.format(collection)
        view_name = '{}_delimiter_search_alias'.format(collection)
        analyzer = 'text_delimiter'
        create_aliases_arango(
            fields_list, index_name, analyzer, view_name)


for collection in collections_to_index:
    indexes = index_config[collection]
    print(('{} - creating...').format(collection))

    try:
        create_indexes(indexes, collection)
        create_aliases(indexes, collection)
    except Exception as error:
        print('{} - index creation failed. {}'.format(collection, error))
