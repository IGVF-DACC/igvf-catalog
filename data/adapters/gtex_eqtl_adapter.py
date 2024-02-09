import csv
import hashlib
import os
import gzip
from math import log10

from adapters import Adapter
from adapters.helpers import build_variant_id, to_float


# Example QTEx eQTL input file:
# variant_id      gene_id tss_distance    ma_samples      ma_count        maf     pval_nominal    slope   slope_se        pval_nominal_threshold  min_pval_nominal        pval_beta
# chr1_845402_A_G_b38     ENSG00000225972.1       216340  4       4       0.0155039       2.89394e-06     2.04385 0.413032        2.775e-05       2.89394e-06     0.00337661
# chr1_920569_G_A_b38     ENSG00000225972.1       291507  4       4       0.0155039       1.07258e-05     1.92269 0.415516        2.775e-05       2.89394e-06     0.00337661

# Ontology id mapping file: GTEx tissue -> UBERON id
# Tissue    Filename    Ontology ID
# Brain - Amygdala	Brain_Amygdala	UBERON:0001876


class GtexEQtl(Adapter):
    # 1-based coordinate system in variant_id
    ALLOWED_LABELS = ['GTEx_eqtl', 'GTEx_eqtl_term']
    SOURCE = 'GTEx'
    SOURCE_URL = 'https://www.gtexportal.org/home/datasets'
    ONTOLOGY_ID_MAPPING_PATH = './data_loading_support_files/GTEx_UBERON_mapping.tsv'

    def __init__(self, filepath, label='GTEx_eqtl'):

        if label not in GtexEQtl.ALLOWED_LABELS:
            raise ValueError('Ivalid label. Allowed values: ' +
                             ','.join(GtexEQtl.ALLOWED_LABELS))

        self.filepath = filepath
        self.dataset = label
        self.label = label

        super(GtexEQtl, self).__init__()

    def process_file(self):
        self.load_ontology_mapping()

        # Iterate over all tissues in the folder, example filename: Brain_Amygdala.v8.signif_variant_gene_pairs.txt.gz
        # Note: The server was crashed due to memory issues when iterating all the 49 tissues at once, had to split the files into 4 folders instead when loading.
        for filename in os.listdir(self.filepath):
            if filename.endswith('signif_variant_gene_pairs.txt.gz'):
                print('Loading ' + filename)
                filename_biological_context = filename.split('.')[0]
                biological_context = self.tissue_name_mapping.get(
                    filename_biological_context)

                if self.label == 'GTEx_eqtl_term':
                    ontology_id = self.ontology_id_mapping.get(
                        filename_biological_context)
                    if ontology_id is None:
                        print('Ontology id unavailable, skipping: ' + filename)
                        continue

                with gzip.open(self.filepath + '/' + filename, 'rt') as qtl:
                    qtl_csv = csv.reader(qtl, delimiter='\t')

                    next(qtl_csv)

                    for row in qtl_csv:
                        chr, pos, ref_seq, alt_seq, assembly_code = row[0].split(
                            '_')

                        if assembly_code != 'b38':
                            print('Unsuported assembly: ' + assembly_code)
                            continue

                        variant_id = build_variant_id(
                            chr, pos, ref_seq, alt_seq, 'GRCh38'
                        )

                        gene_id = row[1].split('.')[0]

                        # this edge id is too long, needs to be hashed
                        variants_genes_id = hashlib.sha256(
                            (variant_id + '_' + gene_id + '_' + biological_context).encode()).hexdigest()

                        if self.label == 'GTEx_eqtl':
                            try:
                                _id = variants_genes_id
                                _source = 'variants/' + variant_id
                                _target = 'genes/' + gene_id

                                pvalue = float(row[6])
                                if pvalue == 0:
                                    log_pvalue = None
                                else:
                                    log_pvalue = -1 * log10(pvalue)

                                _props = {
                                    'biological_context': self.ontology_term_mapping.get(filename_biological_context) or biological_context,
                                    'chr': chr,
                                    'log10pvalue': log_pvalue,
                                    'slope': to_float(row[7]),
                                    'beta': to_float(row[-1]),
                                    'label': 'eQTL',
                                    'source': GtexEQtl.SOURCE,
                                    'source_url': GtexEQtl.SOURCE_URL
                                }

                                yield(_id, _source, _target, self.label, _props)

                            except:
                                print(row)
                                pass

                        elif self.label == 'GTEx_eqtl_term':
                            try:
                                _id = hashlib.sha256(
                                    (variants_genes_id + '_' + ontology_id).encode()).hexdigest()
                                _source = 'variants_genes/' + variants_genes_id
                                _target = 'ontology_terms/' + ontology_id
                                _props = {
                                    'biological_context': biological_context,
                                    'source': GtexEQtl.SOURCE,
                                    'source_url': GtexEQtl.SOURCE_URL
                                }

                                yield(_id, _source, _target, self.label, _props)

                            except:
                                print(row)
                                pass

    def load_ontology_mapping(self):
        self.ontology_id_mapping = {}  # e.g. key: 'Brain_Amygdala', value: 'UBERON_0001876'
        # e.g. filename: Esophagus_Gastroesophageal_Junction -> tissue name: Esophagus - Gastroesophageal Junction
        self.tissue_name_mapping = {}
        # e.g. key: 'Brain_Amygdala', value (UBERON term name): 'amygdala'
        self.ontology_term_mapping = {}

        with open(GtexEQtl.ONTOLOGY_ID_MAPPING_PATH, 'r') as ontology_id_mapfile:
            ontology_id_csv = csv.reader(ontology_id_mapfile, delimiter='\t')
            next(ontology_id_csv)
            for row in ontology_id_csv:
                if row[1]:
                    self.ontology_id_mapping[row[1]] = row[2].replace(':', '_')
                    self.tissue_name_mapping[row[1]] = row[0]
                    self.ontology_term_mapping[row[1]] = row[3]
