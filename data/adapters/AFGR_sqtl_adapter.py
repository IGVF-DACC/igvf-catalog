import csv
import gzip
import hashlib
import json
import pickle
from math import log10
from typing import Optional
import os
import requests
from adapters.base import BaseAdapter
from adapters.helpers import build_variant_id
from adapters.writer import Writer
from adapters.gene_validator import GeneValidator


# sorted.all.AFR.Meta.sQTL.genPC.nominal.maf05.mvmeta.fe.txt.gz
# chr	pos	ref	alt	snp	feature	beta	se	zstat	p	95pct_ci_lower	95pct_ci_upper	qstat	df	p_het
# chr1	88338	G	A	1_88338_G_A	1:187577:187755:clu_2352	0.0723108199416329	0.0685894841949755	1.05425519363987	0.291766096608984	-0.0621220987986983	0.206743738681964	1.23511015771854	5	0.941465002419174


class AFGRSQtl(BaseAdapter):
    ALLOWED_LABELS = ['AFGR_sqtl']
    SOURCE = 'AFGR'
    SOURCE_URL = 'https://github.com/smontgomlab/AFGR'
    INTRON_GENE_MAPPING_PATH = './data_loading_support_files/AFGR/AFGR_sQTL_intron_genes.pkl'
    BIOLOGICAL_CONTEXT = 'lymphoblastoid cell line'
    ONTOLOGY_TERM = 'EFO_0005292'  # lymphoblastoid cell line
    MAX_LOG10_PVALUE = 400  # set the same value as gtex qtl
    IGVF_API = 'https://api.data.igvf.org/reference-files/'

    def __init__(self, filepath, label='AFGR_sqtl', writer: Optional[Writer] = None, validate=False, **kwargs):
        # Initialize base adapter first
        super().__init__(filepath, label, writer, validate)

        # Adapter-specific initialization
        self.gene_validator = GeneValidator()
        self.file_accession = os.path.basename(filepath).split('.')[0]

    def _get_schema_type(self):
        """This adapter creates edges."""
        return 'edges'

    def _get_collection_name(self):
        return 'variants_genes'

    def process_file(self):
        file_metadata = requests.get(
            self.IGVF_API + self.file_accession).json()
        self.collection_class = file_metadata['catalog_class']
        self.method = file_metadata['catalog_method']
        self.writer.open()
        self.load_intron_gene_mapping()

        with gzip.open(self.filepath, 'rt') as qtl_file:
            qtl_csv = csv.reader(qtl_file, delimiter='\t')
            next(qtl_csv)

            for row in qtl_csv:
                chr, pos, ref, alt = row[4].split('_')

                # skipping deletions for now (can't be mapped to a spdi using current ga4gh lib)
                if alt == '*':
                    continue

                variant_id = build_variant_id(chr, pos, ref, alt, 'GRCh38')

                intron_id = row[5]
                gene_ids = self.intron_gene_mapping.get(intron_id)
                if gene_ids is None:
                    self.logger.warning(f'no gene mapping for {intron_id}')
                    continue

                pvalue = float(row[9])
                if pvalue == 0:
                    log_pvalue = AFGRSQtl.MAX_LOG10_PVALUE
                else:
                    log_pvalue = -1 * log10(pvalue)

                for gene_id in gene_ids:
                    is_valid_gene_id = self.gene_validator.validate(gene_id)
                    if not is_valid_gene_id:
                        continue
                    variants_genes_id = hashlib.sha256(
                        (variant_id + '_' + intron_id + '_' + gene_id).encode()).hexdigest()

                    _id = variants_genes_id
                    _source = 'variants/' + variant_id
                    _target = 'genes/' + gene_id

                    _props = {
                        '_key': _id,
                        '_from': _source,
                        '_to': _target,
                        'biological_context': AFGRSQtl.BIOLOGICAL_CONTEXT,
                        'chr': 'chr' + chr,
                        'log10pvalue': log_pvalue,
                        'p_value': pvalue,
                        'effect_size': float(row[6]),
                        'class': self.collection_class,
                        'method': self.method,
                        'label': 'spliceQTL',
                        'intron_chr': 'chr' + intron_id.split(':')[0],
                        'intron_start': intron_id.split(':')[1],
                        'intron_end': intron_id.split(':')[2],
                        'source': AFGRSQtl.SOURCE,
                        'source_url': AFGRSQtl.SOURCE_URL,
                        'name': 'modulates splicing of',
                        'inverse_name': 'splicing modulated by',
                        'biological_process': 'ontology_terms/GO_0043484',
                        'biosample_term': 'ontology_terms/' + AFGRSQtl.ONTOLOGY_TERM
                    }
                    if self.validate:
                        self.validate_doc(_props)

                    self.writer.write(json.dumps(_props))
                    self.writer.write('\n')
            self.writer.close()
            self.gene_validator.log()

    def load_intron_gene_mapping(self):
        # key: intron_id (e.g. 1:187577:187755:clu_2352); value: gene ensembl id
        self.intron_gene_mapping = {}
        with open(AFGRSQtl.INTRON_GENE_MAPPING_PATH, 'rb') as mapfile:
            self.intron_gene_mapping = pickle.load(mapfile)
