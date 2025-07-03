import csv
import hashlib
import json
import gzip
from typing import Optional

from adapters.helpers import build_variant_id, to_float
from adapters.writer import Writer
from adapters.gene_validator import GeneValidator

# metadata file is downloaded from https://github.com/eQTL-Catalogue/eQTL-Catalogue-resources/blob/master/tabix/tabix_ftp_paths.tsv
# metadata file example:
# study_id	dataset_id	study_label	sample_group	tissue_id	tissue_label	condition_label	sample_size	quant_method	ftp_path	ftp_cs_path	ftp_lbf_path
# QTS000001	QTD000001	Alasoo_2018	macrophage_naive	CL_0000235	macrophage	naive	84	ge	ftp://ftp.ebi.ac.uk/pub/databases/spot/eQTL/sumstats/QTS000001/QTD000001/QTD000001.all.tsv.gz	ftp://ftp.ebi.ac.uk/pub/databases/spot/eQTL/susie/QTS000001/QTD000001/QTD000001.credible_sets.tsv.gz	ftp://ftp.ebi.ac.uk/pub/databases/spot/eQTL/susie/QTS000001/QTD000001/QTD000001.lbf_variable.txt.gz
# QTS000001	QTD000002	Alasoo_2018	macrophage_naive	CL_0000235	macrophage	naive	84	exon	ftp://ftp.ebi.ac.uk/pub/databases/spot/eQTL/sumstats/QTS000001/QTD000002/QTD000002.cc.tsv.gz	ftp://ftp.ebi.ac.uk/pub/databases/spot/eQTL/susie/QTS000001/QTD000002/QTD000002.credible_sets.tsv.gz	ftp://ftp.ebi.ac.uk/pub/databases/spot/eQTL/susie/QTS000001/QTD000002/QTD000002.lbf_variable.txt.gz
# QTS000001	QTD000003	Alasoo_2018	macrophage_naive	CL_0000235	macrophage	naive	84	tx	ftp://ftp.ebi.ac.uk/pub/databases/spot/eQTL/sumstats/QTS000001/QTD000003/QTD000003.cc.tsv.gz	ftp://ftp.ebi.ac.uk/pub/databases/spot/eQTL/susie/QTS000001/QTD000003/QTD000003.credible_sets.tsv.gz	ftp://ftp.ebi.ac.uk/pub/databases/spot/eQTL/susie/QTS000001/QTD000003/QTD000003.lbf_variable.txt.gz

# qtl file format example:
# molecular_trait_id	gene_id	cs_id	variant	rsid	cs_size	pip	pvalue	beta	se	z	cs_min_r2	region
# ENSG00000230489	ENSG00000230489	ENSG00000230489_L1	chr1_108004887_G_T	rs1936009	53	0.0197781278649429	7.46541e-09	0.767387	0.116543	7.19210214446939	0.945192225726688	chr1:106964443-108964443
# ENSG00000230489	ENSG00000230489	ENSG00000230489_L1	chr1_108006349_TAAG_T	rs149029272	53	0.0197781278649429	7.46541e-09	0.767387	0.116543	7.19210214446939	0.945192225726688	chr1:106964443-108964443
# ENSG00000230489	ENSG00000230489	ENSG00000230489_L1	chr1_108006349_TAAG_T	rs752693742	53	0.0197781278649429	7.46541e-09	0.767387	0.116543	7.19210214446939	0.945192225726688	chr1:106964443-108964443
# ENSG00000230489	ENSG00000230489	ENSG00000230489_L1	chr1_108006349_TAAG_T	rs564865200	53	0.0197781278649429	7.46541e-09	0.767387	0.116543	7.19210214446939	0.945192225726688	chr1:106964443-108964443

# study metadata file is downloaded from https://github.com/eQTL-Catalogue/eQTL-Catalogue-resources/blob/master/data_tables/dataset_metadata.tsv
# study metadata file example:
# study_id	dataset_id	study_label	sample_group	tissue_id	tissue_label	condition_label	sample_size	quant_method	pmid	study_type
# QTS000001	QTD000001	Alasoo_2018	macrophage_naive	CL_0000235	macrophage	naive	84	ge	29379200	bulk
# QTS000001	QTD000002	Alasoo_2018	macrophage_naive	CL_0000235	macrophage	naive	84	exon	29379200	bulk
# QTS000001	QTD000003	Alasoo_2018	macrophage_naive	CL_0000235	macrophage	naive	84	tx	29379200	bulk
# QTS000001	QTD000004	Alasoo_2018	macrophage_naive	CL_0000235	macrophage	naive	84	txrev	29379200	bulk


