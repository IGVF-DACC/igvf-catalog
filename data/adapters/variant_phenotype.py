import csv
import json
import pickle
from typing import Optional

from adapters.writer import Writer
# Example line from file from Supplementary_Table_S3_cV2F_scores.txt
#CHR	BP	SNP SPDI	CM	cV2F	LIVER.cV2F	BLOOD.cV2F	BRAIN.cV2F	GM12878.cV2F	K562.cV2F	HepG2.cV2F
#1	11008	rs575272151 X	0	0.259558995068073	0.309695184230804	0.458494558930397	0.501427552103996	0.329434263706207	0.458916559815407	0.448281314969063
#1	11012	rs544419019 Y	0	0.3444201618433	0.495591408014298	0.614960989356041	0.72971625328064	0.576766195893288	0.645283776521683	0.626273554563522
#1	13110	rs540538026 Z	0	0.36915679872036	0.250546787679195	0.379640486836433	0.317768284678459	0.358425730466843	0.43017390370369	0.299737627804279


class VariantPhenotypeAdapter:
    ALLOWED_LABELS = ['variant_phenotype']
    SOURCE = 'V2F'
    SOURCE_URL = 'https://data.igvf.org/analysis-sets/IGVFDS0000XXXX/'
    CODING_VARIANTS_MAPPING_PATH = './file_path/SPDI_TO_VARIANT_ID.txt'
    PHENOTYPE_TERM = 'X'  # variant function ontology_terms/PATO_0001509

    def __init__(self, filepath, label='variant_phenotype', writer: Optional[Writer] = None, **kwargs):
        if label not in VariantPhenotypeAdapter.ALLOWED_LABELS:
            raise ValueError('Invalid label. Allowed values: ' +
                             ','.join(VariantPhenotypeAdapter.ALLOWED_LABELS))

        self.filepath = filepath
        self.writer = writer

    def process_file(self):
        self.writer.open()
        self.load_variant_id()

        with open(self.filepath, 'r') as cV2F_file:
            cV2F_csv = csv.reader(cV2F_file)
            next(cV2F_csv)
            for row in cV2F_csv:
                if row[3] in self.load_variant_id:
                    for _id in self.load_variant_id[row[3]]:
                        edge_key = _id + '_' + VariantPhenotypeAdapter.PHENOTYPE_TERM
                        _props = {
                            '_key': edge_key,
                            '_from': 'variants/' + _id,
                            '_to': 'ontology_terms/' + VariantPhenotypeAdapter.PHENOTYPE_TERM,
                            'linkage_disequilibrium': float(row[4]),
                            'general_context_score': float(row[5]),
                            'liver_context_score': float(row[6]),
                            'blood_context_score': float(row[7]),
                            'brain_context_score': float(row[8]),
                            'GM12878_context_score': float(row[9]),
                            'K562_context_score': float(row[10]),
                            'HepG2_context_score': float(row[11]),
                            'source': VariantPhenotypeAdapter.SOURCE,
                            'source_url': VariantPhenotypeAdapter.SOURCE_URL
                        }

                        self.writer.write(json.dumps(_props))
                        self.writer.write('\n')

        self.writer.close()

    def load_variant_id(self):
        self.variant_id = {}
        with open(VariantPhenotypeAdapter.CODING_VARIANTS_MAPPING_PATH, 'rb') as variant_id_file:
            self.variant_id = pickle.load(variant_id_file)
