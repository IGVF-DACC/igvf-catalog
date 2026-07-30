import csv
import hashlib
import json
import os
from typing import Optional

from adapters.base import BaseAdapter
from adapters.writer import Writer
from adapters.gene_validator import GeneValidator
from adapters.helpers import (
    CHR_MAP,
    bulk_query_variant_keys_by_identifier,
    get_file_fileset_by_accession_in_arangodb,
)

# Example row from variant_pathogenicity.tsv
# ClinVar Variation Id	chr	start	stop	Gene ID	HGNC Gene Symbol	Mondo Id	Disease	Mode of Inheritance	Assertion	Summary of interpretation	PubMed Articles	Evidence Repo Link	Retracted	Allele	HGVS Expressions	Allele Registry Id
# 586	12	102917130	102917130	ENSG00000171759	PAH	MONDO:0009861	phenylketonuria	Autosomal recessive inheritance	Pathogenic	PAH-specific ACMG/AMP criteria applied: PM2: gnomAD MAF=0.00002; PP4_Moderate: Seen in PKU patients. BH4 disorders ruled out. (PMID:2574002); PS3: <3% (PMID:9450897). PM3: Detected in trans with known pathogenic variants. In summary this variant meets criteria to be classified as pathogenic for phenylketonuria in an autosomal recessive manner based on the ACMG/AMP criteria applied as specified by the PAH Expert Panel: (PM2, PM3, PP4_Moderate, PS3). Updated to reflect new PVS1 recommendations.	\
# 2574002, 2574002, 9450897	https://erepo.genome.network/evrepo/ui/classification/CA114360/MONDO:0009861/006	FALSE	[T/A/C]	NM_000277.2:c.1A>G, NC_000012.12:g.102917130T>C, CM000674.2:g.102917130T>C, NC_000012.11:g.103310908T>C, CM000674.1:g.103310908T>C, NC_000012.10:g.101835038T>C, NG_008690.1:g.5473A>G, NG_008690.2:g.46281A>G, NM_000277.1:c.1A>G, XM_011538422.1:c.1A>G, NM_001354304.1:c.1A>G, XM_017019370.2:c.1A>G, NM_000277.3:c.1A>G, ENST00000307000.7:c.-147A>G, ENST00000546844.1:c.1A>G, ENST00000547319.1:n.312A>G, ENST00000549111.5:n.97A>G, ENST00000551337.5:c.1A>G, ENST00000551988.5:n.90A>G, ENST00000553106.5:c.1A>G, ENST00000635500.1:n.29-4232A>G, NM_000277.2(PAH):c.1A>G (p.Met1Val)	CA114360
#
# Variant mapping:
# 1) From each row's "HGVS Expressions", pick the GRCh38 genomic HGVS (NC_*:g.).
# 2) Bulk-query variants.hgvs in ArangoDB (retries with a space after the colon,
#    e.g. "NC_...:g." -> "NC_...: g.", for known DB formatting issues).
# 3) For rows still unmatched, bulk-query variants.ca_id using "Allele Registry Id"
#    (treat "-" as missing).
# 4) Per row: use HGVS matches if present, else ca_id matches; skip if neither.
#    Values are lists of variants._key (SPDI); emit one edge per key.


