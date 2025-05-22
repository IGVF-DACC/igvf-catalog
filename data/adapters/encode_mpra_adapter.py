import csv
import gzip
import json
from typing import Optional

from adapters.helpers import build_regulatory_region_id
from adapters.writer import Writer

# Example rows from ENCODE lenti-MPRA bed file ENCFF802FUV.bed: (the last two columns are the same for all rows)
# Column 7: activity score (i.e. log2(RNA/DNA)); Column 8: DNA count; Column 9: RNA count
# chr1	10410	10610	HepG2_DNasePeakNoPromoter1	212	+	-0.843	0.307	0.171	-1	-1


class EncodeMPRA:

    SOURCE = 'ENCODE_MPRA'

    ALLOWED_LABELS = [
        'genomic_element',
        'genomic_element_biosample'
    ]

    def __init__(self, filepath, label, source_url, biological_context, writer: Optional[Writer] = None, **kwargs):
        if label not in EncodeMPRA.ALLOWED_LABELS:
            raise ValueError('Ivalid label. Allowed values: ' +
                             ','.join(EncodeMPRA.ALLOWED_LABELS))
        self.filepath = filepath
        self.label = label
        self.source_url = source_url
        self.file_accession = source_url.split('/')[-2]
        self.biological_context = biological_context
        self.dataset = label
        self.type = 'edge'
        if (self.label == 'genomic_element'):
            self.type = 'node'
        self.writer = writer

    def process_file(self):
        self.writer.open()
        with gzip.open(self.filepath, 'rt') as mpra_file:
            mpra_csv = csv.reader(mpra_file, delimiter='\t')
            for row in mpra_csv:
                chr = row[0]
                start = row[1]
                end = row[2]

                genomic_element_id = build_regulatory_region_id(
                    chr, start, end, 'MPRA'
                )

                if self.label == 'genomic_element':
                    _id = genomic_element_id + '_' + self.file_accession
                    _props = {
                        '_key': _id,
                        'name': _id,
                        'chr': chr,
                        'start': int(start),
                        'end': int(end),
                        'method_type': 'MPRA',
                        'type': 'tested elements',
                        'source': EncodeMPRA.SOURCE,
                        'source_url': self.source_url,
                        'files_filesets': 'files_filesets/' + self.file_accession
                    }

                    self.writer.write(json.dumps(_props))
                    self.writer.write('\n')

                elif self.label == 'genomic_element_biosample':
                    _id = '_'.join(
                        [genomic_element_id, self.file_accession, self.biological_context])
                    _source = 'genomic_elements/' + genomic_element_id + '_' + self.file_accession
                    _target = 'ontology_terms/' + self.biological_context
                    _props = {
                        '_key': _id,
                        '_from': _source,
                        '_to': _target,
                        'element_name': row[3],
                        'strand': row[5],
                        'activity_score': float(row[6]),
                        'bed_score': int(row[4]),
                        'DNA_count': float(row[7]),
                        'RNA_count': float(row[8]),
                        'source': EncodeMPRA.SOURCE,
                        'source_url': self.source_url,
                        'files_filesets': 'files_filesets/' + self.file_accession,
                        'name': 'expression effect in',
                        'inverse_name': 'has expression effect from',
                    }
                    self.writer.write(json.dumps(_props))
                    self.writer.write('\n')
        self.writer.close()
