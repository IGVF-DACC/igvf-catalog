import csv
import json
from adapters.base import BaseAdapter
from adapters.helpers import build_variant_id, split_spdi, build_regulatory_region_id, bulk_check_variants_in_arangodb, load_variant, get_file_fileset_by_accession_in_arangodb
from typing import Optional
from adapters.writer import Writer

# Example lines from file from IGVFFI1663LKVQ
# chr5	1778763	1779094	0.131	NC_000005.10:1778862:T:G
# chr5	1779099	1779256	0.210	NC_000005.10:1779139:G:A
# chr5	1779339	1779683	-0.242	NC_000005.10:1779476:C:G
# chr5	1779339	1779683	0.100	NC_000005.10:1779510:G:C


class BlueSTARRVariantElement(BaseAdapter):
    ALLOWED_LABELS = ['variant', 'variant_genomic_element']
    SOURCE = 'IGVF'
    SOURCE_URL = 'https://data.igvf.org/tabular-files/IGVFFI1663LKVQ/'
    FILE_ACCESSION = 'IGVFFI1663LKVQ'
    ELEMENT_FILE_ACCESSION = 'ENCFF420VPZ'  # CCRE from ENCODE

    def __init__(
        self,
        filepath,
        label='variant_genomic_element',
        writer: Optional[Writer] = None,
        validate=False,
        **kwargs
    ):
        # Initialize base adapter first
        super().__init__(filepath, label, writer, validate)
        self.file_accession = self.SOURCE_URL.split('/')[-2]
        self.collection_label = 'predicted variant effect on gene expression'

    def _get_schema_type(self):
        """Return schema type based on label."""
        if self.label == 'variant_genomic_element':
            return 'edges'
        else:
            return 'nodes'

    def _get_collection_name(self):
        """Get collection based on label."""
        if self.label == 'variant_genomic_element':
            return 'variants_genomic_elements'
        else:
            return 'variants'

    def process_file(self):
        self.writer.open()
        file_fileset_obj = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        self.method = file_fileset_obj['method']
        self.collection_class = file_fileset_obj['class']

        with open(self.filepath, 'r') as bluestarr_tsv:
            reader = csv.reader(bluestarr_tsv, delimiter='\t')
            chunk_size = 6500

            chunk = []
            for i, row in enumerate(reader, 1):
                chunk.append(row)
                if i % chunk_size == 0:
                    if self.label == 'variant':
                        self.process_variant_chunk(chunk)
                    elif self.label == 'variant_genomic_element':
                        self.process_edge_chunk(chunk)
                    chunk = []

            if chunk != []:
                if self.label == 'variant':
                    self.process_variant_chunk(chunk)
                elif self.label == 'variant_genomic_element':
                    self.process_edge_chunk(chunk)

        self.writer.close()

    def process_variant_chunk(self, chunk):
        loaded_spdis = bulk_check_variants_in_arangodb(
            [row[4] for row in chunk])
        skipped_spdis = []

        unloaded_chunk = []
        for row in chunk:
            if row[4] not in loaded_spdis:
                unloaded_chunk.append(row)

        for row in unloaded_chunk:
            spdi = row[4]
            variant, skipped_message = load_variant(spdi)
            if variant:
                variant.update({
                    'source': BlueSTARRVariantElement.SOURCE,
                    'source_url': BlueSTARRVariantElement.SOURCE_URL,
                    'files_filesets': 'files_filesets/' + self.FILE_ACCESSION
                })
                if self.validate:
                    self.validate_doc(variant)
                self.writer.write(json.dumps(variant) + '\n')

            if skipped_message is not None:
                skipped_spdis.append(skipped_message)

        if skipped_spdis:
            self.logger.warning(f'Skipped {len(skipped_spdis)} variants:')
            for skipped in skipped_spdis:
                self.logger.warning(
                    f"  - {skipped['variant_id']}: {skipped['reason']}")
            with open('./skipped_variants.jsonl', 'a') as out:
                for skipped in skipped_spdis:
                    out.write(json.dumps(skipped) + '\n')

    def process_edge_chunk(self, chunk):
        loaded_spdis = bulk_check_variants_in_arangodb(
            [row[4] for row in chunk])

        unloaded_chunk = []
        for row in chunk:
            if row[4] in loaded_spdis:
                unloaded_chunk.append(row)

        for row in unloaded_chunk:
            spdi = row[4]
            chr, pos_start, ref, alt = split_spdi(spdi)
            _id = build_variant_id(chr, pos_start + 1, ref, alt, 'GRCh38')

            element_id = build_regulatory_region_id(
                row[0], row[1], row[2], 'candidate_cis_regulatory_element') + '_' + BlueSTARRVariantElement.ELEMENT_FILE_ACCESSION
            edge_key = _id + '_' + element_id + '_IGVFFI1663LKVQ'

            edge_props = {
                '_key': edge_key,
                '_from': 'variants/' + _id,
                '_to': 'genomic_elements/' + element_id,
                'log2FC': float(row[3]),
                'class': self.collection_class,
                'label': self.collection_label,
                'method': self.method,
                'biosample_context': 'K562',
                'biosample_term': 'ontology_terms/EFO_0002067',
                'name': 'modulates regulatory activity of',
                'inverse_name': 'regulatory activity modulated by',
                'source': self.SOURCE,
                'source_url': self.SOURCE_URL,
                'files_filesets': 'files_filesets/' + self.FILE_ACCESSION
            }

            if self.validate:
                self.validate_doc(edge_props)

            self.writer.write(json.dumps(edge_props) + '\n')
