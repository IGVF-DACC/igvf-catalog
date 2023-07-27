from adapters import Adapter

# Example genocde vcf input file:
# ##description: evidence-based annotation of the human genome (GRCh38), version 42 (Ensembl 108)
# ##provider: GENCODE
# ##contact: gencode-help@ebi.ac.uk
# ##format: gtf
# ##date: 2022-07-20
# chr1    HAVANA  gene    11869   14409   .       +       .       gene_id "ENSG00000290825.1"; gene_type "lncRNA"; gene_name "DDX11L2"; level 2; tag "overlaps_pseudogene";
# chr1    HAVANA  transcript      11869   14409   .       +       .       gene_id "ENSG00000290825.1"; transcript_id "ENST00000456328.2"; gene_type "lncRNA"; gene_name "DDX11L2"; transcript_type "lncRNA"; transcript_name "DDX11L2-202"; level 2; transcript_support_level "1"; tag "basic"; tag "Ensembl_canonical"; havana_transcript "OTTHUMT00000362751.1";
# chr1    HAVANA  exon    11869   12227   .       +       .       gene_id "ENSG00000290825.1"; transcript_id "ENST00000456328.2"; gene_type "lncRNA"; gene_name "DDX11L2"; transcript_type "lncRNA"; transcript_name "DDX11L2-202"; exon_number 1; exon_id "ENSE00002234944.1"; level 2; transcript_support_level "1"; tag "basic"; tag "Ensembl_canonical"; havana_transcript "OTTHUMT00000362751.1";
# chr1    HAVANA  exon    12613   12721   .       +       .       gene_id "ENSG00000290825.1"; transcript_id "ENST00000456328.2"; gene_type "lncRNA"; gene_name "DDX11L2"; transcript_type "lncRNA"; transcript_name "DDX11L2-202"; exon_number 2; exon_id "ENSE00003582793.1"; level 2; transcript_support_level "1"; tag "basic"; tag "Ensembl_canonical"; havana_transcript "OTTHUMT00000362751.1";


class Gencode(Adapter):
    ALLOWED_TYPES = ['transcript',
                     'transcribed to', 'transcribed from']
    ALLOWED_LABELS = ['gencode_transcript',
                      'transcribed_to', 'transcribed_from']
    ALLOWED_KEYS = ['gene_id', 'gene_type', 'gene_name',
                    'transcript_id', 'transcript_type', 'transcript_name']

    INDEX = {'chr': 0, 'type': 2, 'coord_start': 3, 'coord_end': 4, 'info': 8}

    def __init__(self, filepath=None, type='gene', label='gencode_gene', chr='all'):
        if label not in Gencode.ALLOWED_LABELS:
            raise ValueError('Ivalid labelS. Allowed values: ' +
                             ','.join(Gencode.ALLOWED_LABELS))

        self.filepath = filepath
        self.type = type
        self.chr = chr
        self.label = label
        self.dataset = label

        super(Gencode, self).__init__()

    def parse_info_metadata(self, info):
        parsed_info = {}
        for key, value in zip(info, info[1:]):
            if key in Gencode.ALLOWED_KEYS:
                parsed_info[key] = value.replace('"', '').replace(';', '')
        return parsed_info

    def process_file(self):
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
                if self.type == 'transcript':
                    props = {
                        'transcript_id': info['transcript_id'],
                        'transcript_name': info['transcript_name'],
                        'transcript_type': info['transcript_type'],
                        'chr': data[Gencode.INDEX['chr']],
                        # the gtf file format is [1-based,1-based], needs to convert to BED format [0-based,1-based]
                        'start:long': str(int(data[Gencode.INDEX['coord_start']]) - 1),
                        'end:long': data[Gencode.INDEX['coord_end']],
                        'gene_name': info['gene_name'],
                        'source': 'GENCODE',
                        'version': 'v43',
                        'source_url': 'https://www.gencodegenes.org/human/'
                    }
                    yield(transcript_key, self.label, props)
                elif self.type == 'transcribed to':
                    _id = gene_key + '_' + transcript_key
                    _source = 'genes/' + gene_key
                    _target = 'transcripts/' + transcript_key
                    _props = {
                        'source': 'GENCODE',
                        'version': 'v43',
                        'source_url': 'https://www.gencodegenes.org/human/'
                    }
                    yield(_id, _source, _target, self.label, _props)
                elif self.type == 'transcribed from':
                    _id = transcript_key + '_' + gene_key
                    _source = 'transcripts/' + transcript_key
                    _target = 'genes/' + gene_key
                    _props = {
                        'source': 'GENCODE',
                        'version': 'v43',
                        'source_url': 'https://www.gencodegenes.org/human/'
                    }
                    yield(_id, _source, _target, self.label, _props)
            except:
                print(
                    f'fail to process for label to load: {self.label}, type to load: {self.type}, data: {line}')
