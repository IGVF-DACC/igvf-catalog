import csv
import gzip
import json
import math
import re
from typing import Optional
from urllib.parse import urlparse

from adapters.base import BaseAdapter
from adapters.gene_validator import GeneValidator
from adapters.helpers import (
    get_file_fileset_by_accession_in_arangodb,
    get_gene_map_from_arangodb,
)
from adapters.writer import Writer
from db.arango_db import ArangoDB

# MORF overexpression screens measuring a constant readout gene.
# DESeq2 differential ORF quantifications are joined to the ORF/transcript table
# supplied by the caller via MORF_id. Catalog transcript nodes use Ensembl
# (ENST) keys, so RefSeq-only ORFs are skipped until they can be reconciled.

# Example DESeq2 row (IGVFFI6734IWRB / IGVFFI6032GREJ):
# rowID  baseMean  log2FoldChange  lfcSE  stat  pvalue  padj
# AATF_1 13.42     -0.787          0.699  -1.13 0.260   0.998

# Example ORF reference row (IGVFFI2373SYJW):
# Name      MORF_id  RefSeq_Gene_Name  RefSeq_and_Gencode_ID              ENSG_id
# TFORF2521 AATF_1   AATF              NM_012138,ENST00000619387          ENSG00000275700

_ENST_RE = re.compile(
    r'(?<![\w.])(ENST[0-9]{11}(?:_PAR_Y)?)(?:\.[0-9]+)?(?![\w.])')
_ENSG_RE = re.compile(r'^(ENSG[0-9]{11}(?:_PAR_Y)?)(?:\.[0-9]+)?$')
_REFSEQ_RE = re.compile(r'(?:N[MR]|X[MR])_\d+(?:\.\d+)?')
_NA_VALUES = frozenset({'', 'NA', 'NaN', 'nan', 'None', '.'})


