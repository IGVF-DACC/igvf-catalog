import hashlib
import os
import json
from db.arango_db import ArangoDB
from adapters import Adapter
from adapters.helpers import build_variant_id

# Sample file - file has 709 columns:
# #chr	pos(1-based)	ref	alt	aaref	aaalt	rs_dbSNP	hg19_chr	hg19_pos(1-based)	hg18_chr ... Interpro_domain	GTEx_V8_gene	GTEx_V8_tissue	Geuvadis_eQTL_target_gene
# Y	2786989	C	A	X	Y	.	Y	2655030	Y	2715030	205	SRY	ENSG00000184895	ENST00000383070	ENSP00000372547 ... . . . . . .
# Y	2786990	T	C	X	W	.	Y	2655031	Y	2715031	205	SRY	ENSG00000184895	ENST00000383070	ENSP00000372547	... . . . . . .

# Columns of interest:
# pos  name
# 0    chr
# 1    pos(1-based)
# 2    ref
# 3    alt
# 4    aaref: reference amino acid
# 5    aaalt: alternative amino acid
# 11   aapos: amino acid position as to the protein.
# 13   Ensembl_geneid: Ensembl gene id
# 14   Ensembl_transcriptid
# 15   Ensembl_proteinid
# 23   HGVSp_VEP: HGVS protein variant presentation from VEP
# 29   refcodon: reference codon
# 30   codonpos: position on the codon (1, 2 or 3)
# 37   SIFT_score: SIFT score (SIFTori). Scores range from 0 to 1. The smaller the score the
# 38   SIFT_converted_rankscore: SIFTori scores were first converted to SIFTnew=1-SIFTori,
# 39   SIFT_pred: If SIFTori is smaller than 0.05 (rankscore>0.39575) the corresponding nsSNV is
# 40   SIFT4G_score: SIFT 4G score (SIFT4G). Scores range from 0 to 1. The smaller the score the
# 41   SIFT4G_converted_rankscore: SIFT4G scores were first converted to SIFT4Gnew=1-SIFT4G,
# 42   SIFT4G_pred: If SIFT4G is < 0.05 the corresponding nsSNV is
# 695  clinvar_id: clinvar variation ID
# 696  clinvar_clnsig: clinical significance by clinvar
# 700  clinvar_var_source: source of the variant


class DbSNFPAdapter(Adapter):
    LABEL = 'dbSNFP_protein_variants'

    SKIP_BIOCYPHER = True
    OUTPUT_PATH = './parsed-data'
    WRITE_THRESHOLD = 1000000

    def __init__(self, filepath=None, dry_run=True):
        self.filepath = filepath
        self.label = DbSNFPAdapter.LABEL
        self.dataset = self.label
        self.dry_run = dry_run

        self.output_filepath = '{}/{}-{}.json'.format(
            DbSNFPAdapter.OUTPUT_PATH,
            self.dataset,
            filepath.split('/')[-1],
        )

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

            key = variant_id + '_' + protein_id

            # '.' is equivalent to None in this dataset
            def data(pos):
                return data_line[pos] if data_line[pos] != '.' else None

            def long_data(pos):
                try:
                    return float(data_line[pos])
                except:
                    return None

            to_json = {
                '_key': hashlib.sha256((key).encode()).hexdigest(),
                '_from': 'proteins/' + protein_id,
                '_to': 'variants/' + variant_id,
                'aaref': data(4),
                'aaalt': data(5),
                'aapos:long': long_data(11),
                'gene': 'genes/' + data(13) if data(13) else None,
                'transcript': 'transcripts/' + data(14) if data(14) else None,
                'HGVSp_VEP': data(23),
                'refcodon': data(29),
                'codonpos:long': long_data(30),
                'SIFT_score:long': long_data(37),
                'SIFT_converted_rankscore:long': long_data(38),
                'SIFT_pred': data(39),
                'SIFT4G_score:long': long_data(40),
                'SIFT4G_converted_rankscore:long': long_data(41),
                'SIFT4G_pred': data(42),
                'clinvar_id': data(695),
                'clinvar_clnsig': data(696),
                'clinvar_var_source': data(700),
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
        import_sts = ArangoDB().generate_json_import_statement(
            self.output_filepath, self.collection)[0]

        if self.dry_run:
            print(import_sts)
        else:
            os.system(import_sts)
