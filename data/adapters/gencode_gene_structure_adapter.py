import gzip
import json
import os
from typing import Optional

from adapters.writer import Writer

# Example genocde gtf input file:
# ##description: evidence-based annotation of the human genome (GRCh38), version 43 (Ensembl 109)
# ##provider: GENCODE
# ##contact: gencode-help@ebi.ac.uk
# ##format: gtf
# ##date: 2022-11-29
# chr1	HAVANA	gene	11869	14409	.	+	.	gene_id "ENSG00000290825.1"; gene_type "lncRNA"; gene_name "DDX11L2"; level 2; tag "overlaps_pseudogene";
# chr1	HAVANA	transcript	11869	14409	.	+	.	gene_id "ENSG00000290825.1"; transcript_id "ENST00000456328.2"; gene_type "lncRNA"; gene_name "DDX11L2"; transcript_type "lncRNA"; transcript_name "DDX11L2-202"; level 2; transcript_support_level "1"; tag "basic"; tag "Ensembl_canonical"; havana_transcript "OTTHUMT00000362751.1";
# chr1	HAVANA	exon	11869	12227	.	+	.	gene_id "ENSG00000290825.1"; transcript_id "ENST00000456328.2"; gene_type "lncRNA"; gene_name "DDX11L2"; transcript_type "lncRNA"; transcript_name "DDX11L2-202"; exon_number 1; exon_id "ENSE00002234944.1"; level 2; transcript_support_level "1"; tag "basic"; tag "Ensembl_canonical"; havana_transcript "OTTHUMT00000362751.1";
# chr1	HAVANA	exon	12613	12721	.	+	.	gene_id "ENSG00000290825.1"; transcript_id "ENST00000456328.2"; gene_type "lncRNA"; gene_name "DDX11L2"; transcript_type "lncRNA"; transcript_name "DDX11L2-202"; exon_number 2; exon_id "ENSE00003582793.1"; level 2; transcript_support_level "1"; tag "basic"; tag "Ensembl_canonical"; havana_transcript "OTTHUMT00000362751.1";

# Column three has the gene structure info we want to load. Each exon can have substructures of CDS, UTR, start_condon, and stop_condon, which will have the same exon_id.


