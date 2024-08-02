import csv
import gzip
from math import log10

from adapters import Adapter
from adapters.helpers import build_variant_id, build_regulatory_region_id

# Example row from sorted.dist.hwe.af.AFR.caQTL.genPC.maf05.90.qn.idr.txt.gz
# chr	snp_pos	snp_pos2	ref	alt	variant	effect_af_eqtl	p_hwe	feature	dist_start	dist_end	pvalue	beta	se
# 1	66435	66435	ATT	A	1_66435_ATT_A	0.125	0.644802	1:1001657:1002109	-935222	-935674	0.616173	0.055905	0.111128


class AFGRCAQtl(Adapter):
    ALLOWED_LABELS = ['regulatory_region', 'AFGR_caqtl']

    SOURCE = 'AFGR'
    SOURCE_URL = 'https://github.com/smontgomlab/AFGR'

    CLASS_NAME = 'accessible_dna_element'
    ONTOLOGY_TERM_ID = 'EFO_0005292'  # lymphoblastoid cell line
    ONTOLOGY_TERM_NAME = 'lymphoblastoid cell line'

    def __init__(self, filepath, label):
        if label not in AFGRCAQtl.ALLOWED_LABELS:
            raise ValueError('Ivalid label. Allowed values: ' +
                             ','.join(AFGRCAQtl.ALLOWED_LABELS))

        self.filepath = filepath
        self.label = label

        super().__init__()

    def process_file(self):
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
                        'name': _id,
                        'chr': region_chr,
                        'start': region_pos_start,
                        'end': region_pos_end,
                        'source': AFGRCAQtl.SOURCE,
                        'source_url': AFGRCAQtl.SOURCE_URL,
                        'type': 'accessible dna elements'
                    }

                    yield(_id, self.label, _props)

                elif self.label == 'AFGR_caqtl':
                    chr, pos, ref, alt = row[5].split('_')

                    variant_id = build_variant_id(chr, pos, ref, alt, 'GRCh38')

                    pvalue = float(row[-3])  # no 0 cases
                    log_pvalue = -1 * log10(pvalue)

                    _id = variant_id + '_' + regulatory_region_id + '_' + AFGRCAQtl.SOURCE
                    _source = 'variants/' + variant_id
                    _target = 'regulatory_regions/' + regulatory_region_id

                    _props = {
                        'label': 'caQTL',
                        'log10pvalue': log_pvalue,
                        'p_value': pvalue,
                        'beta': float(row[-2]),
                        'source': AFGRCAQtl.SOURCE,
                        'source_url': AFGRCAQtl.SOURCE_URL,
                        'biosample_term': 'ontology_terms/' + AFGRCAQtl.ONTOLOGY_TERM_ID,
                        'biological_context': AFGRCAQtl.ONTOLOGY_TERM_NAME
                    }

                    yield(_id, _source, _target, self.label, _props)
