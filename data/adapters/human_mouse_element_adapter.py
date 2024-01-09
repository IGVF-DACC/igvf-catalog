import gzip
import csv
from adapters import Adapter
from adapters.helpers import build_regulatory_region_id

# ENCFF078OEX – ENCODE contains a mapping of ENCODE mouse and human DNase HS regions
# doc for headers: https://www.encodeproject.org/documents/924f991f-616f-4bfd-ae1f-6d22acb048b4/@@download/attachment/extended_score_txt_format.pdf

# Below is example data:
# human_id	mouse_id	human_region	mouse_region	axnet_id	percent_identical_bp	phastCons4way	phyloP4way	cov_chromatin_accessibility	cov_chromatin_accessibility_pval	cov_chromatin_accessibility_fdr	cob_chromatin_accessibility	cob_chromatin_accessibility_pval	cob_chromatin_accessibility_fdr	cov_H3K27ac	cov_H3K27ac_pval	cov_H3K27ac_fdr	cob_H3K27ac	cob_H3K27ac_pval	cob_H3K27ac_fdr	cov_H3K4me1	cov_H3K4me1_pval	cov_H3K4me1_fdr	cob_H3K4me1	cob_H3K4me1_pval	cob_H3K4me1_fdr	cov_H3K4me3	cov_H3K4me3_pval	cov_H3K4me3_fdr	cob_H3K4me3	cob_H3K4me3_pval	cob_H3K4me3_fdr	source
# 1.10011	1438454	chr1:16072-16271	chr6:121522229-121522428	9	0.495	0	0	-0.08705883748059523	0.74469	0.7880168243061526	0.45999999999999996	0.38023	0.706372507818166	-0.04897145589966213	0.672636	0.8353311889993958	0.33	0.85179	0.9741088464334399	-0.16420816777029995	0.833716	0.9170052784062483	0.30000000000000004	0.87628	0.9810987190296945	-0.13407817495685007	0.892402	0.9650710516056851	0.35	0.87563	0.9758546569869605	Human DHS
# 1.10025	NA	chr1:57252-57451	chr2:111473783-111473982	20	0.57	0.085675	0.045485	-0.009653767783686866	0.56393	0.6568581654918484	0.17	0.99083	0.9985194117979596	0.044790816620770606	0.380092	0.703023214575446	0.15000000000000002	0.99083	0.99775847060561	-0.16182084337300406	0.84638	0.9222579323689643	0.16	0.98757	0.9976702090183495	0.05618651174646711	0.35763	0.809313783751029	0.2	0.98963	0.9985326662931654	Human DHS
# 1.10037	114103	chr1:99572-99771	chr1:176696293-176696492	35	0.685	0	0	0.06919630041947913	0.34608	0.5004039298466973	0.21000000000000002	0.98951	0.9978591566274337	-0.052021391179473866	0.726702	0.8585842652976797	0.19	0.97683	0.9964378384105873	0.1084462724320473	0.32094	0.6965712865165082	0.17	0.98369	0.9970098741614626	4.4396608800866845e-4	0.476906	0.8518265198279255	0.23	0.98641	0.9977305954969775	Human DHS
# 1.10041	NA	chr1:113812-114011	chr8:65735025-65735224	45	0.545	0	0	-0.06775880087167531	0.75368	0.7947352516961186	0.22	0.98563	0.9967849285199359	0.01971503979966921	0.484218	0.7534137295910185	0.22	0.96357	0.9960457248669493	0.03185637476541943	0.499054	0.7825285605280959	0.2	0.96709	0.9949987081515034	0.05150121252879724	0.275416	0.770259351908851	0.28	0.96017	0.9943740240446343	Human DHS
# 1.100658	768986	chr1:182642-182841	chr17:66149209-66149408	79	0.365	0	0	0.20488913938927858	0.07505	0.2488783474706553	0.44000000000000006	0.51208	0.7946192253469723	-0.14758156684637289	0.867434	0.921903764255809	0.35	0.80707	0.9582263288272989	-5.757570779437938e-4	0.445532	0.759015330187268	0.36	0.72525	0.9313437527139579	-0.1215610773579	0.865332	0.9576173531992148	0.39	0.76694	0.9443415427587122	Human DHS
# 1.100662	1438454	chr1:186662-186861	chr6:121522151-121522350	86	0.535	0	-0.72	-0.05629550962678456	0.66674	0.7305980245278588	0.39	0.65782	0.8676486186774324	0.03946098462926984	0.381942	0.7039114967811839	0.26	0.93394	0.9932356318739323	-0.11809601487648684	0.75738	0.886255009014517	0.28	0.90259	0.9858350653958651	0.05086642044035309	0.294362	0.7800442397689894	0.28	0.9596	0.9943740240446343	Human DHS
# 1.100665	1438454	chr1:186812-187011	chr6:121522015-121522214	86	0.565	0	0	0.04901697680352995	0.36181	0.5120691917506229	0.4	0.61953	0.8488400120487138	0.08476425355826231	0.247884	0.62255088570685	0.35	0.8078	0.9582263288272989	0.2223191087084317	0.098838	0.5179134814167031	0.35	0.77205	0.9448270606762671	-0.03258021537080142	0.608598	0.8905854864129351	0.33	0.90596	0.982253094033529	Human DHS
# 1.100668	1438453	chr1:186952-187151	chr6:121521875-121522074	86	0.475	0	0	0.021669820396617735	0.44157	0.5703818980672296	0.43000000000000005	0.50365	0.7946192253469723	0.13256040916503942	0.143664	0.530370008322546	0.42000000000000004	0.55776	0.8728641998631633	0.2795524677418299	0.052742	0.43915947105411346	0.38	0.67834	0.9128897985684592	-0.02061036535654107	0.562736	0.8779724982115326	0.35	0.87563	0.9758546569869605	Human DHS
# 1.100671	1438444	chr1:190772-190971	chr6:121518345-121518544	87	0.595	0	0	0.14204574384648785	0.16878	0.35295128811475457	0.45000000000000007	0.29554	0.6467372850126809	0.07660107275344429	0.290718	0.6516195185696351	0.44000000000000006	0.35876	0.749424691902632	0.09939259539511455	0.340664	0.7073855435688593	0.44000000000000006	0.34273	0.7261781138385377	0.12122052125065466	0.093576	0.6012641180271799	0.38	0.78846	0.9443415427587122	Human DHS


