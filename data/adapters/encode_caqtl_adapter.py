import csv

from adapters import Adapter
from adapters.helpers import build_variant_id, build_accessible_dna_region_id

# Example Encode caQTL input file:
# chr1	766454	766455	chr1_766455_T_C	chr1	766455	T	C	1	778381	779150	FALSE	1_778381_779150	C	T	rs189800799	Progenitor
# chr1	766454	766455	chr1_766455_T_C	chr1	766455	T	C	1	778381	779150	FALSE	1_778381_779150	C	T	rs189800799	Neuron
# chr1	1668541	1668542	chr1_1668542_C_T	chr1	1668542	C	T	1	1658831	1659350	FALSE	1_1658831_1659350	T	C	rs72634822	Progenitor
# chr1	1687152	1687153	chr1_1687153_A_G	chr1	1687153	A	G	1	1745801	1746550	FALSE	1_1745801_1746550	A	G	rs28366981	Progenitor


class CAQtl(Adapter):
    # 1-based coordinate system

    ALLOWED_TYPES = ['caqtl', 'accessible_dna_region']

    def __init__(self, filepath, type='caqtl'):
        if type not in CAQtl.ALLOWED_TYPES:
            raise ValueError('Ivalid type. Allowed values: ' +
                             ','.join(CAQtl.ALLOWED_TYPES))

        self.filepath = filepath
        self.dataset = type
        self.type = type

        super(CAQtl, self).__init__()

    def process_file(self):
        for line in open(self.filepath, 'r'):
            data_line = line.strip().split()

            ocr_chr = 'chr' + data_line[8]
            ocr_pos_start = data_line[9]
            ocr_pos_end = data_line[10]
            accessible_dna_region_id = build_accessible_dna_region_id(
                ocr_chr, ocr_pos_start, ocr_pos_end
            )

            if self.type == 'caqtl':
                chr = data_line[0]
                pos = data_line[2]
                ref = data_line[6]
                alt = data_line[7]
                variant_id = build_variant_id(chr, pos, ref, alt)

                _id = variant_id + '_' + accessible_dna_region_id
                _source = 'variants/' + variant_id
                _target = 'accessible_dna_regions/' + accessible_dna_region_id
                label = 'caqtl'
                _props = {
                    'chr': chr,
                    'rsid': data_line[15]
                }

                yield(_id, _source, _target, label, _props)

            elif self.type == 'accessible_dna_region':
                _id = accessible_dna_region_id
                label = 'accessible_dna_region'
                _props = {
                    'chr': ocr_chr,
                    'start': ocr_pos_start,
                    'end': ocr_pos_end
                }

                yield(_id, label, _props)
