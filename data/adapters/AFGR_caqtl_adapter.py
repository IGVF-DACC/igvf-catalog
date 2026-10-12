import csv
import gzip
import json
from math import log10
from typing import Optional
import os

from adapters.base import BaseAdapter
from adapters.helpers import (
    build_variant_id,
    build_regulatory_region_id,
    bulk_check_variants_in_arangodb,
    get_file_fileset_by_accession_in_arangodb,
    load_variant,
)
from adapters.writer import Writer

# Example row from sorted.dist.hwe.af.AFR.caQTL.genPC.maf05.90.qn.idr.txt.gz
# chr	snp_pos	snp_pos2	ref	alt	variant	effect_af_eqtl	p_hwe	feature	dist_start	dist_end	pvalue	beta	se
# 1	66435	66435	ATT	A	1_66435_ATT_A	0.125	0.644802	1:1001657:1002109	-935222	-935674	0.616173	0.055905	0.111128


class AFGRCAQtl(BaseAdapter):
    ALLOWED_LABELS = ['genomic_element', 'AFGR_caqtl', 'variants']
    CHUNK_SIZE = 6500

    SOURCE = 'AFGR'
    SOURCE_URL = 'https://github.com/smontgomlab/AFGR'

    CLASS_NAME = 'accessible_dna_element'
    ONTOLOGY_TERM_ID = 'EFO_0005292'  # lymphoblastoid cell line
    ONTOLOGY_TERM_NAME = 'lymphoblastoid cell line'
    EDGE_COLLECTION_NAME = 'modulates accessibility of'
    EDGE_COLLECTION_INVERSR_NAME = 'accessibility modulated by'

    def __init__(self, filepath, label, writer: Optional[Writer] = None, validate=False, **kwargs):
        # Initialize base adapter first
        super().__init__(filepath, label, writer, validate)
        self.file_accession = os.path.basename(filepath).split('.')[0]
        self.written_variant_keys = set()

    def _get_schema_type(self):
        """Return schema type based on label."""
        if self.label == 'AFGR_caqtl':
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
        self.file_fileset = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        file_set_accession = self.file_fileset.get('file_set_id')
        if file_set_accession:
            self.writer.add_tag('portal_accessions', file_set_accession)

        with gzip.open(self.filepath, 'rt') as qtl_file:
            qtl_csv = csv.reader(qtl_file, delimiter='\t')
            next(qtl_csv)

            if self.label == 'genomic_element':
                for row in qtl_csv:
                    self.write_genomic_element(row)
                return

            chunk = []
            for row in qtl_csv:
                chunk.append(row)
                if len(chunk) >= AFGRCAQtl.CHUNK_SIZE:
                    self.process_variant_chunk(chunk)
                    chunk = []
            if chunk:
                self.process_variant_chunk(chunk)

    def write_genomic_element(self, row):
        region_chr, region_pos_start, region_pos_end = row[8].split(':')
        genomic_element_id = build_regulatory_region_id(
            region_chr, region_pos_start, region_pos_end, class_name=AFGRCAQtl.CLASS_NAME
        )
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
            'method': self.file_fileset.get('method'),
            'files_filesets': 'files_filesets/' + self.file_accession
        }

        if self.validate:
            self.validate_doc(_props)

        self.writer.write(json.dumps(_props))
        self.writer.write('\n')

    def process_variant_chunk(self, chunk):
        rows_by_variant_id = []
        for row in chunk:
            chr, pos, ref, alt = row[5].split('_')
            try:
                variant_id = build_variant_id(chr, pos, ref, alt, 'GRCh38')
            except Exception as e:
                self.logger.warning(
                    f'Skipping row - unable to build variant id (chr={chr}, pos={pos}, ref={ref}, alt={alt}): {e}')
                continue
            rows_by_variant_id.append((variant_id, row))

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
        for variant_id, row in rows_by_variant_id:
            if variant_id not in loaded_variants:
                skipped_missing += 1
                continue
            self.write_edge(variant_id, row)

        if skipped_missing:
            self.logger.warning(
                f'Skipped {skipped_missing} row(s) - variant not found in variants collection')

    def write_edge(self, variant_id, row):
        region_chr, region_pos_start, region_pos_end = row[8].split(':')
        genomic_element_id = build_regulatory_region_id(
            region_chr, region_pos_start, region_pos_end, class_name=AFGRCAQtl.CLASS_NAME
        )

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
            'neg_log10_pvalue': log_pvalue,
            'p_value': pvalue,
            'beta': float(row[-2]),
            'source': AFGRCAQtl.SOURCE,
            'source_url': AFGRCAQtl.SOURCE_URL,
            'biosample_term': 'ontology_terms/' + AFGRCAQtl.ONTOLOGY_TERM_ID,
            'biological_context': AFGRCAQtl.ONTOLOGY_TERM_NAME,
            'name': AFGRCAQtl.EDGE_COLLECTION_NAME,
            'inverse_name': AFGRCAQtl.EDGE_COLLECTION_INVERSR_NAME,
            'method': self.file_fileset.get('method'),
            'class': self.file_fileset.get('class'),
            'files_filesets': 'files_filesets/' + self.file_accession
        }

        if self.validate:
            self.validate_doc(_props)

        self.writer.write(json.dumps(_props))
        self.writer.write('\n')

    def write_missing_variants(self, rows_by_variant_id, loaded_variants):
        for variant_id, row in rows_by_variant_id:
            if variant_id in loaded_variants or variant_id in self.written_variant_keys:
                continue
            self.written_variant_keys.add(variant_id)

            chr, pos, ref, alt = row[5].split('_')
            variant_props, skipped = load_variant(f'{chr}-{pos}-{ref}-{alt}')
            if variant_props:
                variant_props.update({
                    'source': AFGRCAQtl.SOURCE,
                    'source_url': AFGRCAQtl.SOURCE_URL,
                    'files_filesets': 'files_filesets/' + self.file_accession
                })
                if self.validate:
                    self.validate_doc(variant_props)
                self.writer.write(json.dumps(variant_props))
                self.writer.write('\n')
            elif skipped:
                self.logger.warning(
                    f"Invalid variant: {skipped['variant_id']} - {skipped['reason']}")
