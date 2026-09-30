import csv
import json
import os
import gzip
from typing import Optional

from adapters.base import BaseAdapter
from adapters.writer import Writer
from adapters.helpers import (
    bulk_check_variants_in_arangodb,
    get_file_fileset_by_accession_in_arangodb,
    load_variant,
)
from adapters.protein_map import ProteinMap

# Example prediction file from SEMpl IGVFFI6923RISY.tsv.gz
# #Description: Predictions of variant effects on transcription factor binding
# #TFName: ATF4:CREB1
# #BiosampleOntologyTermName: N/A
# #BiosampleOntologyTermID: N/A
# #AssayContext: ChIP-seq
# #Model: SEMpl_v1.0.0
# chr     pos     spdi    ref     alt     ref_seq_context alt_seq_context ref_score       alt_score       variant_effect_score    pvalue  SEMpl.annotation        SEMpl.baseline
# chr10   10158   NC_000010.11:10157:T:C  T       C       chr10:10150-10159       chr10:10150-10159       0.002765383345015798    0.008308750206634546    1.5871519999999988      N/A     no_binding      -3.177711

# Only load positive variants with significant effects on TF binding status (based on the last column)

# Example mapping file on TFs (SEM provenance file IGVFFI4892QCRR.tsv.gz)
# transcription_factor    ensembl_id      ebi_complex_ac  uniprot_ac      PWM_id  SEM     SEM_baseline    cell_type       neg_log10_pval  chip_ENCODE_accession   dnase_ENCODE_accession  PWM_source
# AHR     ENSG00000106546         P35869  M00778  M00778.sem      -0.671761       HepG2   18.35095        ENCFF242PUG     ENCFF001UVU     TRANSFAC


