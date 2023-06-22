import gzip
import json
import os
from Bio import SeqIO
from adapters import Adapter
from db.arango_db import ArangoDB


# Data file is uniprot_sprot_human.dat.gz and uniprot_trembl_human.dat.gz at https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/taxonomic_divisions/.
# We can use SeqIO from Bio to read the file.
# Each record in file will have those attributes: https://biopython.org/docs/1.75/api/Bio.SeqRecord.html
# id, name will be loaded for protein. Ensembl IDs(example: Ensembl:ENST00000372839.7) in dbxrefs will be used to create protein and transcript relationship.


class UniprotProtein(Adapter):
    OUTPUT_FOLDER = './parsed-data'
    ALLOWED_SOURCES = ['UniProtKB/Swiss-Prot', 'UniProtKB/TrEMBL']

    def __init__(self, filepath, source, dry_run=False):
        if source not in UniprotProtein.ALLOWED_SOURCES:
            raise ValueError('Ivalid source. Allowed values: ' +
                             ', '.join(UniprotProtein.ALLOWED_SOURCES))
        self.filepath = filepath
        self.dataset = 'UniProtKB_protein'
        self.label = 'UniProtKB_protein'
        self.source = source
        self.dry_run = dry_run
        self.SKIP_BIOCYPHER = True

        if not os.path.exists(UniprotProtein.OUTPUT_FOLDER):
            os.makedirs(UniprotProtein.OUTPUT_FOLDER)
        self.output_filepath = '{}/{}.json'.format(
            UniprotProtein.OUTPUT_FOLDER,
            self.dataset,
        )

        super(UniprotProtein, self).__init__()

    def get_dbxrefs(self, dbxrefs):
        dbxrefs_list = set()
        for item in dbxrefs:
            dbxref = item.split(':', 1)[-1]
            dbxrefs_list.add(dbxref)
        return list(dbxrefs_list)

    def process_file(self):
        parsed_data_file = open(self.output_filepath, 'w')
        with gzip.open(self.filepath, 'rt') as input_file:
            records = SeqIO.parse(input_file, 'swiss')
            for record in records:
                dbxrefs = self.get_dbxrefs(record.dbxrefs)
                to_json = {
                    '_key': record.id,
                    'name': record.name,
                    'dbxrefs': dbxrefs,
                    'source': self.source,
                    'source_url': 'https://www.uniprot.org/help/downloads'
                }
                json.dump(to_json, parsed_data_file)
                parsed_data_file.write('\n')
        parsed_data_file.close()
        self.save_to_arango()

    def arangodb(self):
        return ArangoDB().generate_json_import_statement(self.output_filepath, self.collection)

    def save_to_arango(self):
        if self.dry_run:
            print(self.arangodb()[0])
        else:
            os.system(self.arangodb()[0])
