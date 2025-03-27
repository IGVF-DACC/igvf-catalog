import csv
import json
from adapters.helpers import build_variant_id_from_spdi, build_regulatory_region_id
from typing import Optional

from adapters.writer import Writer
# Example line from file from IGVFFI1236SEPK
# chr10	100005234	100005491	0.126	NC_000010.11:100005302:A:C
# chr10	100005234	100005491	0.129	NC_000010.11:100005339:A:C
# chr10	100005234	100005491	-0.136	NC_000010.11:100005425:A:T


class BlueSTARRVariantElement:
    ALLOWED_LABELS = ['variant_genomic_elements']
    SOURCE = 'IGVF'
    SOURCE_URL = 'https://data.igvf.org/prediction-sets/IGVFDS0257SDNV/'

    def __init__(self, filepath, label='variant_element', writer: Optional[Writer] = None, **kwargs):
        if label not in BlueSTARRVariantElement.ALLOWED_LABELS:
            raise ValueError('Invalid label. Allowed values: ' +
                             ','.join(BlueSTARRVariantElement.ALLOWED_LABELS))

        self.filepath = filepath
        self.writer = writer

    def process_file(self):
        self.writer.open()

        with open(self.filepath, 'r') as bluestarr_tsv:
            bluestarr_tsv = csv.reader(bluestarr_tsv, delimiter='\t')
            for row in bluestarr_tsv:
                _id = build_variant_id_from_spdi(row[4])
                element_id = build_regulatory_region_id(row[0], row[1], row[2])
                edge_key = _id + '_' + element_id
                _props = {
                    '_key': edge_key,
                    '_from': 'variants/' + _id,
                    '_to': 'genomic_elements/' + element_id,
                    'log2FC': float(row[5]),
                    'label': 'predicted effect on regulatory function',
                    'method': 'BlueSTARR',
                    'biosample_context': 'K562',
                    'biosample_term': 'ontology_terms/EFO_0002067',
                    'name': 'modulates regulatory activity of',
                    'inverse_name': 'regulatory activity modulated by',
                    'source': BlueSTARRVariantElement.SOURCE,
                    'source_url': BlueSTARRVariantElement.SOURCE_URL
                }

                self.writer.write(json.dumps(_props))
                self.writer.write('\n')

        self.writer.close()