class SEMPred(BaseAdapter):
    ALLOWED_LABELS = ['sem_predicted_asb', 'variants']
    CHUNK_SIZE = 6500
    SOURCE = 'IGVF'
    BINDING_EFFECT_LIST = ['binding_ablated', 'binding_decreased',
                           'binding_created', 'binding_increased']  # ignore negative cases

    def __init__(self, filepath, label='sem_predicted_asb', sem_provenance_path=None, writer: Optional[Writer] = None, validate=False, **kwargs):
        self.sem_provenance_path = sem_provenance_path
        # assumes that both sem_provenance_path and filepath have accession as prefix
        self.sem_provenance_accession = os.path.basename(
            sem_provenance_path).split('.')[0]
        self.file_accession = os.path.basename(filepath).split('.')[0]
        self.source_url = 'https://data.igvf.org/tabular-files/' + self.file_accession
        self.written_variant_keys = set()

        super().__init__(filepath, label, writer, validate)

    def _get_schema_type(self):
        """Return schema type based on label."""
        return 'nodes' if self.label == 'variants' else 'edges'

    def _get_collection_name(self):
        """Get collection based on label."""
        return 'variants' if self.label == 'variants' else 'variants_proteins'

    def load_tf_id_mapping(self):
        self.tf_id_mapping = {}
        with gzip.open(self.sem_provenance_path, 'rt') as map_file:
            map_csv = csv.reader(map_file, delimiter='\t')
            for row in map_csv:
                if ':' in row[0]:
                    if row[2]:
                        # e.g. complexes/CPX-6048
                        self.tf_id_mapping[row[0]] = 'complexes/' + row[2]
                    else:  # 'fake' complex from SEMpl
                        self.tf_id_mapping[row[0]
                                           ] = 'complexes/SEMpl_' + row[0]
                else:
                    # e.g. proteins/P40763
                    self.tf_id_mapping[row[0]] = 'proteins/' + row[3]

    def parse(self):
        self.writer.add_tag('portal_accessions', self.file_accession)
        self.writer.add_tag('portal_accessions', self.sem_provenance_accession)
        self.file_fileset = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        file_set_accession = self.file_fileset.get('file_set_id')
        if file_set_accession:
            self.writer.add_tag('portal_accessions', file_set_accession)

        if self.label == 'sem_predicted_asb':
            self.load_tf_id_mapping()
            self.protein_map = ProteinMap(organism='Homo sapiens')

        with gzip.open(self.filepath, 'rt') as sem_file:
            sem_csv = csv.reader(sem_file, delimiter='\t')
            tf_name = None
            tf_keys = None
            chunk = []

            for row in sem_csv:
                if row[0].startswith('#'):
                    if self.label != 'sem_predicted_asb':
                        continue
                    if row[0].startswith('#TFName: '):
                        tf_name = row[0].replace('#TFName: ', '')
                        tf_id = self.tf_id_mapping.get(tf_name)
                        tf_keys = [tf_id]
                        if tf_id.startswith('proteins'):
                            # convert uniprot to ENSP
                            ensembl_ids = self.protein_map.get(
                                tf_id.split('/')[1])
                            if ensembl_ids is None:
                                if chunk:
                                    self.process_chunk(chunk)
                                self.protein_map.log(self.logger)
                                return
                            else:
                                tf_keys = [
                                    'proteins/' + ensembl_id for ensembl_id in ensembl_ids]
                    else:
                        continue
                elif row[0] == 'chr':
                    continue
                elif row[-2] in SEMPred.BINDING_EFFECT_LIST:
                    chunk.append((row, tf_name, tf_keys))
                    if len(chunk) >= SEMPred.CHUNK_SIZE:
                        self.process_chunk(chunk)
                        chunk = []
            if chunk:
                self.process_chunk(chunk)

        if self.label == 'sem_predicted_asb':
            self.protein_map.log(self.logger)

    def process_chunk(self, chunk):
        rows_by_variant_id = [(row[2], row, tf_name, tf_keys)
                              for row, tf_name, tf_keys in chunk]

        loaded_variants = bulk_check_variants_in_arangodb(
            list({variant_id for variant_id, _, _, _ in rows_by_variant_id}),
            check_by='_key',
        )

        if self.label == 'variants':
            self.write_missing_variants(
                [(variant_id, row) for variant_id, row, _, _ in rows_by_variant_id], loaded_variants)
            return

        skipped_missing = 0
        for variant_id, row, tf_name, tf_keys in rows_by_variant_id:
            if variant_id not in loaded_variants:
                skipped_missing += 1
                continue
            self.write_edges(variant_id, row, tf_name, tf_keys)

        if skipped_missing:
            self.logger.warning(
                f'Skipped {skipped_missing} row(s) - variant not found in variants collection')

    def write_edges(self, variant_id, row, tf_name, tf_keys):
        _from = 'variants/' + variant_id

        for tf_key in tf_keys:  # one uniprot id possible map to multiple ENSP ids
            _to = tf_key  # either complexes/ or proteins/
            _key = '_'.join(
                [variant_id, tf_key.split('/')[-1], self.file_accession])

            _props = {
                '_key': _key,
                '_from': _from,
                '_to': _to,
                'label': 'predicted allele-specific binding',
                'method': self.file_fileset['method'],
                'class': self.file_fileset['class'],
                'biosample_term': self.file_fileset['samples'][0] if self.file_fileset.get('samples') else None,
                'biological_context': self.file_fileset['simple_sample_summaries'][0] if self.file_fileset.get('simple_sample_summaries') else None,
                'motif': 'motifs/' + tf_name + '_SEMpl',
                'ref_seq_context': row[5],
                'alt_seq_context': row[6],
                'ref_score': float(row[7]),
                'alt_score': float(row[8]),
                'variant_effect_score': float(row[9]),
                # 'p_value': row[10], # skipped, all N/A
                'SEMpl_annotation': row[11],
                'SEMpl_baseline': float(row[12]),
                'files_filesets': 'files_filesets/' + self.file_accession,
                'name': 'modulates binding of',
                'inverse_name': 'binding modulated by',
                'biological_process': 'ontology_terms/GO_0051101',
                'source': SEMPred.SOURCE,
                'source_url': self.source_url
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
                    'source': SEMPred.SOURCE,
                    'source_url': self.source_url,
                    'files_filesets': 'files_filesets/' + self.file_accession
                })
                if self.validate:
                    self.validate_doc(variant_props)
                self.writer.write(json.dumps(variant_props))
                self.writer.write('\n')
            elif skipped:
                self.logger.warning(
                    f"Invalid variant: {skipped['variant_id']} - {skipped['reason']}")
