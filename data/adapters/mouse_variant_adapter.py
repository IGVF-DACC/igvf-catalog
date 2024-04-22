from ga4gh.vrs.extras.translator import Translator
from ga4gh.vrs.dataproxy import create_dataproxy
from biocommons.seqrepo import SeqRepo

from adapters import Adapter
from adapters.helpers import build_mouse_variant_id
from scripts.variants_spdi import build_spdi, build_hgvs_from_spdi

from db.arango_db import ArangoDB
import json
import os

# source files are from here: https://ftp.ebi.ac.uk/pub/databases/mousegenomes/REL-2112-v8-SNPs_Indels/
# mouse genomes project info: https://www.sanger.ac.uk/data/mouse-genomes-project/
# query by rsid: https://www.informatics.jax.org/snp/rs37149123
# C57BL/6J  aka “Black 6” is the reference strain
# We need the following 7 collaborative cross strains (possibly more added later):
# 129S1_SvlmJ
# A_J
# CAST_EiJ aka “castaneus”
# NOD_ShiLtJ  (TypeI Diabetes model, immunodeficient)
# NZO_H1LtJ  (T2 diabetes, polygenic obesity model)
# PWK_PhJ
# WSB_EiJ

# Example indel input file:
# CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	129P2_OlaHsd	129S1_SvImJ	129S5SvEvBrd	A_J	AKR_J	B10.RIII	BALB_cByJ	BALB_cJ	BTBR_T+_Itpr3tf_J	BUB_BnJ	C3H_HeH	C3H_HeJ	C57BL_10J	C57BL_10SnJ	C57BL_6NJ	C57BR_cdJ	C57L_J	C58_J	CAST_EiJ	CBA_J	CE_J	CZECHII_EiJ	DBA_1J	DBA_2J	FVB_NJ	I_LnJ	JF1_MsJ	KK_HiJ	LEWES_EiJ	LG_J	LP_J	MAMy_J	MOLF_EiJ	NOD_ShiLtJ	NON_LtJ	NZB_B1NJ	NZO_HlLtJ	NZW_LacJ	PL_J	PWK_PhJ	QSi3	QSi5	RF_J	RIIIS_J	SEA_GnJ	SJL_J	SM_J	SPRET_EiJ	ST_bJ	SWR_J	WSB_EiJ	ZALENDE_EiJ
# 1	3050706	.	T	TG	50110.4	.	AC=51;AF=0.49;AN=104;BaseQRankSum=0.51;DP=3831;ExcessHet=9.4076;FS=1.914;InbreedingCoeff=-0.233;MLEAC=38;MLEAF=0.365;MQ=59.79;MQRankSum=0;QD=17.18;ReadPosRankSum=0.188;SOR=0.569;CSQ=G|intergenic_variant|MODIFIER||||||||||||||||||||	GT:AD:DP:GQ:PGT:PID:PL:PS:FI	0/0:7,0:7:3:.:.:0,3,45:.:0	1/1:2,18:21:14:.:.:508,14,0:.:0	0/0:4,0:4:3:.:.:0,3,45:.:0	0/1:22,20:42:99:.:.:441,0,839:.:0	0/1:3,22:25:11:.:.:563,0,11:.:0	0/0:41,5:61:99:.:.:441,315,1931:.:1	0/1:17,11:28:99:.:.:227,0,664:.:0	0/1:35,22:57:99:.:.:439,0,1369:.:0	0/1:14,40:54:99:.:.:981,0,218:.:0	1/1:0,19:19:57:.:.:539,57,0:.:1	1|1:0,5:5:15:1|1:3050706_T_TG:210,15,0:3050706:0	1|1:0,49:49:99:1|1:3050706_T_TG:2173,147,0:3050706:1	0/0:45,0:45:23:.:.:0,23,1534:.:0	0/0:51,3:69:99:.:.:304,290,2424:.:1	0|0:53,0:65:99:0|1:3050706_T_TGG:330,490,2692:3050706:1	1/0:8,58:151:99:.:.:3486,2267,2906:.:0	0/0:34,9:112:99:.:.:1658,1708,3059:.:1	0/0:43,0:43:21:.:.:0,21,1316:.:0	0/0:27,0:71:99:.:.:1106,1187,1889:.:1	1|1:0,40:40:99:1|1:3050706_T_TG:1714,120,0:3050706:1	0/0:17,3:30:99:.:.:277,188,628:.:1	0/0:115,25:618:99:.:.:11490,11789,17207:.:1	1|1:0,33:33:98:1|1:3050706_T_TG:1345,98,0:3050706:1	1|1:0,19:19:57:1|1:3050706_T_TG:766,57,0:3050706:1	1/1:1,15:16:38:.:.:411,38,0:.:0	0/1:2,13:15:5:.:.:324,0,5:.:0	0/0:80,0:275:99:.:.:4289,4412,6698:.:1	0|0:69,0:83:99:0|1:3050706_T_TGG:372,580,3424:3050706:1	0|1:21,14:35:99:0|1:3050706_T_TG:468,0,820:3050706:0	1|1:0,8:8:24:1|1:3050706_T_TG:353,24,0:3050706:0	1/1:2,28:30:51:.:.:766,51,0:.:1	0/1:2,15:18:1:.:.:408,0,1:.:0	0/0:30,23:141:41:.:.:1884,1442,3120:.:1	1/1:1,27:28:74:.:.:758,74,0:.:1	1/1:0,19:19:57:.:.:524,57,0:.:1	0/0:16,3:28:99:.:.:294,171,544:.:1	0|0:19,0:37:99:0|1:3050706_T_TGG:652,709,1507:3050706:1	0|1:28,20:48:99:0|1:3050706_T_TG:638,0,1074:3050706:0	1/1:1,14:15:16:.:.:361,16,0:.:0	0/0:133,0:458:99:.:.:6169,7180,13470:.:1	0/1:4,17:21:52:.:.:405,0,52:.:0	0/1:2,14:16:9:.:.:345,0,9:.:0	1|1:0,31:31:93:1|1:3050706_T_TG:1373,93,0:3050706:1	0/1:23,20:45:99:.:.:431,0,835:.:0	0|1:20,21:41:99:0|1:3050706_T_TG:717,0,771:3050706:0	1/1:1,19:20:31:.:.:550,31,0:.:0	1/1:0,8:8:24:.:.:228,24,0:.:0	0|0:1,0:4:33:0|1:3050706_T_C:117,120,162:3050706:0	1/1:2,28:30:33:.:.:742,33,0:.:0	1/1:0,3:3:9:.:.:86,9,0:.:0	0/0:36,25:97:99:.:.:1246,732,1592:.:1	0/1:3,3:6:68:.:.:68,0,68:.:0
# 1	3050768	.	TA	T	16293.6	.	AC=19;AF=0.183;AN=104;BaseQRankSum=-0.218;DP=3922;ExcessHet=1.0039;FS=2.492;InbreedingCoeff=0.0319;MLEAC=18;MLEAF=0.173;MQ=59.86;MQRankSum=0;QD=13.78;ReadPosRankSum=-0.146;SOR=0.908;CSQ=-|intergenic_variant|MODIFIER||||||||||||||||||||	GT:AD:DP:GQ:PGT:PID:PL:PS:FI	0/0:15,0:15:45:.:.:0,45,495:.:1	0/0:23,0:23:66:.:.:0,66,990:.:1	0/0:7,0:7:18:.:.:0,18,270:.:0	0|1:23,24:47:99:0|1:3050768_TA_T:939,0,867:3050768:0	0/0:16,0:16:33:.:.:0,33,495:.:0	0|1:48,30:78:99:0|1:3050768_TA_T:1066,0,1898:3050768:0	0|1:17,19:36:99:0|1:3050768_TA_T:740,0,657:3050768:0	0|1:37,27:64:99:0|1:3050768_TA_T:1009,0,1444:3050768:0	0/0:52,0:52:99:.:.:0,120,1800:.:1	0/0:26,0:26:72:.:.:0,72,1080:.:1	0/0:11,0:11:30:.:.:0,30,450:.:0	0/0:46,0:46:99:.:.:0,112,1800:.:1	0|1:47,24:71:99:0|1:3050768_TA_T:813,0,1845:3050768:0	0|1:58,32:90:99:0|1:3050768_TA_T:1169,0,2326:3050768:0	0|1:70,26:96:99:0|1:3050768_TA_T:864,0,2780:3050768:0	0/0:206,0:206:99:.:.:0,120,1800:.:1	0/0:131,0:131:99:.:.:0,120,1800:.:1	0|1:35,38:73:99:0|1:3050768_TA_T:1431,0,1342:3050768:0	0/0:57,0:57:99:.:.:0,120,1800:.:1	0/0:36,0:36:84:.:.:0,84,1260:.:1	0/0:37,0:37:99:.:.:0,99,1485:.:1	0/0:708,0:708:99:.:.:0,120,1800:.:1	1|1:0,44:44:99:1|1:3050768_TA_T:1956,132,0:3050768:1	1|1:0,23:23:69:1|1:3050768_TA_T:1022,69,0:3050768:1	0/0:28,0:28:75:.:.:0,75,1125:.:1	0/0:23,0:23:60:.:.:0,60,900:.:1	0/0:316,0:316:99:.:.:0,120,1800:.:1	0|1:75,25:100:99:0|1:3050768_TA_T:811,0,2967:3050768:0	0|1:23,25:48:99:0|1:3050768_TA_T:967,0,876:3050768:0	0/0:10,0:10:27:.:.:0,27,405:.:0	0/0:24,0:24:70:.:.:0,70,975:.:1	0/0:19,0:19:51:.:.:0,51,765:.:1	0/1:158,23:181:99:.:.:188,0,5450:.:0	0/0:18,0:18:33:.:.:0,33,495:.:0	0/0:25,0:25:72:.:.:0,72,930:.:1	0/0:35,0:35:99:.:.:0,103,1385:.:1	0|1:29,28:57:99:0|1:3050768_TA_T:1088,0,1093:3050768:0	0|1:35,38:73:99:0|1:3050768_TA_T:1477,0,1312:3050768:0	0/0:22,0:22:54:.:.:0,54,810:.:1	0/0:448,0:448:99:.:.:0,120,1800:.:1	0/0:31,0:31:87:.:.:0,87,1305:.:1	0/0:28,0:28:81:.:.:0,81,1215:.:1	0/0:34,0:34:99:.:.:0,99,1485:.:1	0|1:25,30:55:99:0|1:3050768_TA_T:1138,0,912:3050768:0	0|1:23,23:46:99:0|1:3050768_TA_T:842,0,897:3050768:0	0/0:20,0:20:60:.:.:0,60,848:.:1	0/0:5,0:5:12:.:.:0,12,180:.:0	0/0:27,0:27:66:.:.:0,66,949:.:1	0/0:35,0:35:90:.:.:0,90,1350:.:1	0/0:7,0:7:21:.:.:0,21,280:.:0	0/0:92,0:92:99:.:.:0,120,1800:.:1	0/0:14,0:14:42:.:.:0,42,594:.:1
# 1	3050776	.	T	TAAA	7046.84	.	AC=2;AF=0.019;AN=104;BaseQRankSum=-0.382;DP=4058;ExcessHet=0.1499;FS=3.125;InbreedingCoeff=0.1457;MLEAC=2;MLEAF=0.019;MQ=59.91;MQRankSum=0;QD=6.54;ReadPosRankSum=-0.611;SOR=0.99;CSQ=AAA|intergenic_variant|MODIFIER||||||||||||||||||||	GT:AD:DP:GQ:PGT:PID:PL:PS:FI	0/0:15,0:15:45:.:.:0,45,495:.:1	0/0:32,0:32:87:.:.:0,87,1305:.:1	0/0:7,0:7:18:.:.:0,18,270:.:0	0/0:48,0:48:99:.:.:0,120,1800:.:1	0/0:14,0:14:33:.:.:0,33,495:.:0	0/0:79,0:79:99:.:.:0,120,1800:.:1	0/0:40,0:40:79:.:.:0,79,1570:.:1	0/0:66,0:66:99:.:.:0,120,1800:.:1	0/0:52,0:52:99:.:.:0,120,1800:.:1	0/0:25,0:25:66:.:.:0,66,990:.:1	0/0:12,0:12:33:.:.:0,33,495:.:0	0/0:46,0:46:99:.:.:0,112,1800:.:1	0/0:71,0:71:99:.:.:0,120,1800:.:1	0/0:88,0:88:99:.:.:0,120,1800:.:1	0/0:97,0:97:99:.:.:0,120,1800:.:1	0/0:175,0:205:99:.:.:543,1068,7996:.:1	0/0:115,0:138:99:.:.:453,798,5117:.:1	0/0:74,0:74:99:.:.:0,120,1800:.:1	0/0:57,0:57:99:.:.:0,120,1800:.:1	0/0:37,0:37:90:.:.:0,90,1350:.:1	0/0:16,0:39:99:.:.:560,608,1280:.:1	0/0:708,0:708:99:.:.:0,120,1800:.:1	0/0:44,0:44:99:.:.:0,108,1620:.:1	0/0:22,0:22:60:.:.:0,60,900:.:1	0/0:30,0:30:84:.:.:0,84,1260:.:1	0/0:23,0:23:60:.:.:0,60,900:.:1	0/0:270,0:333:99:.:.:1588,2400,12886:.:1	0/0:103,0:103:99:.:.:0,120,1800:.:1	0/0:49,0:49:99:.:.:0,120,1800:.:1	0/0:10,0:10:27:.:.:0,27,405:.:0	0/0:24,0:24:70:.:.:0,70,975:.:1	0/0:19,0:19:54:.:.:0,54,810:.:1	0/0:157,0:181:99:.:.:339,811,6730:.:1	0/0:22,0:22:54:.:.:0,54,810:.:1	0/0:31,0:31:90:.:.:0,90,1142:.:1	0/0:31,0:56:99:.:.:558,651,1946:.:1	0/0:59,0:59:99:.:.:0,120,1800:.:1	0/0:71,0:71:99:.:.:0,120,1800:.:1	0/0:24,0:24:60:.:.:0,60,900:.:1	0/0:416,0:462:99:.:.:0,1251,17229:.:1	0/0:34,0:34:99:.:.:0,99,1485:.:1	0/0:30,0:30:90:.:.:0,90,1263:.:1	0/0:37,0:37:93:.:.:0,93,1395:.:1	0/0:53,0:53:99:.:.:0,120,1800:.:1	0/0:43,0:43:99:.:.:0,120,1800:.:1	0/0:26,0:26:66:.:.:0,66,990:.:1	0/0:5,0:5:12:.:.:0,12,180:.:0	1|1:0,34:34:99:1|1:3050776_T_TAAA:1530,102,0:3050776:1	0/0:37,0:37:99:.:.:0,102,1530:.:1	0/0:9,0:9:27:.:.:0,27,364:.:0	0/0:28,0:92:99:.:.:2102,2187,3180:.:1	0/0:15,0:15:45:.:.:0,45,626:.:1


