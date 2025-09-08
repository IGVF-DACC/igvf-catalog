import os
import json
from typing import Optional
from jsonschema import Draft202012Validator, ValidationError
from schemas.registry import get_schema

from adapters.writer import Writer

# ENSEMBL Mapping extracted from https://www.uniprot.org/id-mapping

# Example TF motif file from HOCOMOCO (e.g. ATF1_HUMAN.H11MO.0.B.pwm), which adastra used.
# Each pwm (position weight matrix) is a N x 4 matrix, where N is the length of the TF motif.
# >ATF1_HUMAN.H11MO.0.B
# 0.13987841615191168	0.3608848685361665	-0.4517428977281205	-0.25006525443490907
# 0.3553616298110878	-0.7707228823699511	0.3663777685862727	-0.4032800768485152
# 0.338606483241983	-0.8414816866844361	0.7066714674964639	-1.975404324094267
# -2.4841943814369576	-3.324736791140142	-1.9754043240942667	1.3195988707291637
# -2.3936647653320064	-2.9606438896517475	1.328010168941795	-2.4841943814369576
# 1.3217083373824634	-2.9606438896517475	-2.5837428525823363	-2.0963708769895044
# -1.9754043240942667	1.191348924768384	-1.4888815002078464	-1.0666727869454955
# -2.2340103118057417	-2.5837428525823363	1.2450934398879747	-1.0666727869454955
# -1.1380405061628662	0.23796182230991783	-2.5837428525823363	0.8481840389725303
# 0.13987841615191168	0.6170180100710398	-0.5426512454816383	-0.8788317538331962
# 0.7561011054759478	-0.7707228823699511	-0.2914989252431338	-0.4151773801942997


class Motif:
    ALLOWED_LABELS = ['motif', 'motif_protein_link']
    SOURCE = 'HOCOMOCOv11'
    SOURCE_URL = 'hocomoco11.autosome.org/motif/'
    TF_ID_MAPPING_PATH = './samples/motifs/HOCOMOCOv11_core_annotation_HUMAN_mono.tsv'
    ENSEMBL_MAPPING = './data_loading_support_files/ensembl_to_uniprot/uniprot_to_ENSP_motifs.tsv'

    def __init__(self, filepath, label='motif', dry_run=True, writer: Optional[Writer] = None, validate=False, **kwargs):
        if label not in Motif.ALLOWED_LABELS:
            raise ValueError('Invalid label. Allowed values: ' +
                             ','.join(Motif.ALLOWED_LABELS))

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
        self.tf_ids = Motif.TF_ID_MAPPING_PATH
        self.source = Motif.SOURCE
        self.source_url = Motif.SOURCE_URL
        self.writer = writer
        self.validate = validate
        if self.validate:
            self.schema = get_schema(
                'nodes', 'motifs', self.__class__.__name__)
            self.validator = Draft202012Validator(self.schema)

    def validate_doc(self, doc):
        try:
            self.validator.validate(doc)
        except ValidationError as e:
            raise ValueError(f'Document validation failed: {e.message}')

    def loading_ensembl_uniprot_mapping(self):
        with open('./data_loading_support_files/ensembl_uniprot_protein_ids.tsv', 'r') as ensembl_uniprot_mapfile:
            for row in ensembl_uniprot_mapfile:
                self.ensembls[row[0]] = row[1]

    def load_tf_ensembl_id_mapping(self):
        ensembls = {}
        with open(Motif.ENSEMBL_MAPPING, 'r') as ensembl_tsv:
            for row in ensembl_tsv:
                row = row.strip().split('\t')
                ensembl_id = row[1].split('.')[0]
                if row[0] in ensembls:
                    ensembls[row[0]].append(ensembl_id)
                else:
                    ensembls[row[0]] = [ensembl_id]

        # e.g. key: 'ANDR_HUMAN'; value: ['ENSP00000301310.3', 'ENSP00000465619.1']
        self.tf_ensembl_id_mapping = {}
        with open(Motif.TF_ID_MAPPING_PATH, 'r') as tf_uniprot_id_mapfile:
            for row in tf_uniprot_id_mapfile:
                if row.startswith('Model'):
                    continue
                mapping = row.strip().split('\t')
                self.tf_ensembl_id_mapping[mapping[-2]] = ensembls[mapping[-1]]
                if len(self.tf_ensembl_id_mapping[mapping[-2]]) == 0:
                    import pdb
                    pdb.set_trace()

    def process_file(self):
        self.writer.open()
        for filename in os.listdir(self.filepath):
            if filename.endswith('.pwm'):
                print(filename)
                tf_name = filename.split('.')[0]
                model_name = filename.replace('.pwm', '')
                if self.label == 'motif':
                    pwm = []
                    with open(self.filepath + '/' + filename, 'r') as pwm_file:
                        next(pwm_file)
                        for line in pwm_file:
                            pwm_row = line.strip().split()
                            pwm.append([str(value)
                                        for value in pwm_row])
                    length = len(pwm)

                    _key = tf_name + '_' + self.source

                    props = {
                        '_key': _key,
                        'name': _key,
                        'tf_name': tf_name,
                        'source': self.source,
                        'source_url': self.source_url + model_name,
                        'pwm': pwm,
                        'length': length
                    }

                    if self.validate:
                        self.validate_doc(props)

                    self.writer.write(json.dumps(props))
                    self.writer.write('\n')

                elif self.label == 'motif_protein_link':
                    self.load_tf_ensembl_id_mapping()
                    tf_ensembl_ids = self.tf_ensembl_id_mapping.get(tf_name)
                    if tf_ensembl_ids is None:
                        print(
                            'TF ensembl ids unavailable, skipping motif_protein_link: ' + tf_name)
                        continue

                    for ensembl_id in tf_ensembl_ids:
                        props = {
                            '_key': tf_name + '_' + self.source + '_' + ensembl_id,
                            '_from': 'motifs/' + tf_name + '_' + self.source,
                            '_to': 'proteins/' + ensembl_id,
                            'name': 'is used by',
                            'inverse_name': 'uses',
                            'biological_process': 'ontology_terms/GO_0003677',  # DNA Binding
                            'source': self.source
                        }

                        self.writer.write(json.dumps(props))
                        self.writer.write('\n')

        self.writer.close()
