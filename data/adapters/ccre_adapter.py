import gzip
import csv
import json
import os
from typing import Optional

from db.arango_db import ArangoDB
from adapters.writer import Writer

# cCRE,all input file has 10 columns: chromsome, start, end, ID, score (all 0), strand (NA), start, end, color, biochemical_activity
# There are 8 types of biochemical_activity:
# pELS - proximal Enhancer-ike signal
# CA → chromatin accessible
# dELS - distal Enhancer-like signal
# TF → TF binding
# CA-CTCF
# CA-TF
# CA-H3K4me3
# PLS

# Below is example data:
# chr1    10033   10250   EH38E2776516    0       .       10033   10250   255,167,0       pELS
# chr1    10385   10713   EH38E2776517    0       .       10385   10713   255,167,0       pELS
# chr1    16097   16381   EH38E3951272    0       .       16097   16381   0,176,240       CA-CTCF
# chr1    17343   17642   EH38E3951273    0       .       17343   17642   190,40,229      CA-TF
# chr1    29320   29517   EH38E3951274    0       .       29320   29517   6,218,147       CA


class CCRE:
    BIOCHEMICAL_DESCRIPTION = {
        'pELS': 'proximal Enhancer-like signal',
        'CA': 'chromatin accessible',
        'dELS': 'distal Enhancer-like signal',
        'TF': 'TF binding',
        'CA-CTCF': 'chromatin accessible + CTCF binding',
        'CA-TF': 'chromatin accessible + TF binding',
        'CA-H3K4me3': 'chromatin accessible + H3K4me3 high signal',
        'PLS': 'Promoter-like signal'
    }

    def __init__(self, filepath, label='regulatory_region', dry_run=True, writer: Optional[Writer] = None):
        self.filepath = filepath
        self.label = label
        self.dataset = label
        self.source_url = 'https://www.encodeproject.org/files/' + \
            filepath.split('/')[-1].split('.')[0]
        self.dry_run = dry_run
        self.type = 'node'
        self.writer = writer

    def process_file(self):
        self.writer.open()
        with gzip.open(self.filepath, 'rt') as input_file:
            reader = csv.reader(input_file, delimiter='\t')

            for row in reader:
                try:
                    description = CCRE.BIOCHEMICAL_DESCRIPTION.get(row[9])
                    _id = row[3]
                    _props = {
                        '_key': _id,
                        'chr': row[0],
                        'start': row[1],
                        'end': row[2],
                        'biochemical_activity': row[9],
                        'biochemical_activity_description': description,
                        'type': 'candidate_cis_regulatory_element',
                        'source': 'ENCODE_SCREEN (ccREs)',
                        'source_url': self.source_url
                    }
                    self.writer.write(json.dumps(_props))
                    self.writer.write('\n')

                except:
                    print(f'fail to process: {row}')
                    pass
        self.writer.close()

    def save_to_arango(self):
        if self.dry_run:
            print(self.arangodb()[0])
        else:
            os.system(self.arangodb()[0])

    def arangodb(self):
        return ArangoDB().generate_json_import_statement(self.writer.destination, self.collection, type=self.type)