class GencodeStructure:
    ALLOWED_KEYS = ['gene_id', 'gene_name',
                    'transcript_id', 'transcript_name', 'exon_number', 'exon_id']

    # should strand be added to transcripts collection?
    INDEX = {'chr': 0, 'type': 2, 'coord_start': 3,
             'coord_end': 4, 'strand': 6, 'info': 8}

    STRUCTURE_TYPES = ['CDS', 'UTR', 'exon', 'start_codon',
                       'stop_codon']  # todo: check Selenocysteine

    ALLOWED_LABELS = [
        'gene_structure',  # human
        'mm_gene_structure',  # mouse
        'transcript_contains_gene_structure',
        'mm_transcript_contains_mm_gene_structure'
    ]

    def __init__(self, filepath=None, chr='all', label='gene_structure', dry_run=True, writer: Optional[Writer] = None):
        if label not in GencodeStructure.ALLOWED_LABELS:
            raise ValueError('Invalid label. Allowed values: ' +
                             ','.join(GencodeStructure.ALLOWED_LABELS))
        self.filepath = filepath
        self.chr = chr
        self.label = label
        self.dry_run = dry_run
        self.source = 'GENCODE'
        self.organism = 'Homo sapiens'
        self.type = 'node'
        if self.label in ['transcript_contains_gene_structure', 'mm_transcript_contains_mm_gene_structure']:
            self.type = 'edge'
        self.transcript_endpoint = 'transcripts/'
        self.gene_structure_endpoint = 'genes_structure/'
        if self.label == 'mm_transcript_contains_mm_gene_structure':
            self.transcript_endpoint = 'mm_transcripts/'
            self.gene_structure_endpoint = 'mm_genes_structure/'

        if self.label in ['gene_structure', 'transcript_contains_gene_structure']:
            self.version = 'v43'
            self.source_url = 'https://www.gencodegenes.org/human/'
        else:
            self.organism = 'Mus musculus'
            self.version = 'vM33'
            self.source_url = 'https://www.gencodegenes.org/mouse/'
        self.writer = writer

    def parse_info_metadata(self, info):
        parsed_info = {}
        for key, value in zip(info, info[1:]):
            if key in GencodeStructure.ALLOWED_KEYS:
                parsed_info[key] = value.replace('"', '').replace(';', '')
        return parsed_info

    def process_file(self):
        self.writer.open()
        UTR_keys = set()
        exon_transcript = None
        last_exon_end = 0
        for line in open(self.filepath, 'r'):
            if line.startswith('#'):
                continue
            split_line = line.strip().split()
            gene_structure_type = split_line[GencodeStructure.INDEX['type']]

            if gene_structure_type not in GencodeStructure.STRUCTURE_TYPES:
                continue
            info = self.parse_info_metadata(
                split_line[GencodeStructure.INDEX['info']:])
            transcript_id_no_version = info['transcript_id'].split('.')[0]
            gene_id_no_version = info['gene_id'].split('.')[0]
            if info['transcript_id'].endswith('_PAR_Y'):
                transcript_id_no_version = transcript_id_no_version + '_PAR_Y'
            if info['gene_id'].endswith('_PAR_Y'):
                gene_id_no_version = gene_id_no_version + '_PAR_Y'
            key = '_'.join([transcript_id_no_version,
                            info['exon_id'].split('.')[0], gene_structure_type])

            if gene_structure_type == 'UTR':
                if key in UTR_keys:
                    # for cases where the exon has both 3' UTR & 5' UTR (e.g. exon ENSE00003709741.1 of ENST00000609375.1)
                    key = key + '_2'
                else:
                    UTR_keys.add(key)
            elif gene_structure_type in ['start_codon', 'stop_codon']:
                key = f'{key}_{info["exon_number"]}'

            if self.label in ['gene_structure', 'mm_gene_structure']:
                to_json = {
                    # exon_id along is not unique, same exon_id can be in multiple transcripts
                    '_key': key,
                    # dropped gene_name since it's part of the transcript_name
                    'name': info['transcript_name'] + '_exon_' + info['exon_number'] + '_' + gene_structure_type,
                    'chr': split_line[GencodeStructure.INDEX['chr']],
                    # the gtf file format is [1-based,1-based], needs to convert to BED format [0-based,1-based]
                    'start:long': int(split_line[GencodeStructure.INDEX['coord_start']]) - 1,
                    'end:long': int(split_line[GencodeStructure.INDEX['coord_end']]),
                    'strand': split_line[GencodeStructure.INDEX['strand']],
                    'type': gene_structure_type,
                    'gene_id': gene_id_no_version,
                    'gene_name': info['gene_name'],
                    'transcript_id': transcript_id_no_version,
                    'transcript_name': info['transcript_name'],
                    # intron will be 1_2
                    'exon_number': str(info['exon_number']),
                    'exon_id': info['exon_id'],
                    'source': self.source,
                    'version': self.version,
                    'source_url': self.source_url,
                    'organism': self.organism
                }
            elif self.label in ['transcript_contains_gene_structure', 'mm_transcript_contains_mm_gene_structure']:
                to_json = {
                    '_from': self.transcript_endpoint + transcript_id_no_version,
                    '_to': self.gene_structure_endpoint + key,
                    'source': self.source,
                    'version': self.version,
                    'source_url': self.source_url,
                    'organism': self.organism,
                    'name': 'contains',
                    'inverse_name': 'contained in'
                }

            self.writer.write(json.dumps(to_json))
            self.writer.write('\n')

            # checked the gtf file is sorted by transcript_id & exon_number so this should work
            if gene_structure_type == 'exon':
                if info['transcript_id'] == exon_transcript:
                    intron_start = last_exon_end if split_line[GencodeStructure.INDEX['strand']] == '+' else int(
                        split_line[GencodeStructure.INDEX['coord_end']])
                    intron_end = int(
                        split_line[GencodeStructure.INDEX['coord_start']]) - 1 if split_line[GencodeStructure.INDEX['strand']] == '+' else last_exon_end - 1
                    intron_exon_number = str(
                        int(info['exon_number']) - 1) + '_' + info['exon_number']
                    key = '_'.join([transcript_id_no_version,
                                   info['exon_id'].split('.')[0], 'intron'])
                    if self.label in ['gene_structure', 'mm_gene_structure']:
                        to_json = {
                            '_key': key,
                            'name': info['transcript_name'] + '_exon_' + intron_exon_number + '_intron',
                            'chr': split_line[GencodeStructure.INDEX['chr']],
                            'start:long': intron_start,
                            'end:long': intron_end,
                            'strand': split_line[GencodeStructure.INDEX['strand']],
                            'type': 'intron',
                            'gene_id': gene_id_no_version,
                            'gene_name': info['gene_name'],
                            'transcript_id': transcript_id_no_version,
                            'transcript_name': info['transcript_name'],
                            # the first intron will be 1_2
                            'exon_number': intron_exon_number,
                            'source': self.source,
                            'version': self.version,
                            'source_url': self.source_url,
                            'organism': self.organism
                        }
                    elif self.label in ['transcript_contains_gene_structure', 'mm_transcript_contains_mm_gene_structure']:
                        to_json = {
                            '_from': self.transcript_endpoint + transcript_id_no_version,
                            '_to': self.gene_structure_endpoint + key,
                            'source': self.source,
                            'version': self.version,
                            'source_url': self.source_url,
                            'organism': self.organism,
                            'name': 'contains',
                            'inverse_name': 'contained in'
                        }

                    self.writer.write(json.dumps(to_json))
                    self.writer.write('\n')

                exon_transcript = info['transcript_id']
                # the 'closer' end to the next exon
                last_exon_end = int(
                    split_line[GencodeStructure.INDEX['coord_end']]) if split_line[GencodeStructure.INDEX['strand']] == '+' else int(
                    split_line[GencodeStructure.INDEX['coord_start']])

        self.writer.close()
