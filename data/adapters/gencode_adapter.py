import json
from typing import Optional

from adapters.writer import Writer
# Example genocde gtf input file:
# ##description: evidence-based annotation of the human genome (GRCh38), version 43 (Ensembl 109)
# ##provider: GENCODE
# ##contact: gencode-help@ebi.ac.uk
# ##format: gtf
# ##date: 2022-11-29
# chr1  HAVANA	gene	11869	14409	.	+	.	gene_id "ENSG00000290825.1"; gene_type "lncRNA"; gene_name "DDX11L2"; level 2; tag "overlaps_pseudogene";
# chr1	HAVANA	transcript	11869	14409	.	+	.	gene_id "ENSG00000290825.1"; transcript_id "ENST00000456328.2"; gene_type "lncRNA"; gene_name "DDX11L2"; transcript_type "lncRNA"; transcript_name "DDX11L2-202"; level 2; transcript_support_level "1"; tag "basic"; tag "Ensembl_canonical"; havana_transcript "OTTHUMT00000362751.1";
# chr1	HAVANA	exon	11869	12227	.	+	.	gene_id "ENSG00000290825.1"; transcript_id "ENST00000456328.2"; gene_type "lncRNA"; gene_name "DDX11L2"; transcript_type "lncRNA"; transcript_name "DDX11L2-202"; exon_number 1; exon_id "ENSE00002234944.1"; level 2; transcript_support_level "1"; tag "basic"; tag "Ensembl_canonical"; havana_transcript "OTTHUMT00000362751.1";
# chr1	HAVANA	exon	12613	12721	.	+	.	gene_id "ENSG00000290825.1"; transcript_id "ENST00000456328.2"; gene_type "lncRNA"; gene_name "DDX11L2"; transcript_type "lncRNA"; transcript_name "DDX11L2-202"; exon_number 2; exon_id "ENSE00003582793.1"; level 2; transcript_support_level "1"; tag "basic"; tag "Ensembl_canonical"; havana_transcript "OTTHUMT00000362751.1";


class Gencode:
    ALLOWED_LABELS = ['gencode_transcript',
                      'mm_gencode_transcript',
                      'transcribed_to', 'transcribed_from']
    ALLOWED_KEYS = ['gene_id', 'gene_type', 'gene_name',
                    'transcript_id', 'transcript_type', 'transcript_name']
    ALLOWED_ORGANISMS = ['HUMAN', 'MOUSE']

    INDEX = {'chr': 0, 'type': 2, 'coord_start': 3, 'coord_end': 4, 'info': 8}

    def __init__(self, filepath=None, label='gencode_transcript', organism='HUMAN', dry_run=True, writer: Optional[Writer] = None, **kwargs):
        if label not in Gencode.ALLOWED_LABELS:
            raise ValueError('Invalid labelS. Allowed values: ' +
                             ','.join(Gencode.ALLOWED_LABELS))

        self.filepath = filepath
        self.label = label
        self.organism = organism
        self.transcript_endpoint = 'transcripts/'
        self.gene_endpoint = 'genes/'
        self.version = 'v43'
        self.source_url = 'https://www.gencodegenes.org/human/'
        if self.organism == 'MOUSE':
            self.transcript_endpoint = 'mm_transcripts/'
            self.gene_endpoint = 'mm_genes/'
            self.version = 'vM33'
            self.source_url = 'https://www.gencodegenes.org/mouse/'
        self.dataset = label
        self.dry_run = dry_run
        self.type = 'edge'
        if(self.label in ['gencode_transcript', 'mm_gencode_transcript']):
            self.type = 'node'
        self.writer = writer

    def parse_info_metadata(self, info):
        parsed_info = {}
        for key, value in zip(info, info[1:]):
            if key in Gencode.ALLOWED_KEYS:
                parsed_info[key] = value.replace('"', '').replace(';', '')
        return parsed_info

    def process_file(self):
        self.writer.open()
        for line in open(self.filepath, 'r'):
            if line.startswith('#'):
                continue

            data_line = line.strip().split()
            if data_line[Gencode.INDEX['type']] != 'transcript':
                continue
            data = data_line[:Gencode.INDEX['info']]
            info = self.parse_info_metadata(data_line[Gencode.INDEX['info']:])
            transcript_key = info['transcript_id'].split('.')[0]
            if info['transcript_id'].endswith('_PAR_Y'):
                transcript_key = transcript_key + '_PAR_Y'
            gene_key = info['gene_id'].split('.')[0]
            if info['gene_id'].endswith('_PAR_Y'):
                gene_key = gene_key + '_PAR_Y'
            try:
                if self.label in ['gencode_transcript', 'mm_gencode_transcript']:
                    props = {
                        '_key': transcript_key,
                        'transcript_id': info['transcript_id'],
                        'name': info['transcript_name'],
                        'transcript_type': info['transcript_type'],
                        'chr': data[Gencode.INDEX['chr']],
                        # the gtf file format is [1-based,1-based], needs to convert to BED format [0-based,1-based]
                        'start': str(int(data[Gencode.INDEX['coord_start']]) - 1),
                        'end': data[Gencode.INDEX['coord_end']],
                        'gene_name': info['gene_name'],
                        'source': 'GENCODE',
                        'version': self.version,
                        'source_url': self.source_url
                    }
                    self.writer.write(json.dumps(props))
                    self.writer.write('\n')

                elif self.label == 'transcribed_to':
                    _id = gene_key + '_' + transcript_key
                    _source = self.gene_endpoint + gene_key
                    _target = self.transcript_endpoint + transcript_key
                    _props = {
                        '_key': _id,
                        '_from': _source,
                        '_to': _target,
                        'source': 'GENCODE',
                        'version': self.version,
                        'source_url': self.source_url,
                        'name': 'transcribes',
                        'inverse_name': 'transcribed by',
                        'biological_process': 'ontology_terms/GO_0010467'
                    }
                    self.writer.write(json.dumps(_props))
                    self.writer.write('\n')

                elif self.label == 'transcribed_from':
                    _id = transcript_key + '_' + gene_key
                    _source = self.transcript_endpoint + transcript_key
                    _target = self.gene_endpoint + gene_key
                    _props = {
                        '_key': _id,
                        '_from': _source,
                        '_to': _target,
                        'source': 'GENCODE',
                        'version': self.version,
                        'source_url': self.source_url,
                        'name': 'transcribed by',
                        'inverse_name': 'transcribes',
                        'biological_process': 'ontology_terms/GO_0010467'
                    }
                    self.writer.write(json.dumps(_props))
                    self.writer.write('\n')
            except:
                print(
                    f'fail to process for label to load: {self.label}, data: {line}')
        self.writer.close()
