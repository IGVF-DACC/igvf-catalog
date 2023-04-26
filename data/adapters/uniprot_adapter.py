import gzip
from Bio import SeqIO
from adapters import Adapter

# Data file is uniprot_sprot_human.dat.gz at https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/taxonomic_divisions/.
# We can use SeqIO from Bio to read the file.
# Each record in file will have those attributes: https://biopython.org/docs/1.75/api/Bio.SeqRecord.html
# id, name will be loaded for protein. Ensembl IDs(example: Ensembl:ENST00000372839.7) in dbxrefs will be used to create protein and transcript relationship.


class Uniprot(Adapter):

    ALLOWED_TYPES = ['protein', 'translates to', 'translation of']
    ALLOWED_LABELS = ['UniProtKB_protein',
                      'UniProtKB_Translates_To', 'UniProtKB_Translation_Of']

    def __init__(self, filepath, type='protein', label='UniProtKB_protein'):
        if type not in Uniprot.ALLOWED_TYPES:
            raise ValueError('Ivalid type. Allowed values: ' +
                             ', '.join(Uniprot.ALLOWED_TYPES))
        if label not in Uniprot.ALLOWED_LABELS:
            raise ValueError('Ivalid label. Allowed values: ' +
                             ', '.join(Uniprot.ALLOWED_LABELS))
        self.filepath = filepath
        self.dataset = label
        self.type = type
        self.label = label

        super(Uniprot, self).__init__()

    def process_file(self):
        with gzip.open(self.filepath, 'rt') as input_file:
            records = SeqIO.parse(input_file, 'swiss')
            for record in records:
                if self.type == 'protein':
                    try:
                        _id = record.id
                        _props = {
                            'name': record.name,
                            'source': 'UniProt',
                            'source_url': 'https://www.uniprot.org/help/downloads'
                        }
                        yield(_id, self.label, _props)

                    except:
                        print(f'fail to process for node protein: {record.id}')
                        pass
                elif self.type == 'translates to':
                    dbxrefs = record.dbxrefs
                    for item in dbxrefs:
                        if item.startswith('Ensembl') and 'ENST' in item:
                            try:
                                ensg_id = item.split(':')[-1].split('.')[0]
                                _id = record.id + '_' + ensg_id
                                _source = 'transcripts/' + ensg_id
                                _target = 'proteins/' + record.id
                                _props = {}
                                yield(_id, _source, _target, self.label, _props)

                            except:
                                print(
                                    f'fail to process for edge translates to: {record.id}')
                                pass
                elif self.type == 'translation of':
                    dbxrefs = record.dbxrefs
                    for item in dbxrefs:
                        if item.startswith('Ensembl') and 'ENST' in item:
                            try:
                                ensg_id = item.split(':')[-1].split('.')[0]
                                _id = ensg_id + '_' + record.id
                                _target = 'transcripts/' + ensg_id
                                _source = 'proteins/' + record.id
                                _props = {}
                                yield(_id, _source, _target, self.label, _props)

                            except:
                                print(
                                    f'fail to process for edge translation of: {record.id}')
                                pass
