
from adapters import Adapter
import pickle
import os

# https://coxpresdb.jp/download/Hsa-r.c6-0/coex/Hsa-r.v22-05.G16651-S235187.combat_pca.subagging.z.d.zip
# There is 16651 files. The file name is entrez gene id. The total genes annotated are 16651, one gene per file, each file contain logit score of other 16650 genes.
# There are two fields in each row: entrez gene id and logit score


class Coxpresdb(Adapter):

    def __init__(self, file_path):

        self.file_path = file_path
        self.dataset = 'coxpresdb'
        self.label = 'coxpresdb'
        self.source = 'CoXPresdb'
        self.source_url = 'https://coxpresdb.jp/'

        super(Coxpresdb, self).__init__()

    def process_file(self):
        with open('./samples/entrez_ensembl.pkl', 'rb') as f:
            entrez_ensembl_dict = pickle.load(f)
        entrez_id = self.file_path.split('/')[-1]
        ensembl_id = entrez_ensembl_dict.get(entrez_id)
        if ensembl_id:
            with open(self.file_path, 'r') as input:
                for line in input:
                    (co_entrez_id, score) = line.strip().split()
                    co_ensembl_id = entrez_ensembl_dict.get(co_entrez_id)
                    if co_ensembl_id:
                        _id = entrez_id + '_' + co_entrez_id + '_' + self.label
                        _source = 'genes/' + ensembl_id
                        _target = 'genes/' + co_ensembl_id
                        _props = {
                            'logit_score': score,
                            'source': self.source,
                            'source_url': self.source_url
                        }
                        yield(_id, _source, _target, self.label, _props)
