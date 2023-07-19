import gzip
import json
import os
from adapters import Adapter
from db.arango_db import ArangoDB
from Bio import SwissProt


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

    def get_dbxrefs(self, cross_references):
        dbxrefs = []
        for cross_reference in cross_references:
            database_name = cross_reference[0]
            if database_name == 'EMBL':
                for item in cross_reference[1:3]:
                    if item != '-':
                        id = database_name + ':' + item
                        dbxrefs.append(id)
            elif database_name in ['RefSeq', 'Ensembl', 'MANE-Select']:
                for item in cross_reference[1:]:
                    if item != '-':
                        id = database_name + ':' + item.split('. ')[0]
                        dbxrefs.append(id)
            else:
                id = cross_reference[0] + ':' + cross_reference[1]
                dbxrefs.append(id)

        return sorted(list(set(dbxrefs)), key=str.casefold)

    def process_file(self):
        parsed_data_file = open(self.output_filepath, 'w')
        with gzip.open(self.filepath, 'rt') as input_file:
            records = SwissProt.parse(input_file)
            for record in records:
                dbxrefs = self.get_dbxrefs(record.cross_references)
                to_json = {
                    '_key': record.accessions[0],
                    'name': record.entry_name,
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