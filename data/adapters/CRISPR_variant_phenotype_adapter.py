import csv
import gzip
import json
import math
from typing import Optional
from urllib.parse import urljoin

import requests

from adapters.archive_utils import get_file_accession
from adapters.base import BaseAdapter
from adapters.helpers import (
    bulk_check_variants_in_arangodb,
    load_variant,
    get_file_fileset_by_accession_in_arangodb,
)
from adapters.ontology_term_validator import OntologyTermValidator
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
# IGVFFI4039BVDA (Bauer ChrX / IGVFDS0120EBCZ) – cell population proliferation
#   (GO:0008283) in HUDEP-2; SpRY-ABE8e base editing; MAGeCK RRA per-variant scores.
#   variant is SPDI (0-based). Only 'variant-concordant' variants from the variant
#   list IGVFFI7806CLOH (passed as reference_filepath) are loaded: their ref
#   alleles match GRCh38. The
#   'variant-nonconcordant' variants carry GRCh38's alt allele as ref (likely the
#   HUDEP-2 genotype), and the clinvar and control rows are excluded.
#   MAGeCK reports neg|/pos| selection results; the direction matching the sign of
#   the log2 fold change supplies p_value and p_value_adj (FDR).
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
    MAGECK_FDR_THRESHOLD = 0.05

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
        'IGVFFI4039BVDA': {
            'phenotype_term': 'GO_0008283',
            'phenotype_name': 'cell population proliferation',
            'format': 'mageck',
            'variant_id_col': 'variant',
            'effect_size_col': 'neg|lfc',
            'num_guides_col': 'num',
            'variant_list_accession': 'IGVFFI7806CLOH',
            'variant_list_type': 'variant-concordant',
        },
    }

    def __init__(self, filepath, label, writer: Optional[Writer] = None, validate=False,
                 reference_filepath: Optional[str] = None, **kwargs):
        self.file_accession = get_file_accession(filepath)
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
        self.ontology_term_validator = OntologyTermValidator()
        self.reference_filepath = reference_filepath
        self.allowed_variant_ids = None
        if label != 'ontology_term' and 'variant_list_accession' in self.file_config:
            self.allowed_variant_ids = self._load_variant_list()

        self.file_fileset = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        self.method = self.file_fileset['method']
        self.collection_class = self.file_fileset.get('class')
        if label != 'ontology_term':
            self.simple_sample_summaries = self.file_fileset['simple_sample_summaries']
            self.biosample_term = self.file_fileset['samples'][0]
            self.treatments_term_ids = self.file_fileset.get(
                'treatments_term_ids')
            self.perturbation = self.file_fileset.get('perturbation')

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

    def _load_variant_list(self):
        """Read variant IDs of the configured type from the reference variant list."""
        accession = self.file_config['variant_list_accession']
        variant_type = self.file_config['variant_list_type']
        if not self.reference_filepath:
            raise ValueError(
                f'{self.file_accession} requires reference_filepath for '
                f'{accession} (variant list).')
        reference_accession = get_file_accession(self.reference_filepath)
        if reference_accession != accession:
            raise ValueError(
                f'Expected variant list {accession}, got {reference_accession}')
        self.reference_source_url = (
            f'https://data.igvf.org/tabular-files/{accession}/'
        )
        with self._open_file(self.reference_filepath) as f:
            reader = csv.DictReader(f)
            missing = {'element_id', 'type'} - set(reader.fieldnames or [])
            if missing:
                raise ValueError(
                    f'Variant list missing columns: {sorted(missing)}')
            variant_ids = {
                row['element_id'].strip()
                for row in reader
                if row['type'].strip() == variant_type
            }
        if not variant_ids:
            raise ValueError(
                f'No {variant_type!r} variants found in {self.reference_filepath}')
        return variant_ids

    def _is_variant_row(self, row) -> bool:
        config = self.file_config
        variant_id = row[config['variant_id_col']].strip()
        if self.allowed_variant_ids is not None:
            return variant_id in self.allowed_variant_ids
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
        For embedded chr:pos:ref:alt IDs, retain the explicit hg38 coordinates
        and extract the trailing alternate allele.
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
        if ':' in alt:
            parts = alt.split(':')
            if len(parts) != 4:
                raise ValueError(
                    'Invalid trailing chr:pos:ref:alt coordinates')
            embedded_chrom, embedded_pos, embedded_ref, alt = parts
            if (not embedded_pos.isdigit() or int(embedded_pos) < 1
                    or not embedded_ref or not alt):
                raise ValueError(
                    'Invalid trailing chr:pos:ref:alt coordinates')
            if embedded_chrom != chrom or embedded_ref != ref:
                raise ValueError(
                    'Trailing chromosome/reference conflicts with hg38 ID')
        if ':' in ref:
            raise ValueError('Invalid reference allele in hg38 variant ID')
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

    def _mageck_statistics(self, row):
        # MAGeCK RRA tests depletion (neg|) and enrichment (pos|) separately;
        # report the test in the direction of the observed fold change.
        effect_size = float(row[self.file_config['effect_size_col']])
        direction = 'neg' if effect_size < 0 else 'pos'
        p_value = float(row[f'{direction}|p-value'])
        p_value_adj = float(row[f'{direction}|fdr'])
        return {
            'z_score': None,
            'significant': p_value_adj < self.MAGECK_FDR_THRESHOLD,
            'effect_size_ci95_lower': None,
            'effect_size_ci95_upper': None,
            'p_value': p_value,
            'p_value_adj': p_value_adj,
            'neg_log10_pvalue_adj': -math.log10(p_value_adj),
        }

    def _bean_statistics(self, row):
        config = self.file_config
        ci_lower, ci_upper = self._effect_size_ci95(row)
        return {
            'z_score': float(row[config['z_score_col']]),
            'significant': (
                ci_lower is not None
                and ci_upper is not None
                and (ci_lower > 0 or ci_upper < 0)
            ),
            'effect_size_ci95_lower': ci_lower,
            'effect_size_ci95_upper': ci_upper,
            'p_value': None,
            'p_value_adj': self._optional_float(
                row, config.get('p_value_adj_col')),
            'neg_log10_pvalue_adj': self._optional_float(
                row, config.get('neg_log10_pvalue_adj_col')),
        }

    def parse(self):
        if self.label == 'ontology_term':
            self._write_ontology_term()
            return

        self.writer.add_tag('portal_accessions', self.file_accession)
        fileset_accession = self.file_fileset.get('file_set_id')
        if fileset_accession:
            self.writer.add_tag('portal_accessions', fileset_accession)

        if self.label == 'variant_phenotype':
            if not self.ontology_term_validator.ensure(self.phenotype_term):
                self.ontology_term_validator.log()
                return

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
            try:
                variant_id = self._to_loadable_variant_id(raw_variant_id)
            except ValueError as exc:
                skipped_variants.append({
                    'variant_id': raw_variant_id,
                    'reason': str(exc),
                })
                continue
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
            missing_spdis = set(spdi_to_rows) - set(loaded_variants)
            if missing_spdis:
                self.logger.error(
                    f'{self.file_accession}: skipping variant-phenotype edges for '
                    f'{len(missing_spdis)} unique variants in this chunk because their '
                    'nodes are missing from variants in ArangoDB. '
                    'Output will be incomplete. Load the variant nodes into ArangoDB '
                    'and rerun edge generation; uploading node files to S3 is not sufficient.')
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
                if config.get('format') == 'mageck':
                    stats = self._mageck_statistics(row)
                else:
                    stats = self._bean_statistics(row)

                props = {
                    '_key': f'{spdi}_{self.phenotype_term}_{self.file_accession}',
                    '_from': f'variants/{spdi}',
                    '_to': f'ontology_terms/{self.phenotype_term}',
                    'effect_size': float(row[config['effect_size_col']]),
                    'z_score': stats['z_score'],
                    'significant': stats['significant'],
                    'num_guides': num_guides,
                    'edit_rate_mean': self._optional_float(
                        row, config.get('edit_rate_mean_col')),
                    'effect_size_ci95_lower': stats['effect_size_ci95_lower'],
                    'effect_size_ci95_upper': stats['effect_size_ci95_upper'],
                    'p_value': stats['p_value'],
                    'p_value_adj': stats['p_value_adj'],
                    'neg_log10_pvalue_adj': stats['neg_log10_pvalue_adj'],
                    'method': self.method,
                    'perturbation': self.perturbation,
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
