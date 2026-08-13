import csv
import gzip
import json
from math import log10
from typing import Optional

from adapters.base import BaseAdapter
from adapters.helpers import build_regulatory_region_id, get_file_fileset_by_accession_in_arangodb
from adapters.writer import Writer

# Element-level CRISPR element-to-phenotype screens (Gersbach lab).
# IGVFFI5135QZCS – cell migration (GO:0016477); columns use migration/mig suffixes.
# IGVFFI9584UDAS – cell population proliferation (GO:0008283); columns use growth suffixes.
# Coordinates are 0-based, half-open (submitter_comment on both files). Stored as provided.

# Example rows (migration):
# dhs	dhs_coords	dhs_count	avg_migration_pZ	hit_gRNA_count_mig	nonhit_gRNA_count_mig	fraction_hit_mig	migration_pval	mig_significant
# 93	chr1:101174581-101175330_93	32	0.011457821	0	32	0	0.623284698	FALSE

# Example rows (growth/proliferation):
# dhs	dhs_coords	dhs_count	avg_growth_pZ	hit_gRNA_count_growth	nonhit_gRNA_count_growth	fraction_hit_growth	growth_pval	growth_significant
# 93	chr1:101174581-101175330_93	32	-0.122645943	1	31	0.03125	0.718493129	FALSE


class CRISPRElementPhenotype(BaseAdapter):
    ALLOWED_LABELS = ['genomic_element', 'genomic_element_phenotype']
    SOURCE = 'IGVF'
    COLLECTION_LABEL = 'regulatory element effect on phenotype'
    MAX_LOG10_PVALUE = 240

    # Accession -> phenotype ontology term and file column names.
    FILE_CONFIG = {
        'IGVFFI5135QZCS': {
            'phenotype_term': 'GO_0016477',  # cell migration
            'z_score_col': 'avg_migration_pZ',
            'num_guides_hit_col': 'hit_gRNA_count_mig',
            'num_guides_nonhit_col': 'nonhit_gRNA_count_mig',
            'fraction_guides_hit_col': 'fraction_hit_mig',
            'p_value_col': 'migration_pval',
            'significant_col': 'mig_significant',
        },
        'IGVFFI9584UDAS': {
            'phenotype_term': 'GO_0008283',  # cell population proliferation
            'z_score_col': 'avg_growth_pZ',
            'num_guides_hit_col': 'hit_gRNA_count_growth',
            'num_guides_nonhit_col': 'nonhit_gRNA_count_growth',
            'fraction_guides_hit_col': 'fraction_hit_growth',
            'p_value_col': 'growth_pval',
            'significant_col': 'growth_significant',
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
        if self.label == 'genomic_element':
            return 'nodes'
        return 'edges'

    def _get_collection_name(self):
        if self.label == 'genomic_element':
            return 'genomic_elements'
        return 'genomic_elements_phenotypes'

    @staticmethod
    def _open_file(filepath):
        if filepath.endswith('.gz'):
            return gzip.open(filepath, 'rt')
        return open(filepath, 'r')

    @staticmethod
    def _parse_element_coords(dhs_coords: str) -> Optional[tuple[str, int, int]]:
        """Parse coords like chr1:101174581-101175330_93 into chr, start, end.

        Returns None only for known non-genomic gene-control rows (NA:NA-NA_*).
        Raises ValueError for any other unparseable coordinate string.
        """
        if dhs_coords.startswith('NA:NA-NA_'):
            return None
        try:
            coords_part = dhs_coords.rsplit('_', 1)[0]
            chrom, rest = coords_part.split(':')
            start_str, end_str = rest.split('-')
            return chrom, int(start_str), int(end_str)
        except (ValueError, IndexError) as exc:
            raise ValueError(
                f'Unrecognized element coordinates: {dhs_coords!r}'
            ) from exc

    @staticmethod
    def _parse_bool(value: str) -> bool:
        return value.strip().upper() == 'TRUE'

    def _neg_log10_pvalue(self, p_value: float) -> float:
        if p_value == 0:
            return self.MAX_LOG10_PVALUE
        return -1 * log10(p_value)

    def parse(self):
        self.writer.add_tag('portal_accessions', self.file_accession)
        fileset_accession = self.file_fileset.get('file_set_id')
        if fileset_accession:
            self.writer.add_tag('portal_accessions', fileset_accession)
        with self._open_file(self.filepath) as f:
            reader = csv.DictReader(f, delimiter='\t')
            if self.label == 'genomic_element':
                self._write_genomic_elements(reader)
            elif self.label == 'genomic_element_phenotype':
                self._write_genomic_element_phenotypes(reader)

    def _write_genomic_elements(self, reader):
        seen = set()

        for row in reader:
            parsed = self._parse_element_coords(row['dhs_coords'])
            if parsed is None:
                continue
            chrom, start, end = parsed
            region_key = (chrom, start, end)
            if region_key in seen:
                continue
            seen.add(region_key)

            genomic_element_id = build_regulatory_region_id(
                chrom, start, end, 'CRISPR') + '_' + self.file_accession
            props = {
                '_key': genomic_element_id,
                'name': genomic_element_id,
                'chr': chrom,
                'start': start,
                'end': end,
                'method': self.method,
                'type': 'tested elements',
                'source_annotation': 'enhancer',
                'source': self.SOURCE,
                'source_url': self.source_url,
                'files_filesets': f'files_filesets/{self.file_accession}',
            }
            if self.validate:
                self.validate_doc(props)
            self.writer.write(json.dumps(props) + '\n')

    def _write_genomic_element_phenotypes(self, reader):
        config = self.file_config
        for row in reader:
            parsed = self._parse_element_coords(row['dhs_coords'])
            if parsed is None:
                continue
            chrom, start, end = parsed
            genomic_element_id = build_regulatory_region_id(
                chrom, start, end, 'CRISPR') + '_' + self.file_accession
            p_value = float(row[config['p_value_col']])
            props = {
                '_key': f'{genomic_element_id}_{self.phenotype_term}',
                '_from': f'genomic_elements/{genomic_element_id}',
                '_to': f'ontology_terms/{self.phenotype_term}',
                'z_score': float(row[config['z_score_col']]),
                'p_value': p_value,
                'neg_log10_pvalue': self._neg_log10_pvalue(p_value),
                'significant': self._parse_bool(row[config['significant_col']]),
                'num_guides': int(row['dhs_count']),
                'num_guides_hit': int(row[config['num_guides_hit_col']]),
                'num_guides_nonhit': int(row[config['num_guides_nonhit_col']]),
                'fraction_guides_hit': float(row[config['fraction_guides_hit_col']]),
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
