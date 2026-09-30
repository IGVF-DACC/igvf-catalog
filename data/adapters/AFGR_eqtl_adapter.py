import csv
import gzip
import hashlib
import json
from typing import Optional
import os
from adapters.base import BaseAdapter
from adapters.helpers import (
    build_variant_id,
    bulk_check_variants_in_arangodb,
    get_file_fileset_by_accession_in_arangodb,
    load_variant,
)
from adapters.writer import Writer
from adapters.gene_validator import GeneValidator

# Example row from sorted.dist.hwe.af.AFR_META.eQTL.nominal.hg38a.txt.gz
# chr	snp_pos	snp_pos2	ref	alt	effect_af_eqtl	variant	feature	log10p	pvalue	beta	se	qstat	df	p_het	p_hwe	dist_start	dist_end	geneSymbol	geneType
# 1	16103	16103	T	G	0.0336427	1_16103_T_G	ENSG00000187583.10	0.1944867	0.6390183	0.242489	0.516955	NA	1.0	NA	1.000000	-950394	-959762	PLEKHN1	protein_coding


class AFGREQtl(BaseAdapter):
    ALLOWED_LABELS = ['AFGR_eqtl', 'variants']
    CHUNK_SIZE = 6500
    SOURCE = 'AFGR'
    SOURCE_URL = 'https://github.com/smontgomlab/AFGR'
    BIOLOGICAL_CONTEXT = 'lymphoblastoid cell line'
    ONTOLOGY_TERM = 'EFO_0005292'  # lymphoblastoid cell line

    def __init__(self, filepath, label='AFGR_eqtl', writer: Optional[Writer] = None, validate=False, **kwargs):
        # Initialize base adapter first
        super().__init__(filepath, label, writer, validate)

        # Adapter-specific initialization
        self.gene_validator = GeneValidator()
        self.file_accession = os.path.basename(filepath).split('.')[0]
        self.written_variant_keys = set()

    def _get_schema_type(self):
        """Return schema type based on label."""
        return 'nodes' if self.label == 'variants' else 'edges'

    def _get_collection_name(self):
        """Get collection based on label."""
        return 'variants' if self.label == 'variants' else 'variants_genes'

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

            chunk = []
            for row in qtl_csv:
                chunk.append(row)
                if len(chunk) >= AFGREQtl.CHUNK_SIZE:
                    self.process_chunk(chunk)
                    chunk = []
            if chunk:
                self.process_chunk(chunk)

        if self.label == 'AFGR_eqtl':
            self.gene_validator.log()

    def process_chunk(self, chunk):
        rows_by_variant_id = []
        for row in chunk:
            chr, pos, ref, alt = row[6].split('_')

            # skipping deletions for now (can't be mapped to a spdi using current ga4gh lib)
            if alt == '*':
                continue

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
        gene_id = row[7].split('.')[0]
        is_gene_id_valid = self.gene_validator.validate(gene_id)
        if not is_gene_id_valid:
            return

        chr = row[0]

        # Include file_accession so distinct population/dataset files
        # (e.g. AFR vs EUR meta) do not collide on the same edge key.
        variants_genes_id = hashlib.sha256(
            (variant_id + '_' + gene_id + '_' + self.file_accession).encode()).hexdigest()

        _id = variants_genes_id
        _source = 'variants/' + variant_id
        _target = 'genes/' + gene_id

        _props = {
            '_key': _id,
            '_from': _source,
            '_to': _target,
            'biological_context': AFGREQtl.BIOLOGICAL_CONTEXT,
            'chr': 'chr' + chr,
            # The three numeric values are not loaded as long data type somehow, though in schema it's labeled as int
            # Manually changed data type from double to long in header file before importing into Arangodb
            'neg_log10_pvalue': float(row[8]),  # MAX=616
            'p_value': float(row[9]),
            'effect_size': float(row[10]),
            'class': self.file_fileset.get('class'),
            'method': self.file_fileset.get('method'),
            'label': 'eQTL',
            'source': AFGREQtl.SOURCE,
            'source_url': AFGREQtl.SOURCE_URL,
            'name': 'modulates expression of',
            'inverse_name': 'expression modulated by',
            'biological_process': 'ontology_terms/GO_0010468',
            'biosample_term': 'ontology_terms/' + AFGREQtl.ONTOLOGY_TERM,
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

            chr, pos, ref, alt = row[6].split('_')
            variant_props, skipped = load_variant(f'{chr}-{pos}-{ref}-{alt}')
            if variant_props:
                variant_props.update({
                    'source': AFGREQtl.SOURCE,
                    'source_url': AFGREQtl.SOURCE_URL,
                    'files_filesets': 'files_filesets/' + self.file_accession
                })
                if self.validate:
                    self.validate_doc(variant_props)
                self.writer.write(json.dumps(variant_props))
                self.writer.write('\n')
            elif skipped:
                self.logger.warning(
                    f"Invalid variant: {skipped['variant_id']} - {skipped['reason']}")
