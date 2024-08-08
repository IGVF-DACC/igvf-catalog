from adapters import Adapter
import gzip
import json
import os
from db.arango_db import ArangoDB

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


class GencodeStructure(Adapter):
    ALLOWED_KEYS = ['gene_id', 'gene_name',
                    'transcript_id', 'transcript_name', 'exon_number', 'exon_id']

    # should strand be added to transcripts collection?
    INDEX = {'chr': 0, 'type': 2, 'coord_start': 3,
             'coord_end': 4, 'strand': 6, 'info': 8}

    STRUCTURE_TYPES = ['CDS', 'UTR', 'exon', 'start_codon',
                       'stop_codon']  # todo: check Selenocysteine

    ALLOWED_LABELS = [
        'gene_structure',  # human
        'mm_gene_structure'  # mouse
    ]

    OUTPUT_FOLDER = './parsed-data'

    def __init__(self, filepath=None, chr='all', label='gene_structure', dry_run=False):
        if label not in GencodeStructure.ALLOWED_LABELS:
            raise ValueError('Ivalid label. Allowed values: ' +
                             ','.join(GencodeStructure.ALLOWED_LABELS))
        self.filepath = filepath
        self.chr = chr
        self.label = label
        self.dry_run = dry_run
        self.organism = 'Homo sapiens'
        self.output_filepath = '{}/{}.json'.format(
            GencodeStructure.OUTPUT_FOLDER,
            self.label
        )
        self.SKIP_BIOCYPHER = True

        if self.label == 'gene_structure':
            self.version = 'v43'
            self.source_url = 'https://www.gencodegenes.org/human/'
        else:
            self.organism = 'Mus musculus'
            self.version = 'vM33'
            self.source_url = 'https://www.gencodegenes.org/mouse/'

        super(GencodeStructure, self).__init__()

    def parse_info_metadata(self, info):
        parsed_info = {}
        for key, value in zip(info, info[1:]):
            if key in GencodeStructure.ALLOWED_KEYS:
                parsed_info[key] = value.replace('"', '').replace(';', '')
        return parsed_info

    def process_file(self):
        parsed_data_file = open(self.output_filepath, 'w')
        UTR_keys = set()
        exon_transcript = None
        last_exon_end = 0
        for line in open(self.filepath, 'r'):
            if line.startswith('#'):
                continue
            split_line = line.strip().split()
            type = split_line[GencodeStructure.INDEX['type']]

            if type in GencodeStructure.STRUCTURE_TYPES:
                info = self.parse_info_metadata(
                    split_line[GencodeStructure.INDEX['info']:])

                key = '_'.join([info['transcript_id'].split(
                    '.')[0], info['exon_id'].split('.')[0], type])

                if type == 'UTR':
                    if key in UTR_keys:
                        # for cases where the exon has both 3' UTR & 5' UTR (e.g. exon ENSE00003709741.1 of ENST00000609375.1)
                        key = key + '_2'
                    else:
                        UTR_keys.add(key)

                to_json = {
                    # exon_id along is not unique, same exon_id can be in multiple transcripts
                    '_key': key,
                    # dropped gene_name since it's part of the transcript_name
                    'name': info['transcript_name'] + '_exon_' + info['exon_number'] + '_' + type,
                    'chr': split_line[GencodeStructure.INDEX['chr']],
                    # the gtf file format is [1-based,1-based], needs to convert to BED format [0-based,1-based]
                    'start:long': int(split_line[GencodeStructure.INDEX['coord_start']]) - 1,
                    'end:long': int(split_line[GencodeStructure.INDEX['coord_end']]),
                    'strand': split_line[GencodeStructure.INDEX['strand']],
                    'type': type,
                    'gene_name': info['gene_name'],
                    'transcript_name': info['transcript_name'],
                    # intron will be 1_2
                    'exon_number': str(info['exon_number']),
                    'exon_id': info['exon_id'],
                    'source': 'GENCODE',
                    'version': self.version,
                    'source_url': self.source_url,
                    'organism': self.organism
                }

                json.dump(to_json, parsed_data_file)
                parsed_data_file.write('\n')

                # checked the gtf file is sorted by transcript_id & exon_number so this should work
                if type == 'exon':
                    if info['transcript_id'] == exon_transcript:
                        intron_start = last_exon_end if GencodeStructure.INDEX[
                            'strand'] == '+' else split_line[GencodeStructure.INDEX['coord_end']]
                        intron_end = int(
                            split_line[GencodeStructure.INDEX['coord_start']]) - 1 if GencodeStructure.INDEX['strand'] == '+' else last_exon_end - 1
                        intron_exon_number = str(
                            int(info['exon_number']) - 1) + '_' + info['exon_number']
                        to_json = {
                            '_key': '_'.join([info['transcript_id'].split('.')[0], info['exon_id'].split('.')[0], 'intron']),
                            'name': info['transcript_name'] + '_exon_' + intron_exon_number + '_intron',
                            'chr': split_line[GencodeStructure.INDEX['chr']],
                            'start:long': intron_start,
                            'end:long': intron_end,
                            'strand': split_line[GencodeStructure.INDEX['strand']],
                            'type': 'intron',
                            'gene_name': info['gene_name'],
                            'transcript_name': info['transcript_name'],
                            # the first intron will be 1_2
                            'exon_number': intron_exon_number,
                            'source': 'GENCODE',
                            'version': self.version,
                            'source_url': self.source_url,
                            'organism': self.organism
                        }

                        json.dump(to_json, parsed_data_file)
                        parsed_data_file.write('\n')

                    exon_transcript = info['transcript_id']
                    # the 'closer' end to the next exon
                    last_exon_end = int(
                        split_line[GencodeStructure.INDEX['coord_end']]) if GencodeStructure.INDEX['strand'] == '+' else int(
                        split_line[GencodeStructure.INDEX['coord_start']])

        parsed_data_file.close()
        self.save_to_arango()

    def arangodb(self):
        return ArangoDB().generate_json_import_statement(self.output_filepath, self.collection)

    def save_to_arango(self):
        if self.dry_run:
            print(self.arangodb()[0])
        else:
            os.system(self.arangodb()[0])
