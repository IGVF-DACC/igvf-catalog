import csv
import gzip
import json
import os
from typing import Optional

import requests

from adapters.base import BaseAdapter
from adapters.helpers import bulk_query_coding_variants_from_spdi_in_arangodb, get_file_fileset_by_accession_in_arangodb
from adapters.writer import Writer

# Vidal lab semi-quantitative Y2H (semi-qY2H) coding variant perturbation assay
# https://data.igvf.org/analysis-sets/IGVFDS9876GIEQ/

# Example rows from IGVFFI1611ZIBI.tsv.gz (semi-qY2H edge-perturbation scores):
# spdi	symbol	ensembl_gene_id	ccsb_mutation_id	CCSB_referenece_orf_id	hgvs_orf	hgvs_protein	allele_type	interactor_id	interactor_symbol	interactor_ensembl_gene_id	consensus_score	wt_consensus_score	log2fc
# 	ACSF3	ENSG00000176715		CCSBORF71337			reference	CCSBORF54668	KRT40	ENSG00000204889	311.16	311.16	0
# NC_000016.10:89102664:C:T	ACSF3	ENSG00000176715	CCSBVarC003578	CCSBORF71337	728C>T	ENSP00000320646.4:p.Pro243Leu	variant	CCSBORF54668	KRT40	ENSG00000204889	26.99	311.16	-3.48

# Example rows from IGVFFI0709BESF.tsv.gz (semi-qY2H edgotyping scores):
# spdi	symbol	ensembl_gene_id	ccsb_mutation_id	CCSB_referenece_orf_id	hgvs_orf	hgvs_protein	norm_dist_rms
# NC_000016.10:89102664:C:T	ACSF3	ENSG00000176715	CCSBVarC003578	CCSBORF71337	728C>T	ENSP00000320646.4:p.Pro243Leu	0.3868541857467328


