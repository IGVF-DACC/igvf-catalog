import csv
import gzip
import hashlib


from adapters import Adapter
from adapters.helpers import build_variant_id


# Example row from sorted.dist.hwe.af.AFR_META.eQTL.nominal.hg38a.txt.gz
# chr	snp_pos	snp_pos2	ref	alt	effect_af_eqtl	variant	feature	log10p	pvalue	beta	se	qstat	df	p_het	p_hwe	dist_start	dist_end	geneSymbol	geneType
# 1	16103	16103	T	G	0.0336427	1_16103_T_G	ENSG00000187583.10	0.1944867	0.6390183	0.242489	0.516955	NA	1.0	NA	1.000000	-950394	-959762	PLEKHN1	protein_coding

class AFGREQtl(Adapter):
    SOURCE = 'AFGR'
    SOURCE_URL = 'https://github.com/smontgomlab/AFGR'
    ONTOLOGY_TERM = 'EFO_0005292'  # lymphoblastoid cell line

    def __init__(self, filepath, label='AFGR_eqtl'):
        self.filepath = filepath
        self.label = label

        super(AFGREQtl, self).__init__()

    def process_file(self):
        with gzip.open(self.filepath, 'rt') as qtl_file:
            qtl_csv = csv.reader(qtl_file, delimiter='\t')
            next(qtl_csv)

            for row in qtl_csv:
                chr, pos, ref, alt = row[6].split('_')

                variant_id = build_variant_id(chr, pos, ref, alt, 'GRCh38')

                gene_id = row[7].split('.')[0]

                variants_genes_id = hashlib.sha256(
                    (variant_id + '_' + gene_id + '_' + AFGREQtl.SOURCE).encode()).hexdigest()

                _id = variants_genes_id
                _source = 'variants/' + variant_id
                _target = 'genes/' + gene_id

                _props = {
                    'biological_context': 'ontology_terms/' + AFGREQtl.ONTOLOGY_TERM,
                    'chr': 'chr' + chr,
                    # The three numeric values are not loaded as long data type somehow, though in schema it's labeled as int
                    # Manually changed data type from double to long in header file before importing into Arangodb
                    'log10pvalue': float(row[8]),  # MAX=616
                    'p_value': float(row[9]),
                    'effect_size': float(row[10]),
                    'label': 'eQTL',
                    'source': AFGREQtl.SOURCE,
                    'source_url': AFGREQtl.SOURCE_URL
                }

                yield(_id, _source, _target, self.label, _props)
