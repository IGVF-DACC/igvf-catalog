import csv
import os
import json
import hashlib
import obonet
import pickle
from adapters import Adapter
from db.arango_db import ArangoDB

# Example lines in merged_PPI.UniProt.csv (and merged_PPI_mouse.UniProt.csv for mouse):
# (Only loading lines with 'genetic interference' in Detection Method column, the other lines are loaded in ProteinsInteraction Adapter)
# Protein ID 1,Protein ID 2,PMID,Detection Method,Detection Method (PSI-MI),Interaction Type,Interaction Type (PSI-MI),Confidence Value (biogrid),Confidence Value (intact),Source
# P82675,Q8WVC0,"[30033366, 30033366]",genetic interference,MI:0254,sensu biogrid,MI:2371; MI:2375,5.400625349,,BioGRID

# The Interaction Type column doesn't have the correct full term name
# We need to look up the full term name from ontology file psi-mi.obo with MI code in Interaction Type (PSI-MI) column
# psi-mi.obo is downloaded from https://github.com/HUPO-PSI/psi-mi-CV/blob/master/psi-mi.obo


class GeneGeneBiogrid(Adapter):

    INTERACTION_MI_CODE_PATH = './data_loading_support_files/Biogrid_gene_gene/psi-mi.obo'
    OUTPUT_PATH = './parsed-data'

    def __init__(self, filepath, label, dry_run=True):
        self.filepath = filepath
        self.dataset = label
        self.label = label
        self.dry_run = dry_run
        self.type = 'edge'

        if 'mouse' in self.filepath.split('/')[-1]:
            self.gene_collection = 'mm_genes'
            self.protein_to_gene_mapping_path = './data_loading_support_files/Biogrid_gene_gene/biogrid_protein_mapping_mouse.pkl'
        else:
            self.gene_collection = 'genes'
            self.protein_to_gene_mapping_path = './data_loading_support_files/Biogrid_gene_gene/biogrid_protein_mapping.pkl'

        self.output_filepath = '{}/{}.json'.format(
            GeneGeneBiogrid.OUTPUT_PATH,
            self.dataset,
        )

        super(GeneGeneBiogrid, self).__init__()

    def process_file(self):
        parsed_data_file = open(self.output_filepath, 'w')
        print('Loading MI code mappings')
        self.load_MI_code_mapping()

        print('Loading protein to gene mappings')
        self.load_protein_gene_mapping()

        with open(self.filepath, 'r') as interaction_file:
            interaction_csv = csv.reader(interaction_file)
            next(interaction_csv)
            for row in interaction_csv:
                # only load rows with detection method = 'genetic interference'
                if row[3] != 'genetic interference':
                    continue

                pmid_url = 'http://pubmed.ncbi.nlm.nih.gov/'
                pmids = [pmid.replace("'", '') for pmid in row[2].replace(
                    '[', '').replace(']', '').split(', ')]

                # look up the full name of MI code in column 7 from obo file, instead of loading from column 6
                interaction_type_code = row[6].split('; ')
                interaction_type = [self.MI_code_mapping.get(
                    code) for code in interaction_type_code]

                # there are some cases where one protein -> multiple genes
                genes_1 = self.protein_gene_mapping.get(row[0])
                genes_2 = self.protein_gene_mapping.get(row[1])
                if genes_1 is None or genes_2 is None:
                    continue

                if row[-1] != 'BioGRID':  # ignore gene-gene pairs from IntAct
                    continue

                for gene_1 in genes_1:
                    for gene_2 in genes_2:
                        # load each combination of gene pairs + pmids as individual edges
                        # some pairs have a long list of pmids
                        _key = hashlib.sha256('_'.join(
                            [gene_1, gene_2] + pmids).encode()).hexdigest()

                        props = {
                            '_key': _key,
                            '_from': self.gene_collection + '/' + gene_1,
                            '_to': self.gene_collection + '/' + gene_2,

                            'detection_method': row[3],
                            'detection_method_code': row[4],
                            'interaction_type': interaction_type,
                            'interaction_type_code': interaction_type_code,
                            'confidence_value_biogrid:long': float(row[7]) if row[7] else None,
                            'confidence_value_intact:long': float(row[-2]) if row[-2] else None,
                            # should be BioGRID for all edges loaded
                            'source': row[-1],
                            'pmids': [pmid_url + pmid for pmid in pmids],
                            # assign a fake value here to get around with the indexing issue on logit_score from gene-gene coexpressdb,
                            'z_score:long': 0,
                            'name': 'interacts with',
                            'inverse_name': 'interacts with',
                            'molecular_function': 'ontology_terms/GO_0005515',
                        }
                        json.dump(props, parsed_data_file)
                        parsed_data_file.write('\n')

        parsed_data_file.close()
        self.save_to_arango()

    def load_MI_code_mapping(self):
        # get mapping for MI code -> name from obo file (e.g. MI:2370 -> synthetic lethality (sensu BioGRID))
        self.MI_code_mapping = {}
        graph = obonet.read_obo(GeneGeneBiogrid.INTERACTION_MI_CODE_PATH)
        for node in graph.nodes():
            self.MI_code_mapping[node] = graph.nodes[node]['name']

    def load_protein_gene_mapping(self):
        # get mapping from protein uniprot id to gene id
        self.protein_gene_mapping = {}
        with open(self.protein_to_gene_mapping_path, 'rb') as mapfile:
            self.protein_gene_mapping = pickle.load(mapfile)

    def save_to_arango(self):
        if self.dry_run:
            print(self.arangodb()[0])
        else:
            os.system(self.arangodb()[0])

    def arangodb(self):
        return ArangoDB().generate_json_import_statement(self.output_filepath, self.collection, type=self.type)
