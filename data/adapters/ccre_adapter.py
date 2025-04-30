import gzip
import csv
import json
from typing import Optional

from adapters.writer import Writer
from adapters.helpers import build_regulatory_region_id

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

    def __init__(self, filepath, label='genomic_element', writer: Optional[Writer] = None, **kwargs):
        self.filepath = filepath
        self.label = label
        self.dataset = label
        self.filename = filepath.split('/')[-1].split('.')[0]
        self.source_url = 'https://data.igvf.org/reference-files/' + self.filename
        self.type = 'node'
        self.writer = writer

    def process_file(self):
        self.writer.open()
        with gzip.open(self.filepath, 'rt') as input_file:
            reader = csv.reader(input_file, delimiter='\t')

            for row in reader:
                try:
                    description = CCRE.BIOCHEMICAL_DESCRIPTION.get(row[9])
                    _props = {
                        '_key': build_regulatory_region_id(row[0], row[1], row[2], 'candidate_cis_regulatory_element') + '_' + self.filename,
                        'name': row[3],
                        'chr': row[0],
                        'start': int(row[1]),
                        'end': int(row[2]),
                        'source_annotation': row[9] + ': ' + description,
                        'method_type': 'integrative',
                        'type': 'candidate cis regulatory element',
                        'source': 'ENCODE_SCREEN (ccREs)',
                        'source_url': self.source_url
                    }
                    self.writer.write(json.dumps(_props))
                    self.writer.write('\n')

                except:
                    print(f'fail to process: {row}')
                    pass
        self.writer.close()
