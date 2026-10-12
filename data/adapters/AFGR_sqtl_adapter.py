import csv
import gzip
import hashlib
import json
import pickle
from math import log10
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


# sorted.all.AFR.Meta.sQTL.genPC.nominal.maf05.mvmeta.fe.txt.gz
# chr	pos	ref	alt	snp	feature	beta	se	zstat	p	95pct_ci_lower	95pct_ci_upper	qstat	df	p_het
# chr1	88338	G	A	1_88338_G_A	1:187577:187755:clu_2352	0.0723108199416329	0.0685894841949755	1.05425519363987	0.291766096608984	-0.0621220987986983	0.206743738681964	1.23511015771854	5	0.941465002419174


class AFGRSQtl(BaseAdapter):
    ALLOWED_LABELS = ['AFGR_sqtl', 'variants']
    CHUNK_SIZE = 6500
    SOURCE = 'AFGR'
    SOURCE_URL = 'https://github.com/smontgomlab/AFGR'
    INTRON_GENE_MAPPING_PATH = './data_loading_support_files/AFGR/AFGR_sQTL_intron_genes.pkl'
    BIOLOGICAL_CONTEXT = 'lymphoblastoid cell line'
    ONTOLOGY_TERM = 'EFO_0005292'  # lymphoblastoid cell line
    MAX_LOG10_PVALUE = 400  # set the same value as gtex qtl

    def __init__(self, filepath, label='AFGR_sqtl', writer: Optional[Writer] = None, validate=False, **kwargs):
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
        self.load_intron_gene_mapping()

        with gzip.open(self.filepath, 'rt') as qtl_file:
            qtl_csv = csv.reader(qtl_file, delimiter='\t')
            next(qtl_csv)

            chunk = []
            for row in qtl_csv:
                chunk.append(row)
                if len(chunk) >= AFGRSQtl.CHUNK_SIZE:
                    self.process_chunk(chunk)
                    chunk = []
            if chunk:
                self.process_chunk(chunk)

        if self.label == 'AFGR_sqtl':
            self.gene_validator.log()

    def process_chunk(self, chunk):
        rows_by_variant_id = []
        for row in chunk:
            chr, pos, ref, alt = row[4].split('_')

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
            self.write_edges(variant_id, row)

        if skipped_missing:
            self.logger.warning(
                f'Skipped {skipped_missing} row(s) - variant not found in variants collection')

    def write_edges(self, variant_id, row):
        chr, _pos, _ref, _alt = row[4].split('_')
        intron_id = row[5]
        gene_ids = self.intron_gene_mapping.get(intron_id)
        if gene_ids is None:
            self.logger.warning(f'no gene mapping for {intron_id}')
            return

        pvalue = float(row[9])
        if pvalue == 0:
            log_pvalue = AFGRSQtl.MAX_LOG10_PVALUE
        else:
            log_pvalue = -1 * log10(pvalue)

        for gene_id in gene_ids:
            is_valid_gene_id = self.gene_validator.validate(gene_id)
            if not is_valid_gene_id:
                continue
            variants_genes_id = hashlib.sha256(
                (variant_id + '_' + intron_id + '_' + gene_id).encode()).hexdigest()

            _id = variants_genes_id
            _source = 'variants/' + variant_id
            _target = 'genes/' + gene_id

            _props = {
                '_key': _id,
                '_from': _source,
                '_to': _target,
                'biological_context': AFGRSQtl.BIOLOGICAL_CONTEXT,
                'chr': 'chr' + chr,
                'neg_log10_pvalue': log_pvalue,
                'p_value': pvalue,
                'effect_size': float(row[6]),
                'class': self.file_fileset.get('class'),
                'method': self.file_fileset.get('method'),
                'label': 'spliceQTL',
                'intron_chr': 'chr' + intron_id.split(':')[0],
                'intron_start': int(intron_id.split(':')[1]),
                'intron_end': int(intron_id.split(':')[2]),
                'source': AFGRSQtl.SOURCE,
                'source_url': AFGRSQtl.SOURCE_URL,
                'name': 'modulates splicing of',
                'inverse_name': 'splicing modulated by',
                'biological_process': 'ontology_terms/GO_0043484',
                'biosample_term': 'ontology_terms/' + AFGRSQtl.ONTOLOGY_TERM,
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

            chr, pos, ref, alt = row[4].split('_')
            variant_props, skipped = load_variant(f'{chr}-{pos}-{ref}-{alt}')
            if variant_props:
                variant_props.update({
                    'source': AFGRSQtl.SOURCE,
                    'source_url': AFGRSQtl.SOURCE_URL,
                    'files_filesets': 'files_filesets/' + self.file_accession
                })
                if self.validate:
                    self.validate_doc(variant_props)
                self.writer.write(json.dumps(variant_props))
                self.writer.write('\n')
            elif skipped:
                self.logger.warning(
                    f"Invalid variant: {skipped['variant_id']} - {skipped['reason']}")

    def load_intron_gene_mapping(self):
        # key: intron_id (e.g. 1:187577:187755:clu_2352); value: gene ensembl id
        self.intron_gene_mapping = {}
        with open(AFGRSQtl.INTRON_GENE_MAPPING_PATH, 'rb') as mapfile:
            self.intron_gene_mapping = pickle.load(mapfile)