class MouseVariant(Adapter):
    # Originally 1-based coordinate system
    # Converted to 0-based

    LABEL = 'mouse_variant'
    OUTPUT_FOLDER = './parsed-data'

    SKIP_BIOCYPHER = True

    WRITE_THRESHOLD = 1000000

    FILE_COLUMNS = ['CHROM', 'POS', 'ID', 'REF', 'ALT', 'QUAL', 'FILTER', 'INFO', 'FORMAT', '129P2_OlaHsd', '129S1_SvImJ', '129S5SvEvBrd', 'A_J', 'AKR_J', 'B10.RIII', 'BALB_cByJ', 'BALB_cJ', 'BTBR_T+_Itpr3tf_J', 'BUB_BnJ', 'C3H_HeH', 'C3H_HeJ', 'C57BL_10J', 'C57BL_10SnJ', 'C57BL_6NJ', 'C57BR_cdJ', 'C57L_J', 'C58_J', 'CAST_EiJ', 'CBA_J',
                    'CE_J', 'CZECHII_EiJ', 'DBA_1J', 'DBA_2J', 'FVB_NJ', 'I_LnJ', 'JF1_MsJ', 'KK_HiJ', 'LEWES_EiJ', 'LG_J', 'LP_J', 'MAMy_J', 'MOLF_EiJ', 'NOD_ShiLtJ', 'NON_LtJ', 'NZB_B1NJ', 'NZO_HlLtJ', 'NZW_LacJ', 'PL_J', 'PWK_PhJ', 'QSi3', 'QSi5', 'RF_J', 'RIIIS_J', 'SEA_GnJ', 'SJL_J', 'SM_J', 'SPRET_EiJ', 'ST_bJ', 'SWR_J', 'WSB_EiJ', 'ZALENDE_EiJ']

    COLUMNS_TO_LOAD = ['CHROM', 'POS', 'ID', 'REF', 'ALT', 'QUAL', 'FILTER', 'FORMAT',
                       '129S1_SvImJ', 'A_J', 'CAST_EiJ', 'NOD_ShiLtJ', 'NZO_HlLtJ', 'PWK_PhJ', 'WSB_EiJ']

    STRAINS = ['129S1_SvImJ', 'A_J', 'CAST_EiJ',
               'NOD_ShiLtJ', 'NZO_HlLtJ', 'PWK_PhJ', 'WSB_EiJ']

    def __init__(self, filepath=None, dry_run=True):
        self.filepath = filepath
        self.label = self.LABEL
        if not os.path.exists(self.OUTPUT_FOLDER):
            os.makedirs(self.OUTPUT_FOLDER)
        self.output_filepath = '{}/{}-{}.json'.format(
            self.OUTPUT_FOLDER,
            self.label,
            filepath.split('/')[-1],
        )
        self.dry_run = dry_run

        super(MouseVariant, self).__init__()

    def process_file(self):
        parsed_data_file = open(self.output_filepath, 'w')

        # Install instructions: https://github.com/biocommons/biocommons.seqrepo
        dp = create_dataproxy(
            'seqrepo+file:///usr/local/share/seqrepo/mouse')
        seq_repo = SeqRepo('/usr/local/share/seqrepo/mouse')
        translator = Translator(data_proxy=dp, default_assembly_name='GRCm39')

        reading_data = False
        record_count = 0
        json_objects = []
        json_object_keys = set()
        line_index = 0

        for line in open(self.filepath, 'r'):
            if line.startswith('#CHROM'):
                reading_data = True
                continue

            if reading_data:
                data_line = line.strip().split()
                spdi = build_spdi(
                    data_line[0],
                    data_line[1],
                    data_line[3],
                    data_line[4],
                    translator,
                    seq_repo,
                    assembly='GRCm39'
                )

                for strain in self.STRAINS:
                    index = self.FILE_COLUMNS.index(strain)

                    genotype_call = data_line[self.FILE_COLUMNS.index(strain)].split(':')[
                        0]
                    # - './.' = no genotype call was made
                    # - '0/0' = genotype is the same as the reference geneome
                    # - '1/1' = homozygous alternative allele; can also be '2/2',
                    # 3/3', etc. if more than one alternative allele is present.
                    # - '0/1' = heterozygous genotype; can also be '1/2', '0/2', etc.
                    # the strain has variant if it is hemozygous or heterzygous
                    if genotype_call != './.' or genotype_call != '0/0':

                        id = build_mouse_variant_id(
                            data_line[0],
                            data_line[1],
                            data_line[3],
                            data_line[4],
                            strain
                        )

                        to_json = {
                            '_key': id,
                            'chr': 'chr' + data_line[0],
                            'pos:long': int(data_line[1]) - 1,
                            'rsid': [] if data_line[2] == '.' else [data_line[2]],
                            'ref': data_line[3],
                            'alt': data_line[4],
                            'strain': strain,
                            'qual': data_line[5],
                            'filter': None if data_line[6] == '.' else data_line[6],
                            'fi': int(data_line[self.FILE_COLUMNS.index(strain)].split(':')[-1]),
                            'spdi': spdi,
                            'hgvs': build_hgvs_from_spdi(spdi),
                            'source': 'MOUSE GENOMES PROJECT',
                            'source_url': 'https://ftp.ebi.ac.uk/pub/databases/mousegenomes/'
                        }

                        # Several variants have the same rsid and are listed in different parts of the file.
                        # Scanning all the dataset twice is non-pratical.
                        # Using simple heuristics: conflicting rsids appear close to each other in data files
                        # keeping a queue of 1M records to check for conflicting rsids and group them
                        # comparing the full file is not feasible

                        if len(json_objects) > 0:
                            found = False
                            if to_json['_key'] in json_object_keys:
                                for object in json_objects:
                                    if object['_key'] == to_json['_key']:
                                        object['rsid'] += to_json['rsid']
                                        found = True
                                        break

                            if not found:
                                json_objects.append(to_json)
                                json_object_keys.add(to_json['_key'])

                            if len(json_objects) > MouseVariant.WRITE_THRESHOLD:
                                store_json = json_objects.pop(0)
                                json_object_keys.remove(store_json['_key'])

                                json.dump(store_json, parsed_data_file)
                                parsed_data_file.write('\n')
                                record_count += 1
                        else:
                            json_objects = [to_json]
                            json_object_keys.add(to_json['_key'])

                        if record_count > MouseVariant.WRITE_THRESHOLD:
                            parsed_data_file.close()
                            self.save_to_arango()

                            os.remove(self.output_filepath)
                            record_count = 0

                            parsed_data_file = open(self.output_filepath, 'w')
                line_index += 1
        for object in json_objects:
            json.dump(object, parsed_data_file)
            parsed_data_file.write('\n')
            record_count += 1

        parsed_data_file.close()
        self.save_to_arango()

    def arangodb(self):
        return ArangoDB().generate_json_import_statement(self.output_filepath, self.collection)

    def save_to_arango(self):
        if self.dry_run:
            print(self.arangodb()[0])
        else:
            os.system(self.arangodb()[0])