class HumanMouseElementAdapter(Adapter):
    SOURCE = 'FUNCODE'
    ALLOWED_LABELS = [
        'regulatory_region',
        'mm_regulatory_region',
        'regulatory_region_mm_regulatory_region',

    ]
    INDEX = {
        'human_region': 2,
        'mouse_region': 3,
        'axnet_id': 4,
        'percent_identical_bp': 5,
        'phastCons4way': 6,
        'phyloP4way': 7,
        'cov_chromatin_accessibility': 8,
        'cov_chromatin_accessibility_pval': 9,
        'cov_chromatin_accessibility_fdr': 10,
        'cob_chromatin_accessibility': 11,
        'cob_chromatin_accessibility_pval': 12,
        'cob_chromatin_accessibility_fdr': 13,
        'cov_H3K27ac': 14,
        'cov_H3K27ac_pval': 15,
        'cov_H3K27ac_fdr': 16,
        'cob_H3K27ac': 17,
        'cob_H3K27ac_pval': 18,
        'cob_H3K27ac_fdr': 19,
        'cov_H3K4me1': 20,
        'cov_H3K4me1_pval': 21,
        'cov_H3K4me1_fdr': 22,
        'cob_H3K4me1': 23,
        'cob_H3K4me1_pval': 24,
        'cob_H3K4me1_fdr': 25,
        'cov_H3K4me3': 26,
        'cov_H3K4me3_pval': 27,
        'cov_H3K4me3_fdr': 28,
        'cob_H3K4me3': 29,
        'cob_H3K4me3_pval': 30,
        'cob_H3K4me3_fdr': 31,
        'source': 32,
    }

    def __init__(self, filepath, label='regulatory_region_mm_regulatory_region'):
        if label not in HumanMouseElementAdapter.ALLOWED_LABELS:
            raise ValueError('Ivalid label. Allowed values: ' +
                             ','.join(HumanMouseElementAdapter.ALLOWED_LABELS))
        self.filepath = filepath
        self.label = label
        self.dataset = label
        self.source_url = 'https://www.encodeproject.org/files/' + \
            filepath.split('/')[-1].split('.')[0]

        super(HumanMouseElementAdapter, self).__init__()

    def process_file(self):
        with gzip.open(self.filepath, 'rt') as input_file:
            reader = csv.reader(input_file, delimiter='\t')
            next(reader)
            for row in reader:
                human_region = row[self.INDEX['human_region']]
                chr_human, range_human = human_region.split(':')
                start_human, end_human = range_human.split('-')
                _id_human = build_regulatory_region_id(
                    chr_human, start_human, end_human)
                mouse_region = row[self.INDEX['mouse_region']]
                chr_mouse, range_mouse = mouse_region.split(':')
                start_mouse, end_mouse = range_mouse.split('-')
                _id_mouse = build_regulatory_region_id(
                    chr_mouse, start_mouse, end_mouse, assembly='mm10')
                if self.label == 'regulatory_region':
                    _props = {
                        'chr': chr_human,
                        'start': start_human,
                        'end': end_human,
                        'type': 'accessible dna elements',
                        'source': self.SOURCE,
                        'source_url': self.source_url
                    }
                    yield(_id_human, self.label, _props)
                elif self.label == 'mm_regulatory_region':
                    _props = {
                        'chr': chr_mouse,
                        'start': start_mouse,
                        'end': end_mouse,
                        'type': 'accessible dna elements (mouse)',
                        'source': self.SOURCE,
                        'source_url': self.source_url
                    }
                    yield(_id_mouse, self.label, _props)
                else:
                    _id = _id_human + '_' + _id_mouse
                    _target = 'regulatory_regions/' + _id_human
                    _source = 'mm_regulatory_regions/' + _id_mouse
                    _props = {
                        'percent_identical_bp': row[self.INDEX['percent_identical_bp']],
                        'phastCons4way': row[self.INDEX['phastCons4way']],
                        'phyloP4way': row[self.INDEX['phyloP4way']],
                        'cov_chromatin_accessibility': row[self.INDEX['cov_chromatin_accessibility']],
                        'cov_chromatin_accessibility_pval': row[self.INDEX['cov_chromatin_accessibility_pval']],
                        'cov_chromatin_accessibility_fdr': row[self.INDEX['cov_chromatin_accessibility_fdr']],
                        'cob_chromatin_accessibility': row[self.INDEX['cob_chromatin_accessibility']],
                        'cob_chromatin_accessibility_pval': row[self.INDEX['cob_chromatin_accessibility_pval']],
                        'cob_chromatin_accessibility_fdr': row[self.INDEX['cob_chromatin_accessibility_fdr']],
                        'cov_H3K27ac': row[self.INDEX['cov_H3K27ac']],
                        'cov_H3K27ac_pval': row[self.INDEX['cov_H3K27ac_pval']],
                        'cov_H3K27ac_fdr': row[self.INDEX['cov_H3K27ac_fdr']],
                        'cob_H3K27ac': row[self.INDEX['cob_H3K27ac']],
                        'cob_H3K27ac_pval': row[self.INDEX['cob_H3K27ac_pval']],
                        'cob_H3K27ac_fdr': row[self.INDEX['cob_H3K27ac_fdr']],
                        'cov_H3K4me1': row[self.INDEX['cov_H3K4me1']],
                        'cov_H3K4me1_pval': row[self.INDEX['cov_H3K4me1_pval']],
                        'cov_H3K4me1_fdr': row[self.INDEX['cov_H3K4me1_fdr']],
                        'cob_H3K4me1': row[self.INDEX['cob_H3K4me1']],
                        'cob_H3K4me1_pval': row[self.INDEX['cob_H3K4me1_pval']],
                        'cob_H3K4me1_fdr': row[self.INDEX['cob_H3K4me1_fdr']],
                        'cov_H3K4me3': row[self.INDEX['cov_H3K4me3']],
                        'cov_H3K4me3_pval': row[self.INDEX['cov_H3K4me3_pval']],
                        'cov_H3K4me3_fdr': row[self.INDEX['cov_H3K4me3_fdr']],
                        'cob_H3K4me3': row[self.INDEX['cob_H3K4me3']],
                        'cob_H3K4me3_pval': row[self.INDEX['cob_H3K4me3_pval']],
                        'cob_H3K4me3_fdr': row[self.INDEX['cob_H3K4me3_fdr']],
                        'source': self.SOURCE,
                        'source_url': self.source_url
                    }
                    yield(_id, _source, _target, self.label, _props)
