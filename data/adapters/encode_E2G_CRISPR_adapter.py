import csv
import json
import pickle
from math import log10
from typing import Optional

from adapters.helpers import build_regulatory_region_id
from adapters.writer import Writer

# Example lines from ENCFF968BZL.tsv (CRISPR tested data for ENCODE E2G training)
# chrom	chromStart	chromEnd	name	EffectSize	strandPerturbationTarget	PerturbationTargetID	chrTSS	startTSS	endTSS	strandGene	EffectSize95ConfidenceIntervalLow	EffectSize95ConfidenceIntervalHigh	measuredGeneSymbol	measuredEnsemblID	guideSpacerSeq	guideSeq	Significant	pValue	pValueAdjusted	PowerAtEffectSize25	PowerAtEffectSize10	PowerAtEffectSize15	PowerAtEffectSize20	PowerAtEffectSize50	ValidConnection	Notes	Reference
# chr1	3774714	3775214	CEP104|chr1:3691278-3691778:.	-0.293431866	.	chr1:3691278-3691778:.	chr1	3857213	3857214	-	NA	NA	CEP104	NA	NA	NA	TRUE	NA	0.004023984	0.825093632	NA	NA	NA	NA	TRUE	Dataset: Nasser2021	Ulirsch et al., 2016
# chr1	3774714	3775214	LRRC47|chr1:3691278-3691778:.	-0.331178093	.	chr1:3691278-3691778:.	chr1	3796503	3796504	-	NA	NA	LRRC47	NA	NA	NA	TRUE	NA	0.007771168	0.608994236	NA	NA	NA	NA	TRUE	Dataset: Nasser2021	Ulirsch et al., 2016

# Note: need to do some changes mannually before running arangoimp, to load the significant field correctly as a boolean type:
# Rename significant:boolean to significant in header file; Replace 'True' with 'true', 'False' with 'false' in parsed data files


class ENCODE2GCRISPR:

    ALLOWED_LABELS = ['genomic_element', 'genomic_element_gene']
    SOURCE = 'ENCODE-E2G-CRISPR'
    SOURCE_URL = 'https://www.encodeproject.org/files/ENCFF968BZL/'
    GENE_ID_MAPPING_PATH = './data_loading_support_files/E2G_CRISPR_gene_id_mapping.pkl'
    FILE_ACCESSION = 'ENCFF968BZL'
    BIOLOGICAL_CONTEXT = 'EFO_0002067'
    MAX_LOG10_PVALUE = 240  # max log10pvalue from file is 235

    def __init__(self, filepath, label, dry_run=True, writer: Optional[Writer] = None, **kwargs):
        if label not in ENCODE2GCRISPR.ALLOWED_LABELS:
            raise ValueError('Invalid label. Allowed values: ' +
                             ','.join(ENCODE2GCRISPR.ALLOWED_LABELS))

        self.filepath = filepath
        self.dataset = label
        self.label = label
        self.dry_run = dry_run
        self.type = 'edge'
        if(self.label == 'genomic_element'):
            self.type = 'node'
        self.writer = writer

    def process_file(self):
        self.writer.open()
        if self.label == 'genomic_element':
            print('loading regulatory regions')
            self.load_genomic_element()

            for region_coordinate, region_type in self.genomic_element_nodes.items():
                chr, start, end = region_coordinate.split(',')
                _id = build_regulatory_region_id(
                    chr, start, end, 'CRISPR') + '_' + ENCODE2GCRISPR.FILE_ACCESSION

                _props = {
                    '_key': _id,
                    'name': _id,
                    'chr': chr,
                    'start': start,
                    'end': end,
                    'type': region_type,
                    # need change here: do we keep this classification?
                    'biochemical_activity': 'ENH' if region_type == 'enhancer' else None,
                    'biochemical_activity_description': 'Enhancer' if region_type == 'enhancer' else None,
                    'source': ENCODE2GCRISPR.SOURCE,
                    'source_url': ENCODE2GCRISPR.SOURCE_URL
                }

                self.writer.write(json.dumps(_props))
                self.writer.write('\n')

        elif self.label == 'genomic_element_gene':
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

                    genomic_element_id = build_regulatory_region_id(
                        chr, start, end, 'CRISPR')

                    _id = genomic_element_id + '_' + gene_id + '_' + ENCODE2GCRISPR.FILE_ACCESSION
                    _source = 'genomic_elements/' + genomic_element_id
                    _target = 'genes/' + gene_id
                    _props = {
                        '_key': _id,
                        '_from': _source,
                        '_to': _target,
                        'score': score,
                        'p_value': p_value,
                        'log10pvalue': log10pvalue,
                        'significant': significant == 'TRUE',
                        'source': ENCODE2GCRISPR.SOURCE,
                        'source_url': ENCODE2GCRISPR.SOURCE_URL,
                        'biological_context': 'ontology_terms/' + ENCODE2GCRISPR.BIOLOGICAL_CONTEXT
                    }
                    self.writer.write(json.dumps(_props))
                    self.writer.write('\n')
        self.writer.close()

    def load_genomic_element(self):
        # each row is a pair of tested regulatory region <-> gene, significant column can be TRUE/FALSE
        # one regulatory region can be tested in multiple rows, i.e. with multiple genes
        # we want to assign type = 'enhancer' if the regulatory region has significant = 'TRUE' with any tested gene, else assign type = 'CRISPR_tested_element'
        # store those info in a dictionary here and output all nodes info at the end, since the file is not big (3,962 unique regions tested)
        self.genomic_element_nodes = {}

        with open(self.filepath, 'r') as crispr_file:
            crispr_csv = csv.reader(crispr_file, delimiter='\t')
            next(crispr_csv)
            for row in crispr_csv:
                genomic_element_coordinate = ','.join(row[:3])

                significant = row[17]

                if self.genomic_element_nodes.get(genomic_element_coordinate) is None:
                    self.genomic_element_nodes[genomic_element_coordinate] = 'CRISPR_tested_element'

                if significant == 'TRUE':
                    self.genomic_element_nodes[genomic_element_coordinate] = 'enhancer'

    def load_gene_id_mapping(self):
        # key: gene symbol; value: gene Ensembl id
        self.gene_id_mapping = {}
        with open(ENCODE2GCRISPR.GENE_ID_MAPPING_PATH, 'rb') as mapfile:
            self.gene_id_mapping = pickle.load(mapfile)
