import csv
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
from adapters.protein_map import ProteinMap

# Example rows from pQTL file (Supplementary Table 9)
# Variant ID (CHROM:GENPOS (hg37):A0:A1:imp:v1)	CHROM	GENPOS (hg38)	Region ID	Region Start	Region End	MHC	UKBPPP ProteinID	Assay Target	Target UniProt	rsID	A1FREQ (discovery)	BETA (discovery, wrt. A1)	SE (discovery)	log10(p) (discovery)	A1FREQ (replication)	BETA (replication)	SE (replication)	log10(p) (replication)	cis/trans	cis gene	Bioinfomatic annotated gene	Ensembl gene ID	Annotated gene consequence	Biotype	Distance to gene	CADD_phred	SIFT	PolyPhen	PHAST Phylop_score	FitCons_score	IMPACT
# 2:27730940:T:C:imp:v1	2	27508073	975	26263266	29121418	0	A1BG:P04217:OID30771:v1	A1BG	P04217	rs1260326	0.6084	-0.137	0.007	79.2	0.6306	-0.105	0.010	23.9	trans	-	GCKR	ENSG00000084734	missense_variant,splice_region_variant	protein_coding	0		T	Benign	408	0.553676	MODERATE


class pQTL(BaseAdapter):

    SOURCE = 'UKB'
    SOURCE_URL = 'https://metabolomips.org/ukbbpgwas/'
    BIOLOGICAL_CONTEXT = 'blood plasma'
    BIOSAMPLE_TERM = 'UBERON_0001969'
    ALLOWED_LABELS = ['variant_protein', 'variants']
    CHUNK_SIZE = 6500

    def __init__(self, filepath, label='variant_protein', writer: Optional[Writer] = None, validate=False, **kwargs):
        self.gene_validator = GeneValidator()
        if label == 'variant_protein':
            self.protein_map = ProteinMap(organism='Homo sapiens')
        super().__init__(filepath, label, writer, validate)
        self.file_accession = os.path.basename(filepath).split('.')[0]
        self.written_variant_keys = set()

    def _get_schema_type(self):
        """Return schema type based on label."""
        return 'nodes' if self.label == 'variants' else 'edges'

    def _get_collection_name(self):
        """Get collection name based on label."""
        return 'variants' if self.label == 'variants' else 'variants_proteins'

    def parse(self):
        self.file_fileset = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)

        self.writer.add_tag('portal_accessions', self.file_accession)
        file_set_accession = self.file_fileset.get('file_set_id')
        if file_set_accession:
            self.writer.add_tag('portal_accessions', file_set_accession)
        self.collection_class = self.file_fileset['class']
        self.method = self.file_fileset['method']

        with open(self.filepath, 'r') as pqtl_file:
            pqtl_csv = csv.reader(pqtl_file)
            next(pqtl_csv)
            chunk = []
            for row in pqtl_csv:
                chunk.append(row)
                if len(chunk) >= pQTL.CHUNK_SIZE:
                    self.process_chunk(chunk)
                    chunk = []
            if chunk:
                self.process_chunk(chunk)

        if self.label == 'variant_protein':
            self.protein_map.log(self.logger)
            self.gene_validator.log()

    def process_chunk(self, chunk):
        rows_by_variant_id = []
        for row in chunk:
            chr, pos, ref, alt = self._variant_fields(row)
            try:
                variant_id = build_variant_id(chr, pos, ref, alt)
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

    @staticmethod
    def _variant_fields(row):
        chr = row[1]
        if chr == '23':
            chr = 'X'
        if chr == '24':
            chr = 'Y'
        pos = row[2]  # 1-based coordinates
        ref, alt = row[0].split(':')[2:4]
        return chr, pos, ref, alt

    def write_edges(self, variant_id, row):
        # a few rows have multiple proteins: e.g. P0DUB6,P0DTE7,P0DTE8
        protein_ids = row[9].split(',')

        gene_id = row[22] if row[22] and row[22] != '-' else None
        if gene_id:
            is_valid_gene_id = self.gene_validator.validate(gene_id)
            if not is_valid_gene_id:
                gene_id = None
        for protein_id in protein_ids:
            ensembl_ids = self.protein_map.get(protein_id)
            if ensembl_ids is None:
                continue
            for ensembl_id in ensembl_ids:
                _id = variant_id + '_' + ensembl_id + '_' + pQTL.SOURCE
                _source = 'variants/' + variant_id
                _target = 'proteins/' + ensembl_id
                _props = {
                    '_key': _id,
                    '_from': _source,
                    '_to': _target,
                    'rsid': row[10] if row[10] != '-' else None,
                    # 'variant_'
                    'label': self.method,
                    'class': self.collection_class,
                    'method': self.method,
                    'neg_log10_pvalue': float(row[14]),
                    'beta': float(row[12]),  # i.e. effect size
                    'se': float(row[13]),
                    'regulatory_type': row[19],  # cis/trans
                    'gene': 'genes/' + gene_id if gene_id else None,
                    'gene_consequence': row[23] if row[23] else None,
                    'biological_context': pQTL.BIOLOGICAL_CONTEXT,
                    'biosample_term': f'ontology_terms/{pQTL.BIOSAMPLE_TERM}',
                    'files_filesets': 'files_filesets/' + self.file_accession,
                    'source': pQTL.SOURCE,
                    'source_url': pQTL.SOURCE_URL,
                    'name': 'associated with levels of',
                    'inverse_name': 'level associated with'
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

            chr, pos, ref, alt = self._variant_fields(row)
            variant_props, skipped = load_variant(f'{chr}-{pos}-{ref}-{alt}')
            if variant_props:
                variant_props.update({
                    'source': pQTL.SOURCE,
                    'source_url': pQTL.SOURCE_URL,
                    'files_filesets': 'files_filesets/' + self.file_accession
                })
                if self.validate:
                    self.validate_doc(variant_props)
                self.writer.write(json.dumps(variant_props))
                self.writer.write('\n')
            elif skipped:
                self.logger.warning(
                    f"Invalid variant: {skipped['variant_id']} - {skipped['reason']}")
