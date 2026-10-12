import csv
import json
from typing import Optional
from math import log10

from adapters.archive_utils import get_file_accession, get_files_from_folder
from adapters.base import BaseAdapter
from adapters.helpers import (
    build_variant_id,
    bulk_check_variants_in_arangodb,
    get_file_fileset_by_accession_in_arangodb,
    load_variant,
)
from adapters.protein_map import ProteinMap
from adapters.writer import Writer

# ADASTRA allele-specific binding (ASB) file downloaded from: https://adastra.autosome.org/assets/cltfdata/adastra.cltf.bill_cipher.zip
# Cell ontology available from GTRD (Gene Transcription Regulation Database): http://gtrd.biouml.org/

# Example file TF_name@cell_name.tsv (e.g. ATF1_HUMAN@HepG2__hepatoblastoma_.tsv):
# chr	pos	ID	ref	alt	repeat_type	mean_BAD	mean_SNP_per_segment	total_cover	n_aggregated	es_mean_ref	es_mean_altlogitp_ref	fdrp_bh_ref	logitp_alt	fdrp_bh_alt	motif_log_pref	motif_log_palt	motif_fc	motif_pos	motif_orient	motif_conc	novel
# chr11	129321262.0 rs10750410	A	G		1.25	518.5	73.0	2.0	-1.508200583122832	1.5220631227173078	0.9999438590195968	1.0	3.776801544248756e-06	0.0024711390339222	2.668977799202377	2.9239362481887974	0.8469536347168959	19	+	No Hit	False


