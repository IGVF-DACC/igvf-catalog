import gzip
import csv
from adapters import Adapter
from adapters.helpers import build_regulatory_region_id

# There are 4 sources from encode:
# ABC (Engrietz)
# ENCODE-E2G (Engrietz)
# EpiRaction (Guigo)
# graphReg (Leslie)

# The file to load is thresholded element-gene links BED file

# The fields to load is:
# chr: chromosome
# start: start of the enhancer
# end: end of the enhancer
# class: the class of the element
# TargetGene:target gene symbol
# Score:Score for that E-G pair being an enhancer-gene regulatory connection

# files from graphReg has no thresholded file yet, we will use element gene links bed file and load GraphReg_LR_thresholded.Score as score.
# Query: https://www.encodeproject.org/search/?type=File&type=Dataset&lab.title=Christina+Leslie%2C+MSKCC&submitted_by.title=Alireza%20Karbalayghareh

# Example
# #chr	start	end	name	class	TargetGene	TargetGeneTSS	CellType	DistanceToTSS	GraphReg_LR.Score	GraphReg_LR_thresholded.Score	H3K4me3_e_max_L_8	H3K27ac_e_max_L_8	DNase_e_max_L_8	H3K4me3_e_grad_max_L_8	H3K27ac_e_grad_max_L_8	DNase_e_grad_max_L_8	H3K4me3_e_grad_min_L_8	H3K27ac_e_grad_min_L_8	DNase_e_grad_min_L_8	H3K4me3_p_max_L_8	H3K27ac_p_max_L_8	DNase_p_max_L_8	H3K4me3_p_grad_max_L_8	H3K27ac_p_grad_max_L_8	DNase_p_grad_max_L_8	H3K4me3_p_grad_min_L_8	H3K27ac_p_grad_min_L_8	DNase_p_grad_min_L_8
# chr1	11623	12123	promoter|chr1:11623-12123	promoter	ACAP3	1307889	GM12878	1296016	2.1734810240238315e-08	0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	30.4843395717308	54.2944393907788	81.3262866909456	164.392501831055	41.6047210693359	161.660919189453	-31.8314514160156	-65.5641326904297	-187.24006652832
# chr1	11623	12123	promoter|chr1:11623-12123	promoter	AGRN	1020122	GM12878	1008249	3.738019658986227e-07	0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	21.2025926767765	43.4051853535529	68.0406910564557	55.1113243103028	47.1869125366211	87.6472702026367	-18.3765087127686	-31.2360553741455	-3.64214277267456

# EpiRaction has 77 thresholded element gene links bed files
# Example
# #chr	start	end	name	class	TargetGene	TargetGeneEnsemblID	TargetGeneTSS	CellType	Score	DistanceToTSS	H3K27ac	Open	Cofactor	Activity	HiC_contacts	HiC_foldchange
# chr1	827140	827667	e:chr1:827140-827667	enhancer	NOC2L	ENSG00000188976	959156	Blood.Myeloid.Erythroblast	0.1094868	131089	29.0349	15.5104	8.8905	60.5940863	0.13094	9.70500
# chr1	778331	778947	e:chr1:778331-778947	enhancer	NOC2L	ENSG00000188976	959156	Blood.Myeloid.Erythroblast	0.0806398	179809	29.9625	26.7842	8.7749	94.1001400	0.06586	4.07600
# chr1	778997	779613	e:chr1:778997-779613	enhancer	NOC2L	ENSG00000188976	959156	Blood.Myeloid.Erythroblast	0.0388132	179143	17.7508	7.2314	22.4898	43.6864031	0.06586	4.06500
# chr1	1157527	1158185	e:chr1:1157527-1158185	enhancer	NOC2L	ENSG00000188976	959156	Blood.Myeloid.Erythroblast	0.0177169	197971	17.8522	6.5309	22.7196	41.6971431	0.03281	2.20300
# chr1	826563	827090	e:chr1:826563-827090	enhancer	NOC2L	ENSG00000188976	959156	Blood.Myeloid.Erythroblast	0.0122145	131666	18.9075	5.0152	5.9345	25.1611698	0.13036	9.74100
# #
# chr1	1024145	1024642	e:chr1:1024145-1024642	enhancer	KLHL17	ENSG00000187961	960684	Blood.Myeloid.Erythroblast	0.0837702	63061	9.9855	7.9918	20.6068	34.0730209	0.10571	2.75800
# chr1	778331	778947	e:chr1:778331-778947	enhancer	KLHL17	ENSG00000187961	960684	Blood.Myeloid.Erythroblast	0.0608322	181337	29.9625	26.7842	8.7749	94.1001400	0.02866	1.78600
# chr1	1068807	1069456	e:chr1:1068807-1069456	enhancer	KLHL17	ENSG00000187961	960684	Blood.Myeloid.Erythroblast	0.0507193	107723	3.0948	18.5308	17.4431	28.0899086	0.08053	3.20700


class EncodeEnhancerGeneLink(Adapter):

    ALLOWED_LABELS = [
        'element_gene_link',
        'regulatory_region',
    ]
    ALLOWED_SOURCES = [
        'ABC',
        'ENCODE-E2G',
        'EpiRaction',
        'graphReg'
    ]

    def __init__(self, filepath, label, source, source_url, biological_context):
        if label not in EncodeEnhancerGeneLink.ALLOWED_LABELS:
            raise ValueError('Ivalid label. Allowed values: ' +
                             ','.join(EncodeEnhancerGeneLink.ALLOWED_LABELS))
        if source not in EncodeEnhancerGeneLink.ALLOWED_SOURCES:
            raise ValueError('Ivalid source. Allowed values: ' +
                             ','.join(EncodeEnhancerGeneLink.ALLOWED_SOURCES))

        self.filepath = filepath
        self.dataset = label
        self.label = label
        self.source = source
        self.source_url = source_url
        self.biological_context = biological_context

        super(EncodeEnhancerGeneLink, self).__init__()

    def process_file(self):
        with gzip.open(self.filepath, 'rt') as input_file:
            reader = csv.reader(input_file, delimiter='\t')
            for row in reader:
                if row[0].startswith('#'):
                    continue
                chr = row[0]
                start = row[1]
                end = row[2]
                class_name = row[4]
                regulatory_element_id = build_regulatory_region_id(
                    class_name, chr, start, end)
                score = row[9]

                if self.label == 'element_gene_link':
                    gene_id = row[6]

                    _id = regulatory_element_id + '_' + gene_id
                    _source = 'regulatory_regions/' + regulatory_element_id
                    _target = 'genes/' + gene_id
                    _props = {
                        'score': score,
                        'source': self.source,
                        'source_url': self.source_url,
                        'biological_context': self.biological_context
                    }
                    yield(_id, _source, _target, self.label, _props)

                elif self.label == 'regulatory_region':
                    _id = regulatory_element_id
                    _props = {
                        'chr': chr,
                        'start': start,
                        'end': end,
                        'class': class_name,
                        'source': self.source,
                        'source_url': self.source_url
                    }

                    yield(_id, self.label, _props)
