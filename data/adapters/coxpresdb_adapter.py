
from adapters import Adapter
import pickle
import os
import json
from db.arango_db import ArangoDB

# https://coxpresdb.jp/download/Hsa-r.c6-0/coex/Hsa-r.v22-05.G16651-S235187.combat_pca.subagging.z.d.zip
# There is 16651 files. The file name is entrez gene id. The total genes annotated are 16651, one gene per file, each file contain logit score of other 16650 genes.
# There are two fields in each row: entrez gene id and logit score


class Coxpresdb(Adapter):
    OUTPUT_PATH = './parsed-data'

    def __init__(self, file_path, dry_run=True):

        self.file_path = file_path
        self.dataset = 'coxpresdb'
        self.label = 'coxpresdb'
        self.source = 'CoXPresdb'
        self.source_url = 'https://coxpresdb.jp/'
        self.type = 'edge'
        self.dry_run = dry_run
        self.output_filepath = '{}/{}.json'.format(
            self.OUTPUT_PATH,
            self.dataset
        )

        super(Coxpresdb, self).__init__()

    def process_file(self):
        parsed_data_file = open(self.output_filepath, 'w')
        # entrez_to_ensembl.pkl is generated using those two files:
        # gencode file: https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_43/gencode.v43.chr_patch_hapl_scaff.annotation.gtf.gz
        # Homo_sapiens.gene_info.gz file: https://ftp.ncbi.nih.gov/gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz
        # every gene has ensembl id in gencode file, every gene has hgnc id if available.
        # every gene has entrez gene id in gene_info file, every gene has ensembl id or hgcn id if available
        with open('./data_loading_support_files/entrez_to_ensembl.pkl', 'rb') as f:
            entrez_ensembl_dict = pickle.load(f)
        entrez_id = self.file_path.split('/')[-1]
        ensembl_id = entrez_ensembl_dict.get(entrez_id)
        if ensembl_id:
            with open(self.file_path, 'r') as input:
                for line in input:
                    (co_entrez_id, score) = line.strip().split()
                    co_ensembl_id = entrez_ensembl_dict.get(co_entrez_id)
                    if co_ensembl_id:
                        # only keep those with logit_scores (i.e. z-scores) absolute value >= 3
                        if abs(float(score)) >= 3:
                            _id = entrez_id + '_' + co_entrez_id + '_' + self.label
                            _source = 'genes/' + ensembl_id
                            _target = 'genes/' + co_ensembl_id
                            _props = {
                                '_key': _id,
                                '_from': _source,
                                '_to': _target,
                                'z_score': score,  # confirmed from their paper that logit_score is essentailly a z_score
                                'source': self.source,
                                'source_url': self.source_url
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
