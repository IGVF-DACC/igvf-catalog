import csv
import json
import os

from adapters import Adapter
from db.arango_db import ArangoDB

# Example motif file from SEMpl M00778.sem
# AHR	A	C	G	T
# 1	-0.0981338	-0.0827793	0.0100979	-0.173785
# 2	-0.284773	-0.333357	-0.24361	0.0154123
# 3	-0.312271	0.025403	-0.288961	-0.152907
# 4	-0.125256	-0.494299	-0.00116848	-0.260581
# 5	-0.53657	0	-0.6353	-0.518209
# 6	-0.451598	-0.585824	0	-0.494461
# 7	-0.0538789	-0.113863	-0.387188	0.00560577
# 8	-0.0698494	-0.172925	0.0229245	-0.182021
# 9	0.0130119	-0.300118	-0.323497	-0.311547
# 10	-0.143318	0.00440271	-0.168156	-0.0833881
# 11	-0.0420202	-0.0158168	0.00441693	-0.00877582

# Example mapping file on TFs
# Transcription Factor Name	ENSEMBL ID	ComplexAc	Uniprot ID	PWM	SEM	Cell Type	ENCODE TF ChIP-seq dataset	ENCODE DNase-seq dataset
# AHR	ENSG00000106546     P35869  M00778.pwm	M00778.sem	HepG2	https://www.encodeproject.org/files/ENCFF242PUG/	http://hgdownload.soe.ucsc.edu/goldenPath/hg19/encodeDCC/wgEncodeOpenChromDnase/wgEncodeOpenChromDnaseHepg2Pk.narrowPeak.gz


class SEMMotif(Adapter):
    ALLOWED_LABELS = ['motif', 'motif_protein_link']
    SOURCE = 'SEMpl'
    SOURCE_URL = 'https://github.com/Boyle-Lab/SEMpl'
    TF_PROTEIN_MAPPING_PATH = './data_loading_support_files/SEMVAR_provenance_uniprot_ids.csv'

    OUTPUT_PATH = './parsed-data'

    def __init__(self, filepath, label='motif', dry_run=True):
        if label not in SEMMotif.ALLOWED_LABELS:
            raise ValueError('Ivalid label. Allowed values: ' +
                             ','.join(SEMMotif.ALLOWED_LABELS))

        self.filepath = filepath
        self.label = label
        self.dataset = label
        if label == 'motif':
            self.type = 'node'
            self.collection = 'motifs'
        else:
            self.type = 'edge'
            self.collection = 'motifs_proteins'

        self.dry_run = dry_run
        self.output_filepath = '{}/{}_{}.json'.format(
            self.OUTPUT_PATH,
            self.SOURCE,
            self.dataset
        )

        super(SEMMotif, self).__init__()

    def load_tf_id_mapping(self):
        self.tf_id_mapping = {}
        with open(SEMMotif.TF_PROTEIN_MAPPING_PATH, 'r') as map_file:
            map_csv = csv.reader(map_file)
            for row in map_csv:
                if row[2]:  # this is a complex
                    self.tf_id_mapping[row[0]] = 'complexes/' + row[2]
                else:
                    self.tf_id_mapping[row[0]] = 'proteins/' + row[3]

    def process_file(self):
        parsed_data_file = open(self.output_filepath, 'w')
        for filename in os.listdir(self.filepath):
            if filename.endswith('.sem'):
                motif_id = filename.split('.')[0]  # e.g. M00778
                if self.label == 'motif':
                    pwm = []
                    with open(self.filepath + '/' + filename, 'r') as sem_file:
                        # read tf name from the first line of sem file
                        tf_name = next(sem_file).strip().split()[0]
                        for row in sem_file:
                            sem_row = row.strip().split()[1:]
                            pwm.append([str(value) for value in sem_row])

                    length = len(pwm)
                    _key = tf_name + '_' + SEMMotif.SOURCE
                    props = {
                        '_key': _key,
                        'name': _key,
                        'tf_name': tf_name,
                        'source': SEMMotif.SOURCE,
                        'source_url': SEMMotif.SOURCE_URL,
                        'pwm': pwm,
                        'length': length
                    }
                elif self.label == 'motif_protein_link':
                    self.load_tf_id_mapping()
                    with open(self.filepath + '/' + filename, 'r') as sem_file:
                        tf_name = next(sem_file).strip().split()[0]

                    tf_id = self.tf_id_mapping.get(tf_name)
                    if tf_id is None:
                        print(
                            'TF id unavailable, skipping motif_protein_link: ' + tf_name)
                        continue

                    _key = motif_id + '_' + SEMMotif.SOURCE + \
                        '_' + tf_id.split('/')[-1]
                    _from = 'motifs/' + tf_name + '_' + SEMMotif.SOURCE
                    _to = tf_id  # nodes in either proteins or complexes -> should the schema be updated?

                    props = {
                        '_key': _key,
                        '_from': _from,
                        '_to': _to,
                        'name': 'is used by',
                        'inverse_name': 'uses',
                        'biological_process': 'ontology_terms/GO_0003677',  # DNA Binding
                        'source': SEMMotif.SOURCE,
                        'source_url': SEMMotif.SOURCE_URL
                    }

                json.dump(props, parsed_data_file)
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
