import csv
import gzip
import json
from typing import Optional
from urllib.parse import urljoin

import requests

from adapters.base import BaseAdapter
from adapters.helpers import (
    bulk_check_variants_in_arangodb,
    load_variant,
    get_file_fileset_by_accession_in_arangodb,
)
from adapters.writer import Writer

# Variant-level CRISPR screens linking variants to cellular phenotypes.
#
# IGVFFI2014OOZP (Sherwood / IGVFDS2873IRMJ) – LDL-C uptake (NTR:0001118); prime editing
#   variant_id is SPDI (0-based); preferred_assay_titles: CRISPR FACS screen.
# IGVFFI6803HZJG (Sherwood / IGVFDS9278NUAZ) – LDL-C uptake (NTR:0001118); prime editing
#   variant_id is SPDI (0-based); preferred_assay_titles: CRISPR FACS screen.
#
# NTR phenotype terms are not loaded by the standard ontology adapter, so this
# adapter also writes ontology_terms for NTR phenotypes (e.g. NTR_0001118).

IGVF_API = 'https://api.data.igvf.org/'
IGVF_PHENOTYPE_TERM_URL = 'https://data.igvf.org/phenotype-terms/'


class CRISPRVariantPhenotype(BaseAdapter):
    ALLOWED_LABELS = ['variant', 'variant_phenotype', 'ontology_term']
    SOURCE = 'IGVF'
    COLLECTION_LABEL = 'variant effect on phenotype'
    CHUNK_SIZE = 6500

    # Accession -> phenotype + column layout.
    FILE_CONFIG = {
        'IGVFFI2014OOZP': {
            'phenotype_term': 'NTR_0001118',
            'phenotype_name': 'LDL-C uptake',
            'variant_id_col': 'variant_id',
            'variant_type_col': 'target_group',
            'variant_type_value': 'Variant',
            'effect_size_col': 'mu',
            'z_score_col': 'mu_z',
            'num_guides_col': 'n_guides',
            'ci_lower_col': 'CI[0.025',
            'ci_upper_col': '0.975]',
        },
        'IGVFFI6803HZJG': {
            'phenotype_term': 'NTR_0001118',
            'phenotype_name': 'LDL-C uptake',
            'variant_id_col': 'variant_id',
            'variant_type_col': 'target_group',
            'variant_type_value': 'Variant',
            'effect_size_col': 'mu_adj',
            'z_score_col': 'mu_z_adj',
            'num_guides_col': 'n_guides',
            'edit_rate_mean_col': 'edit_rate_mean',
            'ci_lower_col': 'CI[0.025',
            'ci_upper_col': '0.975]',
        },
    }

    def __init__(self, filepath, label, source_url, writer: Optional[Writer] = None, validate=False, **kwargs):
        self.source_url = source_url.rstrip('/') + '/'
        self.file_accession = self.source_url.rstrip('/').split('/')[-1]
        if self.file_accession not in self.FILE_CONFIG:
            raise ValueError(
                f'Unsupported file accession {self.file_accession}. '
                f'Expected one of: {", ".join(sorted(self.FILE_CONFIG))}'
            )
        self.file_config = self.FILE_CONFIG[self.file_accession]
        self.phenotype_term = self.file_config['phenotype_term']

        if label != 'ontology_term':
            file_fileset = get_file_fileset_by_accession_in_arangodb(
                self.file_accession)
            self.method = file_fileset['method']
            self.simple_sample_summaries = file_fileset['simple_sample_summaries']
            self.biosample_term = file_fileset['samples'][0]
            self.treatments_term_ids = file_fileset.get('treatments_term_ids')
            self.crispr_modality = file_fileset.get('crispr_modality')
            self.edge_class = file_fileset.get('class')

        super().__init__(filepath, label, writer, validate)

    def _get_schema_type(self):
        if self.label in ('variant', 'ontology_term'):
            return 'nodes'
        return 'edges'

    def _get_collection_name(self):
        if self.label == 'variant':
            return 'variants'
        if self.label == 'ontology_term':
            return 'ontology_terms'
        return 'variants_phenotypes'

    @staticmethod
    def _open_file(filepath):
        if filepath.endswith('.gz'):
            return gzip.open(filepath, 'rt')
        return open(filepath, 'r')

    @staticmethod
    def _optional_float(row, col):
        if not col or col not in row:
            return None
        value = row[col]
        if value is None or str(value).strip() == '':
            return None
        return float(value)

    @staticmethod
    def _optional_int(row, col):
        if not col or col not in row:
            return None
        value = row[col]
        if value is None or str(value).strip() == '':
            return None
        return int(float(value))

    def _is_variant_row(self, row) -> bool:
        config = self.file_config
        variant_id = row[config['variant_id_col']].strip()
        skip_prefix = config.get('skip_id_prefix')
        if skip_prefix and variant_id.startswith(skip_prefix):
            return False

        type_col = config.get('variant_type_col')
        if type_col:
            return row[type_col].strip().lower() == config['variant_type_value'].lower()

        return variant_id.startswith('NC_')

    def _is_significant(self, row) -> bool:
        config = self.file_config
        ci_lower = self._optional_float(row, config.get('ci_lower_col'))
        ci_upper = self._optional_float(row, config.get('ci_upper_col'))
        if ci_lower is not None and ci_upper is not None:
            return ci_lower > 0 or ci_upper < 0
        return False

    def parse(self):
        if self.label == 'ontology_term':
            self._write_ontology_term()
            return

        self.writer.add_tag('portal_accessions', self.file_accession)
        with self._open_file(self.filepath) as f:
            reader = csv.DictReader(f, delimiter=',')
            chunk = []
            for row in reader:
                if not self._is_variant_row(row):
                    continue
                chunk.append(row)
                if len(chunk) >= self.CHUNK_SIZE:
                    self._process_chunk(chunk)
                    chunk = []
            if chunk:
                self._process_chunk(chunk)

    def _process_chunk(self, chunk):
        spdi_to_variant = {}
        spdi_to_rows = {}
        skipped_variants = []

        for row in chunk:
            raw_variant_id = row[self.file_config['variant_id_col']].strip()
            variant, skipped_message = load_variant(raw_variant_id)
            if variant:
                spdi = variant['spdi']
                spdi_to_variant[spdi] = variant
                spdi_to_rows.setdefault(spdi, []).append(row)
            if skipped_message is not None:
                skipped_variants.append(skipped_message)

        if skipped_variants:
            self.logger.warning(
                'Skipped %d variants in %s',
                len(skipped_variants),
                self.file_accession,
            )
            for skipped in skipped_variants:
                self.logger.warning(
                    '  - %s: %s',
                    skipped['variant_id'],
                    skipped['reason'],
                )
            with open('./skipped_variants.jsonl', 'a') as out:
                for skipped in skipped_variants:
                    out.write(json.dumps(skipped) + '\n')

        if self.label == 'variant':
            loaded_variants = bulk_check_variants_in_arangodb(
                list(spdi_to_variant.keys()),
                excluded_files_filesets=f'files_filesets/{self.file_accession}',
            )
            self._write_variants(spdi_to_variant, loaded_variants)
        elif self.label == 'variant_phenotype':
            loaded_variants = bulk_check_variants_in_arangodb(
                list(spdi_to_variant.keys()))
            self._write_variant_phenotypes(spdi_to_rows, loaded_variants)

    def _write_variants(self, spdi_to_variant, loaded_variants):
        for spdi, variant in spdi_to_variant.items():
            if spdi in loaded_variants:
                continue
            variant.update({
                'source': self.SOURCE,
                'source_url': self.source_url,
                'files_filesets': f'files_filesets/{self.file_accession}',
            })
            if self.validate:
                self.validate_doc(variant)
            self.writer.write(json.dumps(variant) + '\n')

    def _write_variant_phenotypes(self, spdi_to_rows, loaded_variants):
        config = self.file_config
        for spdi, rows in spdi_to_rows.items():
            if spdi not in loaded_variants:
                continue
            for row in rows:
                num_guides = self._optional_int(
                    row, config.get('num_guides_col'))

                props = {
                    '_key': f'{spdi}_{self.phenotype_term}_{self.file_accession}',
                    '_from': f'variants/{spdi}',
                    '_to': f'ontology_terms/{self.phenotype_term}',
                    'effect_size': float(row[config['effect_size_col']]),
                    'z_score': float(row[config['z_score_col']]),
                    'significant': self._is_significant(row),
                    'num_guides': num_guides,
                    'edit_rate_mean': self._optional_float(
                        row, config.get('edit_rate_mean_col')),
                    'effect_size_ci95_lower': self._optional_float(
                        row, config.get('ci_lower_col')),
                    'effect_size_ci95_upper': self._optional_float(
                        row, config.get('ci_upper_col')),
                    'method': self.method,
                    'crispr_modality': self.crispr_modality,
                    'class': self.edge_class,
                    'label': self.COLLECTION_LABEL,
                    'name': 'associated with',
                    'inverse_name': 'associated with',
                    'source': self.SOURCE,
                    'source_url': self.source_url,
                    'files_filesets': f'files_filesets/{self.file_accession}',
                    'biological_context': self.simple_sample_summaries[0],
                    'biosample_term': self.biosample_term,
                    'treatments_term_ids': self.treatments_term_ids,
                }
                if self.validate:
                    self.validate_doc(props)
                self.writer.write(json.dumps(props) + '\n')

    def _write_ontology_term(self):
        if not self.phenotype_term.startswith('NTR_'):
            self.logger.info(
                'Skipping ontology_term write for non-NTR phenotype %s',
                self.phenotype_term,
            )
            return

        term_id_colon = self.phenotype_term.replace('_', ':', 1)
        search_url = (
            f'{IGVF_API}search/?type=PhenotypeTerm'
            f'&term_id={term_id_colon}&format=json'
        )
        response = requests.get(search_url, timeout=60)
        response.raise_for_status()
        graph = response.json().get('@graph', [])
        if not graph:
            raise ValueError(
                f'PhenotypeTerm {term_id_colon} not found at {search_url}'
            )

        term = graph[0]
        term_key = term['term_id'].replace(':', '_')
        uri = urljoin(IGVF_PHENOTYPE_TERM_URL, term_key + '/')
        synonyms = term.get('synonyms') or None
        if synonyms == []:
            synonyms = None

        props = {
            '_key': term_key,
            'uri': uri,
            'term_id': term_key,
            'name': term['term_name'],
            'synonyms': synonyms,
            'source': self.SOURCE,
            'source_url': uri,
        }
        if self.validate:
            self.validate_doc(props)
        self.writer.write(json.dumps(props) + '\n')