class ASB(BaseAdapter):
    # 1-based coordinate system
    ALLOWED_LABELS = ['asb', 'variants']
    ONTOLOGY_PRIORITY_LIST = ['CL:', 'UBERON:', 'CLO:', 'EFO:']
    CELL_ONTOLOGY_ID_MAPPING_PATH = './data_loading_support_files/ADASTRA_cell_ontologies_mapped_ids.tsv'
    TF_ID_MAPPING_PATH = './data_loading_support_files/ADASTRA_TF_uniprot_accession.tsv'
    SOURCE = 'ADASTRA'
    MOTIF_SOURCE = 'HOCOMOCOv11'
    MAX_LOG10_PVALUE = 400  # cap when fdrp_bh is 0 (same as AFGR/eQTL Catalog)

    def __init__(
        self,
        filepath,
        label='asb',
        writer: Optional[Writer] = None,
        validate=False,
        **kwargs
    ):
        # Initialize base adapter first
        super().__init__(filepath, label, writer, validate)
        self.file_accession = get_file_accession(filepath)
        self.written_variant_keys = set()

    def _get_schema_type(self):
        """Return schema type based on label."""
        return 'nodes' if self.label == 'variants' else 'edges'

    def _get_collection_name(self):
        """Get collection based on label."""
        return 'variants' if self.label == 'variants' else 'variants_proteins'

    @staticmethod
    def _compute_score(p_value_adj_ref, p_value_adj_alt):
        """Directional ASB significance score.

        Negative FDR-adjusted p-value when only the reference allele is
        significant (< 0.05), positive when only the alternate allele is,
        or None when both or neither are significant (no single direction
        to report).
        """
        ref_significant = p_value_adj_ref < 0.05
        alt_significant = p_value_adj_alt < 0.05
        if ref_significant and alt_significant:
            return None
        if ref_significant:
            return -p_value_adj_ref
        if alt_significant:
            return p_value_adj_alt
        return None

    def load_tf_uniprot_id_mapping(self):
        self.tf_uniprot_id_mapping = {}  # e.g. key: 'ANDR_HUMAN'; value: 'P10275'
        with open(ASB.TF_ID_MAPPING_PATH, 'r') as tf_uniprot_id_mapfile:
            next(tf_uniprot_id_mapfile)
            for row in tf_uniprot_id_mapfile:
                mapping = row.strip().split()
                self.tf_uniprot_id_mapping[mapping[0]] = mapping[1]

    def load_cell_ontology_id_mapping(self):
        self.cell_ontology_id_mapping = {}
        with open(ASB.CELL_ONTOLOGY_ID_MAPPING_PATH, 'r') as cell_ontology_id_mapping_file:
            cell_ontology_csv = csv.reader(
                cell_ontology_id_mapping_file, delimiter='\t')
            next(cell_ontology_csv)
            for row in cell_ontology_csv:
                cell_name = row[2]
                cell_ontology_id = row[-1]  # pre-mapped ontology id
                cell_gtrd_id = row[0]  # cell id in GTRD
                cell_gtrd_name = row[1]  # cell name in GTRD
                self.cell_ontology_id_mapping[cell_name] = [
                    cell_ontology_id, cell_gtrd_id, cell_gtrd_name]

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
        self.load_cell_ontology_id_mapping()
        if self.label == 'asb':
            self.protein_map = ProteinMap(organism='Homo sapiens')

        for input_filepath in get_files_from_folder(self.filepath):
            filename = input_filepath.name
            # ignore test files
            if filename.endswith('__test.tsv'):
                continue
            if '_HUMAN@' not in filename:
                continue
            tf_name = filename.split('@')[0]
            tf_uniprot_id = self.tf_uniprot_id_mapping.get(tf_name)
            if tf_uniprot_id is None:
                self.logger.warning(
                    f'TF uniprot id unavailable, skipping: {filename}')
                continue

            # skeletal_muscles@myoblasts in filename -> skeletal_muscles_and_myoblasts in table
            cell_name = '_and_'.join(
                filename.replace('.tsv', '').split('@')[1:])
            try:
                cell_ontology_id, cell_gtrd_id, cell_gtrd_name = self.cell_ontology_id_mapping[
                    cell_name]
            except KeyError:
                self.logger.warning(
                    f'Cell ontology id unavailable, skipping: {filename}')
                continue

            with open(input_filepath, 'r') as asb:
                asb_csv = csv.reader(asb, delimiter='\t')
                next(asb_csv)

                # ADASTRA variants are expected to already be loaded, e.g.
                # from FAVOR/dbSNP. Missing-but-valid ones are only created
                # via a separate run with label='variants' - the 'asb' pass
                # only skips the edge, rather than emitting a dangling _from
                # reference.
                rows_by_variant_id = []
                for row in asb_csv:
                    chr, pos, rsid, ref, alt = row[:5]
                    # some files have decimal '.0' in position column
                    pos = int(float(pos))
                    try:
                        variant_id = build_variant_id(
                            chr, pos, ref, alt, 'GRCh38'
                        )
                    except Exception as e:
                        self.logger.warning(
                            f'Skipping row - unable to build variant id (chr={chr}, pos={pos}, ref={ref}, alt={alt}): {e}')
                        continue
                    rows_by_variant_id.append((variant_id, row))

                if not rows_by_variant_id:
                    continue

                loaded_variants = bulk_check_variants_in_arangodb(
                    list({variant_id for variant_id,
                         _ in rows_by_variant_id}),
                    check_by='_key',
                )

                if self.label == 'variants':
                    self.write_missing_variants(
                        rows_by_variant_id, loaded_variants, cell_gtrd_id)
                    continue

                skipped_missing = 0

                for variant_id, row in rows_by_variant_id:
                    if variant_id not in loaded_variants:
                        skipped_missing += 1
                        continue
                    chr, pos, rsid, ref, alt = row[:5]
                    pos = int(float(pos))

                    ensembl_ids = self.protein_map.get(tf_uniprot_id)
                    if ensembl_ids is None:
                        continue

                    for ensembl_id in ensembl_ids:
                        _key = variant_id + '_' + \
                            ensembl_id + '_' + \
                            row[21].replace(' ', '_') + \
                            '_ADASTRA_' + cell_gtrd_id

                        _from = 'variants/' + variant_id
                        _to = 'proteins/' + ensembl_id

                        p_value_adj_ref = float(row[13])  # fdrp_bh_ref
                        p_value_adj_alt = float(row[15])  # fdrp_bh_alt
                        neg_log10_pvalue_adj_ref = ASB.MAX_LOG10_PVALUE
                        if p_value_adj_ref > 0:
                            neg_log10_pvalue_adj_ref = 0 - \
                                log10(p_value_adj_ref)  # prevent -0.0 values

                        neg_log10_pvalue_adj_alt = ASB.MAX_LOG10_PVALUE
                        if p_value_adj_alt > 0:
                            neg_log10_pvalue_adj_alt = 0 - \
                                log10(p_value_adj_alt)

                        score = ASB._compute_score(
                            p_value_adj_ref, p_value_adj_alt)

                        props = {
                            '_key': _key,
                            '_from': _from,
                            '_to': _to,
                            'chr': chr,
                            'rsid': rsid,
                            'motif_fc': float(row[18]) if row[18] else None,
                            'motif_pos': int(float(row[19])) if row[19] else None,
                            'motif_orient': row[20],
                            'motif_conc': row[21],
                            'motif': 'motifs/' + tf_name + '_' + ASB.MOTIF_SOURCE,
                            'es_mean_ref': float(row[10]),
                            'es_mean_alt': float(row[11]),
                            'p_value_adj_ref': p_value_adj_ref,
                            'p_value_adj_alt': p_value_adj_alt,
                            'neg_log10_pvalue_adj_ref': neg_log10_pvalue_adj_ref,
                            'neg_log10_pvalue_adj_alt': neg_log10_pvalue_adj_alt,
                            'score': score,
                            'biological_context': cell_gtrd_name,
                            'biosample_term': 'ontology_terms/' + cell_ontology_id,
                            'source': ASB.SOURCE,
                            'source_url': 'http://gtrd.biouml.org/#!table/gtrd_current.cells/Details/ID=' + cell_gtrd_id,
                            'label': 'allele-specific binding',
                            'method': self.method,
                            'class': self.collection_class,
                            'files_filesets': 'files_filesets/' + self.file_accession,
                            'name': 'modulates binding of',
                            'inverse_name': 'binding modulated by',
                            'biological_process': 'ontology_terms/GO_0051101'
                        }

                        if self.validate:
                            self.validate_doc(props)

                        self.writer.write(json.dumps(props))
                        self.writer.write('\n')

                if skipped_missing:
                    self.logger.warning(
                        f'Skipped {skipped_missing} row(s) in {filename} - variant not found in variants collection')

        if self.label == 'asb':
            self.protein_map.log(self.logger)

    def write_missing_variants(self, rows_by_variant_id, loaded_variants, cell_gtrd_id):
        for variant_id, row in rows_by_variant_id:
            if variant_id in loaded_variants or variant_id in self.written_variant_keys:
                continue
            self.written_variant_keys.add(variant_id)

            chr, pos, rsid, ref, alt = row[:5]
            pos = int(float(pos))
            variant_props, skipped = load_variant(f'{chr}-{pos}-{ref}-{alt}')
            if variant_props:
                variant_props.update({
                    'source': ASB.SOURCE,
                    'source_url': 'http://gtrd.biouml.org/#!table/gtrd_current.cells/Details/ID=' + cell_gtrd_id,
                    'files_filesets': 'files_filesets/' + self.file_accession
                })
                if self.validate:
                    self.validate_doc(variant_props)
                self.writer.write(json.dumps(variant_props))
                self.writer.write('\n')
            elif skipped:
                self.logger.warning(
                    f"Invalid variant: {skipped['variant_id']} - {skipped['reason']}")
