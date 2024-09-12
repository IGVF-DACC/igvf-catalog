import csv
import json
import os

from adapters import Adapter
from db.arango_db import ArangoDB
from adapters.helpers import build_variant_id

# Example prediction file from SEMpl SEM_annot_example_AP-1.txt
# #FileType=Node:Variant
# #Contact=Rintsen Sherpa (rintsen@umich.edu), Alan Boyle (apboyle@umich.edu)
# #Genome=GRCh38
# #Description=Y2AVE variants annotated with effect on AP-1 binding at variant positions. Uses SNP Effect Matrices from https://doi.org/10.1093/bioinformatics/btz612
# #Model=SEMpl
# #SEM_file=M00172.sem
# #TF=AP-1
# #Baseline=-1.845151
# #spdi   chrom   start   pos     ref     alt     kmer_coord      ref_score       alt_score       relative_binding_affinity       effect_on_binding
# NC_000001.11:618820:T:C chr1    618820  618821  T       C       .       0       0       0       no_binding
# NC_000001.11:618876:G:A chr1    618876  618877  G       A       chr1:618876-618887      0.366594988777617  0.2759089134631226      0.7526259821039011      binding_ablated
# NC_000001.11:1147778:G:A        chr1    1147778 1147779 G       A       chr1:1147778-1147789    0.8089123149698865      0.6174918626494441      0.7633606896841861      binding_decreased

# Only load positive variants with significant effects on TF binding status (based on the last column)


class SEMPred(Adapter):
    ALLOWED_LABELS = ['sem_predicted_asb']
    SOURCE = 'SEMpl'
    SOURCE_URL = 'https://github.com/Boyle-Lab/SEMpl'
    TF_PROTEIN_MAPPING_PATH = './data_loading_support_files/SEMVAR_provenance_uniprot_ids.csv'
    BINDING_EFFECT_LIST = ['binding_ablated', 'binding_decreased',
                           'binding_created', 'binding_increased']  # ignore negative cases

    OUTPUT_PATH = './parsed-data'

    def __init__(self, filepath, label='sem_predicted_asb', dry_run=True):
        if label not in SEMPred.ALLOWED_LABELS:
            raise ValueError('Ivalid label. Allowed values: ' +
                             ','.join(SEMPred.ALLOWED_LABELS))

        self.filepath = filepath
        self.label = label
        self.dataset = label
        self.type = 'edge'
        self.dry_run = dry_run
        self.output_filepath = '{}/{}.json'.format(
            self.OUTPUT_PATH,
            self.dataset
        )
        super().__init__()

    def load_tf_id_mapping(self):
        self.tf_id_mapping = {}
        with open(SEMPred.TF_PROTEIN_MAPPING_PATH, 'r') as map_file:
            map_csv = csv.reader(map_file)
            for row in map_csv:
                if row[2]:  # this is a complex
                    # todo: check complex name;
                    self.tf_id_mapping[row[0]] = 'complexes/' + row[2]
                else:
                    self.tf_id_mapping[row[0]] = 'proteins/' + row[3]

    def process_file(self):
        parsed_data_file = open(self.output_filepath, 'w')
        self.load_tf_id_mapping()
        for filename in os.listdir(self.filepath):
            if filename.endswith('.tsv'):
                tf_name = filename.split('.')[0].split('_')[-1]
                tf_id = self.tf_id_mapping.get(tf_name)  # protein or complex
                with open(self.filepath + '/' + filename, 'r') as sem_file:
                    sem_csv = csv.reader(sem_file, delimiter='\t')
                    for row in sem_file:
                        if row.startswith('#'):
                            continue

                        if row[-1] in SEMPred.BINDING_EFFECT_LIST:
                            chr = row[1]
                            pos = row[3]  # 1-based coordinate
                            ref = row[4]
                            alt = row[5]

                            variant_id = build_variant_id(
                                chr, pos, ref, alt, 'GRCh38')

                            _key = variant_id + '_' + \
                                tf_id.split('/')[-1] + '_' + SEMPred.SOURCE
                            _from = 'variants/' + variant_id
                            _to = 'proteins/' + tf_id

                            _props = {
                                '_key': _key,
                                '_from': _from,
                                '_to': _to,
                                'label': 'predicted allele specific binding',
                                'motif': 'motifs/' + tf_name + '_' + SEMPred.SOURCE,
                                'kmer_chr': row[6].split(':')[0],
                                'kmer_start': int(row[6].split(':')[-1].split('-')[0]),
                                'kmer_end': int(row[6].split(':')[-1].split('-')[1]),
                                'ref_score': float(row[7]),
                                'alt_score': float(row[8]),
                                'relative_binding_affinity': float(row[9]),
                                'effect_on_binding': row[-1],
                                'name': 'modulates binding of',
                                'inverse_name': 'binding modulated by',
                                'biological_process': 'ontology_terms/GO_0051101'
                            }

                            json.dump(_props, parsed_data_file)
                            parsed_data_file.write('\n')

        parsed_data_file.close()
        self.save_to_arango()

    def save_to_arango(self):
        if self.dry_run:
            print(self.arangodb()[0])
        else:
            os.system(self.arangodb()[0])

    def arangodb(self):
        return ArangoDB().generate_json_import_statement(self.output_filepath, self.collection, type=self.type)
