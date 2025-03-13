import json
import pickle
from typing import Optional
from ga4gh.vrs.extras.translator import AlleleTranslator
from ga4gh.vrs.dataproxy import create_dataproxy
from biocommons.seqrepo import SeqRepo
from xxhash import xxh128_digest

from adapters.helpers import build_variant_id
from scripts.variants_spdi import build_spdi, build_hgvs_from_spdi

from adapters.writer import Writer
from adapters.deduplication import get_container

# Example file format for FAVOR (from chr 21)

# #fileformat=VCFv4.2
# #fileDate=20230212
# #source=SeqArray_Format_v1.0
# #reference=GRCh38.p13
# #contig=<ID=NC_000001.11>
# #contig=<ID=NC_000002.12>
# #contig=<ID=NC_000003.12>
# #contig=<ID=NC_000004.12>
# #contig=<ID=NC_000005.10>
# #...
# #contig=<ID=NW_021160030.1>
# #contig=<ID=NW_021160031.1>
# #INFO=<ID=RS,Number=1,Type=Integer,Description="dbSNP ID (i.e. rs number)">
# #INFO=<ID=GENEINFO,Number=1,Type=String,Description="Pairs each of gene symbol:gene id.  The gene symbol and id are delimited by a colon (:) and each pair is delimited by a vertical bar (|).  Does not include pseu
# dogenes.">
# #...
# #INFO=<>
# #INFO=<>
# #FILTER=<ID=PASS,Description="All filters passed">
# #FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
# #dbSNP_BUILD_ID=155
# #phasing=partial
# #bcftools_normVersion=1.5+htslib-1.5
# #bcftools_normCommand="norm -m -any -Oz -o /n/holystore01/LABS/xlin/Lab/zhouhufeng/Data/WGA/DBSNP/dbSNP155/dbSNP155Oct21.m.gz /n/holystore01/LABS/xlin/Lab/zhouhufeng/Data/WGA/DBSNP/dbSNP155/GCF_000001405.39.gz; Da
# #te=Wed Oct 20 19:20:39 2021"
# #bcftools_viewVersion=1.5+htslib-1.5
# bcftools_viewCommand="view -Ov -o ChromSplit/dbSNP155Nov2.m.vcf dbSNP155Oct21.m.gz; Date=Tue Nov  2 20:37:08 2021"
# bcftools_normVersion=1.9+htslib-1.9
# bcftools_normCommand="norm -f /n/holystore01/LABS/xlin/Lab/zhouhufeng/Data/CCDGF3/Source/RefGenome/hg38.nochr.fa -Ov -o dbSNP155Nov2.chr21.mn.vcf dbSNP155Nov2.chr21.m.vcf; Date=Tue Feb  7 20:30:53 2023"
# #CHROM  POS     ID      REF     ALT     QUAL    FILTER  INFO    FORMAT
# 21      5025532 rs1879593094    G       C       .       NA      RS=1879593094;GENEINFO=LOC102723996:102723996;SSR=0;VC=SNV;INT;GNO;FREQ=dbGaP_PopFreq:0.5001,0.4999;COMMON;FAVORFullDB/VarInfo=21-5025532-G-C;FAVORFul
# lDB/vid=4.53712e+09;FAVORFullDB/variant_vcf=21-5025532-G-C;FAVORFullDB/variant_annovar=21-5025532-5025532-G-C;FAVORFullDB/chromosome=21;FAVORFullDB/start_position=5.02553e+06;FAVORFullDB/end_position=5.02553e+06;FA
# VORFullDB/ref_annovar=G;FAVORFullDB/alt_annovar=C;FAVORFullDB/position=5.02553e+06;FAVORFullDB/ref_vcf=G;FAVORFullDB/alt_vcf=C;FAVORFullDB/apc_conservation=0.717268;FAVORFullDB/apc_conservation_v2=0.61131;FAVORFull
# DB/apc_epigenetics_active=0.226559;FAVORFullDB/apc_epigenetics=0.304623;FAVORFullDB/apc_epigenetics_repressed=0.310309;FAVORFullDB/apc_epigenetics_transcription=0.323364;FAVORFullDB/apc_local_nucleotide_diversity=4
# .27664;FAVORFullDB/apc_local_nucleotide_diversity_v2=14.4278;FAVORFullDB/apc_local_nucleotide_diversity_v3=14.61;FAVORFullDB/apc_mappability=0.184841;FAVORFullDB/apc_micro_rna=99.4512;FAVORFullDB/apc_mutation_densi
# ty=14.3892;FAVORFullDB/apc_protein_function=20.2494;FAVORFullDB/apc_protein_function_v2=4.92793e-10;FAVORFullDB/apc_protein_function_v3=2.96949;FAVORFullDB/apc_proximity_to_coding=0.109188;FAVORFullDB/apc_proximity
# _to_coding_v2=15.1786;FAVORFullDB/apc_proximity_to_tsstes=7.32475;FAVORFullDB/apc_transcription_factor=3.14279;FAVORFullDB/bravo_an=264690;FAVORFullDB/bravo_af=0.499883;FAVORFullDB/filter_status=SVM;FAVORFullDB/fat
# hmm_xf=0.405274;FAVORFullDB/genecode_comprehensive_category=intronic;FAVORFullDB/genecode_comprehensive_info=FP565260.3;FAVORFullDB/linsight=0.214926;FAVORFullDB/gc=0.603;FAVORFullDB/cpg=0.027;FAVORFullDB/min_dist_
# tss=2999;FAVORFullDB/min_dist_tse=9153;FAVORFullDB/priphcons=0.007;FAVORFullDB/mamphcons=0;FAVORFullDB/verphcons=0;FAVORFullDB/priphylop=0.185;FAVORFullDB/mamphylop=-0.62;FAVORFullDB/verphylop=-0.586;FAVORFullDB/ch
# mm_e1=0;FAVORFullDB/chmm_e2=0;FAVORFullDB/chmm_e3=1;FAVORFullDB/chmm_e4=3;FAVORFullDB/chmm_e5=0;FAVORFullDB/chmm_e6=0;FAVORFullDB/chmm_e7=4;FAVORFullDB/chmm_e8=1;FAVORFullDB/chmm_e9=0;FAVORFullDB/chmm_e10=0;FAVORFu
# llDB/chmm_e11=1;FAVORFullDB/chmm_e12=1;FAVORFullDB/chmm_e13=0;FAVORFullDB/chmm_e14=1;FAVORFullDB/chmm_e15=18;FAVORFullDB/chmm_e16=0;FAVORFullDB/chmm_e17=0;FAVORFullDB/chmm_e18=0;FAVORFullDB/chmm_e19=0;FAVORFullDB/c
# hmm_e20=0;FAVORFullDB/chmm_e21=6;FAVORFullDB/chmm_e22=7;FAVORFullDB/chmm_e23=3;FAVORFullDB/chmm_e24=2;FAVORFullDB/chmm_e25=0;FAVORFullDB/gerp_n=0.447;FAVORFullDB/gerp_s=-0.894;FAVORFullDB/encodetotal_rna_sum=0;FAVO
# RFullDB/freq10000bp=2;FAVORFullDB/rare10000bp=5;FAVORFullDB/sngl10000bp=31;FAVORFullDB/cadd_rawscore=0.096711;FAVORFullDB/cadd_phred=2.753;FAVORFullDB/super_enhancer=SE_11779;FAVORFullDB/ucsc_category=intronic;FAVO
# RFullDB/ucsc_info=ENST00000612610.4,ENST00000620481.4,ENST00000623795.1,ENST00000623903.3,ENST00000623960.3


