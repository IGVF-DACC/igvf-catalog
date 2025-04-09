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
    ALLOWED_LABELS = ['variant_genomic_elements']
    SOURCE = 'IGVF'
    SOURCE_URL = 'https://data.igvf.org/prediction-sets/IGVFDS2340WJRV/'

    def __init__(
        self,
        filepath,
        label='variant_genomic_elements',
        edge_writer: Optional[Writer] = None,
        variant_writer: Optional[Writer] = None,
        **kwargs
    ):
        if label not in BlueSTARRVariantElement.ALLOWED_LABELS:
            raise ValueError('Invalid label. Allowed values: ' +
                             ','.join(BlueSTARRVariantElement.ALLOWED_LABELS))

        self.filepath = filepath
        self.edge_writer = edge_writer
        self.variant_writer = variant_writer

    def process_file(self):
        self.edge_writer.open()
        if self.variant_writer:
            self.variant_writer.open()

        with open(self.filepath, 'r') as bluestarr_tsv:
            bluestarr_tsv = csv.reader(bluestarr_tsv, delimiter='\t')
            for row in bluestarr_tsv:
                spdi = row[4]
                chr, pos_start, ref, alt = split_spdi(spdi)
                _id = build_variant_id(chr, pos_start + 1, ref, alt, 'GRCh38')

                if self.variant_writer and not(check_if_variant_loaded(spdi)):
                    print(f'{spdi} has not been loaded yet.')
                    if not(is_variant_snv(spdi)):
                        raise ValueError(f'{spdi} is not a SNV.')
                    if not(validate_snv_ref_seq_by_spdi(spdi)):
                        raise ValueError(
                            f'The reference allele of {spdi} does not match the reference genome at this position.')
                    variant_json = load_variant(
                        _id, spdi, chr, pos_start, ref, alt,
                        source=self.SOURCE,
                        source_url=self.SOURCE_URL,
                        organism='Homo sapiens'
                    )
                    if self.variant_writer:
                        self.variant_writer.write(
                            json.dumps(variant_json) + '\n')

                element_id = build_regulatory_region_id(
                    row[0], row[1], row[2], 'candidate_cis_regulatory_element') + '_IGVFFI7195KIHI'
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

                self.edge_writer.write(json.dumps(_props) + '\n')

        self.edge_writer.close()
        if self.variant_writer:
            self.variant_writer.close()
