import csv
import json
import os
import pickle
import gzip
from typing import Optional

from adapters.base import BaseAdapter
from adapters.writer import Writer
from adapters.helpers import get_file_fileset_by_accession_in_arangodb

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
    ALLOWED_LABELS = ['sem_predicted_asb']
    ENSEMBL_MAPPING = './data_loading_support_files/ensembl_to_uniprot/uniprot_to_ENSP_human.pkl'
    BINDING_EFFECT_LIST = ['binding_ablated', 'binding_decreased',
                           'binding_created', 'binding_increased']  # ignore negative cases

    def __init__(self, filepath, label='sem_predicted_asb', sem_provenance_path=None, writer: Optional[Writer] = None, validate=False, **kwargs):
        self.sem_provenance_path = sem_provenance_path
        self.file_accession = os.path.basename(filepath).split('.')[0]
        self.source_url = 'https://data.igvf.org/tabular-files/' + self.file_accession

        super().__init__(filepath, label, writer, validate)

    def _get_schema_type(self):
        """Return schema type."""
        return 'edges'

    def _get_collection_name(self):
        """Get collection name."""
        return 'variants_proteins'

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

    def process_file(self):
        self.writer.open()
        self.load_tf_id_mapping()
        self.ensembls = pickle.load(open(self.ENSEMBL_MAPPING, 'rb'))
        self.file_fileset = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)

        with gzip.open(self.filepath, 'rt') as sem_file:
            sem_csv = csv.reader(sem_file, delimiter='\t')
            tf_name = None

            for row in sem_csv:
                if row[0].startswith('#'):
                    if row[0].startswith('#TFName: '):
                        tf_name = row[0].replace('#TFName: ', '')
                        tf_id = self.tf_id_mapping.get(tf_name)
                        tf_keys = [tf_id]
                        if tf_id.startswith('proteins'):
                            # convert uniprot to ENSP
                            ensembl_ids = self.ensembls.get(
                                tf_id.split('/')[1])
                            if ensembl_ids is None:
                                self.logger.warning('Unable to map ' +
                                                    tf_name + ' to ensembl id')
                                return
                            else:
                                tf_keys = [
                                    'proteins/' + ensembl_id for ensembl_id in ensembl_ids]
                    else:
                        continue
                elif row[0] == 'chr':
                    continue
                else:
                    if row[-2] in SEMPred.BINDING_EFFECT_LIST:
                        variant_id = row[2]
                        # did precheck for all input variants in IGVFFI6807FCZT.tsv.gz, all are valid and loaded from favor, so skipping checking here
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
                                'source': 'IGVF',
                                'source_url': self.source_url
                            }
                            if self.validate:
                                self.validate_doc(_props)
                            self.writer.write(json.dumps(_props))
                            self.writer.write('\n')

        self.writer.close()
