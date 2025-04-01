import csv
import json
from adapters.helpers import build_variant_id_from_spdi, build_regulatory_region_id, check_spdi
from typing import Optional

from adapters.writer import Writer
# Example lines from file from IGVFFI1663LKVQ
# chr5	1778763	1779094	0.131	NC_000005.10:1778862:T:G
# chr5	1779099	1779256	0.210	NC_000005.10:1779139:G:A
# chr5	1779339	1779683	-0.242	NC_000005.10:1779476:C:G
# chr5	1779339	1779683	0.100	NC_000005.10:1779510:G:C


class BlueSTARRVariantElement:
    ALLOWED_LABELS = ['variant_genomic_elements']
    SOURCE = 'IGVF'
    SOURCE_URL = 'https://data.igvf.org/prediction-sets/IGVFDS2340WJRV/'

    def __init__(self, filepath, label='variant_genomic_elements', writer: Optional[Writer] = None, **kwargs):
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
                spdi = row[4]
                if not(check_spdi(spdi)):
                    print(f'{spdi} has not been loaded yet.')
                    continue
                _id = build_variant_id_from_spdi(spdi)
                element_id = build_regulatory_region_id(row[0], row[1], row[2])
                edge_key = _id + '_' + element_id
                _props = {
                    '_key': edge_key,
                    '_from': 'variants/' + _id,
                    '_to': 'genomic_elements/' + element_id,
                    'log2FC': float(row[3]),
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
