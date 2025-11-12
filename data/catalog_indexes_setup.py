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
        if index == 'inverted':
            continue  # it's already handled by aliases

        sparse = False
        fields_list = indexes[index]['fields']
        if index == 'zkd_sparse':
            index = 'zkd'
            sparse = True

        elif index == 'persistent_sparse':
            index = 'persistent'
            sparse = True

        for fields in fields_list:
            fields = [f.strip() for f in fields.split(',')]
            index_name = 'idx_{}_{}'.format(index, '_'.join(fields))
            ArangoDB().create_index(
                collection,
                index,
                fields,
                sparse=sparse,
                name=index_name
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


def create_inverted_index_and_aliases(indexes, collection):
    if 'inverted' in indexes:
        fields_list = indexes['inverted']['fields']
        analyzers = indexes['inverted']['analyzers']
        for analyzer in analyzers:
            index_name = '{}_{}_inverted_search'.format(collection, analyzer)
            view_name = '{}_{}_inverted_search_alias'.format(
                collection, analyzer)
            create_aliases_arango(
                fields_list, index_name, analyzer, view_name)


for collection in collections_to_index:
    indexes = index_config[collection]
    print(('{} - creating...').format(collection))

    try:
        create_indexes(indexes, collection)
        create_inverted_index_and_aliases(indexes, collection)
    except Exception as error:
        print('{} - index creation failed. {}'.format(collection, error))
