import json
from typing import Optional

from adapters.archive_utils import get_file_accession, get_files_from_folder
from adapters.base import BaseAdapter
from adapters.helpers import get_gene_map_from_arangodb
from adapters.writer import Writer
import requests

# https://coxpresdb.jp/download/Hsa-r.c6-0/coex/Hsa-r.v22-05.G16651-S235187.combat_pca.subagging.z.d.zip
# There is 16651 files. The file name is entrez gene id. The total genes annotated are 16651, one gene per file, each file contain logit score of other 16650 genes.
# There are two fields in each row: entrez gene id and logit score


class Coxpresdb(BaseAdapter):
    ALLOWED_LABELS = ['coxpresdb']
    IGVF_API = 'https://api.data.igvf.org/reference-files/'

    def __init__(
        self,
        filepath,
        label='coxpresdb',
        writer: Optional[Writer] = None,
        validate=False,
        **kwargs
    ):
        self.source = 'COXPRESdb'
        self.collection_label = 'co-expression'
        self.source_url = 'https://coxpresdb.jp/'
        super().__init__(filepath, label, writer, validate)
        self.file_accession = get_file_accession(filepath)

    def _get_schema_type(self):
        """Return schema type."""
        return 'edges'

    def _get_collection_name(self):
        """Get collection name."""
        return 'genes_genes'

    def parse(self):
        file_metadata = requests.get(
            self.IGVF_API + self.file_accession).json()
        self.collection_class = file_metadata['catalog_class']
        self.method = file_metadata['catalog_method']

        gene_map = get_gene_map_from_arangodb('entrez')
        entrez_ensembl_dict = {
            entrez.removeprefix('ENTREZ:'): ensembl_ids
            for entrez, ensembl_ids in gene_map.items()
            if entrez.startswith('ENTREZ:') and ensembl_ids
        }
        for input_filepath in get_files_from_folder(self.filepath):
            filename = input_filepath.name
            entrez_id = filename
            ensembl_ids = entrez_ensembl_dict.get(entrez_id)
            if not ensembl_ids:
                continue
            with open(input_filepath, 'r') as input:
                for line in input:
                    (co_entrez_id, score) = line.strip().split()
                    co_ensembl_ids = entrez_ensembl_dict.get(co_entrez_id)
                    if not co_ensembl_ids:
                        continue
                    # only keep those with logit_scores (i.e. z-scores) absolute value >= 3
                    if abs(float(score)) < 3:
                        continue
                    # Co-expression is symmetric; emit one edge per gene pair in
                    # canonical order to avoid A->B and B->A duplicates.
                    if int(entrez_id) > int(co_entrez_id):
                        continue
                    for ensembl_id in ensembl_ids:
                        for co_ensembl_id in co_ensembl_ids:
                            if len(ensembl_ids) == 1 and len(co_ensembl_ids) == 1:
                                _id = entrez_id + '_' + co_entrez_id + '_' + self.label
                            else:
                                _id = ensembl_id + '_' + co_ensembl_id + '_' + self.label
                            _source = 'genes/' + ensembl_id
                            _target = 'genes/' + co_ensembl_id
                            _props = {
                                '_key': _id,
                                '_from': _source,
                                '_to': _target,
                                # confirmed from their paper that logit_score is essentailly a z_score
                                'z_score': float(score),
                                'source': self.source,
                                'source_url': self.source_url,
                                'name': 'coexpressed with',
                                'inverse_name': 'coexpressed with',
                                'associated_process': 'ontology_terms/GO_0010467',
                                'class': self.collection_class,
                                'method': self.method,
                                'label': self.collection_label,
                            }
                            if self.validate:
                                self.validate_doc(_props)
                            self.writer.write(json.dumps(_props))
                            self.writer.write('\n')
