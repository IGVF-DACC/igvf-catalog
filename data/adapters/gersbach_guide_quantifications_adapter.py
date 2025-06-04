import csv
import gzip
import json
from typing import Optional

from adapters.helpers import build_regulatory_region_id, parse_guide_file
from adapters.file_fileset_adapter import query_fileset_files_props_igvf
from adapters.writer import Writer

# Example rows from Gersbach's CRISPR screen data
# rowID baseMean    log2FoldChange  lfcSE   stat    pvalue  padj
# AHCTF1_1    403.0544398 -0.430896793    0.483371961 -0.891439364    0.372693508 0.842070692
# AHCTF1_2  422.638436 -0.109560771 0.517889371 -0.211552461    0.8324562   0.969028334
# AHCTF1_3  537.6979771 0.231612028 0.431039354 0.537333832 0.59103704  0.932431857


class GersbachGuideQuantifications:

    ALLOWED_LABELS = [
        'genomic_element',
        'genomic_element_gene'
    ]
    SOURCE = 'IGVF'

    def __init__(self, quantification_filepath, guide_filepath, label, source_url, biological_context, writer: Optional[Writer] = None, **kwargs):
        if label not in GersbachGuideQuantifications.ALLOWED_LABELS:
            raise ValueError('Ivalid label. Allowed values: ' +
                             ','.join(GersbachGuideQuantifications.ALLOWED_LABELS))
        self.quantification_filepath = quantification_filepath
        self.guide_filepath = guide_filepath
        self.label = label
        self.source_url = source_url
        self.file_accession = source_url.split('/')[-2]
        self.biological_context = biological_context
        self.dataset = label
        self.type = 'edge'
        if (self.label == 'genomic_element'):
            self.type = 'node'
        self.writer = writer

    def process_file(self):
        self.writer.open()
        guide_rna_sequences = parse_guide_file(self.guide_filepath)
        genomic_elements = {}
        for guide_id, guide_rna in guide_rna_sequences.items():
            name = guide_rna.get('intended_target_name')
            gene = name.split('.')[0] if name.startswith('ENSG') else None
            chr = guide_rna.get('intended_target_chr')
            start = guide_rna.get('intended_target_start')
            end = guide_rna.get('intended_target_end')
            guide_id_to_element_id = {}
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
                element_type = 'promoter'
                if genomic_elements[genomic_element]['end'] - genomic_elements[genomic_element]['start']:
                    element_type = 'transcription start site'
                _id = genomic_element + '_' + self.file_accession
                _props = {
                    '_key': _id,
                    'name': _id,
                    'chr': genomic_elements[genomic_element]['chr'],
                    'start': genomic_elements[genomic_element]['start'],
                    'end': genomic_elements[genomic_element]['end'],
                    'method_type': 'CRISPR',
                    'type': element_type,
                    'source': GersbachGuideQuantifications.SOURCE,
                    'source_url': self.source_url,
                    'files_filesets': 'files_filesets/' + self.file_accession
                }
                self.writer.write(json.dumps(_props))
                self.writer.write('\n')
        elif self.label == 'genomic_element_gene':
            file_set_props = query_fileset_files_props_igvf(
                self, self.file_accession)
            biosample_context = file_set_props['simple_sample_summaries']
            biosample_term = file_set_props['samples']
            biosample_qualifier = file_set_props['treatments_term_ids']
            with gzip.open(self.quantification_filepath, 'rt') as quantification_filepath:
                reader = csv.reader(quantification_filepath, delimiter='\t')
                next(reader)
                for row in reader:
                    guide_id = row[0]
                    if guide_id not in guide_id_to_element_id:
                        raise ValueError(
                            f'{guide_id} not in guide RNA sequences file.')
                    element_id = guide_id_to_element_id[guide_id]
                    gene = genomic_elements[element_id]['gene']
                    log2FC = float(row[2])
                    _id = '_'.join([element_id, gene, self.file_accession])
                    _source = 'genomic_elements/' + element_id + '_' + self.file_accession
                    _props = {
                        '_key': _id,
                        '_from': _source,
                        '_to': 'genomic_elements/' + element_id,
                        'log2FC': log2FC,
                        'source': GersbachGuideQuantifications.SOURCE,
                        'source_url': self.source_url,
                        'files_filesets': 'files_filesets/' + self.file_accession,
                        'name': 'modulates expression of',
                        'inverse_name': 'expression modulated by',
                        'biosample_context': biosample_context,
                        'biosample_term': biosample_term,
                        'biosample_qualifier': biosample_qualifier,
                    }
                    self.writer.write(json.dumps(_props))
                    self.writer.write('\n')
        self.writer.close()
