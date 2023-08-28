import json
import os
from collections import defaultdict

from db.arango_db import ArangoDB
from adapters import Adapter

# CRISPRGeneDependency.csv is downloaded from DepMap portal: https://depmap.org/portal/download/all/ in DepMap Public 23Q2 Primary Files set.
# The original matrix in file is organized as ModelID (1,095 rows) X Gene (17,931 coloumns).
# The transpose of the original matrix is loaded here for easier processing.

# Example of part of the loading matrix:
# Gene,ACH-000001,ACH-000004,ACH-000005,ACH-000007,ACH-000009,ACH-000011,ACH-000012,ACH-000013,ACH-000014
# A1BG (1),0.0553211648540664,0.0234180490346237,0.0595523208289766,0.0238795185094775,0.0276524140275033,0.011752429730298,0.0543502827694051,0.0124079166941024,0.040318101157517
# A1CF (29974),0.01403856306881,0.0487237248460492,0.0254784832528157,0.0350823083989964,0.0748604776571315,0.0185146565164343,0.0124800836750166,0.0565492355005334,0.060836485655342
# A2M (2),0.014083962468692,0.0580835979659146,0.009988767666177,0.0065561956482438,0.0110209379651418,0.0060609112443749,0.0072958232853707,0.0179317372336054,0.0065760777739698
# A2ML1 (144568),0.0338284534541587,0.0194828713741789,0.0087747320511599,0.0043219200079226,0.0091529955757067,0.0012808358556768,0.0047749277968025,0.0060950766332704,0.0044051485846711
# A3GALT2 (127550),0.0495109597139512,0.0497933372469599,0.0993215225089184,0.0222002915981626,0.0216318159720975,0.0691636263860943,0.0171814961410507,0.0878640626935068,0.0289686576103241
# A4GALT (53947),0.0049549043798291,0.0644720329570723,0.0995723644759633,0.0171211497280876,0.0677580998736281,0.1066244413858098,0.0842259302575638,0.0347167502889501,0.0467279313668812
# A4GNT (51146),0.0269933824143704,0.0017749187371471,0.0075438544746256,0.0096048506255836,0.0135592402503593,0.0101073432171285,0.0021596303931416,0.0229722081510304,0.0652710662490125
# AAAS (8086),0.131006482326207,0.0712890616055635,0.0496013615174664,0.1493775190934886,0.2167959119007355,0.0509210708384526,0.1354858251710864,0.1042089421935019,0.0645025243815082
# AACS (65985),0.0031017110004655,0.0037316464915786,0.0475549666425148,0.052872923167593,0.0136603726345243,0.0079949689832072,0.0193872501805128,0.0305006545923165,0.0792603149045092

# Other files needed for loading:
# DepMap_model.csv is also downloaded from DepMap portal: https://depmap.org/portal/download/all/ in DepMap Public 23Q2 Primary Files set (Model.csv).
# DepMap_gene_id_mapping.tsv is premapped file from gene symbol to gene ensembl id, queried from IGVF catalog gene collection.


class DepMap(Adapter):
    SOURCE = 'DepMap'
    SOURCE_URL = 'https://depmap.org/portal/'
    GENE_ID_MAPPING_PATH = './data_loading_support_files/DepMap_gene_id_mapping.tsv'
    CELL_ONTOLOGY_ID_MAPPING_PATH = './data_loading_support_files/DepMap_model.csv'

    CUTOFF = 0.5  # only load genes with dependency scores greater or equal to 0.5 for each cell

    def __init__(self, filepath, type, label):
        self.filepath = filepath
        self.dataset = label
        self.label = label
        self.type = type

        super(DepMap, self).__init__()

    def process_file(self):
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

                        _id = gene_id + '_' + cell_ontology_id
                        _source = 'genes/' + gene_id
                        _target = 'ontology_terms/' + cell_ontology_id

                        _props = {
                            'biology_context': self.cell_ontology_id_mapping[gene_model_id]['biology_context'],
                            'model_id': gene_model_id,
                            'model_type': self.cell_ontology_id_mapping[gene_model_id]['model_type'],
                            # oncotree code can be mapped to NCIT ids
                            'oncotree_code': self.cell_ontology_id_mapping[gene_model_id]['oncotree_code'],
                            'gene_dependency': float(value),
                            'source': DepMap.SOURCE,
                            'source_url': DepMap.SOURCE_URL
                        }

                        yield(_id, _source, _target, self.label, _props)

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
