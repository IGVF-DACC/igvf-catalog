import csv
import json
import pickle
from math import log10
from typing import Optional

from adapters.base import BaseAdapter
from adapters.writer import Writer


# Data source: https://www.synapse.org/Synapse:syn65484409
# example rows:
# chr	pos	spdi	ref	alt	TF	ensembl_id	experiment	hg19_oligo_coord	oligo_auc	oligo_pval	ref_auc	alt_auc	pbs	pval	fdr	rsid
# chr10	112626980	NC_000010.11:112626979:C:T	C	T	ALX1	ENSG00000180318	FL.6.0.G12	chr10:114386719-114386759	3.02599	0.00133	1.44024	-1.28154	2.72179	0.31704	1.0	rs76124550
# chr10	112627010	NC_000010.11:112627009:T:C	T	C	ALX1	ENSG00000180318	FL.6.0.G12	chr10:114386749-114386789	3.6725	0.00049	-1.62935	0.59975	-2.2291	0.4039	1.0	rs115699571


class ASB_GVATDB(BaseAdapter):
    TF_ID_MAPPING_PATH = './data_loading_support_files/GVATdb_TF_mapping.pkl'
    SOURCE = 'GVATdb allele-specific TF binding calls'
    SOURCE_URL = 'https://renlab.sdsc.edu/GVATdb/'
    ENSEMBL_MAPPING = './data_loading_support_files/ensembl_to_uniprot/uniprot_to_ENSP_human.pkl'
    # smallest pvalue in this file is 0, the second smallest pvalue is 1e-05, so we will replace 0 with 1e-05 to calculate log10pvalue
    # so the max log10pvalue is 5.
    MAX_LOG10_PVALUE = 5
    ALLOWED_LABELS = ['variant_protein']

    def __init__(self, filepath, label='variant_protein', writer: Optional[Writer] = None, validate=False, **kwargs):
        super().__init__(filepath, label, writer, validate)

    def _get_schema_type(self):
        """Return schema type."""
        return 'edges'

    def _get_collection_name(self):
        """Get collection name."""
        return 'variants_proteins'

    def process_file(self):
        self.writer.open()
        self.load_tf_uniprot_id_mapping()
        self.ensembls = pickle.load(open(ASB_GVATDB.ENSEMBL_MAPPING, 'rb'))
        ensembl_unmatched = 0

        with open(self.filepath, 'r') as input_file:
            rows = csv.reader(input_file, delimiter='\t')
            next(rows)
            for row in rows:
                pvalue = float(row[-3])
                if pvalue == 0:
                    log10pvalue = ASB_GVATDB.MAX_LOG10_PVALUE
                else:
                    log10pvalue = -1 * log10(pvalue)
                variant_id = row[2]

                tf_uniprot_id = self.tf_uniprot_id_mapping.get(row[5])
                if tf_uniprot_id is None or len(tf_uniprot_id) == 0:
                    continue

                ensembl_ids = self.ensembls.get(tf_uniprot_id[0]) or self.ensembls.get(
                    tf_uniprot_id[0].split('-')[0])
                if ensembl_ids is None:
                    ensembl_unmatched += 1
                    continue
                experiment = row[7]

                for ensembl_id in ensembl_ids:
                    # create separate edges for same variant-tf pairs in different experiments
                    _id = variant_id + '_' + \
                        ensembl_id + '_' + experiment.replace('.', '_')
                    _source = 'variants/' + variant_id
                    _target = 'proteins/' + ensembl_id

                    _props = {
                        '_key': _id,
                        '_from': _source,
                        '_to': _target,
                        'p_value': pvalue,
                        'log10pvalue': log10pvalue,
                        'experiment': experiment,
                        'hg19_coordinate': row[8],
                        'oligo_auc': float(row[9]),
                        'oligo_pval': float(row[10]),
                        'ref_auc': float(row[11]),
                        'alt_auc': float(row[12]),
                        'pbs': float(row[13]),
                        'fdr': float(row[15]),
                        'source': ASB_GVATDB.SOURCE,
                        'source_url': ASB_GVATDB.SOURCE_URL,
                        'label': 'allele-specific binding',
                        'method': 'GVATdb',
                        'name': 'modulates binding of',
                        'inverse_name': 'binding modulated by',
                        'biological_process': 'ontology_terms/GO_0051101'
                    }

                    if self.validate:
                        self.validate_doc(_props)

                    self.writer.write(json.dumps(_props))
                    self.writer.write('\n')

        if ensembl_unmatched != 0:
            self.logger.warning(
                f'{ensembl_unmatched} unmatched uniprot -> ensembl ids')

        self.writer.close()

    def load_tf_uniprot_id_mapping(self):
        # map tf names to uniprot ids
        self.tf_uniprot_id_mapping = {}
        with open(ASB_GVATDB.TF_ID_MAPPING_PATH, 'rb') as tf_uniprot_id_mapfile:
            self.tf_uniprot_id_mapping = pickle.load(tf_uniprot_id_mapfile)
