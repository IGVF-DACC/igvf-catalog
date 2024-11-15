import os
import pickle
import json
from typing import Optional

from adapters.writer import Writer

# https://coxpresdb.jp/download/Hsa-r.c6-0/coex/Hsa-r.v22-05.G16651-S235187.combat_pca.subagging.z.d.zip
# There is 16651 files. The file name is entrez gene id. The total genes annotated are 16651, one gene per file, each file contain logit score of other 16650 genes.
# There are two fields in each row: entrez gene id and logit score


class Coxpresdb:

    def __init__(self, filepath, dry_run=True, writer: Optional[Writer] = None, **kwargs):

        self.filepath = filepath
        self.dataset = 'coxpresdb'
        self.label = 'coxpresdb'
        self.source = 'CoXPresdb'
        self.source_url = 'https://coxpresdb.jp/'
        self.type = 'edge'
        self.dry_run = dry_run
        self.writer = writer

    def process_file(self):
        self.writer.open()
        # entrez_to_ensembl.pkl is generated using those two files:
        # gencode file: https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_43/gencode.v43.chr_patch_hapl_scaff.annotation.gtf.gz
        # Homo_sapiens.gene_info.gz file: https://ftp.ncbi.nih.gov/gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz
        # every gene has ensembl id in gencode file, every gene has hgnc id if available.
        # every gene has entrez gene id in gene_info file, every gene has ensembl id or hgcn id if available
        with open('./data_loading_support_files/entrez_to_ensembl.pkl', 'rb') as f:
            entrez_ensembl_dict = pickle.load(f)

        for filename in os.listdir(self.filepath):
            entrez_id = filename.split('/')[-1]
            ensembl_id = entrez_ensembl_dict.get(entrez_id)
            if ensembl_id:
                with open(self.filepath + '/' + filename, 'r') as input:
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
                                    'source_url': self.source_url,
                                    'name': 'coexpressed with',
                                    'inverse_name': 'coexpressed with',
                                    'associated process': 'ontology_terms/GO_0010467'
                                }
                                self.writer.write(json.dumps(_props))
                                self.writer.write('\n')
        self.writer.close()
