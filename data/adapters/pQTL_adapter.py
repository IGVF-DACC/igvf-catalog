import csv
from adapters import Adapter
from adapters.helpers import build_variant_id

# Example rows from pQTL file (Supplementary Table 9)
# Variant ID (CHROM:GENPOS (hg37):A0:A1:imp:v1)	CHROM	GENPOS (hg38)	Region ID	Region Start	Region End	MHC	UKBPPP ProteinID	Assay Target	Target UniProt	rsID	A1FREQ (discovery)	BETA (discovery, wrt. A1)	SE (discovery)	log10(p) (discovery)	A1FREQ (replication)	BETA (replication)	SE (replication)	log10(p) (replication)	cis/trans	cis gene	Bioinfomatic annotated gene	Ensembl gene ID	Annotated gene consequence	Biotype	Distance to gene	CADD_phred	SIFT	PolyPhen	PHAST Phylop_score	FitCons_score	IMPACT
# 2:27730940:T:C:imp:v1	2	27508073	975	26263266	29121418	0	A1BG:P04217:OID30771:v1	A1BG	P04217	rs1260326	0.6084	-0.137	0.007	79.2	0.6306	-0.105	0.010	23.9	trans	-	GCKR	ENSG00000084734	missense_variant,splice_region_variant	protein_coding	0		T	Benign	408	0.553676	MODERATE


class pQTL(Adapter):

    SOURCE = 'UKB'
    SOURCE_URL = 'https://metabolomips.org/ukbbpgwas/'

    def __init__(self, filepath, label):

        self.filepath = filepath
        self.label = label

        super(pQTL, self).__init__()

    def process_file(self):
        with open(self.filepath, 'r') as pqtl_file:
            pqtl_csv = csv.reader(pqtl_file)
            next(pqtl_csv)
            for row in pqtl_csv:
                chr = row[1]
                pos = row[2]  # 1-based coordinates
                ref, alt = row[0].split(':')[2:4]

                variant_id = build_variant_id(chr, pos, ref, alt)
                # a few rows have multiple proteins: e.g. P0DUB6,P0DTE7,P0DTE8
                protein_ids = row[9].split(',')
                for protein_id in protein_ids:
                    _id = variant_id + '_' + protein_id + '_' + pQTL.SOURCE
                    _source = 'variants/' + variant_id
                    _target = 'proteins/' + protein_id
                    _props = {
                        'rsid': row[10] if row[10] != '-' else None,
                        'type': 'pQTL',
                        'log10pvalue': float(row[14]),
                        'beta': float(row[12]),  # i.e. effect size
                        'se': float(row[13]),
                        'class': row[19],  # cis/trans
                        'gene': 'genes/' + row[22] if row[22] and row[22] != '-' else None,
                        'gene_consequence': row[23] if row[23] else None,
                        'source': pQTL.SOURCE,
                        'source_url': pQTL.SOURCE_URL
                    }

                    yield(_id, _source, _target, self.label, _props)
