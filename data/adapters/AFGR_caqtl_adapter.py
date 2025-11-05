import csv
import gzip
import json
from math import log10
from typing import Optional

from adapters.base import BaseAdapter
from adapters.helpers import build_variant_id, build_regulatory_region_id
from adapters.writer import Writer

# Example row from sorted.dist.hwe.af.AFR.caQTL.genPC.maf05.90.qn.idr.txt.gz
# chr	snp_pos	snp_pos2	ref	alt	variant	effect_af_eqtl	p_hwe	feature	dist_start	dist_end	pvalue	beta	se
# 1	66435	66435	ATT	A	1_66435_ATT_A	0.125	0.644802	1:1001657:1002109	-935222	-935674	0.616173	0.055905	0.111128


class AFGRCAQtl(BaseAdapter):
    ALLOWED_LABELS = ['genomic_element', 'AFGR_caqtl']

    SOURCE = 'AFGR'
    SOURCE_URL = 'https://github.com/smontgomlab/AFGR'

    CLASS_NAME = 'accessible_dna_element'
    ONTOLOGY_TERM_ID = 'EFO_0005292'  # lymphoblastoid cell line
    ONTOLOGY_TERM_NAME = 'lymphoblastoid cell line'
    EDGE_COLLECTION_NAME = 'modulates accessibility of'
    EDGE_COLLECTION_INVERSR_NAME = 'accessibility modulated by'
    # EDGE_COLLECTION_METHOD = 'BAO_0040027'  # chromatin acessibility method

    def __init__(self, filepath, label, writer: Optional[Writer] = None, validate=False, **kwargs):
        # Initialize base adapter first
        super().__init__(filepath, label, writer, validate)

    def _get_schema_type(self):
        """Return schema type based on label."""
        if self.label == 'genomic_element':
            return 'nodes'
        else:
            return 'edges'

    def _get_collection_name(self):
        """Get collection based on label."""
        if self.label == 'genomic_element':
            return 'genomic_elements'
        else:
            return 'variants_genomic_elements'

    def process_file(self):
        self.writer.open()

        with gzip.open(self.filepath, 'rt') as qtl_file:
            qtl_csv = csv.reader(qtl_file, delimiter='\t')
            next(qtl_csv)

            for row in qtl_csv:
                region_chr, region_pos_start, region_pos_end = row[8].split(
                    ':')
                genomic_element_id = build_regulatory_region_id(
                    region_chr, region_pos_start, region_pos_end, class_name=AFGRCAQtl.CLASS_NAME
                )

                if self.label == 'genomic_element':
                    _id = genomic_element_id + '_' + AFGRCAQtl.SOURCE
                    _props = {
                        '_key': _id,
                        'name': _id,
                        'chr': 'chr' + region_chr,
                        'start': int(region_pos_start),
                        'end': int(region_pos_end),
                        'source': AFGRCAQtl.SOURCE,
                        'source_url': AFGRCAQtl.SOURCE_URL,
                        'type': 'accessible dna elements',
                        'method': 'caQTL'
                    }

                elif self.label == 'AFGR_caqtl':
                    chr, pos, ref, alt = row[5].split('_')

                    variant_id = build_variant_id(chr, pos, ref, alt, 'GRCh38')

                    pvalue = float(row[-3])  # no 0 cases
                    log_pvalue = -1 * log10(pvalue)

                    _id = variant_id + '_' + genomic_element_id + '_' + AFGRCAQtl.SOURCE
                    _source = 'variants/' + variant_id
                    _target = 'genomic_elements/' + genomic_element_id + '_' + AFGRCAQtl.SOURCE

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
                        'name': AFGRCAQtl.EDGE_COLLECTION_NAME,
                        'inverse_name': AFGRCAQtl.EDGE_COLLECTION_INVERSR_NAME,
                        'method': 'caQTL'  # changed from ontology term to term name here to align with other collections, we will need to revisit label and method in future
                    }

                if self.validate:
                    self.validate_doc(_props)

                self.writer.write(json.dumps(_props))
                self.writer.write('\n')

        self.writer.close()
