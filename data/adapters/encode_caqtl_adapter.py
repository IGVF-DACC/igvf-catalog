import json
import os
from typing import Optional

from adapters.base import BaseAdapter
from adapters.helpers import (
    build_variant_id,
    build_regulatory_region_id,
    bulk_check_variants_in_arangodb,
    get_file_fileset_by_accession_in_arangodb,
    load_variant,
)
from adapters.writer import Writer

# Example Encode caQTL input file:
# chr1	766454	766455	chr1_766455_T_C	chr1	766455	T	C	1	778381	779150	FALSE	1_778381_779150	C	T	rs189800799	Progenitor
# chr1	766454	766455	chr1_766455_T_C	chr1	766455	T	C	1	778381	779150	FALSE	1_778381_779150	C	T	rs189800799	Neuron
# chr1	1668541	1668542	chr1_1668542_C_T	chr1	1668542	C	T	1	1658831	1659350	FALSE	1_1658831_1659350	T	C	rs72634822	Progenitor
# chr1	1687152	1687153	chr1_1687153_A_G	chr1	1687153	A	G	1	1745801	1746550	FALSE	1_1745801_1746550	A	G	rs28366981	Progenitor

# Columns parsed in ths adapter:
# 1: variant chrom; 3: variant position (1-based); 7: variant ref allele; 8: variant alt allele; 2nd last: rsID
# 9: caPeak chrom; 10: caPeak start; 11: caPeak end;
# last column: cell name


