import os
from adapters import Adapter
from adapters.helpers import build_variant_id, build_regulatory_region_id

# Example Encode caQTL input file:
# chr1	766454	766455	chr1_766455_T_C	chr1	766455	T	C	1	778381	779150	FALSE	1_778381_779150	C	T	rs189800799	Progenitor
# chr1	766454	766455	chr1_766455_T_C	chr1	766455	T	C	1	778381	779150	FALSE	1_778381_779150	C	T	rs189800799	Neuron
# chr1	1668541	1668542	chr1_1668542_C_T	chr1	1668542	C	T	1	1658831	1659350	FALSE	1_1658831_1659350	T	C	rs72634822	Progenitor
# chr1	1687152	1687153	chr1_1687153_A_G	chr1	1687153	A	G	1	1745801	1746550	FALSE	1_1745801_1746550	A	G	rs28366981	Progenitor


class CAQtl(Adapter):
    # 1-based coordinate system

    ALLOWED_LABELS = ['regulatory_region', 'encode_caqtl']
    CLASS_NAME = 'accessible_dna_element'
    # we can have a map file if loading more datasets in future
    CELL_ONTOLOGY = {'Progenitor': 'CL_0011020',
                     'Neuron': 'CL_0000540', 'Liver': 'UBERON_0002107'}

    def __init__(self, filepath, pmid, label):
        if label not in CAQtl.ALLOWED_LABELS:
            raise ValueError('Ivalid label. Allowed values: ' +
                             ','.join(CAQtl.ALLOWED_LABELS))

        self.filepath = filepath
        self.dataset = label
        self.label = label
        self.pmid = pmid

        super(CAQtl, self).__init__()

    def process_file(self):
        for line in open(self.filepath, 'r'):
            data_line = line.strip().split()

            ocr_chr = 'chr' + data_line[8]
            ocr_pos_start = data_line[9]
            ocr_pos_end = data_line[10]
            regulatory_region_id = build_regulatory_region_id(
                CAQtl.CLASS_NAME, ocr_chr, ocr_pos_start, ocr_pos_end
            )

            if self.label == 'encode_caqtl':
                chr = data_line[0]
                pos = data_line[2]
                ref = data_line[6]
                alt = data_line[7]
                variant_id = build_variant_id(chr, pos, ref, alt)
                cell_name = data_line[-1]

                _id = variant_id + '_' + regulatory_region_id
                _source = 'variants/' + variant_id
                _target = 'regulatory_regions/' + regulatory_region_id
                _props = {
                    'rsid': data_line[15],
                    'label': 'caQTL',
                    'source': 'ENCODE',
                    'source_url': 'https://www.encodeproject.org/files/' + os.path.basename(self.filepath).split('.')[0],
                    'pmid': self.pmid,
                    'biological_context': 'ontology_terms/' + CAQtl.CELL_ONTOLOGY[cell_name]
                }

                yield(_id, _source, _target, self.label, _props)

            elif self.label == 'regulatory_region':
                _id = regulatory_region_id
                _props = {
                    'chr': ocr_chr,
                    'start': ocr_pos_start,
                    'end': ocr_pos_end,
                    'source': 'ENCODE',
                    'source_url': 'https://www.encodeproject.org/files/' + os.path.basename(self.filepath).split('.')[0],
                    'pmid': self.pmid,
                    'type': 'ATAC-seq peak'  # might need to rename
                }

                yield(_id, self.label, _props)