class ClinGen(BaseAdapter):
    ALLOWED_LABELS = ['variant_disease', 'variant_disease_gene']
    SOURCE = 'ClinGen'
    SOURCE_URL = 'https://search.clinicalgenome.org/kb/downloads'
    GRCH38_ACCESSIONS = set(CHR_MAP['GRCh38'].values())

    def __init__(self, filepath, label, writer: Optional[Writer] = None, validate=False, **kwargs):
        self.gene_validator = GeneValidator()
        super().__init__(filepath, label, writer, validate)
        self.file_accession = os.path.basename(filepath).split('.')[0]

    def _get_schema_type(self):
        """Return schema type."""
        return 'edges'

    def _get_collection_name(self):
        """Get collection based on label."""
        if self.label == 'variant_disease':
            return 'variants_diseases'
        elif self.label == 'variant_disease_gene':
            return 'variants_diseases_genes'

    @classmethod
    def extract_grch38_genomic_hgvs(cls, expressions):
        """Return canonical GRCh38 genomic HGVS from a comma-separated expression list."""
        if not expressions:
            return None
        for part in expressions.split(','):
            part = part.strip()
            if not part or ':' not in part:
                continue
            accession, rest = part.split(':', 1)
            rest = rest.lstrip()
            if accession in cls.GRCH38_ACCESSIONS and rest.startswith('g.'):
                return f'{accession}:{rest}'
        return None

    @staticmethod
    def normalize_identifier(value):
        value = (value or '').strip()
        if not value or value == '-':
            return None
        return value

    def load_variant_id_maps(self, rows):
        """Bulk-resolve catalog variant keys: HGVS first, then ca_id fallback."""
        hgvs_ids = set()
        ca_ids = set()
        for row in rows:
            hgvs = self.extract_grch38_genomic_hgvs(
                row.get('HGVS Expressions'))
            if hgvs:
                hgvs_ids.add(hgvs)
            ca_id = self.normalize_identifier(row.get('Allele Registry Id'))
            if ca_id:
                ca_ids.add(ca_id)

        self.hgvs_to_keys = bulk_query_variant_keys_by_identifier(
            hgvs_ids, check_by='hgvs') if hgvs_ids else {}

        unresolved_ca_ids = set()
        for row in rows:
            hgvs = self.extract_grch38_genomic_hgvs(
                row.get('HGVS Expressions'))
            if hgvs and hgvs in self.hgvs_to_keys:
                continue
            ca_id = self.normalize_identifier(row.get('Allele Registry Id'))
            if ca_id:
                unresolved_ca_ids.add(ca_id)

        self.ca_id_to_keys = bulk_query_variant_keys_by_identifier(
            unresolved_ca_ids, check_by='ca_id') if unresolved_ca_ids else {}

    def resolve_variant_keys(self, row):
        hgvs = self.extract_grch38_genomic_hgvs(row.get('HGVS Expressions'))
        if hgvs and hgvs in self.hgvs_to_keys:
            return self.hgvs_to_keys[hgvs]
        ca_id = self.normalize_identifier(row.get('Allele Registry Id'))
        if ca_id and ca_id in self.ca_id_to_keys:
            return self.ca_id_to_keys[ca_id]
        return []

    def parse(self):
        self.writer.add_tag('portal_accessions', self.file_accession)
        file_metadata = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        self.collection_class = file_metadata['class']
        self.method = file_metadata['method']

        with open(self.filepath, 'r') as clingen_file:
            rows = list(csv.DictReader(clingen_file))

        self.load_variant_id_maps(rows)

        unmatched = 0
        pmid_url = 'http://pubmed.ncbi.nlm.nih.gov/'

        for row in rows:
            variant_keys = self.resolve_variant_keys(row)
            if not variant_keys:
                unmatched += 1
                continue

            gene_id = row.get('Gene ID')
            is_valid_gene_id = self.gene_validator.validate(gene_id)
            if not is_valid_gene_id:
                continue

            disease_id = (row.get('Mondo Id') or '').replace(':', '_')
            assertion = row.get('Assertion')
            inheritance_mode = row.get('Mode of Inheritance')
            pmids_raw = row.get('PubMed Articles') or ''
            pmids = [
                pmid_url + pmid.strip()
                for pmid in pmids_raw.split(',')
                if pmid.strip()
            ]

            for variant_id in variant_keys:
                variant_disease_id = hashlib.sha256(
                    '_'.join([variant_id, disease_id]).encode()).hexdigest()

                if self.label == 'variant_disease':
                    props = {
                        '_key': variant_disease_id,
                        '_from': 'variants/' + variant_id,
                        '_to': 'ontology_terms/' + disease_id,
                        'gene_id': 'genes/' + gene_id,
                        'assertion': assertion,
                        'pmids': pmids,
                        'name': 'associated with',
                        'inverse_name': 'associated with',
                        'source': ClinGen.SOURCE,
                        'source_url': ClinGen.SOURCE_URL,
                        'class': self.collection_class,
                        'method': self.method,
                        'label': self.method,
                        'files_filesets': 'files_filesets/' + self.file_accession,
                    }
                    if self.validate:
                        self.validate_doc(props)
                    self.writer.write(json.dumps(props))
                    self.writer.write('\n')

                elif self.label == 'variant_disease_gene':
                    variant_disease_gene_id = hashlib.sha256(
                        '_'.join([variant_disease_id, gene_id]).encode()).hexdigest()

                    props = {
                        '_key': variant_disease_gene_id,
                        '_from': 'variants_diseases/' + variant_disease_id,
                        '_to': 'genes/' + gene_id,
                        'name': 'associated with',
                        'inverse_name': 'associated with',
                        'inheritance_mode': inheritance_mode,
                        'source': ClinGen.SOURCE,
                        'source_url': ClinGen.SOURCE_URL,
                        'class': self.collection_class,
                        'method': self.method,
                        'label': self.method,
                        'files_filesets': 'files_filesets/' + self.file_accession,
                    }
                    if self.validate:
                        self.validate_doc(props)
                    self.writer.write(json.dumps(props))
                    self.writer.write('\n')

        if unmatched:
            self.logger.info(
                f'{unmatched} ClinGen rows skipped (no catalog variant match via hgvs/ca_id)')

        self.gene_validator.log()
