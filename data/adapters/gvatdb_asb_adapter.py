import csv
import json
import pickle
from math import log10
from typing import Optional
import os

from adapters.base import BaseAdapter
from adapters.helpers import (
    bulk_check_variants_in_arangodb,
    get_file_fileset_by_accession_in_arangodb,
    load_variant,
)
from adapters.protein_map import ProteinMap
from adapters.writer import Writer


# Data source: https://www.synapse.org/Synapse:syn65484409
# example rows:
# chr	pos	spdi	ref	alt	TF	ensembl_id	experiment	hg19_oligo_coord	oligo_auc	oligo_pval	ref_auc	alt_auc	pbs	pval	fdr	rsid
# chr10	112626980	NC_000010.11:112626979:C:T	C	T	ALX1	ENSG00000180318	FL.6.0.G12	chr10:114386719-114386759	3.02599	0.00133	1.44024	-1.28154	2.72179	0.31704	1.0	rs76124550
# chr10	112627010	NC_000010.11:112627009:T:C	T	C	ALX1	ENSG00000180318	FL.6.0.G12	chr10:114386749-114386789	3.6725	0.00049	-1.62935	0.59975	-2.2291	0.4039	1.0	rs115699571


class ASB_GVATDB(BaseAdapter):
    TF_ID_MAPPING_PATH = './data_loading_support_files/GVATdb_TF_mapping.pkl'
    SOURCE = 'GVATdb'
    SOURCE_URL = 'https://renlab.sdsc.edu/GVATdb/'
    # smallest pvalue in this file is 0, the second smallest pvalue is 1e-05, so we will replace 0 with 1e-05 to calculate log10pvalue
    # so the max log10pvalue is 5.
    MAX_LOG10_PVALUE = 5
    # label=variants does not need to be run regularly for this adapter for now - a full pass
    # over its already-loaded edges found no variants missing from the variants collection
    # (unlike AFGR_caqtl/AFGR_eqtl/AFGR_sqtl/TopLD/EQTLCatalog/PharmGKB/pQTL, which do have
    # missing variants and need label=variants run as part of their regular load).
    ALLOWED_LABELS = ['variant_protein', 'variants']
    CHUNK_SIZE = 6500

    def __init__(self, filepath, label='variant_protein', writer: Optional[Writer] = None, validate=False, **kwargs):
        super().__init__(filepath, label, writer, validate)
        self.file_accession = os.path.basename(filepath).split('.')[0]
        self.written_variant_keys = set()

    def _get_schema_type(self):
        """Return schema type based on label."""
        return 'nodes' if self.label == 'variants' else 'edges'

    def _get_collection_name(self):
        """Get collection based on label."""
        return 'variants' if self.label == 'variants' else 'variants_proteins'

    def parse(self):
        self.writer.add_tag('portal_accessions', self.file_accession)
        self.file_fileset = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        self.collection_class = self.file_fileset['class']
        self.method = self.file_fileset['method']
        file_set_accession = self.file_fileset.get('file_set_id')
        if file_set_accession:
            self.writer.add_tag('portal_accessions', file_set_accession)
        self.load_tf_uniprot_id_mapping()
        if self.label == 'variant_protein':
            self.protein_map = ProteinMap(organism='Homo sapiens')

        with open(self.filepath, 'r') as input_file:
            rows = csv.reader(input_file, delimiter='\t')
            next(rows)
            chunk = []
            for row in rows:
                chunk.append(row)
                if len(chunk) >= ASB_GVATDB.CHUNK_SIZE:
                    self.process_chunk(chunk)
                    chunk = []
            if chunk:
                self.process_chunk(chunk)

        if self.label == 'variant_protein':
            self.protein_map.log(self.logger)

    def process_chunk(self, chunk):
        rows_by_variant_id = [(row[2], row) for row in chunk]

        loaded_variants = bulk_check_variants_in_arangodb(
            list({variant_id for variant_id, _ in rows_by_variant_id}),
            check_by='_key',
        )

        if self.label == 'variants':
            self.write_missing_variants(rows_by_variant_id, loaded_variants)
            return

        skipped_missing = 0
        for variant_id, row in rows_by_variant_id:
            if variant_id not in loaded_variants:
                skipped_missing += 1
                continue
            self.write_edges(variant_id, row)

        if skipped_missing:
            self.logger.warning(
                f'Skipped {skipped_missing} row(s) - variant not found in variants collection')

    def write_edges(self, variant_id, row):
        pvalue = float(row[-3])
        if pvalue == 0:
            log10pvalue = ASB_GVATDB.MAX_LOG10_PVALUE
        else:
            log10pvalue = -1 * log10(pvalue)

        tf_uniprot_id = self.tf_uniprot_id_mapping.get(row[5])
        if tf_uniprot_id is None or len(tf_uniprot_id) == 0:
            return

        ensembl_ids = self.protein_map.get(tf_uniprot_id[0])
        if ensembl_ids is None:
            return
        experiment = row[7]

        for ensembl_id in ensembl_ids:
            # create separate edges for same variant-tf pairs in different experiments
            _id = variant_id + '_' + \
                ensembl_id + '_' + experiment.replace('.', '_')
            _source = 'variants/' + variant_id
            _target = 'proteins/' + ensembl_id

            # if p_value_adj is 0, we will set neg_log10_pvalue_adj to 2 (max value in the dataset), otherwise we will calculate it as -log10(p_value_adj)
            p_value_adj = float(row[15])
            neg_log10_pvalue_adj = 2
            if p_value_adj > 0:
                neg_log10_pvalue_adj = -1 * log10(p_value_adj)

            _props = {
                '_key': _id,
                '_from': _source,
                '_to': _target,
                'p_value': pvalue,
                'neg_log10_pvalue': log10pvalue,
                'experiment': experiment,
                'hg19_coordinate': row[8],
                'oligo_auc': float(row[9]),
                'oligo_pval': float(row[10]),
                'ref_auc': float(row[11]),
                'alt_auc': float(row[12]),
                'pbs': float(row[13]),
                'p_value_adj': p_value_adj,
                'neg_log10_pvalue_adj': neg_log10_pvalue_adj,
                'source': ASB_GVATDB.SOURCE,
                'source_url': ASB_GVATDB.SOURCE_URL,
                'label': 'allele-specific binding',
                'method': self.method,
                'class': self.collection_class,
                'files_filesets': 'files_filesets/' + self.file_accession,
                'name': 'modulates binding of',
                'inverse_name': 'binding modulated by',
                'biological_process': 'ontology_terms/GO_0051101'
            }

            if self.validate:
                self.validate_doc(_props)

            self.writer.write(json.dumps(_props))
            self.writer.write('\n')

    def write_missing_variants(self, rows_by_variant_id, loaded_variants):
        for variant_id, row in rows_by_variant_id:
            if variant_id in loaded_variants or variant_id in self.written_variant_keys:
                continue
            self.written_variant_keys.add(variant_id)

            chr, pos, ref, alt = row[0], row[1], row[3], row[4]
            variant_props, skipped = load_variant(f'{chr}-{pos}-{ref}-{alt}')
            if variant_props:
                variant_props.update({
                    'source': ASB_GVATDB.SOURCE,
                    'source_url': ASB_GVATDB.SOURCE_URL,
                    'files_filesets': 'files_filesets/' + self.file_accession
                })
                if self.validate:
                    self.validate_doc(variant_props)
                self.writer.write(json.dumps(variant_props))
                self.writer.write('\n')
            elif skipped:
                self.logger.warning(
                    f"Invalid variant: {skipped['variant_id']} - {skipped['reason']}")

    def load_tf_uniprot_id_mapping(self):
        # map tf names to uniprot ids
        self.tf_uniprot_id_mapping = {}
        with open(ASB_GVATDB.TF_ID_MAPPING_PATH, 'rb') as tf_uniprot_id_mapfile:
            self.tf_uniprot_id_mapping = pickle.load(tf_uniprot_id_mapfile)
