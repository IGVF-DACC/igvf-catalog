import csv
import json
from adapters.helpers import build_variant_id, split_spdi, build_regulatory_region_id, check_if_variant_loaded, load_variant
from adapters.utils.variant_validation import is_variant_snv, validate_snv_ref_seq_by_spdi
from typing import Optional

from adapters.writer import Writer
# Example lines from file from IGVFFI1663LKVQ
# chr5	1778763	1779094	0.131	NC_000005.10:1778862:T:G
# chr5	1779099	1779256	0.210	NC_000005.10:1779139:G:A
# chr5	1779339	1779683	-0.242	NC_000005.10:1779476:C:G
# chr5	1779339	1779683	0.100	NC_000005.10:1779510:G:C


class BlueSTARRVariantElement:
    ALLOWED_LABELS = ['variant', 'variant_genomic_element']
    SOURCE = 'IGVF'
    SOURCE_URL = 'https://data.igvf.org/tabular-files/IGVFFI1663LKVQ/'

    def __init__(
        self,
        filepath,
        label='variant_genomic_element',
        writer: Optional[Writer] = None,
        **kwargs
    ):
        if label not in BlueSTARRVariantElement.ALLOWED_LABELS:
            raise ValueError('Invalid label. Allowed values: ' +
                             ','.join(BlueSTARRVariantElement.ALLOWED_LABELS))

        self.filepath = filepath
        self.writer = writer
        self.label = label

    def process_file(self):
        self.writer.open()

        with open(self.filepath, 'r') as bluestarr_tsv:
            reader = csv.reader(bluestarr_tsv, delimiter='\t')
            for row in reader:
                if self.label == 'variant':
                    self.process_variant(row)
                elif self.label == 'variant_genomic_element':
                    self.process_edge(row)

        self.writer.close()

    def process_variant(self, row):
        spdi = row[4]
        loaded, _ = check_if_variant_loaded(spdi)
        if loaded:
            return

        if not is_variant_snv(spdi):
            raise ValueError(f'{spdi} is not a SNV.')
        if not validate_snv_ref_seq_by_spdi(spdi):
            raise ValueError(f'Reference allele mismatch for {spdi}.')

        chr, pos_start, ref, alt = split_spdi(spdi)
        _id = build_variant_id(chr, pos_start + 1, ref, alt, 'GRCh38')

        variant = load_variant(
            _id, spdi, chr, pos_start, ref, alt,
            source=self.SOURCE,
            source_url=self.SOURCE_URL,
            organism='Homo sapiens'
        )
        self.writer.write(json.dumps(variant) + '\n')

    def process_edge(self, row):
        spdi = row[4]
        loaded, _ = check_if_variant_loaded(spdi)
        if not loaded:
            raise ValueError(f'{spdi} has not been loaded yet.')

        chr, pos_start, ref, alt = split_spdi(spdi)
        _id = build_variant_id(chr, pos_start + 1, ref, alt, 'GRCh38')

        element_id = build_regulatory_region_id(
            row[0], row[1], row[2], 'candidate_cis_regulatory_element') + '_IGVFFI7195KIHI'
        edge_key = _id + '_' + element_id

        edge_props = {
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
            'source': self.SOURCE,
            'source_url': self.SOURCE_URL
        }

        self.writer.write(json.dumps(edge_props) + '\n')
