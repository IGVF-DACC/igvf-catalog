import gzip
import json
import os
import hashlib
import csv
from math import log10
from typing import Optional

from adapters.helpers import build_variant_id, to_float
from adapters.writer import Writer

# The splice QTLs from GTEx are here: https://storage.googleapis.com/adult-gtex/bulk-qtl/v8/single-tissue-cis-qtl/GTEx_Analysis_v8_sQTL.tar
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

# Ontology id mapping file: GTEx tissue -> UBERON id
# Tissue    Filename    Ontology ID
# Brain - Amygdala	Brain_Amygdala	UBERON:0001876


class GtexSQtl:
    ALLOWED_LABELS = ['GTEx_splice_QTL', 'GTEx_splice_QTL_term']
    SOURCE = 'GTEx'
    SOURCE_URL_PREFIX = 'https://storage.googleapis.com/adult-gtex/bulk-qtl/v8/single-tissue-cis-qtl/GTEx_Analysis_v8_sQTL/'
    ONTOLOGY_ID_MAPPING_PATH = './data_loading_support_files/GTEx_UBERON_mapping.tsv'  # same as eqtl
    MAX_LOG10_PVALUE = 400  # based on max p_value from sqtl dataset

    def __init__(self, filepath, label='GTEx_splice_QTL', dry_run=True, writer: Optional[Writer] = None):
        if label not in GtexSQtl.ALLOWED_LABELS:
            raise ValueError('Invalid label. Allowed values: ' +
                             ','.join(GtexSQtl.ALLOWED_LABELS))

        self.filepath = filepath
        self.dataset = label
        self.label = label
        self.dry_run = dry_run
        self.type = 'edge'
        self.writer = writer

    def process_file(self):
        self.writer.open()
        self.load_ontology_mapping()

        # Iterate over all tissues in the folder, example filename: Brain_Amygdala.v8.sqtl_signifpairs.txt.gz
        # Note: The server was crashed due to memory issues when iterating all the 49 tissues at once, had to split the files into 4 folders instead when loading.
        for filename in os.listdir(self.filepath):
            if filename.endswith('sqtl_signifpairs.txt.gz'):
                print('Loading ' + filename)
                filename_biological_context = filename.split('.')[0]

                if self.label == 'GTEx_splice_QTL_term':
                    ontology_id = self.ontology_id_mapping.get(
                        filename_biological_context)
                    if ontology_id is None:
                        print('Ontology id unavailable, skipping: ' + filename)
                        continue

                with gzip.open(self.filepath + '/' + filename, 'rt') as input:
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
                        gene_id = phenotype_id_ls[-1].split('.')[0]

                        # this edge id is too long, needs to be hashed
                        # used phenotype_id instead of gene_id in the id part,
                        # in case there's same variant-gene-biological_context combination in eQTL (though unlikely)
                        variants_genes_id = hashlib.sha256(
                            (variant_id + '_' + phenotype_id + '_' + filename_biological_context).encode()).hexdigest()

                        if self.label == 'GTEx_splice_QTL':
                            try:
                                _id = variants_genes_id
                                _source = 'variants/' + variant_id
                                _target = 'genes/' + gene_id

                                pvalue = float(line_ls[6])
                                if pvalue == 0:
                                    log_pvalue = GtexSQtl.MAX_LOG10_PVALUE
                                else:
                                    log_pvalue = -1 * log10(pvalue)

                                _props = {
                                    '_key': _id,
                                    '_from': _source,
                                    '_to': _target,
                                    'chr': variant_id_ls[0],
                                    # use UBERON term names
                                    'biological_context': self.ontology_term_mapping.get(filename_biological_context),
                                    'sqrt_maf': to_float(line_ls[5]),
                                    'p_value': pvalue,
                                    'log10pvalue': log_pvalue,
                                    'pval_nominal_threshold': to_float(line_ls[9]),
                                    'min_pval_nominal': to_float(line_ls[10]),
                                    'effect_size': to_float(line_ls[7]),
                                    'effect_size_se': to_float(line_ls[8]),
                                    'pval_beta': to_float(line_ls[11]),
                                    'intron_chr': phenotype_id_ls[0],
                                    'intron_start': phenotype_id_ls[1],
                                    'intron_end': phenotype_id_ls[2],
                                    'label': 'splice_QTL',
                                    'source': GtexSQtl.SOURCE,
                                    'source_url': GtexSQtl.SOURCE_URL_PREFIX + filename,
                                    'name': 'modulates splicing of',
                                    'inverse_name': 'splicing modulated by',
                                    'biological_process': 'ontology_terms/GO_0043484'
                                }
                                self.writer.write(json.dumps(_props))
                                self.writer.write('\n')

                            except:
                                print(
                                    f'fail to process edge for GTEx sQTL: {variant_id_info} and {phenotype_id}')

                        elif self.label == 'GTEx_splice_QTL_term':
                            try:
                                _id = hashlib.sha256(
                                    (variants_genes_id + '_' + ontology_id).encode()).hexdigest()
                                _source = 'variants_genes/' + variants_genes_id
                                _target = 'ontology_terms/' + ontology_id
                                _props = {
                                    '_key': _id,
                                    '_from': _source,
                                    '_to': _target,
                                    'biological_context': self.ontology_term_mapping.get(filename_biological_context),
                                    'source': GtexSQtl.SOURCE,
                                    'source_url': GtexSQtl.SOURCE_URL_PREFIX + filename,
                                    'name': 'occurs in',
                                    'inverse_name': 'has measurement'
                                }

                                self.writer.write(json.dumps(_props))
                                self.writer.write('\n')

                            except:
                                print(
                                    f'fail to process edge for GTEx sQTL: {variant_id_info} and {phenotype_id}')
                                pass

        self.writer.close()

    def load_ontology_mapping(self):
        self.ontology_id_mapping = {}  # e.g. key: 'Brain_Amygdala', value: 'UBERON_0001876'
        # e.g. key: 'Brain_Amygdala', value (UBERON term name): 'amygdala'
        self.ontology_term_mapping = {}

        with open(GtexSQtl.ONTOLOGY_ID_MAPPING_PATH, 'r') as ontology_id_mapfile:
            ontology_id_csv = csv.reader(ontology_id_mapfile, delimiter='\t')
            next(ontology_id_csv)
            for row in ontology_id_csv:
                if row[1]:
                    self.ontology_id_mapping[row[1]] = row[2].replace(':', '_')
                    self.ontology_term_mapping[row[1]] = row[3]
