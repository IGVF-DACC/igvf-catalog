"""IGVF gene programs, membership, regulator effects, and targeted elements.

Program definitions, regulator results, and program correlations share this
adapter, including correlations between regulators.
Correlation files are optional: other labels never read or require them.
Regulator coordinates are GRCh38, 0-based, end-exclusive.
Supplied program/GO annotations are ignored.
"""

import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Optional

from adapters.base import BaseAdapter
from adapters.gene_validator import GeneValidator
from adapters.helpers import build_regulatory_region_id, get_file_fileset_by_accession_in_arangodb
from adapters.writer import Writer


class GenePrograms(BaseAdapter):
    ALLOWED_LABELS = ['gene_program', 'gene_program_membership',
                      'gene_program_regulation', 'genomic_element',
                      'genomic_element_regulator_correlation', 'gene_program_correlation',
                      'regulator_correlation']
    REQUIRED_COLUMNS = {'program_id', 'gene', 'score'}
    REGULATOR_COLUMNS = {
        'program_id', 'gene', 'genomic_element', 'genomic_element_coordinates',
        'log2FC', 'reference_group', 'test_statistic', 'p_nominal_nlog10',
        'fdr_nlog10', 'fdr_method',
    }
    SIGNIFICANCE_NLOG10 = -math.log10(0.05)
    CORRELATION_ELEMENT_COLUMNS = {
        f'{field}_{side}' for side in (1, 2)
        for field in ('gene', 'genomic_element', 'genomic_element_coordinates')
    }

    def __init__(self, filepath, label='gene_program', writer: Optional[Writer] = None,
                 validate=True, reference_filepath=None, **kwargs):
        self.reference_filepath = reference_filepath
        self.file_accession = Path(filepath).name.split('.')[0]
        if not re.fullmatch(r'IGVFFI[0-9]{4}[A-Z]{4}', self.file_accession):
            raise ValueError(
                'Gene-program input filename must begin with its IGVF file accession')
        super().__init__(filepath, label, writer, validate)

    def _get_schema_collection(self):
        if self.label == 'regulator_correlation':
            return 'edges', 'genes_genes'
        if self.label == 'gene_program_correlation':
            return 'edges', 'gene_programs_gene_programs'
        if self.label == 'gene_program':
            return 'nodes', 'gene_programs'
        if self.label in ('genomic_element', 'genomic_element_regulator_correlation'):
            return 'nodes', 'genomic_elements'
        return 'edges', 'genes_gene_programs'

    @staticmethod
    def program_key(defining_file_accession, program_id):
        """Condition-specific relationship files must use the shared defining file."""
        if not re.fullmatch(r'[A-Za-z0-9_-]+', program_id):
            raise ValueError(f'Invalid program ID: {program_id!r}')
        return f'{defining_file_accession}_{program_id}'

    @staticmethod
    def _rows(filepath, required_columns):
        opener = gzip.open if str(filepath).endswith('.gz') else open
        with opener(filepath, 'rt', encoding='utf-8-sig', newline='') as source:
            # TeloHAEC definitions have metadata comments before the TSV header.
            reader = csv.DictReader(
                (line for line in source if line.strip()
                 and not line.startswith('#')),
                delimiter='\t',
            )
            missing = required_columns - set(reader.fieldnames or [])
            if missing:
                raise ValueError(
                    f'Missing gene-program columns: {", ".join(sorted(missing))}')
            for row in reader:
                if None in row or any(value is None for value in row.values()):
                    raise ValueError(
                        f'Malformed gene-program row {reader.line_num}')
                yield row

    def _read_program_genes(self, filepath=None):
        programs = {}
        for row in self._rows(filepath or self.filepath, self.REQUIRED_COLUMNS):
            program_id = row['program_id'].strip()
            self.program_key(self.file_accession, program_id)
            gene = row['gene'].strip()
            if not gene:
                raise ValueError(f'Missing gene for program {program_id}')
            # Catalog gene keys omit Ensembl versions, retaining PAR suffixes.
            gene = re.sub(r'\.\d+(?=_PAR_Y$|$)', '', gene)
            if not re.fullmatch(r'ENSG[0-9]{11}(?:_PAR_Y)?', gene):
                raise ValueError(f'Invalid Ensembl gene ID: {gene!r}')
            try:
                score = float(row['score'])
            except ValueError as error:
                raise ValueError(
                    f'Invalid membership score for {program_id}/{gene}') from error
            if not math.isfinite(score):
                raise ValueError(
                    f'Non-finite membership score for {program_id}/{gene}')
            genes = programs.setdefault(program_id, {})
            if gene in genes:
                raise ValueError(
                    f'Duplicate member {gene} in program {program_id}')
            genes[gene] = score
        if not programs:
            raise ValueError(
                'Gene-program input contains no program definitions')
        return programs

    def _provenance(self, accession=None):
        accession = accession or self.file_accession
        metadata = get_file_fileset_by_accession_in_arangodb(
            accession)
        if not metadata:
            raise ValueError(
                f'Load files_filesets metadata for {accession} before gene programs')
        self.writer.add_tag('portal_accessions', accession)
        if metadata.get('file_set_id'):
            self.writer.add_tag('portal_accessions', metadata['file_set_id'])
        sample_summaries = metadata.get('simple_sample_summaries') or []
        provenance = {
            'source': 'IGVF',
            'source_url': f'https://data.igvf.org/tabular-files/{accession}/',
            'files_filesets': f'files_filesets/{accession}',
            'class': metadata['class'],
            'method': metadata.get('method'),
            'label': metadata.get('method'),
            'biological_context': sample_summaries[0] if sample_summaries else None,
            'treatments_term_ids': metadata.get('treatments_term_ids'),
            'perturbation': metadata.get('perturbation'),
        }
        samples = metadata.get('samples') or []
        if samples:
            provenance['biosample_term'] = samples[0]
        # Temporary attribution requested for the shared iPSC-to-EC programs.
        # TODO: revisit when biosample context supports multiple terms; the
        # current singular field represents these programs as endothelial cell.
        # Keep this explanation in the adapter, not in the emitted records.
        if accession == 'IGVFFI6391GCJR':
            provenance['biosample_term'] = 'ontology_terms/CL_0000115'
        return provenance

    def parse(self):
        if self.label == 'gene_program_correlation':
            self._parse_program_correlations()
            return
        if self.label in ('genomic_element_regulator_correlation', 'regulator_correlation'):
            self._parse_regulator_correlations()
            return
        if self.label in ('gene_program_regulation', 'genomic_element'):
            self._parse_regulators()
            return
        programs = self._read_program_genes()
        provenance = self._provenance()
        gene_validator = GeneValidator() if self.label == 'gene_program_membership' else None
        for program_id, genes in programs.items():
            program_key = self.program_key(self.file_accession, program_id)
            if self.label == 'gene_program':
                self._write({
                    **provenance,
                    '_key': program_key,
                    'name': program_id,
                    'program_id': program_id,
                    'reported_gene_count': len(genes),
                })
            else:
                for gene, score in genes.items():
                    if not gene_validator.validate(gene):
                        continue
                    self._write({
                        **provenance,
                        '_key': f'{program_key}_{gene}_membership',
                        '_from': f'genes/{gene}',
                        '_to': f'gene_programs/{program_key}',
                        'name': 'is a member of',
                        'inverse_name': 'has member',
                        'score': score,
                    })
        if gene_validator is not None:
            gene_validator.log()

    def _reference_programs(self):
        if not self.reference_filepath:
            raise ValueError(
                'Relationship inputs require program definitions via --reference-filepath')
        reference = Path(self.reference_filepath)
        if not reference.is_file():
            raise ValueError(f'Missing program definitions: {reference}')
        accession = reference.name.split('.')[0]
        if not re.fullmatch(r'IGVFFI[0-9]{4}[A-Z]{4}', accession):
            raise ValueError(
                'Program definition filename must begin with its IGVF file accession')
        return accession, self._read_program_genes(reference)

    @staticmethod
    def _regulator_number(value, field, optional=False):
        if optional and value.strip().lower() in ('', 'na', 'n/a', 'nan', 'null', '.'):
            return None
        try:
            number = float(value)
        except ValueError as error:
            raise ValueError(
                f'Invalid regulator {field}: {value!r}') from error
        if not math.isfinite(number):
            raise ValueError(f'Non-finite regulator {field}: {value!r}')
        return number

    def _regulator_elements(self, row, gene, accession=None):
        if row['genomic_element'].strip() != 'promoter':
            raise ValueError(
                f'Unsupported regulator genomic_element: {row["genomic_element"]!r}')
        elements = {}
        for interval in row['genomic_element_coordinates'].split(','):
            match = re.fullmatch(
                r'(chr[A-Za-z0-9_.-]+):(\d+)-(\d+)', interval.strip())
            if not match:
                raise ValueError(
                    f'Invalid regulator coordinates: {interval!r}')
            chrom, start, end = match.groups()
            start, end = int(start), int(end)
            if end <= start:
                raise ValueError(f'Invalid regulator interval: {interval!r}')
            # Coordinates are already 0-based, end-exclusive; do not shift them.
            key = build_regulatory_region_id(
                chrom, start, end, 'CRISPR', assembly='GRCh38')
            # A shared interval can be a promoter for multiple genes. Preserve
            # each gene association without overwriting the scalar promoter_of.
            key += f'_{gene}_{accession or self.file_accession}'
            elements[key] = {
                '_key': key, 'name': key, 'chr': chrom, 'start': start, 'end': end,
                'type': 'tested elements', 'source_annotation': 'promoter',
                'promoter_of': f'genes/{gene}',
            }
        return elements

    def _parse_regulators(self):
        defining_accession, programs = self._reference_programs()
        provenance = self._provenance()
        gene_validator = GeneValidator()
        seen_pairs = set()
        emitted_elements = set()
        negative_nominal_count = 0
        row_count = 0
        for row in self._rows(self.filepath, self.REGULATOR_COLUMNS):
            row_count += 1
            program_id = row['program_id'].strip()
            if program_id not in programs:
                raise ValueError(
                    f'Program {program_id!r} is not defined in {defining_accession}')
            gene = re.sub(r'\.\d+(?=_PAR_Y$|$)', '', row['gene'].strip())
            if not re.fullmatch(r'ENSG[0-9]{11}(?:_PAR_Y)?', gene):
                raise ValueError(
                    f'Invalid regulator Ensembl gene ID: {gene!r}')
            pair = (program_id, gene)
            if pair in seen_pairs:
                raise ValueError(
                    f'Duplicate regulator result for {program_id}/{gene}')
            seen_pairs.add(pair)
            elements = self._regulator_elements(row, gene)
            metrics = {
                'log2FC': self._regulator_number(row['log2FC'], 'log2FC'),
                'test_statistic': self._regulator_number(row['test_statistic'], 'test_statistic'),
                'neg_log10_pvalue': self._regulator_number(row['p_nominal_nlog10'], 'p_nominal_nlog10', optional=True),
                'neg_log10_pvalue_adj': self._regulator_number(row['fdr_nlog10'], 'fdr_nlog10', optional=True),
            }
            adjusted = metrics['neg_log10_pvalue_adj']
            if adjusted is not None and adjusted < 0:
                raise ValueError(
                    f'Negative fdr_nlog10 for {program_id}/{gene}')
            if metrics['neg_log10_pvalue'] is not None and metrics['neg_log10_pvalue'] < 0:
                negative_nominal_count += 1
            reference_group = row['reference_group'].strip()
            if not reference_group:
                raise ValueError(
                    f'Missing reference_group for {program_id}/{gene}')
            if not gene_validator.validate(gene):
                continue
            if self.label == 'genomic_element':
                for key, element in elements.items():
                    if key not in emitted_elements:
                        self._write({**provenance, **element})
                        emitted_elements.add(key)
            else:
                program_key = self.program_key(defining_accession, program_id)
                self._write({
                    **provenance, **metrics,
                    '_key': f'{self.file_accession}_{program_key}_{gene}_regulation',
                    '_from': f'genes/{gene}', '_to': f'gene_programs/{program_key}',
                    'name': 'regulates', 'inverse_name': 'regulated by',
                    'genomic_elements': [f'genomic_elements/{key}' for key in elements],
                    'reference_group': reference_group,
                    'fdr_method': row['fdr_method'].strip() or None,
                    'significant': adjusted > self.SIGNIFICANCE_NLOG10 if adjusted is not None else None,
                })
        if row_count == 0:
            raise ValueError('Regulator input contains no results')
        if negative_nominal_count:
            self.logger.warning(
                'Preserved %s submitted negative p_nominal_nlog10 values', negative_nominal_count)
        gene_validator.log()

    def _parse_program_correlations(self):
        defining_accession, programs = self._reference_programs()
        provenance = self._provenance()
        seen_pairs = {}
        columns = {'program_1_id', 'program_2_id', 'pearson_correlation'}
        for row in self._rows(self.filepath, columns):
            pair = tuple(
                sorted((row['program_1_id'].strip(), row['program_2_id'].strip())))
            for program_id in pair:
                if program_id not in programs:
                    raise ValueError(
                        f'Program {program_id!r} is not defined in {defining_accession}')
            try:
                correlation = float(row['pearson_correlation'])
            except ValueError as error:
                raise ValueError(
                    f'Invalid Pearson correlation for {pair}') from error
            if not math.isfinite(correlation) or not -1 <= correlation <= 1:
                raise ValueError(
                    f'Pearson correlation must be finite and within [-1, 1]: {pair}')
            if pair in seen_pairs:
                if seen_pairs[pair] != correlation:
                    raise ValueError(
                        f'Conflicting Pearson correlations for {pair}')
                continue
            seen_pairs[pair] = correlation
            # Pearson correlation is symmetric. Canonical ordering also makes
            # keys stable if a submitter reverses the columns or row order.
            # Hash an encoded pair to avoid ambiguous delimiters in program IDs.
            pair_key = hashlib.sha256(json.dumps(pair).encode()).hexdigest()
            self._write({
                **provenance,
                '_key': f'{self.file_accession}_{defining_accession}_{pair_key}_correlation',
                '_from': f'gene_programs/{self.program_key(defining_accession, pair[0])}',
                '_to': f'gene_programs/{self.program_key(defining_accession, pair[1])}',
                'name': 'correlated with', 'inverse_name': 'correlated with',
                'pearson_correlation': correlation,
            })
        if not seen_pairs:
            raise ValueError('Program correlation input contains no results')

    @staticmethod
    def _regulator_gene(value):
        gene = re.sub(r'\.\d+(?=_PAR_Y$|$)', '', value.strip())
        if not re.fullmatch(r'ENSG[0-9]{11}(?:_PAR_Y)?', gene):
            raise ValueError(f'Invalid regulator Ensembl gene ID: {gene!r}')
        return gene

    def _reference_regulators(self):
        if not self.reference_filepath:
            raise ValueError(
                'Regulator correlations require upstream regulator results via --reference-filepath')
        reference = Path(self.reference_filepath)
        if not reference.is_file():
            raise ValueError(
                f'Missing upstream regulator results: {reference}')
        accession = reference.name.split('.')[0]
        if not re.fullmatch(r'IGVFFI[0-9]{4}[A-Z]{4}', accession):
            raise ValueError(
                'Regulator reference filename must begin with its IGVF file accession')
        elements_by_gene = {}
        seen_annotations = set()
        for row in self._rows(reference, self.REGULATOR_COLUMNS):
            annotation = (row['gene'], row['genomic_element'],
                          row['genomic_element_coordinates'])
            if annotation in seen_annotations:
                continue
            gene = self._regulator_gene(row['gene'])
            elements_by_gene.setdefault(gene, {}).update(
                self._regulator_elements(row, gene, accession))
            seen_annotations.add(annotation)
        if not elements_by_gene:
            raise ValueError('Upstream regulator input contains no results')
        return accession, elements_by_gene

    def _parse_regulator_correlations(self):
        upstream_accession, upstream_elements = self._reference_regulators()
        nodes_only = self.label == 'genomic_element_regulator_correlation'
        provenance = self._provenance(
            upstream_accession if nodes_only else self.file_accession)
        self.writer.add_tag('portal_accessions', upstream_accession)
        gene_validator = GeneValidator()
        valid_genes = {gene: gene_validator.validate(
            gene) for gene in upstream_elements}
        gene_indices = {gene: index for index,
                        gene in enumerate(sorted(upstream_elements))}
        # One bit per unordered pair (including the diagonal): about 21 MiB
        # for 18,715 regulators, instead of a Python set with 175 million pairs.
        count = len(gene_indices)
        seen_pairs = bytearray(
            (count * (count + 1) // 2 + 7) // 8) if not nodes_only else None
        annotations = {}
        emitted_elements = set()
        row_count = 0
        columns = self.CORRELATION_ELEMENT_COLUMNS | (
            {'pearson_correlation'} if not nodes_only else set())
        for row in self._rows(self.filepath, columns):
            row_count += 1
            endpoints = []
            for side in (1, 2):
                annotation = tuple(row[f'{field}_{side}'].strip() for field in
                                   ('gene', 'genomic_element', 'genomic_element_coordinates'))
                if annotation not in annotations:
                    gene, element_type, coordinates = annotation
                    gene = self._regulator_gene(gene)
                    if gene not in upstream_elements:
                        raise ValueError(
                            f'Regulator {gene} is not defined in {upstream_accession}')
                    elements = self._regulator_elements({
                        'genomic_element': element_type,
                        'genomic_element_coordinates': coordinates,
                    }, gene, upstream_accession)
                    if not elements.keys() <= upstream_elements[gene].keys():
                        raise ValueError(
                            f'Regulator elements for {gene} do not match {upstream_accession}')
                    annotations[annotation] = (gene, sorted(elements))
                gene, keys = annotations[annotation]
                endpoints.append((gene, keys))
                if nodes_only and valid_genes[gene]:
                    for key in keys:
                        if key not in emitted_elements:
                            self._write(
                                {**provenance, **upstream_elements[gene][key]})
                            emitted_elements.add(key)
            if nodes_only:
                continue
            endpoints.sort(key=lambda endpoint: endpoint[0])
            (gene_from, keys_from), (gene_to, keys_to) = endpoints
            try:
                correlation = float(row['pearson_correlation'])
            except ValueError as error:
                raise ValueError(
                    f'Invalid Pearson correlation for {gene_from}/{gene_to}') from error
            if not math.isfinite(correlation) or not -1 <= correlation <= 1:
                raise ValueError(
                    f'Pearson correlation must be finite and within [-1, 1]: {gene_from}/{gene_to}')
            i, j = gene_indices[gene_from], gene_indices[gene_to]
            pair_index = j * (j + 1) // 2 + i
            byte, bit = divmod(pair_index, 8)
            mask = 1 << bit
            if seen_pairs[byte] & mask:
                raise ValueError(
                    f'Duplicate regulator correlation pair: {gene_from}/{gene_to}')
            seen_pairs[byte] |= mask
            if not valid_genes[gene_from] or not valid_genes[gene_to]:
                continue
            self._write({
                **provenance,
                '_key': f'{self.file_accession}_{upstream_accession}_{gene_from}_{gene_to}_correlation',
                '_from': f'genes/{gene_from}', '_to': f'genes/{gene_to}',
                'name': 'correlated with', 'inverse_name': 'correlated with',
                'pearson_correlation': correlation,
                'genomic_elements_from': [f'genomic_elements/{key}' for key in keys_from],
                'genomic_elements_to': [f'genomic_elements/{key}' for key in keys_to],
            })
        if row_count == 0:
            raise ValueError('Regulator correlation input contains no results')
        gene_validator.log()

    def _write(self, props):
        self.validate_doc(props)
        self.writer.write(json.dumps(props, allow_nan=False))
        self.writer.write('\n')
