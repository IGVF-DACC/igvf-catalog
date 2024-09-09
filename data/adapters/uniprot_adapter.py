import gzip
import json
from typing import Optional

from Bio import SeqIO

from adapters.writer import Writer

# Data file is uniprot_sprot_human.dat.gz and uniprot_trembl_human.dat.gz at https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/taxonomic_divisions/.
# We can use SeqIO from Bio to read the file.
# Each record in file will have those attributes: https://biopython.org/docs/1.75/api/Bio.SeqRecord.html
# id, name will be loaded for protein. Ensembl IDs(example: Ensembl:ENST00000372839.7) in dbxrefs will be used to create protein and transcript relationship.


class Uniprot:

    ALLOWED_LABELS = ['UniProtKB_Translates_To']
    ALLOWED_SOURCES = ['UniProtKB/Swiss-Prot', 'UniProtKB/TrEMBL']
    ALLOWED_ORGANISMS = ['HUMAN', 'MOUSE']

    def __init__(self, filepath, label, source, organism='HUMAN', dry_run=True, writer: Optional[Writer] = None):
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
        self.dataset = label
        self.dry_run = dry_run
        self.type = 'edge'
        self.writer = writer

    def process_file(self):
        self.writer.open()
        with gzip.open(self.filepath, 'rt') as input_file:
            records = SeqIO.parse(input_file, 'swiss')
            for record in records:
                if not record.name.endswith(self.organism):
                    continue
                dbxrefs = record.dbxrefs
                _props = {
                    'source': self.source,
                    'source_url': 'https://www.uniprot.org/help/downloads',
                    'name': 'translates to',
                    'inverse_name': 'translated from',
                    'biological_process': 'ontology_terms/GO_0006412'
                }
                for item in dbxrefs:
                    if item.startswith('Ensembl') and self.ensembl_prefix in item:
                        try:
                            ensg_id = item.split(':')[-1].split('.')[0]

                            _id = ensg_id + '_' + record.id
                            _source = self.transcript_endpoint + ensg_id
                            _target = 'proteins/' + record.id
                            _props['_key'] = _id
                            _props['_from'] = _source
                            _props['_to'] = _target
                            self.writer.write(json.dumps(_props))
                            self.writer.write('\n')
                        except:
                            print(
                                f'fail to process for label {self.label}: {record.id}')
                            pass
        self.writer.close()
