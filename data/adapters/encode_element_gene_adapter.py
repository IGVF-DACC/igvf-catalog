import gzip
import csv
import json
import requests
from typing import Optional

from adapters.helpers import build_regulatory_region_id
from adapters.writer import Writer

# There are 2 sources from encode:
# ENCODE-E2G (Engrietz)
# EpiRaction (Guigo)

# Epiraction files:
# [‘/files/ENCFF363HJR/‘, ‘/files/ENCFF727IKD/‘, ‘/files/ENCFF679GQI/‘, ‘/files/ENCFF074MTS/‘, ‘/files/ENCFF270VCQ/‘, ‘/files/ENCFF257ABE/‘, ‘/files/ENCFF318HEA/‘, ‘/files/ENCFF698USH/‘,
# ‘/files/ENCFF034GOH/‘, ‘/files/ENCFF612XCP/‘, ‘/files/ENCFF584DPV/‘, ‘/files/ENCFF390YHZ/‘, ‘/files/ENCFF006FTZ/‘, ‘/files/ENCFF260UTE/‘, ‘/files/ENCFF314RKK/‘, ‘/files/ENCFF910TJJ/‘,
# ‘/files/ENCFF985UDL/‘, ‘/files/ENCFF138UMI/‘, ‘/files/ENCFF712SUP/‘, ‘/files/ENCFF893FXX/‘, ‘/files/ENCFF751BIV/‘, ‘/files/ENCFF251XYE/‘, ‘/files/ENCFF772YKX/‘, ‘/files/ENCFF564XCH/‘,
# ‘/files/ENCFF202FBA/‘, ‘/files/ENCFF489MJA/‘, ‘/files/ENCFF804CAK/‘, ‘/files/ENCFF268SIZ/‘, ‘/files/ENCFF730TCG/‘, ‘/files/ENCFF201SDO/‘, ‘/files/ENCFF976SSI/‘, ‘/files/ENCFF592OLR/‘,
# ‘/files/ENCFF079SJR/‘, ‘/files/ENCFF843HTC/‘, ‘/files/ENCFF580UUB/‘, ‘/files/ENCFF302YPU/‘, ‘/files/ENCFF580TON/‘, ‘/files/ENCFF778CUH/‘, ‘/files/ENCFF299DOF/‘, ‘/files/ENCFF176YAF/‘,
# ‘/files/ENCFF822SZV/‘, ‘/files/ENCFF984XCI/‘, ‘/files/ENCFF573KXM/‘, ‘/files/ENCFF537CGJ/‘, ‘/files/ENCFF036LSB/‘, ‘/files/ENCFF073KUI/‘, ‘/files/ENCFF754QRZ/‘, ‘/files/ENCFF407GPD/‘,
# ‘/files/ENCFF213WPV/‘, ‘/files/ENCFF383EUA/‘, ‘/files/ENCFF958QJL/‘, ‘/files/ENCFF393MCX/‘, ‘/files/ENCFF343CVG/‘, ‘/files/ENCFF888NZL/‘, ‘/files/ENCFF383YLO/‘, ‘/files/ENCFF197HRR/‘,
# ‘/files/ENCFF362RIQ/‘, ‘/files/ENCFF546JWS/‘, ‘/files/ENCFF698ZKD/’]

# The file to load is thresholded element-gene links BED file

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

