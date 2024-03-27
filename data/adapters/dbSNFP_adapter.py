import hashlib
import os
import json
from db.arango_db import ArangoDB
from adapters import Adapter
from adapters.helpers import build_variant_id, build_coding_variant_id

# Sample file - file has 709 columns:
# #chr	pos(1-based)	ref	alt	aaref	aaalt	rs_dbSNP	hg19_chr	hg19_pos(1-based)	hg18_chr ... Interpro_domain	GTEx_V8_gene	GTEx_V8_tissue	Geuvadis_eQTL_target_gene
# Y	2786989	C	A	X	Y	.	Y	2655030	Y	2715030	205	SRY	ENSG00000184895	ENST00000383070	ENSP00000372547 ... . . . . . .
# Y	2786990	T	C	X	W	.	Y	2655031	Y	2715031	205	SRY	ENSG00000184895	ENST00000383070	ENSP00000372547	... . . . . . .


class DbSNFPAdapter(Adapter):
    LABEL = 'dbSNFP_protein_variants'

    SKIP_BIOCYPHER = True
    OUTPUT_PATH = './parsed-data'
    WRITE_THRESHOLD = 1000000

    def __init__(self, filepath=None, collection='coding_variants', dry_run=True):
        self.output_filepath = '{}/{}-{}-{}.json'.format(
            DbSNFPAdapter.OUTPUT_PATH,
            DbSNFPAdapter.LABEL,
            collection,
            filepath.split('/')[-1]
        )

        self.filepath = filepath
        self.label = DbSNFPAdapter.LABEL
        self.dataset = self.label
        self.dry_run = dry_run
        self.collection_name = collection

        super(DbSNFPAdapter, self).__init__()

    def process_file(self):
        parsed_data_file = open(self.output_filepath, 'w')

        record_count = 0

        for line in open(self.filepath, 'r'):
            if line.startswith('#chr'):
                continue

            data_line = line.strip().split('\t')

            variant_id = build_variant_id(
                data_line[0],
                data_line[1],  # 1-based
                data_line[2],
                data_line[3]
            )

            protein_id = data_line[16].split('-')[0]
            if ';' in protein_id:
                protein_id = protein_id.split(';')[0]

            # '.' is equivalent to None in this dataset
            def data(pos):
                return data_line[pos] if data_line[pos] != '.' else None

            def long_data(pos):
                try:
                    return float(data_line[pos])
                except:
                    return None

            gene_id = data(13)
            if gene_id and ';' in gene_id:
                gene_id = gene_id.split(';')[0]

            transcript_id = data(14)
            if transcript_id and ';' in transcript_id:
                transcript_id = transcript_id.split(';')[0]

            key = build_coding_variant_id(
                variant_id, protein_id, transcript_id, gene_id)

            if self.collection_name == 'variants_coding_variants':
                to_json = {
                    '_from': 'variants/' + variant_id,
                    '_to': 'coding_variants/' + key,
                    'source': 'dbSNFP 4.5a',
                    'source_url': 'http://database.liulab.science/dbNSFP',

                    'chr': data(0),
                    'pos:long': long_data(1),
                    'ref': data(2),  # 1-based
                    'alt': data(3),
                }
            elif self.collection_name == 'coding_variants_proteins':
                to_json = {
                    '_from': 'coding_variants/' + key,
                    '_to': 'proteins/' + protein_id,
                    'source': 'dbSNFP 4.5a',
                    'source_url': 'http://database.liulab.science/dbNSFP'
                }
            else:
                to_json = {
                    '_key': key,
                    'name': (data(12) or '') + '_' + (data(22) or ''),
                    'ref': data(4),
                    'alt': data(5),
                    'aapos:long': long_data(11),  # 1-based
                    'gene_name': data(12),
                    'protein_name': data(18),
                    'hgvsp': data(22),
                    'refcodon': data(29),
                    'codonpos:long': long_data(30),
                    'transcript_id': transcript_id,
                    'SIFT_score:long': long_data(37),
                    'SIFT4G_score:long': long_data(40),
                    'Polyphen2_HDIV_score:long': long_data(43),
                    'Polyphen2_HVAR_score:long': long_data(46),
                    'VEST4_score:long': long_data(67),
                    'Mcap_score:long': long_data(79),
                    'REVEL_score:long': long_data(82),
                    'MutPred_score:long': long_data(84),
                    'BayesDel_addAF_score:long': long_data(101),
                    'BayesDel_noAF_score:long': long_data(104),
                    'VARITY_R_score:long': long_data(113),
                    'VARITY_ER_score:long': long_data(115),
                    'VARITY_R_LOO_score:long': long_data(117),
                    'VARITY_ER_LOO_score:long': long_data(119),
                    'ESM1b_score:long': long_data(121),
                    'EVE_score:long': long_data(124),
                    'AlphaMissense_score:long': long_data(137),
                    'CADD_raw_score:long': long_data(146),
                    'source': 'dbSNFP 4.5a',
                    'source_url': 'http://database.liulab.science/dbNSFP'
                }

            json.dump(to_json, parsed_data_file)
            parsed_data_file.write('\n')
            record_count += 1

            if record_count > DbSNFPAdapter.WRITE_THRESHOLD:
                parsed_data_file.close()
                self.save_to_arango()

                os.remove(self.output_filepath)
                record_count = 0

                parsed_data_file = open(self.output_filepath, 'w')

        parsed_data_file.close()
        self.save_to_arango()

    def save_to_arango(self):
        collection_type = 'node' if self.collection_name == 'coding_variants' else 'edge'

        import_sts = ArangoDB().generate_json_import_statement(
            self.output_filepath, self.collection_name, type=collection_type)[0]

        if self.dry_run:
            print(import_sts)
        else:
            os.system(import_sts)