class EQTLCatalog:
    METADATA_PATH = 'data_loading_support_files/eqtl_catalog/tabix_ftp_paths.tsv'
    ALLOWED_LABELS = ['qtl', 'study']

    def __init__(self, filepath=None, label='qtl', writer: Optional[Writer] = None, **kwargs):
        if label not in EQTLCatalog.ALLOWED_LABELS:
            raise ValueError('Invalid label. Allowed values: ' +
                             ','.join(EQTLCatalog.ALLOWED_LABELS))
        self.filepath = filepath
        self.label = label
        self.type = 'edge'
        self.writer = writer
        self.source = 'eQTL Catalogue'
        self.gene_validator = GeneValidator()

    def process_file(self):
        if self.label == 'qtl':
            self.process_qtl()
        elif self.label == 'study':
            self.process_study()

    def process_qtl(self):
        dataset_id = self.filepath.split('/')[-1].split('.')[0]
        found_dataset = False
        with open(self.METADATA_PATH, 'r') as f:
            metadata_reader = csv.reader(f, delimiter='\t')
            next(metadata_reader)
            for row in metadata_reader:
                if row[1] == dataset_id:
                    if row[8] == 'ge':
                        label = 'eQTL'
                        name = 'modulates expression of'
                        inverse_name = 'expression modulated by'
                        biological_process = 'ontology_terms/GO_0010468'
                    else:
                        label = 'splice_QTL'
                        name = 'modulates splicing of'
                        inverse_name = 'splicing modulated by'
                        biological_process = 'ontology_terms/GO_0043484'
                    biological_context = f'ontology_terms/{row[4]}'
                    studay = f'studies/{row[0]}'
                    simple_sample_summaries = [row[5]]
                    # example: ftp://ftp.ebi.ac.uk/pub/databases/spot/eQTL/susie/QTS000001/QTD000001/QTD000001.credible_sets.tsv.gz
                    source_url = row[10]
                    found_dataset = True
                    break
        if not found_dataset:
            raise ValueError(f'No metadata found for dataset {dataset_id}')

        with gzip.open(self.filepath, 'rt') as f:
            self.writer.open()
            qtl_reader = csv.reader(f, delimiter='\t')
            next(qtl_reader)
            for row in qtl_reader:
                variant_vcf_format = row[3]
                chr, pos, ref_seq, alt_seq = variant_vcf_format.split('_')
                variant_id = build_variant_id(
                    chr, pos, ref_seq, alt_seq, 'GRCh38'
                )
                gene_id = row[1]
                is_valid_gene_id = self.gene_validator.validate(
                    gene_id)
                if not is_valid_gene_id:
                    continue
                # this edge id is too long, needs to be hashed
                variants_genes_id = hashlib.sha256(
                    (variant_id + '_' + gene_id + '_' + dataset_id).encode()).hexdigest()
                _props = {
                    '_key': variants_genes_id,
                    '_from': f'variants/{variant_id}',
                    '_to': f'genes/{gene_id}',
                    'biological_context': biological_context,
                    'biological_process': biological_process,
                    'study': studay,
                    'simple_sample_summaries': simple_sample_summaries,
                    'label': label,
                    'source': self.source,
                    'source_url': source_url,
                    'name': name,
                    'inverse_name': inverse_name,
                    'molecular_trait_id': row[0],
                    'gene_id': gene_id,
                    'credible_set_id': row[2],
                    'variant_chromosome_position_ref_alt': variant_vcf_format,
                    'rsid': row[4],
                    'credible_set_size': int(row[5]),
                    'posterior_inclusion_probability': float(row[6]),
                    'pvalue': to_float(row[7]),
                    'beta': to_float(row[8]),
                    'standard_error': float(row[9]),
                    'z_score': float(row[10]),
                    'credible_set_min_r2': float(row[11]),
                    'region': row[12]
                }
                self.writer.write(json.dumps(_props) + '\n')

            self.writer.close()
            self.gene_validator.log()

    def process_study(self):
        study_list = []
        with open(self.METADATA_PATH, 'r') as f:
            metadata_reader = csv.reader(f, delimiter='\t')
            next(metadata_reader)
            for row in metadata_reader:
                if row[8] in ['ge', 'leafcutter'] and row[6] == 'naive':
                    if row[0] not in study_list:
                        study_list.append(row[0])
        visited_study_ids = []
        with open(self.filepath, 'r') as f:
            self.writer.open()
            study_reader = csv.reader(f, delimiter='\t')
            next(study_reader)
            for row in study_reader:
                _id = row[0]
                if _id in study_list and (_id not in visited_study_ids):
                    visited_study_ids.append(_id)
                    _props = {
                        '_key': _id,
                        'name': row[2],
                        'pmid': row[9],
                        'study_type': row[10],
                        'source': self.source

                    }
                    self.writer.write(json.dumps(_props) + '\n')
            self.writer.close()
