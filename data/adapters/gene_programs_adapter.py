"""IGVF gene programs, membership, and eventually regulatory relationships.

The gene_program label emits nodes; gene_program_membership emits scored edges.
Supplied program/GO annotations are ignored.
"""

import csv
import gzip
import json
import math
from pathlib import Path
import re
from typing import Optional

from adapters.base import BaseAdapter
from adapters.gene_validator import GeneValidator
from adapters.helpers import get_file_fileset_by_accession_in_arangodb
from adapters.writer import Writer


class GenePrograms(BaseAdapter):
    ALLOWED_LABELS = ['gene_program', 'gene_program_membership']
    REQUIRED_COLUMNS = {'program_id', 'gene', 'score'}

    def __init__(self, filepath, label='gene_program', writer: Optional[Writer] = None,
                 validate=True, **kwargs):
        self.file_accession = Path(filepath).name.split('.')[0]
        if not re.fullmatch(r'IGVFFI[0-9]{4}[A-Z]{4}', self.file_accession):
            raise ValueError(
                'Gene-program input filename must begin with its IGVF file accession')
        super().__init__(filepath, label, writer, validate)

    def _get_schema_collection(self):
        if self.label == 'gene_program':
            return 'nodes', 'gene_programs'
        return 'edges', 'genes_gene_programs'

    @staticmethod
    def program_key(defining_file_accession, program_id):
        """Condition-specific relationship files must use the shared defining file."""
        if not re.fullmatch(r'[A-Za-z0-9_-]+', program_id):
            raise ValueError(f'Invalid program ID: {program_id!r}')
        return f'{defining_file_accession}_{program_id}'

    def _read_program_genes(self):
        programs = {}
        opener = gzip.open if str(self.filepath).endswith('.gz') else open
        with opener(self.filepath, 'rt', encoding='utf-8-sig', newline='') as source:
            # TeloHAEC definitions have metadata comments before the TSV header.
            reader = csv.DictReader(
                (line for line in source if line.strip()
                 and not line.startswith('#')),
                delimiter='\t',
            )
            missing = self.REQUIRED_COLUMNS - set(reader.fieldnames or [])
            if missing:
                raise ValueError(
                    f'Missing gene-program columns: {", ".join(sorted(missing))}')
            for row in reader:
                if None in row or any(value is None for value in row.values()):
                    raise ValueError(
                        f'Malformed gene-program row {reader.line_num}')
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

    def parse(self):
        programs = self._read_program_genes()
        metadata = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        if not metadata:
            raise ValueError(
                f'Load files_filesets metadata for {self.file_accession} before gene programs')
        self.writer.add_tag('portal_accessions', self.file_accession)
        if metadata.get('file_set_id'):
            self.writer.add_tag('portal_accessions', metadata['file_set_id'])
        sample_summaries = metadata.get('simple_sample_summaries') or []
        provenance = {
            'source': 'IGVF',
            'source_url': f'https://data.igvf.org/tabular-files/{self.file_accession}/',
            'files_filesets': f'files_filesets/{self.file_accession}',
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
        if self.file_accession == 'IGVFFI6391GCJR':
            provenance['biosample_term'] = 'ontology_terms/CL_0000115'
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

    def _write(self, props):
        self.validate_doc(props)
        self.writer.write(json.dumps(props, allow_nan=False))
        self.writer.write('\n')
