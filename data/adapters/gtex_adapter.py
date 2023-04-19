import gzip
from adapters import Adapter
from adapters.helpers import build_variant_id

# The splice QTLs from GTEx are here: https://storage.googleapis.com/gtex_analysis_v8/single_tissue_qtl_data/GTEx_Analysis_v8_sQTL.tar
# All the files use assembly grch38
# sample data:
# variant_id      phenotype_id    tss_distance    ma_samples      ma_count        maf     pval_nominal    slope   slope_se        pval_nominal_threshold  min_pval_nominal        pval_beta
# chr1_739465_TTTTG_T_b38 chr1:497299:498399:clu_51878:ENSG00000237094.11 237848  11      11      0.00946644      1.09562e-05     1.28383 0.289287        5.70798e-05     1.29619e-11     5.5868e-07
# chr1_763097_C_T_b38     chr1:497299:498399:clu_51878:ENSG00000237094.11 261480  14      15      0.0129088       1.94322e-07     1.22972 0.233293        5.70798e-05     1.29619e-11     5.5868e-07
# chr1_763107_A_G_b38     chr1:497299:498399:clu_51878:ENSG00000237094.11 261490  14      15      0.0129088       1.94322e-07     1.22972 0.233293        5.70798e-05     1.29619e-11     5.5868e-07
# chr1_767270_T_C_b38     chr1:497299:498399:clu_51878:ENSG00000237094.11 265653  17      18      0.0154905       2.03414e-09     1.32509 0.217368        5.70798e-05     1.29619e-11     5.5868e-07
# chr1_767578_T_C_b38     chr1:497299:498399:clu_51878:ENSG00000237094.11 265961  17      18      0.0154905       2.03414e-09     1.32509 0.217368        5.70798e-05     1.29619e-11     5.5868e-07
# chr1_774708_C_A_b38     chr1:497299:498399:clu_51878:ENSG00000237094.11 273091  15      16      0.0137694       3.69542e-08     1.27217 0.227855        5.70798e-05     1.29619e-11     5.5868e-07
# chr1_774815_A_G_b38     chr1:497299:498399:clu_51878:ENSG00000237094.11 273198  17      18      0.0154905       2.03414e-09     1.32509 0.217368        5.70798e-05     1.29619e-11     5.5868e-07
# chr1_775065_A_G_b38     chr1:497299:498399:clu_51878:ENSG00000237094.11 273448  15      16      0.0137694       3.22485e-06     1.07183 0.227863        5.70798e-05     1.29619e-11     5.5868e-07
# chr1_775962_A_G_b38     chr1:497299:498399:clu_51878:ENSG00000237094.11 274345  16      17      0.0146299       4.77356e-10     1.41823 0.223716        5.70798e-05     1.29619e-11     5.5868e-07

# The phenotype ids represent the alternative intron excision events within the genes, which were used in LeafCutter to identify those sQTLs.


class Gtex(Adapter):

    ALLOWED_TYPES = ['gtex splice variant to gene association']
    ALLOWED_LABELS = ['GTEx_splice_QTL']

    def __init__(self, filepath, tissue, type='gtex splice variant to gene association', label='GTEx_splice_QTL'):
        self.filepath = filepath
        self.dataset = label
        self.type = type
        self.label = label
        self.tissue = tissue

        super(Gtex, self).__init__()

    def process_file(self):
        with gzip.open(self.filepath, 'rt') as input:
            next(input)
            for line in input:
                line_ls = line.split()
                variant_id_info = line_ls[0]
                variant_id_ls = line_ls[0].split('_')
                variant_id = build_variant_id(
                    variant_id_ls[0],
                    variant_id_ls[1],
                    variant_id_ls[2],
                    variant_id_ls[3]
                )

                phenotype_id = line_ls[1]
                phenotype_id_ls = phenotype_id.split(':')
                gene_id = phenotype_id_ls[-1]

                try:
                    _id = variant_id + '_' + gene_id + '_' + self.tissue
                    _source = 'transcripts/' + variant_id
                    _target = 'genes/' + gene_id
                    _props = {
                        'chr': variant_id_ls[0],
                        'sqrt_maf': line_ls[5],
                        'p_value': line_ls[6],
                        'pval_nominal_threshold': line_ls[9],
                        'min_pval_nominal': line_ls[10],
                        'slope': line_ls[7],
                        'slope_se': line_ls[8],
                        'beta': line_ls[11],
                        'intron_chr': phenotype_id_ls[0],
                        'intron_start': phenotype_id_ls[1],
                        'intron_end': phenotype_id_ls[2],
                    }
                    yield(_id, _source, _target, self.label, _props)

                except:
                    print(
                        f'fail to process edge for GTEx sQTL: {variant_id_info} and {phenotype_id}')