# ENCODE-E2G files(354 files): https://www.encodeproject.org/report/?type=File&lab.title=Jesse+Engreitz%2C+Stanford&submitted_by.title=Andreas+Roman+Gschwind&output_type=thresholded+element+gene+links&field=%40id&field=file_format&field=file_format_type&field=file_size&field=biosample_ontology.term_name&field=output_type
# example:
# #chr	start	end	name	class	TargetGene	TargetGeneEnsemblID	TargetGeneTSS	isSelfPromoter	CellType	EpiMapScore.Feature	glsCoefficient.Feature	numTSSEnhGene.Feature	distanceToTSS.Feature	normalizedDNase_enh.Feature	normalizedDNase_prom.Feature	normalizedH3K27ac_enh.Feature	normalizedH3K27ac_prom.Feature	activity_enh.Feature	3DContact.Feature	activity_enh_squared.Feature	3DContact_squared.Feature	activity_prom.Feature	ABCNumerator.Feature	ABCScore.Feature	ABCDenominator.Feature	numNearbyEnhancers.Feature	sumNearbyEnhancers.Feature	PEToutsideNormalized.Feature	PETcrossNormalized.Feature	promCTCF.Feature	enhCTCF.Feature	H3K4me3_e_max_L_8.Feature	H3K4me3_e_grad_max_L_8.Feature	H3K27ac_e_grad_max_L_8.Feature	DNase_e_grad_max_L_8.Feature	H3K4me3_e_grad_min_L_8.Feature	H3K27ac_e_grad_min_L_8.Feature	DNase_e_grad_min_L_8.Feature	H3K4me3_p_max_L_8.Feature	H3K4me3_p_grad_max_L_8.Feature	H3K27ac_p_grad_max_L_8.Feature	DNase_p_grad_max_L_8.Feature	H3K4me3_p_grad_min_L_8.Feature	H3K27ac_p_grad_min_L_8.Feature	DNase_p_grad_min_L_8.Feature	averageCorrWeighted.Feature	phastConMax.Feature	phyloPMax.Feature	P2PromoterClass.Feature	ubiquitousExpressedGene.Feature	HiCLoopOutsideNormalized.Feature	HiCLoopCrossNormalized.Feature	inTAD.Feature	inCCD.Feature	normalizedEP300_enhActivity.Feature	Score
# chr1	115484	115984	chr1:115484-115984	intergenic	SAMD11	ENSG00000187634	925740	FALSE	K562	0	0.318550433866599	10	810006	4.368531	0.534821	0.61417	0.323086	1.637993	0	2.683021	0	0.458579	0	0	3.08742331288344	11	31.29876	0.0080645161290322	0.032258064516129	3.83579	2.30443	6.69200326471163	0	0	0	0	0	0	37.7827647768576	1.7668262720108	1.44349265098572	5.23154640197754	-2.47238302230835	-1.43976318836212	-0.892485201358795	0.0122622213158049	0.4244210526	0.4244210526	0	0	0.333333333333333	0.333333333333333	0	0	7.489511	0.4101592077174314
# chr1	628759	629259	chr1:628759-629259	promoter	PLEKHN1	ENSG00000187583	966496	FALSE	K562	0	0.139653296016946	0	337487	0.900822	0.622766	0.203454	0.626927	0.428107	0	0.183276	0	0.610264	0	0	4.80920142449183	15	24.512589	0.0138888888888889	1.54166666666667	2.06394	0.242583	71.2928594282424	0	0	0	0	0	0	113.241063124412	30.5455837249756	17.9066829681397	-0.283713817596436	4.48486375808716	0.720926642417908	-17.0570507049561	0.19443103731964	0.2234074074	2.306574468	0.333333333333333	1.33333333333333	0	0	12.672126	0.34896357298211617
# chr1	628759	629259	chr1:628759-629259	promoter	RNF223	ENSG00000237330	1074307	FALSE	K562	0	0.139653296016946	0	445298	0.900822	0.436014	0.203454	0.323086	0.428107	0	0.183276	0	0.426607	0	0	4.80920142449183	15	24.512589	0.009009009009009	1.8018018018018	0.97649	0.242583	71.2928594282424	0	0	0	0	0	0	4.30812787040792	0.479083895683289	1.65028297901154	3.27148389816284	-1.92647445201874	-1.20478999614716	0.364352941513062	0.0179037384386948	0.2234074074	2.306574468	0	0.333333333333333	2.66666666666667	0	0	12.672126	0.34384723529178157

# those types of element are used in the data:
# EpiRaction: enhancer(ENH)
# ENCODE-E2G: intergenic(ENH), promoter(PRO) and genic(ENH)


