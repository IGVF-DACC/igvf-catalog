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
#   variant_id is SPDI (0-based)
# IGVFFI6803HZJG (Sherwood / IGVFDS9278NUAZ) – LDL-C uptake (NTR:0001118); prime editing
#   variant_id is SPDI (0-based)
# IGVFFI9726GFTC (Sherwood / IGVFDS6504OLWV) – LDL-C uptake (NTR:0001118); CRISPRi
#   target_id is 1-based chr_pos_hg38_ref_alt.
# IGVFFI1678CDBR (Sherwood / IGVFDS0021NCLH) – LDL-C uptake (NTR:0001118); base editing
#   target_id is 1-based chr_pos_hg38_ref_alt.
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
    WALD_Z_95 = 1.96

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
        'IGVFFI9726GFTC': {
            'phenotype_term': 'NTR_0001118',
            'phenotype_name': 'LDL-C uptake',
            'variant_id_col': 'target_id',
            'variant_type_col': 'target_type',
            'variant_type_value': 'variant',
            'effect_size_col': 'mu',
            'z_score_col': 'mu_z',
            'num_guides_col': 'n_guides',
            'ci_lower_col': 'CI[0.025',
            'ci_upper_col': '0.975]',
        },
        'IGVFFI1678CDBR': {
            'phenotype_term': 'NTR_0001118',
            'phenotype_name': 'LDL-C uptake',
            'variant_id_col': 'target_id',
            'variant_type_col': 'target_type',
            'variant_type_value': 'variant',
            'effect_size_col': 'mu_adj',
            'z_score_col': 'mu_z_adj',
            'effect_size_sd_col': 'mu_sd_adj',
            'edit_rate_mean_col': 'edit_rate_mean',
            'p_value_adj_col': 'fdr_adj',
            'neg_log10_pvalue_adj_col': 'log_fdr_adj',
        },
    }

    def __init__(self, filepath, label, source_url, writer: Optional[Writer] = None, validate=False, **kwargs):
        self.file_accession = source_url.rstrip('/').split('/')[-1]
        if self.file_accession not in self.FILE_CONFIG:
            raise ValueError(
                f'Unsupported file accession {self.file_accession}. '
                f'Expected one of: {", ".join(sorted(self.FILE_CONFIG))}'
            )
        self.source_url = (
            f'https://data.igvf.org/tabular-files/{self.file_accession}/'
        )
        self.file_config = self.FILE_CONFIG[self.file_accession]
        self.phenotype_term = self.file_config['phenotype_term']

        self.file_fileset = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        self.method = self.file_fileset['method']
        self.collection_class = self.file_fileset.get('class')
        if label != 'ontology_term':
            self.simple_sample_summaries = self.file_fileset['simple_sample_summaries']
            self.biosample_term = self.file_fileset['samples'][0]
            self.treatments_term_ids = self.file_fileset.get(
                'treatments_term_ids')
            self.crispr_modality = self.file_fileset.get('crispr_modality')

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

    @staticmethod
    def _to_loadable_variant_id(raw_id: str) -> str:
        """Convert 1-based chr_pos_hg38_ref_alt IDs to VCF (1-based) for load_variant.

        Example: 19_11091518_hg38_GC_G -> 19-11091518-GC-G
        SPDI IDs (NC_...) are returned unchanged.
        """
        if raw_id.startswith('NC_'):
            return raw_id
        marker = '_hg38_'
        if marker not in raw_id:
            return raw_id
        left, right = raw_id.split(marker, 1)
        if '_' not in left or '_' not in right:
            return raw_id
        chrom, pos = left.rsplit('_', 1)
        ref, alt = right.rsplit('_', 1)
        if not pos.isdigit() or not ref or not alt:
            return raw_id
        return f'{chrom}-{pos}-{ref}-{alt}'

    def _effect_size_ci95(self, row):
        config = self.file_config
        ci_lower = self._optional_float(row, config.get('ci_lower_col'))
        ci_upper = self._optional_float(row, config.get('ci_upper_col'))
        if ci_lower is not None and ci_upper is not None:
            return ci_lower, ci_upper

        # BEAN files that omit CI columns still report mu_sd; the 95% CI on
        # IGVFFI6803HZJG matches this Wald interval around mu_adj.
        sd = self._optional_float(row, config.get('effect_size_sd_col'))
        if sd is None:
            return None, None
        effect_size = float(row[config['effect_size_col']])
        margin = self.WALD_Z_95 * sd
        return effect_size - margin, effect_size + margin

    def parse(self):
        if self.label == 'ontology_term':
            self._write_ontology_term()
            return

        self.writer.add_tag('portal_accessions', self.file_accession)
        fileset_accession = self.file_fileset.get('file_set_id')
        if fileset_accession:
            self.writer.add_tag('portal_accessions', fileset_accession)
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
            variant_id = self._to_loadable_variant_id(raw_variant_id)
            variant, skipped_message = load_variant(variant_id)
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
                ci_lower, ci_upper = self._effect_size_ci95(row)

                props = {
                    '_key': f'{spdi}_{self.phenotype_term}_{self.file_accession}',
                    '_from': f'variants/{spdi}',
                    '_to': f'ontology_terms/{self.phenotype_term}',
                    'effect_size': float(row[config['effect_size_col']]),
                    'z_score': float(row[config['z_score_col']]),
                    'significant': (
                        ci_lower is not None
                        and ci_upper is not None
                        and (ci_lower > 0 or ci_upper < 0)
                    ),
                    'num_guides': num_guides,
                    'edit_rate_mean': self._optional_float(
                        row, config.get('edit_rate_mean_col')),
                    'effect_size_ci95_lower': ci_lower,
                    'effect_size_ci95_upper': ci_upper,
                    'p_value_adj': self._optional_float(
                        row, config.get('p_value_adj_col')),
                    'neg_log10_pvalue_adj': self._optional_float(
                        row, config.get('neg_log10_pvalue_adj_col')),
                    'method': self.method,
                    'crispr_modality': self.crispr_modality,
                    'class': self.collection_class,
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
            'class': self.collection_class,
            'method': self.method,
            'files_filesets': None,  # should not be associated with any datasets. See DSERV-1466
        }
        if self.validate:
            self.validate_doc(props)
        self.writer.write(json.dumps(props) + '\n')
