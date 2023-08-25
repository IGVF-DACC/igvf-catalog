import json
import os
import requests
from collections import defaultdict

from db.arango_db import ArangoDB
from adapters import Adapter

## description (tranposed matrix...) ##


class DepMap(Adapter):
    SOURCE = 'DepMap'
    SOURCE_URL = 'https://depmap.org/portal/'
    GENE_ID_MAPPING_PATH = './data_loading_support_files/DepMap_gene_id_mapping.tsv'
    CELL_ONTOLOGY_ID_MAPPING_PATH = './data_loading_support_files/DepMap_model.csv'

    CUTOFF = 0.5  # only load genes with dependency scores greater or equal to 0.5 for each cell
    SKIP_BIOCYPHER = True
    OUTPUT_PATH = './parsed-data'

    def __init__(self, filepath, dry_run=True):
        self.filepath = filepath
        self.dry_run = dry_run
        self.dataset = 'gene_term'
        self.type = 'edge'

        self.output_filepath = '{}/{}.json'.format(
            DepMap.OUTPUT_PATH,
            self.dataset
        )

        super(DepMap, self).__init__()

    def process_file(self):
        parsed_data_file = open(self.output_filepath, 'w')
        self.load_cell_ontology_id_mapping()
        self.load_gene_id_mapping()

        with open(self.filepath, 'r') as depmap_file:
            # read model ids on the first row
            model_ids = next(depmap_file).strip().split(',')[1:]
            # record the column index of each model ID (start from 2nd column)
            model_ids_column_mapping = {}
            for column_index, model_id in enumerate(model_ids):
                model_ids_column_mapping[column_index] = model_id
                # check CVCL id mapping for all models once first
                cell_ontology_id = self.cell_ontology_id_mapping[model_id]['cell_ontology_id']
                if not cell_ontology_id:
                    print('Cell ontology unavailable for model id ' + model_id)

            for line in depmap_file:
                gene, *values = line.strip().split(',')
                gene_symbol = gene.split(' ')[0]
                gene_id = self.gene_id_mapping.get(gene_symbol)
                if gene_id is None:
                    print('no gene id mapping for ' + gene)
                    continue

                for value_index, value in enumerate(values):
                    if not value:  # skip NA values
                        continue
                    # only load gene-cell pairs with values >= cutoff (0.5)
                    elif float(value) >= DepMap.CUTOFF:
                        gene_model_id = model_ids_column_mapping[value_index]
                        cell_ontology_id = self.cell_ontology_id_mapping[gene_model_id]['cell_ontology_id']
                        if not cell_ontology_id:  # no CVCL id provided for this model
                            continue

                        _key = gene_id + '_' + cell_ontology_id
                        _from = 'genes/' + gene_id
                        _to = 'ontology_terms/' + cell_ontology_id
                        props = {
                            '_key': _key,
                            '_from': _from,
                            '_to': _to,

                            'biology_context': self.cell_ontology_id_mapping[gene_model_id]['biology_context'],
                            'model_id': gene_model_id,
                            'model_type': self.cell_ontology_id_mapping[gene_model_id]['model_type'],
                            # oncotree code can be mapped to NCIT ids
                            'oncotree_code': self.cell_ontology_id_mapping[gene_model_id]['oncotree_code'],
                            'gene_dependency': float(value),
                            'source': DepMap.SOURCE,
                            'source_url': DepMap.SOURCE_URL
                        }
                        json.dump(props, parsed_data_file)
                        parsed_data_file.write('\n')

        parsed_data_file.close()
        self.save_to_arango()

    def load_cell_ontology_id_mapping(self):
        # key: DepMap Model ID; value: ontology ids (i.e. CVCL ids) and properties of each cell
        self.cell_ontology_id_mapping = defaultdict(dict)
        column_index_mapping = {
            'biology_context': 2,
            'cell_ontology_id': 7,
            'model_type': 8,
            'oncotree_code': 26
        }
        with open(DepMap.CELL_ONTOLOGY_ID_MAPPING_PATH, 'r') as cell_ontology_id_mapping_file:
            next(cell_ontology_id_mapping_file)
            for line in cell_ontology_id_mapping_file:
                cell_ontology_row = line.strip().split(',')
                model_id = cell_ontology_row[0]
                for prop, column_index in column_index_mapping.items():
                    self.cell_ontology_id_mapping[model_id][prop] = cell_ontology_row[column_index]

    def load_gene_id_mapping(self):
        self.gene_id_mapping = {}  # key: gene symbol; value: gene ensembl id
        with open(DepMap.GENE_ID_MAPPING_PATH, 'r') as gene_id_mapping_file:
            for line in gene_id_mapping_file:
                gene_symbol, gene_id = line.strip().split('\t')
                self.gene_id_mapping[gene_symbol] = gene_id

    def save_to_arango(self):
        if self.dry_run:
            print(self.arangodb()[0])
        else:
            os.system(self.arangodb()[0])

    def arangodb(self):
        return ArangoDB().generate_json_import_statement(self.output_filepath, self.collection, type=self.type)