class EncodeElementGeneLink:

    ALLOWED_LABELS = [
        'genomic_element_gene',  # genomic_element --(edge)--> gene
        'genomic_element',
        'donor',
        'ontology_term'  # to load NTR biosample ontology terms from encode
    ]
    ALLOWED_SOURCES = [
        'ENCODE-E2G-DNaseOnly',
        'ENCODE-E2G-Full',
        'ENCODE_EpiRaction',
    ]

    SCORE_COL_INDEX = {
        'ENCODE_EpiRaction': 9,
        'ENCODE-E2G-DNaseOnly': -1,
        'ENCODE-E2G-Full': -1,
    }

    TYPE = 'accessible dna elements'

    def __init__(self, filepath, label, source, source_url, biological_context, dry_run=True, writer: Optional[Writer] = None, **kwargs):
        if label not in EncodeElementGeneLink.ALLOWED_LABELS:
            raise ValueError('Invalid label. Allowed values: ' +
                             ','.join(EncodeElementGeneLink.ALLOWED_LABELS))
        if source not in EncodeElementGeneLink.ALLOWED_SOURCES:
            raise ValueError('Invalid source. Allowed values: ' +
                             ','.join(EncodeElementGeneLink.ALLOWED_SOURCES))

        self.filepath = filepath
        self.dataset = label
        self.label = label
        self.source = source
        self.source_url = source_url
        self.file_accession = source_url.split('/')[-1]
        self.biological_context = biological_context
        self.dry_run = dry_run
        self.type = 'edge'
        if (self.label in ['donor', 'ontology_term', 'genomic_element']):
            self.type = 'node'
        self.writer = writer

    def process_file(self):
        self.writer.open()

        if self.label in ['donor']:
            donors = self.get_donor_info()
            if not donors:
                return

        if self.label == 'ontology_term':
            # only load NTR ontology terms
            if not self.biological_context.startswith('NTR'):
                return
            else:
                _props = self.get_biosample_term_info()
                self.writer.write(json.dumps(_props))
                self.writer.write('\n')

        if self.label == 'genomic_element_gene':
            treatments = self.get_treatment_info()

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
                    chr, start, end, class_name=class_name)
                score = row[self.SCORE_COL_INDEX[self.source]]
                gene_id = row[6]
                if gene_id == 'NA':
                    continue

                if self.label == 'genomic_element_gene':
                    # genomic_element -> gene per file
                    _id = regulatory_element_id + '_' + gene_id + '_' + \
                        self.file_accession
                    _source = 'genomic_elements/' + regulatory_element_id + '_' + self.file_accession
                    _target = 'genes/' + gene_id
                    _props = {
                        '_key': _id,
                        '_from': _source,
                        '_to': _target,
                        'score': float(score),
                        'source': self.source,
                        'source_url': self.source_url,
                        'file_accession': self.file_accession,
                        'biological_context': 'ontology_terms/' + self.biological_context,
                    }
                    # denormalize treatment info under edges (they should be in fileset collection in future)
                    if treatments:
                        _props['treatment_name'] = [treatment.get(
                            'treatment_term_name') for treatment in treatments],
                        _props['treatment_duration'] = [treatment.get(
                            'duration') for treatment in treatments],
                        _props['treatment_duration_units'] = [treatment.get(
                            'duration_units') for treatment in treatments],
                        _props['treatment_amount'] = [treatment.get(
                            'amount') for treatment in treatments],
                        _props['treatment_amount_units'] = [treatment.get(
                            'amount_units') for treatment in treatments],
                        _props['treatment_notes'] = [treatment.get(
                            'notes') for treatment in treatments]
                    self.writer.write(json.dumps(_props))
                    self.writer.write('\n')

                elif self.label == 'genomic_element':
                    # load genomic_element per file
                    _id = regulatory_element_id + '_' + self.file_accession
                    _props = {
                        '_key': _id,
                        'name': _id,
                        'chr': chr,
                        'start': int(start),
                        'end': int(end),
                        'type': EncodeElementGeneLink.TYPE,
                        'source_annotation': class_name,
                        'source': self.source,
                        'source_url': self.source_url,
                        'file_accession': self.file_accession
                    }

                    self.writer.write(json.dumps(_props))
                    self.writer.write('\n')

                elif self.label == 'donor':
                    for donor in donors:
                        _id = donor['accession']
                        _props = {
                            '_key': _id,
                            'name': donor['accession'],
                            'donor_id': donor['accession'],
                            'sex': donor.get('sex'),
                            'ethnicity': donor.get('ethnicity'),
                            'age': donor.get('age'),
                            'age_units': donor.get('age_units'),
                            'health_status': donor.get('health_status'),
                            'source': 'ENCODE',
                            'source_url': self.source_url,
                        }
                        self.writer.write(json.dumps(_props))
                        self.writer.write('\n')
        self.writer.close()

    def get_treatment_info(self):
        # get the treatment info of its annotation from the file url
        annotation = requests.get(
            self.source_url + '?format=json').json()['dataset']
        annotation_json = requests.get(
            'https://www.encodeproject.org/' + annotation + '?format=json').json()
        treatments = annotation_json.get('treatments')
        return treatments

    def get_donor_info(self):
        # get the donor info of its annotation from the file url
        annotation = requests.get(
            self.source_url + '?format=json').json()['dataset']
        annotation_json = requests.get(
            'https://www.encodeproject.org/' + annotation + '?format=json').json()
        # e.g. '/human-donors/ENCDO882UJI/'
        donor = annotation_json.get('donor')
        donors = []
        if donor is not None:
            donor_json = requests.get(
                'https://www.encodeproject.org/' + donor + '?format=json').json()
            donors.append(donor_json)
        else:
            # We have a few annotations with mixed donors, that don't have a donor field (e.g. /annotations/ENCSR370ZTQ/)
            # Get the donors accession from their description field, as a temporary solution
            # An example description: ENCODE-rE2G predictions of enhancer-gene regulatory interactions for common myeloid progenitor, CD34-positive; Donor: ENCDO410ZKA, ENCDO707VTH
            descriptions = annotation_json['description'].split('; ')
            for info in descriptions:
                if info.startswith('Donor: '):
                    donor_ids = info.replace('Donor: ', '').split(', ')
                    for donor_id in donor_ids:
                        donor_json = requests.get(
                            'https://www.encodeproject.org/human-donors/' + donor_id + '/?format=json').json()
                        donors.append(donor_json)
        return donors

    def get_biosample_term_info(self):
        # get biosample info for NTR ontology terms from ENCODE, then load them in ontology_terms collection
        biosample_dict = requests.get(
            self.source_url + '?format=json').json()['biosample_ontology']
        biosample_id = self.biological_context

        props = {
            '_key': biosample_id,
            'uri': 'https://www.encodeproject.org' + biosample_dict['@id'],
            'term_id': self.biological_context,
            'name': biosample_dict['term_name'],
            'synonyms': biosample_dict['synonyms'],
            'source': 'ENCODE',
        }

        return props
