import csv
import json
import hashlib
from typing import Optional

from adapters.base import BaseAdapter
from adapters.helpers import (
    build_variant_id,
    bulk_check_variants_in_arangodb,
    load_variant,
)
from adapters.writer import Writer

# Example TOPLD input data file:

# SNP1,SNP2,Uniq_ID_1,Uniq_ID_2,R2,Dprime,+/-corr
# 5031031,5032123,5031031:C:T,5032123:G:A,0.251,0.888,+
# 5031031,5063457,5031031:C:T,5063457:G:C,0.443,0.832,+

# Example TOPLD annotation file:

# Position,rsID,MAF,REF,ALT,Uniq_ID,VEP_ensembl_Gene_Name,VEP_ensembl_Consequence,CADD_phred,fathmm_XF_coding_or_noncoding,FANTOM5_enhancer_expressed_tissue_cell
# 5031031,rs1441313282,0.010486891385767793,C,T,5031031:C:T,FP565260.3|FP565260.3|FP565260.3|FP565260.3|FP565260.3,"intron_variant|intron_variant|intron_variant|intron_variant,NMD_transcript_variant|intron_variant",2.135,.,.


class TopLD(BaseAdapter):
    ALLOWED_LABELS = ['topld_linkage_disequilibrium', 'variants']
    CHUNK_SIZE = 6500
    SOURCE = 'TopLD'
    SOURCE_URL = 'http://topld.genetics.unc.edu/'

    def __init__(self, filepath, annotation_filepath, chr, ancestry='SAS', label='topld_linkage_disequilibrium', writer: Optional[Writer] = None, validate=False, **kwargs):
        self.annotation_filepath = annotation_filepath
        self.chr = chr
        self.ancestry = ancestry
        self.written_variant_keys = set()

        super().__init__(filepath, label, writer, validate)

    def _get_schema_type(self):
        """Return schema type based on label."""
        return 'nodes' if self.label == 'variants' else 'edges'

    def _get_collection_name(self):
        """Get collection based on label."""
        return 'variants' if self.label == 'variants' else 'variants_variants'

    def process_annotations(self):
        self.logger.info('Processing annotations...')
        self.ids = {}
        with open(self.annotation_filepath, 'r') as annotations:
            annotations_csv = csv.reader(annotations)

            next(annotations_csv)

            for row in annotations_csv:
                self.ids[row[0]] = {
                    'rsid': row[1],
                    'variant_id': 'variants/' + build_variant_id(
                        self.chr,
                        row[0],
                        row[3],
                        row[4]
                    )
                }

    def parse(self):
        if self.label == 'variants':
            self.process_variants()
            return

        self.process_annotations()

        self.logger.info('Processing data...')

        chunk = []
        for line in open(self.filepath, 'r'):
            row = line.split(',')

            if row[0] == 'SNP1':
                continue

            chunk.append(row)
            if len(chunk) >= TopLD.CHUNK_SIZE:
                self.process_chunk(chunk)
                chunk = []
        if chunk:
            self.process_chunk(chunk)

    def process_chunk(self, chunk):
        pending_edges = []
        for row in chunk:
            _from = self.ids[row[0]]['variant_id']
            _to = self.ids[row[1]]['variant_id']
            pending_edges.append((_from, _to, row))

        variant_ids = {edge_id.replace('variants/', '')
                       for _from, _to, _ in pending_edges
                       for edge_id in (_from, _to)}
        loaded_variants = bulk_check_variants_in_arangodb(
            list(variant_ids), check_by='_key')

        skipped_missing = 0
        for _from, _to, row in pending_edges:
            if _from.replace('variants/', '') not in loaded_variants or \
                    _to.replace('variants/', '') not in loaded_variants:
                skipped_missing += 1
                continue
            self.write_edge(_from, _to, row)

        if skipped_missing:
            self.logger.warning(
                f'Skipped {skipped_missing} row(s) - variant not found in variants collection')

    def write_edge(self, _from, _to, row):
        variant_1_base_pair = ':'.join(row[2].split(':')[1:3])
        variant_2_base_pair = ':'.join(row[3].split(':')[1:3])

        key = _from + '_' + variant_1_base_pair + '_' + _to + \
            '_' + variant_2_base_pair + '_' + self.ancestry
        key = key.replace('variants/', '')
        if len(key) >= 254:
            key = hashlib.sha256(key.encode()).hexdigest()

        props = {
            '_from': _from,
            '_to': _to,
            '_key': key,
            'chr': self.chr,
            'negated': row[6] == '+',
            'variant_1_base_pair': variant_1_base_pair,
            'variant_2_base_pair': variant_2_base_pair,
            'variant_1_rsid': self.ids[row[0]]['rsid'],
            'variant_2_rsid': self.ids[row[1]]['rsid'],
            'r2': float(row[4]),
            'd_prime': float(row[5]),
            'ancestry': self.ancestry,
            'label': 'linkage disequilibrium',
            'name': 'correlated with',
            'inverse_name': 'correlated with',
            'source': TopLD.SOURCE,
            'source_url': TopLD.SOURCE_URL
        }

        if self.validate:
            self.validate_doc(props)

        self.writer.write(json.dumps(props))
        self.writer.write('\n')

    def process_variants(self):
        with open(self.annotation_filepath, 'r') as annotations:
            annotations_csv = csv.reader(annotations)
            next(annotations_csv)

            chunk = []
            for row in annotations_csv:
                chunk.append(row)
                if len(chunk) >= TopLD.CHUNK_SIZE:
                    self.process_variant_chunk(chunk)
                    chunk = []
            if chunk:
                self.process_variant_chunk(chunk)

    def process_variant_chunk(self, chunk):
        rows_by_variant_id = []
        for row in chunk:
            pos, ref, alt = row[0], row[3], row[4]
            try:
                variant_id = build_variant_id(self.chr, pos, ref, alt)
            except Exception as e:
                self.logger.warning(
                    f'Skipping row - unable to build variant id (chr={self.chr}, pos={pos}, ref={ref}, alt={alt}): {e}')
                continue
            rows_by_variant_id.append((variant_id, row))

        if not rows_by_variant_id:
            return

        loaded_variants = bulk_check_variants_in_arangodb(
            list({variant_id for variant_id, _ in rows_by_variant_id}),
            check_by='_key',
        )
        self.write_missing_variants(rows_by_variant_id, loaded_variants)

    def write_missing_variants(self, rows_by_variant_id, loaded_variants):
        for variant_id, row in rows_by_variant_id:
            if variant_id in loaded_variants or variant_id in self.written_variant_keys:
                continue
            self.written_variant_keys.add(variant_id)

            pos, ref, alt = row[0], row[3], row[4]
            variant_props, skipped = load_variant(
                f'{self.chr}-{pos}-{ref}-{alt}')
            if variant_props:
                variant_props.update({
                    'source': TopLD.SOURCE,
                    'source_url': TopLD.SOURCE_URL,
                })
                if self.validate:
                    self.validate_doc(variant_props)
                self.writer.write(json.dumps(variant_props))
                self.writer.write('\n')
            elif skipped:
                self.logger.warning(
                    f"Invalid variant: {skipped['variant_id']} - {skipped['reason']}")
