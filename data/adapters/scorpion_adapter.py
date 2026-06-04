import csv
import requests
import gzip
import json
from typing import Optional

from adapters.helpers import get_file_fileset_by_accession_in_arangodb
from adapters.base import BaseAdapter
from adapters.writer import Writer

# Sample data:
# tf,tf_ensembl,target,target_ensembl,beta,P,FDR
# ZNF250,ENSG00000196150,WNK1,ENSG00000060237,2.79614395634379,2.23950511461299e-22,2.2770944348533403e-19
# ZNF770,ENSG00000198146,IL32,ENSG00000008517,2.68504180081855,1.80943850543389e-22,1.8921041491990902e-19
# ZNF250,ENSG00000196150,RAB3GAP1,ENSG00000115839,2.60846182810368,6.8583125999997006e-15,4.46018704732234e-13
# ZNF770,ENSG00000198146,FXYD5,ENSG00000089327,2.47636665757162,2.6083752753581298e-30,2.82424470955305e-26
# ZNF250,ENSG00000196150,ECD,ENSG00000122882,2.47274455661664,1.0652979856438198e-11,2.14332529077824e-10
# SP2,ENSG00000167182,IL32,ENSG00000008517,2.46075901773533,4.1256177738298497e-22,3.83064494763081e-19
# KLF5,ENSG00000102554,RGS1,ENSG00000090104,-2.45832343792633,9.80241382630337e-12,1.9972107166922901e-10
# ZNF250,ENSG00000196150,SECISBP2L,ENSG00000138593,2.44734259208731,8.10284619583455e-10,8.828469446648141e-09


class ScorpionAdapter(BaseAdapter):
    SOURCE = 'IGVF'
    LABEL = 'predicted gene regulatory networks'

    def __init__(self, filepath=None, writer: Optional[Writer] = None, validate=False, **kwargs):
        self.filepath = filepath
        self.file_accession = self.filepath.split('/')[-1].split('.')[0]
        self.source_url = 'https://data.igvf.org/tabular-files/' + self.file_accession
        super().__init__(filepath, '', writer, validate)

    def process_file(self) -> Optional[dict]:
        file_fileset_obj = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        self.method = file_fileset_obj['method']
        self.collection_class = file_fileset_obj['class']

        with gzip.open(self.filepath, 'rt') as data_file:
            data_csv = csv.DictReader(
                data_file, delimiter='\t', fieldnames=self.filepath)

            for row in data_csv:
                props = {
                    '_key': row['tf_ensembl'] + '_' + row['target_ensembl'] + '_' + self.LABEL.replace(' ', '_'),
                    '_from': 'genes/' + row['tf_ensembl'],
                    '_to': 'genes/' + row['target_ensembl'],
                    'beta': row['beta'],
                    'p_value': row['P'],
                    'fdr': row['FDR'],
                    'name': 'regulates',
                    'inverse_name': 'is regulated by',
                    'files_filesets': 'files_filesets/' + self.file_accession,
                    'class': self.collection_class,
                    'method': self.method,
                    'label': self.LABEL,
                    'source': self.SOURCE,
                    'source_url': self.source_url

                }
                if self.validate:
                    self.validate_doc(props)

                self.writer.write(json.dumps(props))
                self.writer.write('\n')
        self.writer.close()
