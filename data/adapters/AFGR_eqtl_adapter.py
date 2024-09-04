import csv
import gzip
import hashlib
import json
import os
from adapters import Adapter
from adapters.helpers import build_variant_id
from db.arango_db import ArangoDB


# Example row from sorted.dist.hwe.af.AFR_META.eQTL.nominal.hg38a.txt.gz
# chr	snp_pos	snp_pos2	ref	alt	effect_af_eqtl	variant	feature	log10p	pvalue	beta	se	qstat	df	p_het	p_hwe	dist_start	dist_end	geneSymbol	geneType
# 1	16103	16103	T	G	0.0336427	1_16103_T_G	ENSG00000187583.10	0.1944867	0.6390183	0.242489	0.516955	NA	1.0	NA	1.000000	-950394	-959762	PLEKHN1	protein_coding

class AFGREQtl(Adapter):
    ALLOWED_LABELS = ['AFGR_eqtl', 'AFGR_eqtl_term']
    SOURCE = 'AFGR'
    SOURCE_URL = 'https://github.com/smontgomlab/AFGR'
    BIOLOGICAL_CONTEXT = 'lymphoblastoid cell line'
    ONTOLOGY_TERM = 'EFO_0005292'  # lymphoblastoid cell line
    OUTPUT_PATH = './parsed-data'

    def __init__(self, filepath, label='AFGR_eqtl', dry_run=True):
        if label not in AFGREQtl.ALLOWED_LABELS:
            raise ValueError('Ivalid label. Allowed values: ' +
                             ','.join(AFGREQtl.ALLOWED_LABELS))

        self.filepath = filepath
        self.label = label
        self.dataset = label
        self.dry_run = dry_run
        self.type = 'edge'

        self.output_filepath = '{}/{}.json'.format(
            self.OUTPUT_PATH,
            self.dataset
        )

        super(AFGREQtl, self).__init__()

    def process_file(self):
        parsed_data_file = open(self.output_filepath, 'w')
        with gzip.open(self.filepath, 'rt') as qtl_file:
            qtl_csv = csv.reader(qtl_file, delimiter='\t')
            next(qtl_csv)

            for row in qtl_csv:
                chr, pos, ref, alt = row[6].split('_')

                variant_id = build_variant_id(chr, pos, ref, alt, 'GRCh38')

                gene_id = row[7].split('.')[0]

                variants_genes_id = hashlib.sha256(
                    (variant_id + '_' + gene_id + '_' + AFGREQtl.SOURCE).encode()).hexdigest()

                if self.label == 'AFGR_eqtl':
                    _id = variants_genes_id
                    _source = 'variants/' + variant_id
                    _target = 'genes/' + gene_id

                    _props = {
                        '_key': _id,
                        '_from': _source,
                        '_to': _target,
                        'biological_context': AFGREQtl.BIOLOGICAL_CONTEXT,
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

                elif self.label == 'AFGR_eqtl_term':
                    _id = hashlib.sha256(
                        (variants_genes_id + '_' + AFGREQtl.ONTOLOGY_TERM).encode()).hexdigest()
                    _source = 'variants_genes/' + variants_genes_id
                    _target = 'ontology_terms/' + AFGREQtl.ONTOLOGY_TERM
                    _props = {
                        '_key': _id,
                        '_from': _source,
                        '_to': _target,
                        'biological_context': AFGREQtl.BIOLOGICAL_CONTEXT,
                        'source': AFGREQtl.SOURCE,
                        'source_url': AFGREQtl.SOURCE_URL
                    }
                json.dump(_props, parsed_data_file)
                parsed_data_file.write('\n')
        parsed_data_file.close()
        self.save_to_arango()

    def save_to_arango(self):
        if self.dry_run:
            print(self.arangodb()[0])
        else:
            os.system(self.arangodb()[0])

    def arangodb(self):
        return ArangoDB().generate_json_import_statement(self.output_filepath, self.collection, type=self.type)
