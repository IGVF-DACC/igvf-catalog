import csv
import gzip
import json
from typing import Optional

from adapters.helpers import build_regulatory_region_id, parse_guide_file
from adapters.file_fileset_adapter import FileFileSet
from adapters.gene_validator import GeneValidator
from adapters.writer import Writer

# Example rows from Gersbach's CRISPR screen data
# rowID baseMean    log2FoldChange  lfcSE   stat    pvalue  padj
# AHCTF1_1    403.0544398 -0.430896793    0.483371961 -0.891439364    0.372693508 0.842070692
# AHCTF1_2  422.638436 -0.109560771 0.517889371 -0.211552461    0.8324562   0.969028334
# AHCTF1_3  537.6979771 0.231612028 0.431039354 0.537333832 0.59103704  0.932431857


class GersbachE2GCRISPR:

    ALLOWED_LABELS = [
        'genomic_element',
        'genomic_element_gene'
    ]
    SOURCE = 'IGVF'

    def __init__(self, filepath, reference_filepath, label, source_url, writer: Optional[Writer] = None, **kwargs):
        if label not in GersbachE2GCRISPR.ALLOWED_LABELS:
            raise ValueError('Ivalid label. Allowed values: ' +
                             ','.join(GersbachE2GCRISPR.ALLOWED_LABELS))
        self.data_file = filepath
        self.guide_file = reference_filepath
        self.label = label
        self.source_url = source_url
        self.file_accession = source_url.split('/')[-2]
        self.dataset = label
        self.type = 'edge'
        if (self.label == 'genomic_element'):
            self.type = 'node'
        self.writer = writer
        self.gene_validator = GeneValidator()
        self.files_filesets = FileFileSet(
            self.file_accession, writer=None, label='igvf_file_fileset')

    def process_file(self):
        self.writer.open()

        file_set_props, _, _ = self.files_filesets.query_fileset_files_props_igvf(
            self.file_accession, replace=False)
        simple_sample_summaries = file_set_props['simple_sample_summaries']
        biosample_term = file_set_props['samples']
        treatments_term_ids = file_set_props['treatments_term_ids']
        method = file_set_props['method']

        guide_rna_sequences = parse_guide_file(self.guide_file)
        genomic_elements = {}
        guide_id_to_element_id = {}
        for guide_id, guide_rna in guide_rna_sequences.items():
            name = guide_rna.get('intended_target_name')
            gene = name.split('.')[0] if (
                name and name.startswith('ENSG')) else None
            if gene:
                if not self.gene_validator.validate(gene):
                    raise ValueError(f'{gene} is not a valid gene.')
            chr = guide_rna.get('intended_target_chr')
            start = guide_rna.get('intended_target_start')
            end = guide_rna.get('intended_target_end')
            if gene and chr and start is not None and end is not None:
                element_id = build_regulatory_region_id(
                    chr, start, end, 'CRISPR'
                )
                guide_id_to_element_id[guide_id] = element_id
                if element_id not in genomic_elements:
                    genomic_elements[element_id] = {
                        'gene': gene, 'chr': chr, 'start': start, 'end': end}
        if self.label == 'genomic_element':
            for genomic_element in genomic_elements:
                source_annotation = 'promoter'
                if genomic_elements[genomic_element]['end'] - genomic_elements[genomic_element]['start'] == 1:
                    source_annotation = 'transcription start site'
                _id = genomic_element + '_' + self.file_accession
                _props = {
                    '_key': _id,
                    'name': _id,
                    'chr': genomic_elements[genomic_element]['chr'],
                    'start': genomic_elements[genomic_element]['start'],
                    'end': genomic_elements[genomic_element]['end'],
                    'method': method,
                    'source_annotation': source_annotation,
                    'source': GersbachE2GCRISPR.SOURCE,
                    'source_url': self.source_url,
                    'type': 'tested elements',
                    'files_filesets': 'files_filesets/' + self.file_accession
                }
                self.writer.write(json.dumps(_props))
                self.writer.write('\n')
        elif self.label == 'genomic_element_gene':
            with gzip.open(self.data_file, 'rt') as data_file:
                reader = csv.reader(data_file, delimiter='\t')
                next(reader)
                for row in reader:
                    guide_id = row[0]
                    if guide_rna_sequences[guide_id]['type'] == 'non-targeting':
                        continue
                    if guide_id not in guide_id_to_element_id:
                        raise ValueError(
                            f'{guide_id} is listed in the data file but not in the reference data file of the guide RNA sequences.')
                    element_id = guide_id_to_element_id[guide_id]
                    gene = genomic_elements[element_id]['gene']
                    baseMean = float(row[1])
                    log2FC = float(row[2])
                    lfcSE = float(row[3])
                    stat = float(row[4])
                    pvalue = float(row[5])
                    padj = float(row[6])
                    _id = '_'.join([element_id, gene, self.file_accession])
                    _source = 'genomic_elements/' + element_id + '_' + self.file_accession
                    _props = {
                        '_key': _id,
                        '_from': _source,
                        '_to': 'genes/' + gene,
                        'baseMean': baseMean,
                        'log2FC': log2FC,
                        'lfcSE': lfcSE,
                        'stat': stat,
                        'pvalue': pvalue,
                        'padj': padj,
                        'source': GersbachE2GCRISPR.SOURCE,
                        'source_url': self.source_url,
                        'files_filesets': 'files_filesets/' + self.file_accession,
                        'label': f'element effect on gene expression of {gene}',
                        'name': 'modulates expression of',
                        'inverse_name': 'expression modulated by',
                        'method': method,
                        'simple_sample_summaries': simple_sample_summaries,
                        'biological_context': biosample_term,
                        'treatments_term_ids': treatments_term_ids,
                    }
                    self.writer.write(json.dumps(_props))
                    self.writer.write('\n')
        self.writer.close()
