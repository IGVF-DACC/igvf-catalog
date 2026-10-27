"""BATF3 overexpression ATAC-seq peaks and differential accessibility.

IGVFFI0911IUZS and IGVFFI2320OTYL are DESeq2 outputs with GRCh38 intervals
encoded as chr_start_end in rowID. Keep the supplied 0-based, half-open
coordinates.
"""
import csv
import gzip
import json
import math
import re

from adapters.archive_utils import get_file_accession
from adapters.base import BaseAdapter
from adapters.helpers import build_regulatory_region_id, get_file_fileset_by_accession_in_arangodb
from db.arango_db import ArangoDB


class OverexpressionATAC(BaseAdapter):
    ALLOWED_LABELS = ['genomic_element', 'gene_transcript_genomic_element']
    GENE_TRANSCRIPT = 'ENSG00000123685_ENST00000243440'
    FILE_ACCESSIONS = frozenset({'IGVFFI0911IUZS', 'IGVFFI2320OTYL'})
    SIGNIFICANCE_THRESHOLD = 0.05
    MAX_LOG10_PVALUE = 240
    METRICS = {'log2FC': 'log2FoldChange', 'standard_error': 'lfcSE',
               'base_mean': 'baseMean', 'p_value': 'pvalue', 'p_value_adj': 'padj'}

    def __init__(self, filepath, label, writer=None, validate=False, **kwargs):
        self.file_accession = get_file_accession(filepath)
        if self.file_accession not in self.FILE_ACCESSIONS:
            raise ValueError(
                f'Unsupported file accession: {self.file_accession}')
        self.source_url = f'https://data.igvf.org/tabular-files/{self.file_accession}/'
        super().__init__(filepath, label, writer, validate)

    def _get_schema_type(self):
        return 'nodes' if self.label == 'genomic_element' else 'edges'

    def _get_collection_name(self):
        return 'genomic_elements' if self.label == 'genomic_element' else 'genes_transcripts_genomic_elements'

    @staticmethod
    def _interval(row_id):
        match = re.fullmatch(r'(chr\S+)_(\d+)_(\d+)', row_id)
        if not match:
            raise ValueError(f'Invalid peak identifier: {row_id!r}')
        chrom, start, end = match.groups()
        start, end = int(start), int(end)
        if end <= start:
            raise ValueError(f'Invalid peak interval: {row_id!r}')
        return chrom, start, end

    @staticmethod
    def _number(value):
        if value.strip() in {'', 'NA', 'NaN', 'nan', '.'}:
            return None
        number = float(value)
        if not math.isfinite(number):
            raise ValueError(f'Expected a finite number, got {value!r}')
        return number

    def _metrics(self, row):
        metrics = {field: self._number(row[column])
                   for field, column in self.METRICS.items()}
        for field in ('base_mean', 'standard_error'):
            if metrics[field] is not None and metrics[field] < 0:
                raise ValueError(f'{field} must be nonnegative')
        for field, transformed in [('p_value', 'neg_log10_pvalue'), ('p_value_adj', 'neg_log10_pvalue_adj')]:
            value = metrics[field]
            if value is not None and not 0 <= value <= 1:
                raise ValueError(f'{field} must be between 0 and 1')
            metrics[transformed] = (None if value is None else
                                    self.MAX_LOG10_PVALUE if value == 0 else -math.log10(value))
        metrics['significant'] = (metrics['p_value_adj'] is not None and
                                  metrics['p_value_adj'] < self.SIGNIFICANCE_THRESHOLD)
        return metrics

    def parse(self):
        metadata = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        if not metadata:
            raise ValueError(
                f'Load files_filesets/{self.file_accession} before adapting overexpression ATAC-seq.')
        if self.label == 'gene_transcript_genomic_element':
            source = ArangoDB().get_igvf_connection().collection(
                'genes_transcripts').get(self.GENE_TRANSCRIPT)
            if not source or source.get('_from') != 'genes/ENSG00000123685' or source.get('_to') != 'transcripts/ENST00000243440':
                raise ValueError(
                    f'Missing or inconsistent genes_transcripts/{self.GENE_TRANSCRIPT}')
        for accession in (self.file_accession, metadata.get('file_set_id')):
            if accession:
                self.writer.add_tag('portal_accessions', accession)
        common = {'method': metadata['method'], 'source': 'IGVF',
                  'source_url': self.source_url,
                  'files_filesets': f'files_filesets/{self.file_accession}'}
        opener = gzip.open if str(self.filepath).endswith('.gz') else open
        with opener(self.filepath, 'rt', encoding='utf-8-sig', newline='') as stream:
            reader = csv.DictReader(stream, delimiter='\t')
            id_column = 'rowID'
            required = {id_column}
            if self.label == 'gene_transcript_genomic_element':
                required.update(self.METRICS.values())
            missing = required - set(reader.fieldnames or [])
            if missing:
                raise ValueError(
                    f'{self.file_accession}: missing columns: {sorted(missing)}')
            seen = set()
            for line, row in enumerate(reader, start=2):
                try:
                    chrom, start, end = self._interval(row[id_column].strip())
                    element = build_regulatory_region_id(
                        chrom, start, end, 'ATAC')
                    key = f'{element}_{self.file_accession}'
                    if key in seen:
                        raise ValueError(f'Duplicate peak: {row[id_column]}')
                    seen.add(key)
                    if self.label == 'genomic_element':
                        doc = {'_key': key, 'name': key, 'chr': chrom,
                               'start': start, 'end': end,
                               'type': 'accessible dna elements', **common}
                    else:
                        doc = {
                            '_key': f'{self.GENE_TRANSCRIPT}_{key}',
                            '_from': f'genes_transcripts/{self.GENE_TRANSCRIPT}',
                            '_to': f'genomic_elements/{key}',
                            'label': 'gene overexpression effect on chromatin accessibility',
                            'name': 'modulates accessibility of',
                            'inverse_name': 'accessibility modulated by',
                            'class': metadata['class'],
                            'perturbation': 'ORF overexpression',
                            'biological_context': metadata['simple_sample_summaries'][0],
                            'biosample_term': metadata['samples'][0],
                            'treatments_term_ids': metadata.get('treatments_term_ids'),
                            **common, **self._metrics(row),
                        }
                    if self.validate:
                        self.validate_doc(doc)
                    self.writer.write(json.dumps(doc, allow_nan=False) + '\n')
                except (ValueError, TypeError) as error:
                    raise ValueError(
                        f'{self.file_accession} line {line}: {error}') from error
