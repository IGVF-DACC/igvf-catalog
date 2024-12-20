import json
from typing import Optional

from adapters.helpers import build_variant_id
from adapters.writer import Writer

# Sample file - file has 709 columns:
# #chr	pos(1-based)	ref	alt	aaref	aaalt	rs_dbSNP	hg19_chr	hg19_pos(1-based)	hg18_chr ... Interpro_domain	GTEx_V8_gene	GTEx_V8_tissue	Geuvadis_eQTL_target_gene
# Y	2786989	C	A	X	Y	.	Y	2655030	Y	2715030	205	SRY	ENSG00000184895	ENST00000383070	ENSP00000372547 ... . . . . . .
# Y	2786990	T	C	X	W	.	Y	2655031	Y	2715031	205	SRY	ENSG00000184895	ENST00000383070	ENSP00000372547	... . . . . . .


class DbSNFP:
    LABEL = 'dbSNFP_protein_variants'

    def __init__(self, filepath=None, collection='coding_variants', writer: Optional[Writer] = None, **kwargs):
        self.filepath = filepath
        self.label = DbSNFP.LABEL
        self.dataset = self.label
        self.collection_name = collection
        self.writer = writer

    def multiple_records(self, data_line):
        indexes = [11, 12, 13, 14, 15, 17]
        for idx in indexes:
            if ';' in data_line[idx]:
                return True
        return False

    def breakdown_line(self, original_data_line):
        data_lines = []

        # original_data_line:  "1     69091    A    C    M    L    .    1    6901    1    58954    22;1    OR4F5;OR4FA    ..."
        data_line = []
        for column in original_data_line:
            data_line.append(column.strip().split(';'))

        # data_line example: [['1'], ['69091'], ['A'], ['C'], ['M'], ['L'], ['.'], ['1'], ... ,
        # ['69091'], ['1'], ['58954'], ['22', '1'], ['OR4F5', 'OR4FA'], ['ENSG00000186092', 'ENSG00000186090'], ...

        # data_lines output:
        # record 1: [['1'], ['69091'], ['A'], ['C'], ['M'], ['L'], ['.'], ['1'], ... ,
        # ['69091'], ['1'], ['58954'], ['22'], ['OR4F5'], ['ENSG00000186092'], ...

        # record 2: [['1'], ['69091'], ['A'], ['C'], ['M'], ['L'], ['.'], ['1'], ... ,
        # ['69091'], ['1'], ['58954'], ['1'], ['OR4FA'], ['ENSG00000186090'], ...

        # Assuming position is essential to define a coding variant
        # We are determining how many records are defined per row based on how many positions are listed
        # in the current example, max_idx = len(['22', '1']) = 2
        # assuming all related arrays will be of length 2
        max_idx = len(data_line[11])

        idx = 0
        while idx < max_idx:
            individual_data_line = []
            for column in data_line:
                # there are cases where we have missing values in a few scores
                # example: aapos: ['22', '1'] => max_idx = 2 and score: ['1']
                # assuming the missing value is the last one and filling up with None
                if len(column) > 1 and idx >= len(column):
                    individual_data_line.append(None)
                else:
                    individual_data_line.append(
                        column[idx] if len(column) > 1 else column[0])
            data_lines.append(individual_data_line)
            idx += 1

        return data_lines

    def process_file(self):
        self.writer.open()

        for line in open(self.filepath, 'r'):
            if line.startswith('#chr'):
                continue

            original_data_line = line.strip().split('\t')

            if self.multiple_records(original_data_line):
                data_lines = self.breakdown_line(original_data_line)
            else:
                data_lines = [original_data_line]

            for data_line in data_lines:
                variant_id = build_variant_id(
                    data_line[0],
                    data_line[1],  # 1-based
                    data_line[2],
                    data_line[3]
                )

                # '.' is equivalent to None in this dataset
                def data(pos):
                    return data_line[pos] if data_line[pos] != '.' else None

                def long_data(pos):
                    try:
                        value = data_line[pos]

                        # a few terms have a trailing ';', e.g. '0.489;', in rows with no need of breakdown
                        # removing ; in that case:
                        if value[-1] == ';':
                            value = value[:-1]

                        return float(value) if value != '.' and value != '.;' else None
                    except:
                        return None

                # gene_name + transcript_id + hgvsp + hgvs + splicing (in case pos == -1)
                key = data(12) + '_' + data(14) + '_' + \
                    (data(23) or '') + '_' + (data(22) or '')

                if long_data(11) == -1:
                    key += '_splicing'

                key = key.replace('?', '!').replace('>', '-')

                if self.collection_name == 'variants_coding_variants':
                    to_json = {
                        '_from': 'variants/' + variant_id,
                        '_to': 'coding_variants/' + key,
                        'source': 'dbSNFP 4.5a',
                        'source_url': 'http://database.liulab.science/dbNSFP',
                        'name': 'codes for',
                        'inverse_name': 'encoded by',
                        'chr': data(0),
                        'pos': long_data(1),
                        'ref': data(2),  # 1-based
                        'alt': data(3),
                    }
                elif self.collection_name == 'coding_variants_proteins':
                    to_json = {
                        '_from': 'coding_variants/' + key,
                        '_to': 'proteins/' + data(15),
                        'type': 'protein coding' if (long_data(11) != -1) else 'splicing',
                        'name': 'variant of',
                        'inverse_name': 'has variant',
                        'source': 'dbSNFP 4.5a',
                        'source_url': 'http://database.liulab.science/dbNSFP'
                    }
                else:
                    to_json = {
                        '_key': key,
                        'name': key,
                        'ref': data(4),
                        'alt': data(5),
                        'aapos': long_data(11),  # 1-based
                        'gene_name': data(12),
                        'protein_name': data(17),
                        'hgvs': data(22),
                        'hgvsp': data(23),
                        'refcodon': data(29),
                        'codonpos': long_data(30),
                        'transcript_id': data(14),
                        'SIFT_score': long_data(37),
                        'SIFT4G_score': long_data(40),
                        'Polyphen2_HDIV_score': long_data(43),
                        'Polyphen2_HVAR_score': long_data(46),
                        'VEST4_score': long_data(67),
                        'Mcap_score': long_data(79),
                        'REVEL_score': long_data(82),
                        'MutPred_score': long_data(84),
                        'BayesDel_addAF_score': long_data(101),
                        'BayesDel_noAF_score': long_data(104),
                        'VARITY_R_score': long_data(113),
                        'VARITY_ER_score': long_data(115),
                        'VARITY_R_LOO_score': long_data(117),
                        'VARITY_ER_LOO_score': long_data(119),
                        'ESM1b_score': long_data(121),
                        'EVE_score': long_data(124),
                        'AlphaMissense_score': long_data(137),
                        'CADD_raw_score': long_data(146),
                        'source': 'dbSNFP 4.5a',
                        'source_url': 'http://database.liulab.science/dbNSFP'
                    }

                self.writer.write(json.dumps(to_json))
                self.writer.write('\n')
        self.writer.close()
