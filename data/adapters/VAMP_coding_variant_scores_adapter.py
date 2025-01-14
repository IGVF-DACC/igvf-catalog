import csv
import json
import pickle
import re
from typing import Optional

from adapters.writer import Writer
# Example line from file from CYP2C19 VAMP-seq (IGVFFI5890AHYL):
# variant	abundance_score	abundance_sd	abundance_se	ci_upper	ci_lower	abundance_Rep1	abundance_Rep2	abundance_Rep3
# ENSP00000360372.3:p.Ala103Cys	0.902654998066618	0.0954803288299908	0.0551255935523091	0.9564024517801190	0.8489075443531170	0.7974194877182200	0.983743944202336	0.926801562279298
# ENSP00000360372.3:p.Ala103Asp	0.5857497278869870	0.0603323988117348	0.0348329266948109	0.6197118314144270	0.5517876243595460	0.5265040329858070	0.647113071129789	0.5836320795453640


class VAMPAdapter:
    # The labels except the first one are loaded for enumerated variants with >1 base substitutions from CYP2C19 VAMP-seq data
    ALLOWED_LABELS = [
        'vamp_coding_variants_phenotypes', 'vamp_coding_variants', 'vamp_coding_variants_proteins', 'vamp_variants', 'vamp_variants_coding_variants', ]
    SOURCE = 'VAMP-seq'
    SOURCE_URL = 'https://data.igvf.org/analysis-sets/IGVFDS0368ZLPX/'
    GENE_NAME = 'CYP2C19'
    TRANSCRIPT_ID = 'ENST00000371321'
    CODING_VARIANTS_MAPPING_PATH = './data_loading_support_files/VAMP/VAMP_coding_variants_ids.pkl'
    ENUMERATED_VARIANTS_MAPPING_PATH = './data_loading_support_files/VAMP/VAMP_coding_variants_enumerated_mutation_ids.pkl'
    PHENOTYPE_TERM = 'OBA_0000128'  # protein stability

    def __init__(self, filepath, label='vamp_coding_variants_phenotypes', writer: Optional[Writer] = None, **kwargs):
        if label not in VAMPAdapter.ALLOWED_LABELS:
            raise ValueError('Invalid label. Allowed values: ' +
                             ','.join(VAMPAdapter.ALLOWED_LABELS))
        self.label = label
        self.type = 'edge'
        if self.label in ['vamp_coding_variants', 'vamp_variants']:
            self.type = 'node'

        self.filepath = filepath
        self.writer = writer

    def process_file(self):
        self.writer.open()
        self.load_coding_variant_id()
        self.load_enumerated_variant_id()

        with open(self.filepath, 'r') as vamp_file:
            vamp_csv = csv.reader(vamp_file)
            next(vamp_csv)
            for row in vamp_csv:
                if not row[1]:  # no abundance score
                    continue

                if self.label == 'vamp_coding_variants_phenotypes':
                    if row[0] in self.coding_variant_id:
                        _ids = self.coding_variant_id[row[0]]
                    elif row[0] in self.enumerated_variant_id:
                        _ids = self.enumerated_variant_id[row[0]
                                                          ]['mutation_ids']

                    for _id in _ids:
                        edge_key = _id + '_' + VAMPAdapter.PHENOTYPE_TERM
                        _props = {
                            '_key': edge_key,
                            '_from': 'coding_variants/' + _id,
                            '_to': 'ontology_terms/' + VAMPAdapter.PHENOTYPE_TERM,
                            'abundance_score': float(row[1]),
                            'abundance_sd': float(row[2]) if row[2] else None,
                            'abundance_se': float(row[3]) if row[3] else None,
                            'ci_upper': float(row[4]) if row[4] else None,
                            'ci_lower': float(row[5]) if row[5] else None,
                            'abundance_Rep1': float(row[6]) if row[6] else None,
                            'abundance_Rep2': float(row[7]) if row[7] else None,
                            'abundance_Rep3': float(row[8]) if row[8] else None,
                            'source': VAMPAdapter.SOURCE,
                            'source_url': VAMPAdapter.SOURCE_URL
                        }

                        self.writer.write(json.dumps(_props))
                        self.writer.write('\n')
                elif self.label == 'vamp_coding_variants':
                    if row[0] in self.enumerated_variant_id:
                        _ids = self.enumerated_variant_id[row[0]
                                                          ]['mutation_ids']
                        for i, _id in enumerate(_ids):
                            hgvsp = _id.split('_')[2]  # e.g. p.Ala103Cys
                            props = {
                                '_key': _id,
                                'aapos': int(self.enumerated_variant_id[row[0]]['aa_pos']),
                                'alt': self.enumerated_variant_id[row[0]]['alt_aa'],
                                'ref': self.enumerated_variant_id[row[0]]['ref_aa'],
                                # 'codonpos': # which number to put since it's the whole codon?
                                'gene_name': VAMPAdapter.GENE_NAME,
                                'transcript_id': VAMPAdapter.TRANSCRIPT_ID,
                                'hgvs': self.enumerated_variant_id[row[0]]['hgvsc_ids'][i],
                                'hgvsp': hgvsp,
                                'name': _id,
                                'ref_codon': self.enumerated_variant_id[row[0]]['refcodon'],
                                'source': VAMPAdapter.SOURCE,
                                'source_url': VAMPAdapter.SOURCE_URL
                            }

        self.writer.close()

    def load_coding_variant_id(self):
        self.coding_variant_id = {}
        with open(VAMPAdapter.CODING_VARIANTS_MAPPING_PATH, 'rb') as coding_variant_id_file:
            self.coding_variant_id = pickle.load(coding_variant_id_file)

    def load_enumerated_variant_id(self):
        self.enumerated_variant_id = {}
        # e.g. key: ENSP00000360372.3:p.Ala103Ter; value:
        # {'refcodon': 'GCT',
        # 'aa_pos': '103',
        # 'ref_aa': 'A',
        # 'alt_aa': '*',
        # 'ref_pos': 94775195,
        # 'alt_seqs': ['TAA', 'TAG', 'TGA'],
        # 'hgvsc_ids': ['c.307_309delinsTAA', 'c.307_309delinsTAG', 'c.307_309delinsTGA'],
        # 'mutation_ids': ['CYP2C19_ENST00000371321_p.Ala103Ter_c.307_309delinsTAA', 'CYP2C19_ENST00000371321_p.Ala103Ter_c.307_309delinsTAG', 'CYP2C19_ENST00000371321_p.Ala103Ter_c.307_309delinsTGA'],
        # 'hgvsc_ids': ['c.307_309delinsTAA', 'c.307_309delinsTAG', 'c.307_309delinsTGA'],
        # 'hgvsg_ids': ['NC_000010.11:g.94775196_94775198delinsTAA', 'NC_000010.11:g.94775196_94775198delinsTAG', 'NC_000010.11:g.94775196_94775198delinsTGA'],
        # 'spdi_ids': ['NC_000010.11:g.94775195:GCT:TAA', 'NC_000010.11:g.94775195:GCT:TAG', 'NC_000010.11:g.94775195:GCT:TGA']}
        with open(VAMPAdapter.ENUMERATED_VARIANTS_MAPPING_PATH, 'rb') as enumerated_variant_id_file:
            self.enumerated_variant_id = pickle.load(
                enumerated_variant_id_file)
