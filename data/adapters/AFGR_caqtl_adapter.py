import csv
import gzip
import json
from math import log10
import os
from typing import Optional

from adapters.helpers import build_variant_id, build_regulatory_region_id
from db.arango_db import ArangoDB

from adapters.writer import Writer
# Example row from sorted.dist.hwe.af.AFR.caQTL.genPC.maf05.90.qn.idr.txt.gz
# chr	snp_pos	snp_pos2	ref	alt	variant	effect_af_eqtl	p_hwe	feature	dist_start	dist_end	pvalue	beta	se
# 1	66435	66435	ATT	A	1_66435_ATT_A	0.125	0.644802	1:1001657:1002109	-935222	-935674	0.616173	0.055905	0.111128


class AFGRCAQtl:
    ALLOWED_LABELS = ['regulatory_region', 'AFGR_caqtl']

    SOURCE = 'AFGR'
    SOURCE_URL = 'https://github.com/smontgomlab/AFGR'

    CLASS_NAME = 'accessible_dna_element'
    ONTOLOGY_TERM_ID = 'EFO_0005292'  # lymphoblastoid cell line
    ONTOLOGY_TERM_NAME = 'lymphoblastoid cell line'

    def __init__(self, filepath, label, dry_run=True, writer: Optional[Writer] = None, **kwargs):
        if label not in AFGRCAQtl.ALLOWED_LABELS:
            raise ValueError('Ivalid label. Allowed values: ' +
                             ','.join(AFGRCAQtl.ALLOWED_LABELS))

        self.filepath = filepath
        self.label = label
        self.dataset = label
        self.dry_run = dry_run
        self.type = 'edge'
        if(self.label == 'regulatory_region'):
            self.type = 'node'
        self.writer = writer

        super(AFGRCAQtl, self).__init__()

    def process_file(self):
        self.writer.open()

        with gzip.open(self.filepath, 'rt') as qtl_file:
            qtl_csv = csv.reader(qtl_file, delimiter='\t')
            next(qtl_csv)

            for row in qtl_csv:
                region_chr, region_pos_start, region_pos_end = row[8].split(
                    ':')
                regulatory_region_id = build_regulatory_region_id(
                    region_chr, region_pos_start, region_pos_end, class_name=AFGRCAQtl.CLASS_NAME
                )

                if self.label == 'regulatory_region':
                    _id = regulatory_region_id
                    _props = {
                        '_key': regulatory_region_id,
                        'name': _id,
                        'chr': region_chr,
                        'start': region_pos_start,
                        'end': region_pos_end,
                        'source': AFGRCAQtl.SOURCE,
                        'source_url': AFGRCAQtl.SOURCE_URL,
                        'type': 'accessible dna elements'
                    }

                elif self.label == 'AFGR_caqtl':
                    chr, pos, ref, alt = row[5].split('_')

                    variant_id = build_variant_id(chr, pos, ref, alt, 'GRCh38')

                    pvalue = float(row[-3])  # no 0 cases
                    log_pvalue = -1 * log10(pvalue)

                    _id = variant_id + '_' + regulatory_region_id + '_' + AFGRCAQtl.SOURCE
                    _source = 'variants/' + variant_id
                    _target = 'regulatory_regions/' + regulatory_region_id

                    _props = {
                        '_key': _id,
                        '_from': _source,
                        '_to': _target,
                        'label': 'caQTL',
                        'log10pvalue': log_pvalue,
                        'p_value': pvalue,
                        'beta': float(row[-2]),
                        'source': AFGRCAQtl.SOURCE,
                        'source_url': AFGRCAQtl.SOURCE_URL,
                        'biosample_term': 'ontology_terms/' + AFGRCAQtl.ONTOLOGY_TERM_ID,
                        'biological_context': AFGRCAQtl.ONTOLOGY_TERM_NAME,
                        'name': 'associates with',
                        'inverse_name': 'associates with'
                    }

                self.writer.write(json.dumps(_props))
                self.writer.write('\n')

        self.writer.close()
