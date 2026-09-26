"""Promoter perturbation effects on peak accessibility in Multiome Perturb-seq."""
import csv
import gzip
import json
import math

from adapters.base import BaseAdapter
from adapters.CRISPR_element_gene_IGVF_adapter import CRISPRElementGeneIGVF
from adapters.gene_validator import GeneValidator
from adapters.helpers import build_regulatory_region_id, get_file_fileset_by_accession_in_arangodb


# Example lines from IGVFFI2419ZSGC.tsv.gz (GRCh38, tab-separated):
# effect_score	p_val	p_val_adj	peak_id	chr	start	end	guide_id	intended_target_name	intended_target_chr	intended_target_start	intended_target_end
# 4.777302097678887	3.4310611866199616e-08	0.005168859367031106	chr1:3586345-3586846	chr1	3586345	3586846	YY1_GGCCGGGCCCGAGCAGAGTG	ENSG00000100811	chr14	100238144	100239154
# 1.8888953106751614	1.5888994237987365e-06	0.029920763661981983	chr1:103529706-103530207	chr1	103529706	103530207	YY1_GGCCGGGCCCGAGCAGAGTG	ENSG00000100811	chr14	100238144	100239154

# The intended_target_* columns describe the perturbed promoter; chr/start/end
# describe the readout peak. Coordinates are 0-based, half-open and kept unchanged.
# Emit promoter -> peak edges in genomic_elements_genomic_elements, with the gene
# hyperedge on the promoter node as promoter_of: genes/<Ensembl ID>.
# effect_score is accessibility log2 fold change with a 1e-3 pseudocount, unlike
# the companion expression file's z-score. The source calls use adjusted p < 0.1.
# Keep all input rows; reject duplicate promoter/peak pairs instead of choosing
# a guide arbitrarily. Metadata and promoter gene membership require the catalog.


class CRISPRElementElement(BaseAdapter):
    ALLOWED_LABELS = ['genomic_element', 'genomic_element_genomic_element']
    SIGNIFICANCE_THRESHOLD = 0.1
    REQUIRED_COLUMNS = {
        'effect_score', 'p_val', 'p_val_adj', 'chr', 'start', 'end',
        'intended_target_name', 'intended_target_chr',
        'intended_target_start', 'intended_target_end',
    }

    def __init__(self, filepath, label, source_url, writer=None, validate=False, **kwargs):
        self.source_url = source_url
        self.file_accession = source_url.rstrip('/').split('/')[-1]
        self.gene_validator = GeneValidator()
        super().__init__(filepath, label, writer, validate)

    def _get_schema_type(self):
        return 'nodes' if self.label == 'genomic_element' else 'edges'

    def _get_collection_name(self):
        return 'genomic_elements' if self.label == 'genomic_element' else 'genomic_elements_genomic_elements'

    def _write_doc(self, doc):
        if self.validate:
            self.validate_doc(doc)
        self.writer.write(json.dumps(doc, allow_nan=False))
        self.writer.write('\n')

    def _element(self, row, prefix, gene=None):
        chrom = row[prefix + 'chr'].strip()
        start, end = int(row[prefix + 'start']), int(row[prefix + 'end'])
        if not chrom.startswith('chr') or start < 0 or end <= start:
            raise ValueError(
                f'Invalid genomic interval: {chrom}:{start}-{end}')
        element_id = build_regulatory_region_id(
            chrom, start, end, 'CRISPR' if gene else 'ATAC')
        key = f'{element_id}_{self.file_accession}'
        doc = {
            '_key': key, 'name': key, 'chr': chrom, 'start': start, 'end': end,
            'method': self.file_fileset['method'],
            'source_annotation': 'promoter' if gene else 'accessible element',
            'source': 'IGVF', 'source_url': self.source_url,
            'type': 'tested elements',
            'files_filesets': f'files_filesets/{self.file_accession}',
        }
        if gene:
            doc['promoter_of'] = f'genes/{gene}'
        return element_id, doc

    def parse(self):
        self.file_fileset = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        for accession in (self.file_accession, self.file_fileset.get('file_set_id')):
            if accession:
                self.writer.add_tag('portal_accessions', accession)
        elements, edge_ids = {}, set()
        with gzip.open(self.filepath, 'rt', encoding='utf-8-sig') as stream:
            reader = csv.DictReader(stream, delimiter='\t')
            missing = self.REQUIRED_COLUMNS - set(reader.fieldnames or [])
            if missing:
                raise ValueError(
                    f'{self.file_accession}: missing columns: {sorted(missing)}')
            for line, row in enumerate(reader, start=2):
                try:
                    gene = CRISPRElementGeneIGVF._normalize_ensembl_gene_id(
                        row['intended_target_name'])
                    if not CRISPRElementGeneIGVF._is_ensembl_gene_id(gene) or not self.gene_validator.validate(gene):
                        raise ValueError(f'Invalid promoter gene: {gene!r}')
                    promoter_id, promoter = self._element(
                        row, 'intended_target_', gene)
                    peak_id, peak = self._element(row, '')
                    for doc in (promoter, peak):
                        existing = elements.get(doc['_key'])
                        if existing is not None and existing != doc:
                            raise ValueError(
                                f'Conflicting element annotation: {doc["_key"]}')
                        elements[doc['_key']] = doc
                    metrics = {field: float(row[column]) for field, column in (
                        ('log2FC', 'effect_score'), ('p_value', 'p_val'), ('p_value_adj', 'p_val_adj'))}
                    if not all(math.isfinite(value) for value in metrics.values()):
                        raise ValueError('Non-finite accessibility metric')
                    if any(not 0 <= metrics[field] <= 1 for field in ('p_value', 'p_value_adj')):
                        raise ValueError('P-values must be between 0 and 1')
                    for field, source in [('neg_log10_pvalue', 'p_value'), ('neg_log10_pvalue_adj', 'p_value_adj')]:
                        metrics[field] = CRISPRElementGeneIGVF._neg_log10_pvalue(
                            metrics[source])
                    metrics['significant'] = metrics['p_value_adj'] < self.SIGNIFICANCE_THRESHOLD
                    key = f'{promoter_id}_{peak_id}_{self.file_accession}'
                    if key in edge_ids:
                        raise ValueError(
                            f'Duplicate promoter-peak edge: {key}')
                    edge_ids.add(key)
                    if self.label == 'genomic_element_genomic_element':
                        self._write_doc({
                            '_key': key, '_from': f'genomic_elements/{promoter["_key"]}',
                            '_to': f'genomic_elements/{peak["_key"]}',
                            'source': 'IGVF', 'source_url': self.source_url,
                            'files_filesets': f'files_filesets/{self.file_accession}',
                            'label': 'regulatory element effect on chromatin accessibility',
                            'name': 'modulates accessibility of',
                            'inverse_name': 'accessibility modulated by',
                            'class': self.file_fileset['class'],
                            'method': self.file_fileset['method'],
                            'crispr_modality': self.file_fileset.get('crispr_modality'),
                            'biological_context': self.file_fileset['simple_sample_summaries'][0],
                            'biosample_term': self.file_fileset['samples'][0],
                            'treatments_term_ids': self.file_fileset['treatments_term_ids'],
                            **metrics,
                        })
                except (ValueError, TypeError) as error:
                    raise ValueError(
                        f'{self.file_accession} line {line}: {error}') from error
        if self.label == 'genomic_element':
            for doc in elements.values():
                self._write_doc(doc)
