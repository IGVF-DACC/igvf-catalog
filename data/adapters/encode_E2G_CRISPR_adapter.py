import csv
import pickle
from adapters import Adapter
from adapters.helpers import build_regulatory_region_id
from math import log10

# Example lines from ENCFF968BZL.tsv (CRISPR tested data for ENCODE E2G training)
# chrom	chromStart	chromEnd	name	EffectSize	strandPerturbationTarget	PerturbationTargetID	chrTSS	startTSS	endTSS	strandGene	EffectSize95ConfidenceIntervalLow	EffectSize95ConfidenceIntervalHigh	measuredGeneSymbol	measuredEnsemblID	guideSpacerSeq	guideSeq	Significant	pValue	pValueAdjusted	PowerAtEffectSize25	PowerAtEffectSize10	PowerAtEffectSize15	PowerAtEffectSize20	PowerAtEffectSize50	ValidConnection	Notes	Reference
# chr1	3774714	3775214	CEP104|chr1:3691278-3691778:.	-0.293431866	.	chr1:3691278-3691778:.	chr1	3857213	3857214	-	NA	NA	CEP104	NA	NA	NA	TRUE	NA	0.004023984	0.825093632	NA	NA	NA	NA	TRUE	Dataset: Nasser2021	Ulirsch et al., 2016
# chr1	3774714	3775214	LRRC47|chr1:3691278-3691778:.	-0.331178093	.	chr1:3691278-3691778:.	chr1	3796503	3796504	-	NA	NA	LRRC47	NA	NA	NA	TRUE	NA	0.007771168	0.608994236	NA	NA	NA	NA	TRUE	Dataset: Nasser2021	Ulirsch et al., 2016


class ENCODE2GCRISPR(Adapter):

    ALLOWED_LABELS = ['regulatory_region', 'regulatory_region_gene']
    SOURCE = 'ENCODE-E2G-CRISPR'
    SOURCE_URL = 'https://www.encodeproject.org/files/ENCFF968BZL/'
    GENE_ID_MAPPING_PATH = './data_loading_support_files/E2G_CRISPR_gene_id_mapping.pkl'
    FILE_ACCESSION = 'ENCFF968BZL'
    BIOLOGICAL_CONTEXT = 'EFO_0002067'
    MAX_LOG10_PVALUE = 240  # max log10pvalue from file is 235

    def __init__(self, filepath, label):
        if label not in ENCODE2GCRISPR.ALLOWED_LABELS:
            raise ValueError('Invalid label. Allowed values: ' +
                             ','.join(ENCODE2GCRISPR.ALLOWED_LABELS))

        self.filepath = filepath
        self.dataset = label
        self.label = label

        super(ENCODE2GCRISPR, self).__init__()

    def process_file(self):
        if self.label == 'regulatory_region':
            print('loading regulatory regions')
            self.load_regulatory_region()

            for region_coordinate, region_type in self.regulatory_region_nodes.items():
                chr, start, end = region_coordinate.split(',')
                _id = build_regulatory_region_id(chr, start, end, 'CRISPR')

                _props = {
                    'name': _id,
                    'chr': chr,
                    'start': start,
                    'end': end,
                    'type': region_type,
                    'source': ENCODE2GCRISPR.SOURCE,
                    'source_url': ENCODE2GCRISPR.SOURCE_URL
                }

                yield(_id, self.label, _props)

        elif self.label == 'regulatory_region_gene':
            self.load_gene_id_mapping()

            with open(self.filepath, 'r') as crispr_file:
                crispr_csv = csv.reader(crispr_file, delimiter='\t')
                next(crispr_csv)
                for row in crispr_csv:
                    gene_id = row[14]
                    if gene_id == 'NA':  # map the gene id from gene symbol in column 14
                        gene_id = self.gene_id_mapping.get(row[13])
                        if gene_id is None:
                            print('no gene id mapping for ' + row[13])
                            continue

                    chr = row[0]
                    start = row[1]
                    end = row[2]
                    score = row[4]  # i.e. effect size from perturb experiment
                    if score == 'NA':
                        score = 0  # assign 0 if unavailable
                    p_value = row[19]  # pValueAdjusted
                    if p_value == 'NA':
                        log10pvalue = None
                    elif float(p_value) == 0:
                        log10pvalue = ENCODE2GCRISPR.MAX_LOG10_PVALUE
                    else:
                        log10pvalue = -1 * log10(float(p_value))

                    significant = row[17]  # TRUE or FALSE

                    regulatory_region_id = build_regulatory_region_id(
                        chr, start, end, 'CRISPR')

                    _id = regulatory_region_id + '_' + gene_id + '_' + ENCODE2GCRISPR.FILE_ACCESSION
                    _source = 'regulatory_regions/' + regulatory_region_id
                    _target = 'genes/' + gene_id
                    _props = {
                        'score': score,
                        'p_value': p_value,
                        'log10pvalue': log10pvalue,
                        'significant': significant == 'TRUE',
                        'source': ENCODE2GCRISPR.SOURCE,
                        'source_url': ENCODE2GCRISPR.SOURCE_URL,
                        'biological_context': 'ontology_terms/' + ENCODE2GCRISPR.BIOLOGICAL_CONTEXT
                    }
                    yield(_id, _source, _target, self.label, _props)

    def load_regulatory_region(self):
        # each row is a pair of tested regulatory region <-> gene, significant column can be TRUE/FALSE
        # one regulatory region can be tested in multiple rows, i.e. with multiple genes
        # we want to assign type = 'enhancer' if the regulatory region has significant = 'TRUE' with any tested gene, else assign type = 'CRISPR_tested_element'
        # store those info in a dictionary here and output all nodes info at the end, since the file is not big (3,962 unique regions tested)
        self.regulatory_region_nodes = {}

        with open(self.filepath, 'r') as crispr_file:
            crispr_csv = csv.reader(crispr_file, delimiter='\t')
            next(crispr_csv)
            for row in crispr_csv:
                regulatory_region_coordinate = ','.join(row[:3])

                significant = row[17]

                if self.regulatory_region_nodes.get(regulatory_region_coordinate) is None:
                    self.regulatory_region_nodes[regulatory_region_coordinate] = 'CRISPR_tested_element'

                if significant == 'TRUE':
                    self.regulatory_region_nodes[regulatory_region_coordinate] = 'enhancer'

    def load_gene_id_mapping(self):
        # key: gene symbol; value: gene Ensembl id
        self.gene_id_mapping = {}
        with open(ENCODE2GCRISPR.GENE_ID_MAPPING_PATH, 'rb') as mapfile:
            self.gene_id_mapping = pickle.load(mapfile)
