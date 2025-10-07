import csv
import json
from typing import Optional
from jsonschema import Draft202012Validator, ValidationError

from adapters.helpers import build_variant_id
from adapters.writer import Writer
from schemas.registry import get_schema

# Example TOPLD input data file:

# SNP1,SNP2,Uniq_ID_1,Uniq_ID_2,R2,Dprime,+/-corr
# 5031031,5032123,5031031:C:T,5032123:G:A,0.251,0.888,+
# 5031031,5063457,5031031:C:T,5063457:G:C,0.443,0.832,+

# Example TOPLD annotation file:

# Position,rsID,MAF,REF,ALT,Uniq_ID,VEP_ensembl_Gene_Name,VEP_ensembl_Consequence,CADD_phred,fathmm_XF_coding_or_noncoding,FANTOM5_enhancer_expressed_tissue_cell
# 5031031,rs1441313282,0.010486891385767793,C,T,5031031:C:T,FP565260.3|FP565260.3|FP565260.3|FP565260.3|FP565260.3,"intron_variant|intron_variant|intron_variant|intron_variant,NMD_transcript_variant|intron_variant",2.135,.,.


class TopLD:
    DATASET = 'topld_linkage_disequilibrium'

    def __init__(self, filepath,  annotation_filepath, chr, ancestry='SAS', writer: Optional[Writer] = None, validate=False, **kwargs):
        self.filepath = filepath
        self.annotation_filepath = annotation_filepath
        self.writer = writer
        self.chr = chr
        self.ancestry = ancestry
        self.dataset = TopLD.DATASET
        self.label = TopLD.DATASET
        self.validate = validate
        if self.validate:
            self.schema = get_schema(
                'edges', 'variants_variants', self.__class__.__name__)
            self.validator = Draft202012Validator(self.schema)

    def validate_doc(self, doc):
        try:
            self.validator.validate(doc)
        except ValidationError as e:
            raise ValueError(f'Document validation failed: {e.message}')

    def process_annotations(self):
        print('Processing annotations...')
        self.ids = {}
        with open(self.annotation_filepath, 'r') as annotations:
            annotations_csv = csv.reader(annotations)

            next(annotations_csv)

            for row in annotations_csv:
                self.ids[row[0]] = {
                    'rsid': row[1],
                    'variant_id': 'variants/' + build_variant_id(
                        self.chr,
                        row[0],
                        row[3],
                        row[4]
                    )
                }

    def process_file(self):
        self.process_annotations()

        print('Processing data...')

        self.writer.open()

        for line in open(self.filepath, 'r'):
            row = line.split(',')

            if row[0] == 'SNP1':
                continue

            # there are no use cases for custom _id
            # letting ArangoDB create the _id speeds up loading and query times
            props = {
                '_from': self.ids[row[0]]['variant_id'],
                '_to': self.ids[row[1]]['variant_id'],
                'chr': self.chr,
                'negated': row[6] == '+',
                'variant_1_base_pair': ':'.join(row[2].split(':')[1:3]),
                'variant_2_base_pair': ':'.join(row[3].split(':')[1:3]),
                'variant_1_rsid': self.ids[row[0]]['rsid'],
                'variant_2_rsid': self.ids[row[1]]['rsid'],
                'r2': float(row[4]),
                'd_prime': float(row[5]),
                'ancestry': self.ancestry,
                'label': 'linkage disequilibrum',
                'name': 'correlated with',
                'inverse_name': 'correlated with',
                'source': 'TopLD',
                'source_url': 'http://topld.genetics.unc.edu/'
            }

            if self.validate:
                self.validator.validate(props)

            self.writer.write(json.dumps(props))
            self.writer.write('\n')

        self.writer.close()