class SemiQY2H(BaseAdapter):
    ALLOWED_LABELS = ['proteins_proteins', 'coding_variants_phenotypes']
    SOURCE = 'IGVF'
    IGVF_API = 'https://api.data.igvf.org'
    ORF_SEARCH_CHUNK_SIZE = 100

    PROTEIN_BINDING_TERM = 'GO_0005515'  # protein binding
    PROTEINS_PROTEINS_EDGE_NAME = 'physically interacts with'
    CODING_VARIANTS_PHENOTYPES_EDGE_NAME = 'mutational effect'
    CODING_VARIANTS_PHENOTYPES_EDGE_INVERSE_NAME = 'altered due to mutation'
    COLLECTION_LABEL = 'semi-quantitative yeast two-hybrid'

    def __init__(self, filepath, label='proteins_proteins', writer: Optional[Writer] = None, validate=False, **kwargs):
        self.file_accession = os.path.basename(filepath).split('.')[0]
        self.source_url = 'https://data.igvf.org/tabular-files/' + self.file_accession
        super().__init__(filepath, label, writer, validate)

    def _get_schema_type(self):
        """Return schema type."""
        return 'edges'

    def _get_collection_name(self):
        """Get collection name."""
        return self.label

    @staticmethod
    def parse_hgvs_protein(hgvs_protein):
        # e.g. 'ENSP00000320646.4:p.Pro243Leu' -> ('ENSP00000320646', 'p.Pro243Leu')
        protein_id, hgvsp = hgvs_protein.split(':')
        return protein_id.split('.')[0], hgvsp

    def get_interactor_protein_map(self, orf_ids):
        # bulk lookup of interactor open reading frame accession -> ENSP protein_id (no version)
        # via the portal search API, chunked to keep query URLs a reasonable length
        protein_map = {}
        orf_ids = sorted(orf_ids)
        for i in range(0, len(orf_ids), self.ORF_SEARCH_CHUNK_SIZE):
            chunk = orf_ids[i:i + self.ORF_SEARCH_CHUNK_SIZE]
            query = '&'.join(f'orf_id={orf_id}' for orf_id in chunk)
            url = f'{self.IGVF_API}/search/?type=OpenReadingFrame&{query}&field=orf_id&field=protein_id&format=json&limit=all'
            response = requests.get(url).json()
            for result in response.get('@graph', []):
                protein_id = result.get('protein_id')
                if protein_id:
                    protein_map[result['orf_id']] = protein_id.split('.')[0]

        missing = set(orf_ids) - set(protein_map.keys())
        if missing:
            self.logger.warning(
                f'No protein_id found for {len(missing)} interactor ORFs: {sorted(missing)}')
        return protein_map

    def get_coding_variant_map(self, rows):
        triples = [
            (row['spdi'], *self.parse_hgvs_protein(row['hgvs_protein']))
            for row in rows
        ]
        return bulk_query_coding_variants_from_spdi_in_arangodb(triples)

    def parse(self):
        self.writer.add_tag('portal_accessions', self.file_accession)
        file_fileset = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        if file_fileset is None:
            self.logger.warning(
                f'file_fileset not found for {self.file_accession}, file_fileset fields will be None')
            file_fileset = {}

        if self.label == 'proteins_proteins':
            self.parse_proteins_proteins(file_fileset)
        else:
            self.parse_coding_variants_phenotypes(file_fileset)

    def parse_proteins_proteins(self, file_fileset):
        with gzip.open(self.filepath, 'rt') as edge_file:
            rows = [row for row in csv.DictReader(
                edge_file, delimiter='\t') if row['allele_type'] == 'variant']

        interactor_protein_map = self.get_interactor_protein_map(
            {row['interactor_id'] for row in rows})
        coding_variant_map = self.get_coding_variant_map(rows)

        for row in rows:
            interactor_protein_id = interactor_protein_map.get(
                row['interactor_id'])
            if interactor_protein_id is None:
                self.logger.warning(
                    f"Skipping {row['ccsb_mutation_id']}: no protein_id for interactor {row['interactor_id']}")
                continue

            protein_id, hgvsp = self.parse_hgvs_protein(row['hgvs_protein'])
            coding_variant_keys = coding_variant_map.get(
                (row['spdi'], protein_id, hgvsp))
            if not coding_variant_keys:
                self.logger.warning(
                    f"Skipping {row['ccsb_mutation_id']}: no coding variant found for {row['spdi']}, {protein_id}, {hgvsp}")
                continue

            _props = {
                '_key': row['ccsb_mutation_id'] + '_' + row['interactor_id'],
                '_from': 'proteins/' + protein_id,
                '_to': 'proteins/' + interactor_protein_id,
                'name': self.PROTEINS_PROTEINS_EDGE_NAME,
                'inverse_name': self.PROTEINS_PROTEINS_EDGE_NAME,
                'coding_variants': 'coding_variants/' + coding_variant_keys[0],
                'consensus_score': float(row['consensus_score']),
                'wt_consensus_score': float(row['wt_consensus_score']),
                'log2FC': float(row['log2fc']),
                'molecular_function': 'ontology_terms/' + self.PROTEIN_BINDING_TERM,
                'method': file_fileset.get('method'),
                'label': self.COLLECTION_LABEL,
                'class': file_fileset.get('class'),
                'source': self.SOURCE,
                'source_url': self.source_url,
                'files_filesets': 'files_filesets/' + self.file_accession
            }
            if self.validate:
                self.validate_doc(_props)
            self.writer.write(json.dumps(_props))
            self.writer.write('\n')

    def parse_coding_variants_phenotypes(self, file_fileset):
        with gzip.open(self.filepath, 'rt') as edgotyping_file:
            rows = list(csv.DictReader(edgotyping_file, delimiter='\t'))

        coding_variant_map = self.get_coding_variant_map(rows)

        for row in rows:
            protein_id, hgvsp = self.parse_hgvs_protein(row['hgvs_protein'])
            coding_variant_keys = coding_variant_map.get(
                (row['spdi'], protein_id, hgvsp))
            if not coding_variant_keys:
                self.logger.warning(
                    f"Skipping {row['ccsb_mutation_id']}: no coding variant found for {row['spdi']}, {protein_id}, {hgvsp}")
                continue
            coding_variant_key = coding_variant_keys[0]

            _props = {
                '_key': '_'.join([coding_variant_key, self.PROTEIN_BINDING_TERM, self.file_accession]),
                '_from': 'coding_variants/' + coding_variant_key,
                '_to': 'ontology_terms/' + self.PROTEIN_BINDING_TERM,
                'name': self.CODING_VARIANTS_PHENOTYPES_EDGE_NAME,
                'inverse_name': self.CODING_VARIANTS_PHENOTYPES_EDGE_INVERSE_NAME,
                'norm_dist_rms': float(row['norm_dist_rms']),
                'method': file_fileset.get('method'),
                'label': self.COLLECTION_LABEL,
                'class': file_fileset.get('class'),
                'source': self.SOURCE,
                'source_url': self.source_url,
                'files_filesets': 'files_filesets/' + self.file_accession
            }
            if self.validate:
                self.validate_doc(_props)
            self.writer.write(json.dumps(_props))
            self.writer.write('\n')