class MORFTranscriptGene(BaseAdapter):
    ALLOWED_LABELS = ['transcript_gene']
    SOURCE = 'IGVF'
    COLLECTION_LABEL = 'transcript effect on gene expression'
    SIGNIFICANCE_THRESHOLD = 0.05
    MAX_LOG10_PVALUE = 240
    CONTROL_MORF_IDS = frozenset({'GFP_1', 'mCherry_1'})
    # Both current files sort on TOX-GFP (same readout as CRISPR-SURF IGVFFI4396TZAN).
    TOX_ENSEMBL_ID = 'ENSG00000198846'
    FILE_CONFIG = {
        'IGVFFI6734IWRB': {
            'readout_gene': TOX_ENSEMBL_ID,
        },
        'IGVFFI6032GREJ': {
            'readout_gene': TOX_ENSEMBL_ID,
        },
    }

    def __init__(
        self,
        filepath,
        label,
        source_url,
        writer: Optional[Writer] = None,
        validate=False,
        reference_filepath: Optional[str] = None,
        reference_source_url: Optional[str] = None,
        **kwargs
    ):
        self.file_accession = self._file_accession(source_url, 'source_url')
        if self.file_accession not in self.FILE_CONFIG:
            raise ValueError(
                f'Unsupported file accession {self.file_accession}. '
                f'Expected one of: {", ".join(sorted(self.FILE_CONFIG))}'
            )
        if not reference_filepath:
            raise ValueError(
                'reference_filepath is required (ORF transcript table).'
            )

        self.source_url = (
            f'https://data.igvf.org/tabular-files/{self.file_accession}/'
        )
        self.reference_accession = self._file_accession(
            reference_source_url, 'reference_source_url')
        self.reference_filepath = reference_filepath
        self.reference_source_url = reference_source_url
        self.readout_gene = self.FILE_CONFIG[self.file_accession]['readout_gene']
        self.gene_validator = GeneValidator()

        self.file_fileset = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        if not self.file_fileset:
            raise ValueError(
                f'files_filesets/{self.file_accession} not found. '
                'Load files_filesets before adapting MORF screens.'
            )
        self.method = self.file_fileset['method']
        self.simple_sample_summaries = self.file_fileset['simple_sample_summaries']
        self.biosample_term = self.file_fileset['samples'][0]
        self.treatments_term_ids = self.file_fileset.get('treatments_term_ids')
        self.crispr_modality = self.file_fileset.get('crispr_modality')
        self.edge_class = self.file_fileset.get('class') or 'observed data'

        super().__init__(filepath, label, writer, validate)

    def _get_schema_type(self):
        return 'edges'

    def _get_collection_name(self):
        return 'transcripts_genes'

    @staticmethod
    def _file_accession(source_url: Optional[str], field: str) -> str:
        parsed = urlparse(source_url or '')
        parts = parsed.path.strip('/').split('/')
        if (parsed.scheme not in {'http', 'https'} or not parsed.netloc
                or len(parts) != 2 or parts[0] != 'tabular-files'
                or not re.fullmatch(r'IGVFFI[0-9A-Z]{8}', parts[-1])):
            raise ValueError(f'{field} must be an IGVF tabular-file URL.')
        return parts[-1]

    @staticmethod
    def _open_file(filepath):
        opener = gzip.open if str(filepath).endswith('.gz') else open
        return opener(filepath, 'rt', encoding='utf-8-sig', newline='')

    @staticmethod
    def _check_columns(reader, required, filepath):
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f'{filepath}: missing required columns: {", ".join(sorted(missing))}')

    @staticmethod
    def _normalize_morf_id(morf_id: str) -> str:
        # DESeq2 rowIDs use HGNC hyphens (NKX2-1_1); the ORF table uses underscores.
        return morf_id.strip().replace('-', '_')

    @staticmethod
    def _parse_optional_float(value: Optional[str]) -> Optional[float]:
        if value is None:
            return None
        normalized = value.strip()
        if normalized in _NA_VALUES:
            return None
        number = float(normalized)
        if not math.isfinite(number):
            raise ValueError(f'Expected a finite number, got {value!r}')
        return number

    @classmethod
    def _neg_log10_pvalue(cls, p_value: Optional[float]) -> Optional[float]:
        if p_value is None:
            return None
        if not math.isfinite(p_value) or not 0 <= p_value <= 1:
            raise ValueError(
                f'P-value must be between 0 and 1, got {p_value!r}')
        if p_value == 0:
            return cls.MAX_LOG10_PVALUE
        return -1 * math.log10(p_value)

    @classmethod
    def _normalize_ensembl_gene_id(cls, gene_id: str) -> Optional[str]:
        if not gene_id:
            return None
        match = _ENSG_RE.match(gene_id.strip())
        if not match:
            return None
        return match.group(1)

    @staticmethod
    def _parse_transcript_ids(refseq_and_gencode_id: str) -> tuple[list[str], list[str]]:
        raw = (refseq_and_gencode_id or '').strip()
        ensembl_ids = list(dict.fromkeys(_ENST_RE.findall(raw)))
        refseq_ids = list(dict.fromkeys(_REFSEQ_RE.findall(raw)))
        return ensembl_ids, refseq_ids

    def _load_orf_reference(self) -> dict[str, dict]:
        orfs = {}
        with self._open_file(self.reference_filepath) as reference_file:
            reader = csv.DictReader(reference_file, delimiter='\t')
            self._check_columns(reader, {'MORF_id', 'RefSeq_Gene_Name',
                                         'RefSeq_and_Gencode_ID', 'ENSG_id'}, self.reference_filepath)
            for row in reader:
                morf_id = (row.get('MORF_id') or '').strip()
                if not morf_id:
                    continue
                normalized = self._normalize_morf_id(morf_id)
                if normalized in orfs:
                    raise ValueError(
                        f'Duplicate MORF_id {morf_id!r} in ORF reference '
                        f'{self.reference_accession}.'
                    )
                ensembl_ids, refseq_ids = self._parse_transcript_ids(
                    row.get('RefSeq_and_Gencode_ID') or '')
                orfs[normalized] = {
                    'morf_id': morf_id,
                    'orf_gene': self._normalize_ensembl_gene_id(
                        row.get('ENSG_id') or ''),
                    'orf_gene_symbol': (row.get('RefSeq_Gene_Name') or '').strip() or None,
                    'ensembl_transcript_ids': ensembl_ids,
                    'refseq_transcript_ids': refseq_ids,
                }
        if not orfs:
            raise ValueError(
                f'No ORF rows loaded from {self.reference_filepath}.'
            )
        return orfs

    def _resolve_missing_orf_genes(self, orfs):
        """Resolve names, then synonyms; disambiguate using all listed transcripts.

        Supplied gene IDs are preserved. Unresolved mappings remain null rather
        than selecting one of several candidates arbitrarily.
        """
        missing = [orf for orf in orfs.values()
                   if not orf['orf_gene'] and orf['morf_id'] not in self.CONTROL_MORF_IDS]
        if not missing:
            return
        names = get_gene_map_from_arangodb('name')
        synonyms = None
        ambiguous = []
        for orf in missing:
            symbol = orf['orf_gene_symbol']
            candidates = set(names.get(symbol, []))
            if not candidates and symbol:
                if synonyms is None:
                    synonyms = get_gene_map_from_arangodb('synonyms')
                candidates = set(synonyms.get(symbol, []))
            if len(candidates) == 1:
                orf['orf_gene'] = next(iter(candidates))
            elif len(candidates) > 1:
                ambiguous.append((orf, candidates))
        transcript_ids = sorted({f'transcripts/{t}' for orf, _ in ambiguous
                                 for t in orf['ensembl_transcript_ids']})
        parents = {}
        if transcript_ids:
            db = ArangoDB().get_igvf_connection()
            for edge in db.aql.execute(
                'FOR e IN genes_transcripts FILTER e._to IN @ids '
                'RETURN {transcript: e._to, gene: e._from}',
                bind_vars={'ids': transcript_ids}
            ):
                parents.setdefault(edge['transcript'], set()).add(
                    edge['gene'].removeprefix('genes/'))
        for orf, candidates in ambiguous:
            mappings = [parents.get(f'transcripts/{t}', set())
                        for t in orf['ensembl_transcript_ids']]
            # Require every listed transcript to agree on one candidate gene.
            if mappings and all(len(m) == 1 for m in mappings):
                genes = set.union(*mappings)
                if len(genes) == 1 and genes <= candidates:
                    orf['orf_gene'] = next(iter(genes))
        for orf in missing:
            if not orf['orf_gene']:
                self.logger.warning('Unresolved ORF gene for %s (%s)',
                                    orf['morf_id'], orf['orf_gene_symbol'])

    def _write_doc(self, props: dict) -> None:
        if self.validate:
            self.validate_doc(props)
        self.writer.write(json.dumps(props, allow_nan=False) + '\n')

    def _log_skipped(self, missing_ensembl: list[str], missing_reference: list[str], na_stats: list[str]) -> None:
        if missing_ensembl:
            self.logger.warning(
                'Flagged %d ORF(s) in %s with no Ensembl transcript ID; '
                'skipped until reconciliation: %s',
                len(missing_ensembl),
                self.file_accession,
                ', '.join(missing_ensembl),
            )
        if missing_reference:
            self.logger.warning(
                'Skipped %d row(s) in %s with no matching MORF_id in the ORF '
                'reference: %s',
                len(missing_reference),
                self.file_accession,
                ', '.join(missing_reference),
            )
        if na_stats:
            self.logger.info(
                'Skipped %d ORF(s) in %s with missing DESeq2 log2FoldChange.',
                len(na_stats),
                self.file_accession,
            )

    def parse(self):
        self.writer.add_tag('portal_accessions', self.file_accession)
        file_set_accession = self.file_fileset.get('file_set_id')
        if file_set_accession:
            self.writer.add_tag('portal_accessions', file_set_accession)
        self.writer.add_tag('portal_accessions', self.reference_accession)

        if not self.gene_validator.validate(self.readout_gene):
            raise ValueError(
                f'{self.readout_gene} is not a valid gene.'
            )

        orfs = self._load_orf_reference()
        self._resolve_missing_orf_genes(orfs)
        missing_ensembl = []
        missing_reference = []
        na_stats = []

        with self._open_file(self.filepath) as deseq_file:
            reader = csv.DictReader(deseq_file, delimiter='\t')
            self._check_columns(reader, {'rowID', 'log2FoldChange', 'lfcSE',
                                         'baseMean', 'pvalue', 'padj'}, self.filepath)
            seen_ids = set()
            for row in reader:
                row_id = (row.get('rowID') or '').strip()
                if not row_id:
                    continue
                if self._normalize_morf_id(row_id) in self.CONTROL_MORF_IDS:
                    continue
                normalized = self._normalize_morf_id(row_id)
                if normalized in seen_ids:
                    raise ValueError(
                        f'{self.filepath}: duplicate rowID {row_id!r}')
                seen_ids.add(normalized)
                orf = orfs.get(normalized)
                if orf is None:
                    missing_reference.append(row_id)
                    continue

                ensembl_ids = orf['ensembl_transcript_ids']
                if not ensembl_ids:
                    refseq_label = ','.join(
                        orf['refseq_transcript_ids']) or 'none'
                    symbol = orf['orf_gene_symbol'] or ''
                    missing_ensembl.append(
                        f'{orf["morf_id"]} ({symbol} {refseq_label})'.strip()
                    )
                    continue

                try:
                    stats = {field: self._parse_optional_float(row.get(field))
                             for field in ('log2FoldChange', 'lfcSE', 'baseMean', 'pvalue', 'padj')}
                    p_value = stats['pvalue']
                    p_value_adj = stats['padj']
                    neg_log10_pvalue = self._neg_log10_pvalue(p_value)
                    neg_log10_pvalue_adj = self._neg_log10_pvalue(p_value_adj)
                    for field in ('lfcSE', 'baseMean'):
                        if stats[field] is not None and stats[field] < 0:
                            raise ValueError(f'{field} must be nonnegative')
                except ValueError as error:
                    raise ValueError(
                        f'{self.filepath}: row {row_id!r}: {error}') from error
                log2fc = stats['log2FoldChange']
                if log2fc is None:
                    na_stats.append(row_id)
                    continue

                significant = (
                    p_value_adj is not None
                    and p_value_adj < self.SIGNIFICANCE_THRESHOLD
                )
                for transcript_id in ensembl_ids:
                    self._write_doc({
                        '_key': (
                            f'{transcript_id}_{self.readout_gene}_'
                            f'{self.file_accession}_{orf["morf_id"]}'
                        ),
                        '_from': f'transcripts/{transcript_id}',
                        '_to': f'genes/{self.readout_gene}',
                        'log2FC': log2fc,
                        'log2FC_se': stats['lfcSE'],
                        'base_mean': stats['baseMean'],
                        'p_value': p_value,
                        'p_value_adj': p_value_adj,
                        'neg_log10_pvalue': neg_log10_pvalue,
                        'neg_log10_pvalue_adj': neg_log10_pvalue_adj,
                        'significant': significant,
                        'morf_id': orf['morf_id'],
                        'orf_gene': orf['orf_gene'],
                        'ensembl_transcript_ids': ensembl_ids,
                        'refseq_transcript_ids': orf['refseq_transcript_ids'],
                        'class': self.edge_class,
                        'label': self.COLLECTION_LABEL,
                        'name': 'modulates expression of',
                        'inverse_name': 'expression modulated by',
                        'source': self.SOURCE,
                        'source_url': self.source_url,
                        'files_filesets': f'files_filesets/{self.file_accession}',
                        'method': self.method,
                        'crispr_modality': self.crispr_modality,
                        'biological_context': self.simple_sample_summaries[0],
                        'biosample_term': self.biosample_term,
                        'treatments_term_ids': self.treatments_term_ids,
                    })

        self._log_skipped(missing_ensembl, missing_reference, na_stats)
        self.gene_validator.log()
