import csv
import json
from adapters.helpers import build_variant_id
from typing import Optional

from adapters.writer import Writer
# Example line from file from Supplementary_Table_S3_cV2F_scores.txt
# Second column (pos) is 0-based
# CHR    pos ref alt	SNP	CM	cV2F	LIVER.cV2F	BLOOD.cV2F	BRAIN.cV2F	GM12878.cV2F	K562.cV2F	HepG2.cV2F
# 1 11007   C   G	rs575272151	0	0.259558995068073	0.309695184230804	0.458494558930397	0.501427552103996	0.329434263706207	0.458916559815407	0.448281314969063
# 1  11011  C   G	rs544419019	0	0.3444201618433	0.495591408014298	0.614960989356041	0.72971625328064	0.576766195893288	0.645283776521683	0.626273554563522
# 1  13109   G   A	rs540538026	0	0.36915679872036	0.250546787679195	0.379640486836433	0.317768284678459	0.358425730466843	0.43017390370369	0.299737627804279
# 1  13115   T   G	rs62635286	0	0.235178226232529	0.254660964012146	0.234443159401417	0.49997838139534	0.320095548033714	0.388241451978683	0.307152247428894
# 1  13272   G   C	rs531730856	0	0.659086990356445	0.646302890777588	0.372124403715134	0.416639888286591	0.494327172636986	0.462538683414459	0.462254992127419
# 1	13549   G   C    13550	rs554008981	0	0.503440541028976	0.504938441514969	0.412174689769745	0.508037388324738	0.458340626955032	0.572471630573273	0.659147709608078
# 1	14463   A   T    14464	rs546169444	0	0.302759596705437	0.490839466452599	0.522221061587334	0.58622761964798	0.425303816795349	0.445275992155075	0.399437755346298
# 1	14603   A   C   rs541940975	0	0.243947102129459	0.51446305513382	0.535988602042198	0.505189189314842	0.478271931409836	0.534100893139839	0.469385460019112


class VariantPhenotypeV2FAdapter:
    ALLOWED_LABELS = ['variant_phenotype']
    SOURCE = 'V2F'
    SOURCE_URL = 'https://data.igvf.org/analysis-sets/IGVFDS0000XXXX/'
    PHENOTYPE_TERM = 'PATO_0001509'

    def __init__(self, filepath, label='variant_phenotype', writer: Optional[Writer] = None, **kwargs):
        if label not in VariantPhenotypeV2FAdapter.ALLOWED_LABELS:
            raise ValueError('Invalid label. Allowed values: ' +
                             ','.join(VariantPhenotypeV2FAdapter.ALLOWED_LABELS))

        self.filepath = filepath
        self.writer = writer

    def process_file(self):
        self.writer.open()

        with open(self.filepath, 'r') as cV2F_file:
            cV2F_csv = csv.reader(cV2F_file)
            next(cV2F_csv)
            for row in cV2F_csv:
                chr = row[0]
                pos = row[1] + 1
                ref = row[2]
                alt = row[3]
                _id = build_variant_id(chr, pos, ref, alt)
                edge_key = _id + '_' + VariantPhenotypeV2FAdapter.PHENOTYPE_TERM
                _props = {
                    '_key': edge_key,
                    '_from': 'variants/' + _id,
                    '_to': 'ontology_terms/' + VariantPhenotypeV2FAdapter.PHENOTYPE_TERM,
                    'linkage_disequilibrium': float(row[4]),
                    'general_context_score': float(row[5]),
                    'liver_context_score': float(row[6]),
                    'blood_context_score': float(row[7]),
                    'brain_context_score': float(row[8]),
                    'GM12878_context_score': float(row[9]),
                    'K562_context_score': float(row[10]),
                    'HepG2_context_score': float(row[11]),
                    'source': VariantPhenotypeV2FAdapter.SOURCE,
                    'source_url': VariantPhenotypeV2FAdapter.SOURCE_URL
                }

                self.writer.write(json.dumps(_props))
                self.writer.write('\n')

        self.writer.close()