class CAQtl(BaseAdapter):
    # 1-based coordinate system

    ALLOWED_LABELS = ['genomic_element', 'encode_caqtl', 'variants']
    CHUNK_SIZE = 6500
    CLASS_NAME = 'accessible_dna_element'
    # we can have a map file if loading more datasets in future
    CELL_ONTOLOGY = {
        'Progenitor': {
            'term_id': 'CL_0011020',
            'term_name': 'neural progenitor cell'
        },
        'Neuron': {
            'term_id': 'CL_0000540',
            'term_name': 'neuron'
        },
        'Liver': {
            'term_id': 'UBERON_0002107',
            'term_name': 'liver'
        }
    }
    EDGE_COLLECTION_NAME = 'modulates accessibility of'
    EDGE_COLLECTION_INVERSR_NAME = 'accessibility modulated by'
    EDGE_COLLECTION_METHOD = 'BAO_0040027'  # chromatin acessibility method

    def __init__(self, filepath, source, label, writer: Optional[Writer] = None, validate=False, **kwargs):
        self.file_accession = os.path.basename(filepath).split('.')[0]
        self.source = source
        self.collection_label = 'caQTL'
        self.file_fileset = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        self.written_variant_keys = set()
        super().__init__(filepath, label, writer, validate)

    def _get_schema_type(self):
        """Return schema type based on label."""
        if self.label == 'encode_caqtl':
            return 'edges'
        else:
            return 'nodes'

    def _get_collection_name(self):
        """Get collection based on label."""
        if self.label == 'genomic_element':
            return 'genomic_elements'
        elif self.label == 'variants':
            return 'variants'
        else:
            return 'variants_genomic_elements'

    def parse(self):
        self.writer.add_tag('portal_accessions', self.file_accession)
        file_set_accession = self.file_fileset.get('file_set_id')
        if file_set_accession:
            self.writer.add_tag('portal_accessions', file_set_accession)
        self.method = self.file_fileset['method']
        self.collection_class = self.file_fileset['class']

        if self.label == 'genomic_element':
            for line in open(self.filepath, 'r'):
                self.write_genomic_element(line.strip().split())
            return

        chunk = []
        for line in open(self.filepath, 'r'):
            chunk.append(line.strip().split())
            if len(chunk) >= CAQtl.CHUNK_SIZE:
                self.process_variant_chunk(chunk)
                chunk = []
        if chunk:
            self.process_variant_chunk(chunk)

    def write_genomic_element(self, data_line):
        ocr_chr = 'chr' + data_line[8]
        ocr_pos_start = data_line[9]
        ocr_pos_end = data_line[10]
        genomic_element_id = build_regulatory_region_id(
            ocr_chr, ocr_pos_start, ocr_pos_end, class_name=CAQtl.CLASS_NAME
        )
        _id = genomic_element_id + '_' + self.file_accession
        _props = {
            '_key': _id,
            'name': _id,
            'chr': ocr_chr,
            'start': int(ocr_pos_start),
            'end': int(ocr_pos_end),
            'method': self.method,
            'source': 'ENCODE',
            'source_url': 'https://www.encodeproject.org/files/' + self.file_accession,
            'files_filesets': 'files_filesets/' + self.file_accession,
            'type': 'accessible dna elements',
        }
        if self.validate:
            self.validate_doc(_props)
        self.writer.write(json.dumps(_props))
        self.writer.write('\n')

    def process_variant_chunk(self, chunk):
        rows_by_variant_id = []
        for data_line in chunk:
            chr = data_line[0]
            pos = data_line[2]
            ref = data_line[6]
            alt = data_line[7]
            try:
                variant_id = build_variant_id(chr, pos, ref, alt)
            except Exception as e:
                self.logger.warning(
                    f'Skipping row - unable to build variant id (chr={chr}, pos={pos}, ref={ref}, alt={alt}): {e}')
                continue
            rows_by_variant_id.append((variant_id, data_line))

        if not rows_by_variant_id:
            return

        loaded_variants = bulk_check_variants_in_arangodb(
            list({variant_id for variant_id, _ in rows_by_variant_id}),
            check_by='_key',
        )

        if self.label == 'variants':
            self.write_missing_variants(rows_by_variant_id, loaded_variants)
            return

        skipped_missing = 0
        for variant_id, data_line in rows_by_variant_id:
            if variant_id not in loaded_variants:
                skipped_missing += 1
                continue
            self.write_edge(variant_id, data_line)

        if skipped_missing:
            self.logger.warning(
                f'Skipped {skipped_missing} row(s) - variant not found in variants collection')

    def write_edge(self, variant_id, data_line):
        ocr_chr = 'chr' + data_line[8]
        ocr_pos_start = data_line[9]
        ocr_pos_end = data_line[10]
        genomic_element_id = build_regulatory_region_id(
            ocr_chr, ocr_pos_start, ocr_pos_end, class_name=CAQtl.CLASS_NAME
        )
        cell_name = data_line[-1]

        # there can be same variant -> atac peak in multiple cells in same file, we want to make edges for each cell
        _id = variant_id + '_' + genomic_element_id + \
            '_' + cell_name + '_' + self.file_accession
        _source = 'variants/' + variant_id
        _target = 'genomic_elements/' + genomic_element_id + '_' + self.file_accession
        _props = {
            '_key': _id,
            '_from': _source,
            '_to': _target,
            'rsid': data_line[-2],
            'label': 'caQTL',
            'method': self.method,
            'class': self.collection_class,
            'source': 'ENCODE',
            'source_url': 'https://www.encodeproject.org/files/' + self.file_accession,
            'files_filesets': 'files_filesets/' + self.file_accession,
            'biological_context': CAQtl.CELL_ONTOLOGY[cell_name]['term_name'],
            'biosample_term': 'ontology_terms/' + CAQtl.CELL_ONTOLOGY[cell_name]['term_id'],
            'name': CAQtl.EDGE_COLLECTION_NAME,
            'inverse_name': CAQtl.EDGE_COLLECTION_INVERSR_NAME,
            'method_term': 'ontology_terms/' + CAQtl.EDGE_COLLECTION_METHOD,
        }
        if self.validate:
            self.validate_doc(_props)
        self.writer.write(json.dumps(_props))
        self.writer.write('\n')

    def write_missing_variants(self, rows_by_variant_id, loaded_variants):
        for variant_id, data_line in rows_by_variant_id:
            if variant_id in loaded_variants or variant_id in self.written_variant_keys:
                continue
            self.written_variant_keys.add(variant_id)

            chr = data_line[0]
            pos = data_line[2]
            ref = data_line[6]
            alt = data_line[7]
            variant_props, skipped = load_variant(f'{chr}-{pos}-{ref}-{alt}')
            if variant_props:
                variant_props.update({
                    'source': 'ENCODE',
                    'source_url': 'https://www.encodeproject.org/files/' + self.file_accession,
                    'files_filesets': 'files_filesets/' + self.file_accession
                })
                if self.validate:
                    self.validate_doc(variant_props)
                self.writer.write(json.dumps(variant_props))
                self.writer.write('\n')
            elif skipped:
                self.logger.warning(
                    f"Invalid variant: {skipped['variant_id']} - {skipped['reason']}")