class Favor:
    # Originally 1-based coordinate system
    # Converted to 0-based

    DATASET = 'favor'

    NUMERIC_FIELDS = ['start_position', 'end_position', 'vid', 'linsight', 'gc', 'cpg', 'priphcons', 'mamphcons', 'verphcons',
                      'priphylop', 'mamphylop', 'verphylop', 'bstatistic', 'freq10000bp', 'rare10000', 'k36_umap', 'k50_umap', 'k100_uma', 'nucdiv']

    WRITE_THRESHOLD = 1000000

    FIELDS = [
        'varinfo', 'vid', 'variant_vcf', 'variant_annovar', 'start_position',
        'end_position', 'ref_annovar', 'alt_annovar', 'ref_vcf', 'alt_vcf', 'aloft_value', 'aloft_description',
        'apc_conservation', 'apc_conservation_v2', 'apc_epigenetics_active', 'apc_epigenetics',
        'apc_epigenetics_repressed', 'apc_epigenetics_transcription', 'apc_local_nucleotide_diversity',
        'apc_local_nucleotide_diversity_v2', 'apc_local_nucleotide_diversity_v3', 'apc_mappability', 'apc_micro_rna',
        'apc_mutation_density', 'apc_protein_function', 'apc_protein_function_v2', 'apc_protein_function_v3',
        'apc_proximity_to_coding', 'apc_proximity_to_coding_v2', 'apc_proximity_to_tsstes', 'apc_transcription_factor',
        'bravo_an', 'bravo_af', 'filter_status', 'clnsig', 'clnsigincl', 'clndn', 'clndnincl', 'clnrevstat', 'origin',
        'clndisdb', 'clndisdbincl', 'geneinfo', 'polyphen2_hdiv_score', 'polyphen2_hvar_score', 'mutation_taster_score',
        'mutation_assessor_score', 'metasvm_pred', 'fathmm_xf', 'funseq_value', 'funseq_description',
        'genecode_comprehensive_categoty', 'af_total', 'af_asj_female', 'af_eas_female', 'af_afr_male', 'af_female',
        'af_fin_male', 'af_oth_female', 'af_ami', 'af_oth', 'af_male', 'af_ami_female', 'af_afr', 'af_eas_male', 'af_sas',
        'af_nfe_female', 'af_asj_male', 'af_raw', 'af_oth_male', 'af_nfe_male', 'af_asj', 'af_amr_male', 'af_amr_female',
        'af_sas_female', 'af_fin', 'af_afr_female', 'af_sas_male', 'af_amr', 'af_nfe', 'af_eas', 'af_ami_male',
        'af_fin_female', 'sift_cat', 'sift_val', 'polyphen_cat', 'polyphen_val', 'cadd_rawscore', 'cadd_phred',
        'refseq_category', 'tg_afr', 'tg_all', 'tg_amr', 'tg_eas', 'tg_eur', 'tg_sas', 'linsight', 'gc', 'cpg',
        'priphcons', 'mamphcons', 'verphcons', 'priphylop', 'mamphylop', 'verphylop', 'bstatistic', 'freq10000bp',
        'rare10000', 'k36_umap', 'k50_umap', 'k100_uma', 'nucdiv'
    ]

    def __init__(self, filepath=None, ca_ids_path=None, writer: Optional[Writer] = None, **kwargs):
        self.filepath = filepath
        self.dataset = Favor.DATASET
        self.label = Favor.DATASET
        self.writer = writer

        # pickle file of a dict { hgvs => ca_id } from ClinGen, per chromosome
        # for example: 1.pickle from s3://igvf-catalog-datasets/hgvs/hgvs_caid_mappings, for chromosome 1
        self.ca_ids = pickle.load(open(ca_ids_path, 'rb'))
        self.container = get_container()

    def convert_freq_value(self, value):
        if value == '.':
            value = 0

        try:
            value = float(value)
        except:
            pass

        return value

    # only selecting FREQ value from INFO data
    def parse_metadata(self, info):
        info_obj = {}
        for pair in info.strip().split(';'):
            try:
                key, value = pair.split('=', 1)
            except:
                if len(pair.split('=')) == 1:
                    key = pair.split('=')[0]
                    value = None

            # example of FREQ value: 'Korea1K:0.9545,0.04545|TOPMED:0.8587|dbGaP_PopFreq:0.9243,0.07566'
            if key == 'FREQ':
                info_obj['freq'] = {}
                for freq in value.split('|'):
                    freq_name, freq_value = freq.split(':')
                    freq_name = freq_name.lower()
                    values = freq_value.split(',')

                    info_obj['freq'][freq_name] = {
                        'ref': self.convert_freq_value(values[0])
                    }

                    if len(values) > 1:
                        info_obj['freq'][freq_name]['alt'] = self.convert_freq_value(
                            values[1])
                    else:
                        if self.convert_freq_value(values[0]) == 1.0:
                            info_obj['freq'][freq_name]['alt'] = 0.0

            # e.g. FAVORFullDB/variant_annovar
            if key.startswith('FAVOR'):
                key = key.split('/')[1].lower()

                if key.lower() not in Favor.FIELDS:
                    continue

                if key.startswith('tg'):
                    try:
                        value = float(value)
                        key = key.replace('tg', '1kg')
                    except:
                        pass

                if key.startswith('apc') or key.startswith('af') or key.startswith('tg') or key.startswith('bravo') or key.startswith('cadd') or key.startswith('fathmm') or key.startswith('min_dist') or key.startswith('chmm') or key.startswith('gerp') or key.startswith('encode') or key.startswith('freq'):
                    try:
                        value = float(value)
                    except:
                        pass

                if key in Favor.NUMERIC_FIELDS:
                    try:
                        value = float(value)
                    except:
                        pass

                info_obj[key] = value

        return info_obj

    def process_file(self):
        self.writer.open()
        # Install instructions: https://github.com/biocommons/biocommons.seqrepo
        dp = create_dataproxy(
            'seqrepo+file:///usr/local/share/seqrepo/2018-11-26')
        seq_repo = SeqRepo('/usr/local/share/seqrepo/2018-11-26')
        translator = AlleleTranslator(data_proxy=dp)

        reading_data = False
        json_objects = []
        json_object_keys = set()

        for line in open(self.filepath, 'r'):
            if line.startswith('#CHROM'):
                reading_data = True
                continue

            if reading_data:
                data_line = line.strip().split()

                # data files sometimes add 'chr' before the chromosome value and sometimes they do not, normalizing it:
                chrm = data_line[0].replace('chr', '')

                ref = data_line[3]
                alt = data_line[4]

                id = build_variant_id(chrm, data_line[1], ref, alt)

                annotations = self.parse_metadata(data_line[7])

                try:
                    spdi = build_spdi(
                        chrm,
                        data_line[1],
                        ref,
                        alt,
                        translator,
                        seq_repo
                    )
                    # hash is always 49 bytes, so it does save space and make estimation of memory usage easy
                    spdi_hash = xxh128_digest(spdi)
                    if self.container.contains(spdi_hash):
                        continue
                    self.container.add(spdi_hash)
                except Exception as e:
                    print('Failed to generate SPDI for chr' + chrm + ', pos: ' +
                          data_line[1] + ', ref: ' + ref + ' alt: ' + alt)
                    print(repr(e))
                    continue

                variation_type = 'SNP'
                if len(ref) < len(alt):
                    variation_type = 'insertion'
                elif len(ref) > len(alt):
                    variation_type = 'deletion'

                hgvs = build_hgvs_from_spdi(spdi)

                to_json = {
                    '_key': id,
                    'name': spdi,
                    'chr': 'chr' + chrm,
                    'pos': int(data_line[1]) - 1,
                    'rsid': [data_line[2]],
                    'ref': data_line[3],
                    'alt': data_line[4],
                    'qual': data_line[5],
                    'filter': None if data_line[6] == 'NA' else data_line[6],
                    'variation_type': variation_type,
                    'annotations': annotations,
                    'format': data_line[8] if (len(data_line) > 8) else None,
                    'spdi': spdi,
                    'hgvs': hgvs,
                    'ca_id': self.ca_ids.get(hgvs),
                    'organism': 'Homo sapiens',
                    'source': 'FAVOR',
                    'source_url': 'http://favor.genohub.org/'
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

                    if len(json_objects) > Favor.WRITE_THRESHOLD:
                        store_json = json_objects.pop(0)
                        json_object_keys.remove(store_json['_key'])

                        self.writer.write(json.dumps(store_json))
                        self.writer.write('\n')
                else:
                    json_objects = [to_json]
                    json_object_keys.add(to_json['_key'])

        for object in json_objects:
            self.writer.write(json.dumps(object))
            self.writer.write('\n')

        self.writer.close()
