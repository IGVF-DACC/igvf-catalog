import csv
import json
import os
import gzip
import pickle
from typing import Optional

from adapters.writer import Writer
# Example motif file (IGVFFI8823UTCQ) from SEMpl M00778.sem
# #BASELINE:-0.671761
# AHR	A	C	G	T
# 1	-0.0981338	-0.0827793	0.0100979	-0.173785
# 2	-0.284773	-0.333357	-0.24361	0.0154123
# 3	-0.312271	0.025403	-0.288961	-0.152907
# 4	-0.125256	-0.494299	-0.00116848	-0.260581
# 5	-0.53657	0	-0.6353	-0.518209
# 6	-0.451598	-0.585824	0	-0.494461
# 7	-0.0538789	-0.113863	-0.387188	0.00560577
# 8	-0.0698494	-0.172925	0.0229245	-0.182021
# 9	0.0130119	-0.300118	-0.323497	-0.311547
# 10	-0.143318	0.00440271	-0.168156	-0.0833881
# 11	-0.0420202	-0.0158168	0.00441693	-0.00877582

# Example mapping file on TFs (SEM provenance file IGVFFI4892QCRR)
# transcription_factor    ensembl_id      ebi_complex_ac  uniprot_ac      PWM_id  SEM     SEM_baseline    cell_type       neg_log10_pval  chip_ENCODE_accession   dnase_ENCODE_accession  PWM_source
# AHR     ENSG00000106546         P35869  M00778  M00778.sem      -0.671761       HepG2   18.35095        ENCFF242PUG     ENCFF001UVU     TRANSFAC


class SEMMotif:
    ALLOWED_LABELS = ['motif', 'motif_protein', 'complex', 'complex_protein']
    ENSEMBL_MAPPING = './data_loading_support_files/ensembl_to_uniprot/uniprot_to_ENSP_human.pkl'

    def __init__(self, filepath, label='motif', sem_provenance_path=None, writer: Optional[Writer] = None, **kwargs):
        if label not in SEMMotif.ALLOWED_LABELS:
            raise ValueError('Invalid label. Allowed values: ' +
                             ','.join(SEMMotif.ALLOWED_LABELS))

        self.filepath = filepath
        self.sem_provenance_path = sem_provenance_path
        self.file_accession = os.path.basename(self.filepath).split('.')[0]
        self.source_url = 'https://data.igvf.org/model-files/' + self.file_accession
        self.label = label
        self.writer = writer

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

    def load_complexes(self):
        if self.label == 'complex_protein':
            self.ensembl = pickle.load(open(SEMMotif.ENSEMBL_MAPPING, 'rb'))
        with gzip.open(self.filepath, 'rt') as map_file:
            map_csv = csv.reader(map_file, delimiter='\t')
            for row in map_csv:
                if ':' in row[0]:
                    if not row[2]:  # complex not loaded from EBI
                        if self.label == 'complex':
                            _props = {
                                '_key': 'SEMpl_' + row[0],
                                'name': row[0] + ' complex',
                                'source': 'IGVF',
                                'source_url': 'https://data.igvf.org/tabular-files/' + self.file_accession
                            }
                            self.writer.write(json.dumps(_props))
                            self.writer.write('\n')
                        else:
                            # TAL1:TCF3 has an unexpected space in the end
                            uniprot_ids = row[3].strip().split(';')
                            ensembl_ids = []
                            for uniprot_id in uniprot_ids:
                                if uniprot_id not in self.ensembl:
                                    print('Unable to map ' +
                                          uniprot_id + ' to ensembl ids')
                                else:
                                    ensembl_ids.extend(
                                        self.ensembl.get(uniprot_id))
                            for ensembl_id in ensembl_ids:
                                if ensembl_id is None:
                                    print('Unable to map ' +
                                          row[3] + ' to ensembl ids')
                                    return
                                else:
                                    _props = {
                                        '_key': 'SEMpl_' + row[0] + '_' + ensembl_id,
                                        '_from': 'complexes/' + 'SEMpl_' + row[0],
                                        '_to': 'proteins/' + ensembl_id,
                                        'name': 'contains',
                                        'inverse_name': 'belongs to',
                                        'source': 'IGVF',
                                        'source_url': 'https://data.igvf.org/tabular-files/' + self.file_accession
                                    }
                                self.writer.write(json.dumps(_props))
                                self.writer.write('\n')
        self.writer.close()

    def process_file(self):
        self.writer.open()
        if self.label in ['complex', 'complex_protein']:
            self.load_complexes()
            return

        self.load_tf_id_mapping()
        self.ensembl = pickle.load(open(SEMMotif.ENSEMBL_MAPPING, 'rb'))

        with gzip.open(self.filepath, 'rt') as sem_file:
            baseline = next(sem_file).strip().split(':')[1]
            tf_name = next(sem_file).strip().split()[0]
            motif_key = tf_name + '_SEMpl'

            if self.label == 'motif':
                pwm = []
                for row in sem_file:
                    sem_row = row.strip().split()[1:]
                    pwm.append([str(value) for value in sem_row])

                length = len(pwm)
                props = {
                    '_key': motif_key,
                    'name': motif_key,
                    'tf_name': tf_name,
                    'source': 'IGVF',
                    'source_url': self.source_url,
                    'pwm': pwm,
                    'length': length,
                    'baseline': float(baseline),
                }
                self.writer.write(json.dumps(props))
                self.writer.write('\n')

            elif self.label == 'motif_protein':
                tf_id = self.tf_id_mapping.get(tf_name)
                tf_keys = [tf_id]

                if tf_id.startswith('proteins'):
                    # convert uniprot to ENSP
                    ensembl_ids = self.ensembl.get(tf_id.split('/')[1])
                    if ensembl_ids is None:
                        print('Unable to map ' + tf_name + ' to ensembl id')
                        return
                    else:
                        tf_keys = ['proteins/' +
                                   ensembl_id for ensembl_id in ensembl_ids]

                for tf_key in tf_keys:  # one uniprot id possible map to multiple ENSP ids

                    _key = motif_key + '_' + tf_key.split('/')[-1]
                    _from = 'motifs/' + motif_key
                    _to = tf_key  # either complexes/ or proteins/
                    props = {
                        '_key': _key,
                        '_from': _from,
                        '_to': _to,
                        'name': 'is used by',
                        'inverse_name': 'uses',
                        'biological_process': 'ontology_terms/GO_0003677',  # DNA Binding
                        'source': 'IGVF',
                        'source_url': self.source_url
                    }

                    self.writer.write(json.dumps(props))
                    self.writer.write('\n')

        self.writer.close()
