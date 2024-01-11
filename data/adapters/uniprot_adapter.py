import gzip
from Bio import SeqIO
from adapters import Adapter

# Data file is uniprot_sprot_human.dat.gz and uniprot_trembl_human.dat.gz at https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/taxonomic_divisions/.
# We can use SeqIO from Bio to read the file.
# Each record in file will have those attributes: https://biopython.org/docs/1.75/api/Bio.SeqRecord.html
# id, name will be loaded for protein. Ensembl IDs(example: Ensembl:ENST00000372839.7) in dbxrefs will be used to create protein and transcript relationship.


class Uniprot(Adapter):

    ALLOWED_LABELS = ['UniProtKB_Translates_To', 'UniProtKB_Translation_Of']
    ALLOWED_SOURCES = ['UniProtKB/Swiss-Prot', 'UniProtKB/TrEMBL']
    ALLOWED_ORGANISMS = ['HUMAN', 'MOUSE']

    def __init__(self, filepath, label, source, organism='HUMAN'):
        if label not in Uniprot.ALLOWED_LABELS:
            raise ValueError('Ivalid label. Allowed values: ' +
                             ', '.join(Uniprot.ALLOWED_LABELS))
        if organism not in Uniprot.ALLOWED_ORGANISMS:
            raise ValueError('Ivalid organism. Allowed values: ' +
                             ', '.join(Uniprot.ALLOWED_ORGANISMS))
        self.filepath = filepath
        self.label = label
        self.source = source
        self.transcript_endpoint = 'transcripts/'
        self.organism = organism
        self.ensembl_prefix = 'ENST'
        if self.organism == 'MOUSE':
            self.transcript_endpoint = 'mm_transcripts/'
            self.ensembl_prefix = 'ENSMUST'

        super(Uniprot, self).__init__()

    def process_file(self):
        with gzip.open(self.filepath, 'rt') as input_file:
            records = SeqIO.parse(input_file, 'swiss')
            for record in records:
                if not record.name.endswith(self.organism):
                    continue
                dbxrefs = record.dbxrefs
                _props = {
                    'source': self.source,
                    'source_url': 'https://www.uniprot.org/help/downloads'
                }
                for item in dbxrefs:
                    if item.startswith('Ensembl') and self.ensembl_prefix in item:
                        try:
                            ensg_id = item.split(':')[-1].split('.')[0]

                            if self.label == 'UniProtKB_Translates_To':
                                _id = ensg_id + '_' + record.id
                                _source = self.transcript_endpoint + ensg_id
                                _target = 'proteins/' + record.id
                            elif self.label == 'UniProtKB_Translation_Of':
                                _id = record.id + '_' + ensg_id
                                _target = self.transcript_endpoint + ensg_id
                                _source = 'proteins/' + record.id
                            yield(_id, _source, _target, self.label, _props)
                        except:
                            print(
                                f'fail to process for label {self.label}: {record.id}')
                            pass
