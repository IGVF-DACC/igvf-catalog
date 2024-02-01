import csv
import gzip
from adapters import Adapter
from adapters.helpers import build_regulatory_region_id


# Example rows from ENCODE lenti-MPRA bed file ENCFF802FUV.bed: (the last two columns are the same for all rows)
# Column 7: activity score (i.e. log2(RNA/DNA)); Column 8: DNA count; Column 9: RNA count
# chr1	10410	10610	HepG2_DNasePeakNoPromoter1	212	+	-0.843	0.307	0.171	-1	-1

class EncodeMPRA(Adapter):

    SOURCE = 'ENCODE_MPRA'

    ALLOWED_LABELS = [
        'regulatory_region',
        'regulatory_region_biosample'
    ]

    def __init__(self, filepath, label, source_url, biological_context):  # other?
        if label not in EncodeMPRA.ALLOWED_LABELS:
            raise ValueError('Ivalid label. Allowed values: ' +
                             ','.join(EncodeMPRA.ALLOWED_LABELS))
        self.filepath = filepath
        self.label = label
        self.source_url = source_url
        self.file_accession = source_url.split('/')[-2]
        self.biological_context = biological_context

        super(EncodeMPRA, self).__init__()

    def process_file(self):
        with gzip.open(self.filepath, 'rt') as mpra_file:
            mpra_csv = csv.reader(mpra_file, delimiter='\t')
            for row in mpra_csv:
                chr = row[0]
                start = row[1]
                end = row[2]

                regulatory_region_id = build_regulatory_region_id(
                    chr, start, end, 'MPRA'
                )

                if self.label == 'regulatory_region':
                    _id = regulatory_region_id
                    _props = {
                        'chr': chr,
                        'start': start,
                        'end': end,
                        'type': 'MPRA_tested_regulatory_element',
                        'source': EncodeMPRA.SOURCE,
                        'source_url': self.source_url
                    }

                    yield(_id, self.label, _props)

                elif self.label == 'regulatory_region_biosample':
                    _id = '_'.join(
                        [regulatory_region_id, self.file_accession, self.biological_context])
                    _source = 'regulatory_regions/' + regulatory_region_id
                    _target = 'ontology_terms/' + self.biological_context
                    _props = {
                        'type': 'MPRA_tested_measurements',
                        'element_name': row[3],
                        'strand': row[5],
                        'activity_score': row[6],
                        'bed_score': row[4],
                        'DNA_count': row[7],
                        'RNA_count': row[8],
                        'source': EncodeMPRA.SOURCE,
                        'source_url': self.source_url
                    }
                    yield(_id, _source, _target, self.label, _props)
