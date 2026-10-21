import gzip
import csv
import json
from typing import Optional

from adapters.archive_utils import get_file_accession
from adapters.base import BaseAdapter
from adapters.writer import Writer
from adapters.helpers import build_regulatory_region_id, get_file_fileset_by_accession_in_arangodb

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


class CCRE(BaseAdapter):
    ALLOWED_LABELS = ['genomic_element', 'mm_genomic_element']
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

    def __init__(self, filepath, label='genomic_element', writer: Optional[Writer] = None, validate=False, **kwargs):
        self.accession = get_file_accession(filepath)
        if label == 'mm_genomic_element':
            self.source_url = f'https://data.igvf.org/reference-files/{self.accession}/'
        else:
            self.source_url = f'https://www.encodeproject.org/files/{self.accession}'
        super().__init__(filepath, label, writer, validate)

    def _get_schema_type(self):
        """Return schema type."""
        return 'nodes'

    def _get_collection_name(self):
        """Get collection name."""
        if self.label == 'mm_genomic_element':
            return 'mm_genomic_elements'
        else:
            return 'genomic_elements'

    def parse(self):
        self.file_fileset = get_file_fileset_by_accession_in_arangodb(
            self.accession)
        # in case of encode file/fileset igvf accession/fileset accession are in dbxref_name/dbxref_fileset_id
        if self.label == 'mm_genomic_element':
            self.fileset_accession = self.file_fileset.get('dbxref_fileset_id')
            self.writer.add_tag('portal_accessions', self.accession)
            self.writer.add_tag('portal_accessions', self.fileset_accession)
        else:
            self.igvf_accession = self.file_fileset.get('dbxref_name')
            self.igvf_fileset_accession = self.file_fileset.get(
                'dbxref_fileset_id')
            self.writer.add_tag('portal_accessions', self.igvf_accession)
            self.writer.add_tag('portal_accessions',
                                self.igvf_fileset_accession)
        with gzip.open(self.filepath, 'rt') as input_file:
            reader = csv.reader(input_file, delimiter='\t')

            for row in reader:
                description = CCRE.BIOCHEMICAL_DESCRIPTION.get(row[9])
                assembly = 'GRCm39' if self.label == 'mm_genomic_element' else 'GRCh38'
                _props = {
                    '_key': build_regulatory_region_id(
                        row[0], row[1], row[2], 'candidate_cis_regulatory_element', assembly
                    ) + '_' + self.accession,
                    'name': row[3],
                    'chr': row[0],
                    'start': int(row[1]),
                    'end': int(row[2]),
                    'source_annotation': row[9] + ': ' + description,
                    'method': self.file_fileset.get('method'),
                    'type': 'candidate cis regulatory element',
                    'source': 'ENCODE',
                    'source_url': self.source_url,
                    'files_filesets': f'files_filesets/{self.accession}'
                }
                if self.validate:
                    self.validate_doc(_props)
                self.writer.write(json.dumps(_props))
                self.writer.write('\n')
