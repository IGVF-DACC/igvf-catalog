import csv
import gzip
import hashlib
import pickle
from math import log10

from adapters import Adapter
from adapters.helpers import build_variant_id

# sorted.all.AFR.Meta.sQTL.genPC.nominal.maf05.mvmeta.fe.txt.gz
# chr	pos	ref	alt	snp	feature	beta	se	zstat	p	95pct_ci_lower	95pct_ci_upper	qstat	df	p_het
# chr1	88338	G	A	1_88338_G_A	1:187577:187755:clu_2352	0.0723108199416329	0.0685894841949755	1.05425519363987	0.291766096608984	-0.0621220987986983	0.206743738681964	1.23511015771854	5	0.941465002419174


class AFGRSQtl(Adapter):
    ALLOWED_LABELS = ['AFGR_sqtl', 'AFGR_sqtl_term']
    SOURCE = 'AFGR'
    SOURCE_URL = 'https://github.com/smontgomlab/AFGR'
    INTRON_GENE_MAPPING_PATH = './data_loading_support_files/AFGR/AFGR_sQTL_intron_genes.pkl'
    BIOLOGICAL_CONTEXT = 'lymphoblastoid cell line'
    ONTOLOGY_TERM = 'EFO_0005292'  # lymphoblastoid cell line
    MAX_LOG10_PVALUE = 400  # set the same value as gtex qtl

    def __init__(self, filepath, label='AFGR_sqtl'):
        if label not in AFGRSQtl.ALLOWED_LABELS:
            raise ValueError('Ivalid label. Allowed values: ' +
                             ','.join(AFGRSQtl.ALLOWED_LABELS))

        self.filepath = filepath
        self.label = label

        super(AFGRSQtl, self).__init__()

    def process_file(self):
        self.load_intron_gene_mapping()

        with gzip.open(self.filepath, 'rt') as qtl_file:
            qtl_csv = csv.reader(qtl_file, delimiter='\t')
            next(qtl_csv)

            for row in qtl_csv:
                chr, pos, ref, alt = row[4].split('_')

                variant_id = build_variant_id(chr, pos, ref, alt, 'GRCh38')

                intron_id = row[5]
                gene_ids = self.intron_gene_mapping.get(intron_id)
                if gene_ids is None:
                    print('no gene mapping for ' + intron_id)
                    continue

                pvalue = float(row[9])
                if pvalue == 0:
                    log_pvalue = AFGRSQtl.MAX_LOG10_PVALUE
                else:
                    log_pvalue = -1 * log10(pvalue)

                for gene_id in gene_ids:
                    variants_genes_id = hashlib.sha256(
                        (variant_id + '_' + intron_id + '_' + gene_id).encode()).hexdigest()

                    if self.label == 'AFGR_sqtl':
                        _id = variants_genes_id
                        _source = 'variants/' + variant_id
                        _target = 'genes/' + gene_id

                        _props = {
                            'biological_context': AFGRSQtl.BIOLOGICAL_CONTEXT,
                            'chr': 'chr' + chr,
                            'log10pvalue': log_pvalue,
                            'p_value': pvalue,
                            'effect_size': float(row[6]),
                            'label': 'splice_QTL',
                            'intron_chr': 'chr' + intron_id.split(':')[0],
                            'intron_start': intron_id.split(':')[1],
                            'intron_end': intron_id.split(':')[2],
                            'source': AFGRSQtl.SOURCE,
                            'source_url': AFGRSQtl.SOURCE_URL
                        }
                        yield(_id, _source, _target, self.label, _props)

                    elif self.label == 'AFGR_sqtl_term':
                        _id = hashlib.sha256(
                            (variants_genes_id + '_' + AFGRSQtl.ONTOLOGY_TERM).encode()).hexdigest()
                    _source = 'variants_genes/' + variants_genes_id
                    _target = 'ontology_terms/' + AFGRSQtl.ONTOLOGY_TERM
                    _props = {
                        'biological_context': AFGRSQtl.BIOLOGICAL_CONTEXT,
                        'source': AFGRSQtl.SOURCE,
                        'source_url': AFGRSQtl.SOURCE_URL
                    }

                    yield(_id, _source, _target, self.label, _props)

    def load_intron_gene_mapping(self):
        # key: intron_id (e.g. 1:187577:187755:clu_2352); value: gene ensembl id
        self.intron_gene_mapping = {}
        with open(AFGRSQtl.INTRON_GENE_MAPPING_PATH, 'rb') as mapfile:
            self.intron_gene_mapping = pickle.load(mapfile)
