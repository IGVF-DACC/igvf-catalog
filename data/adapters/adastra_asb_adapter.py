import csv
import json
import os

from adapters import Adapter
from db.arango_db import ArangoDB
from adapters.helpers import build_variant_id

# ADASTRA allele-specific binding (ASB) file downloaded from: https://adastra.autosome.org/assets/cltfdata/adastra.cltf.bill_cipher.zip
# Cell ontology available from GTRD (Gene Transcription Regulation Database): http://gtrd.biouml.org/

# Example file TF_name@cell_name.tsv (e.g. ATF1_HUMAN@HepG2__hepatoblastoma_.tsv):
# chr	pos	ID	ref	alt	repeat_type	mean_BAD	mean_SNP_per_segment	total_cover	n_aggregated	es_mean_ref	es_mean_altlogitp_ref	fdrp_bh_ref	logitp_alt	fdrp_bh_alt	motif_log_pref	motif_log_palt	motif_fc	motif_pos	motif_orient	motif_conc	novel
# chr11	129321262.0 rs10750410	A	G		1.25	518.5	73.0	2.0	-1.508200583122832	1.5220631227173078	0.9999438590195968	1.0	3.776801544248756e-06	0.0024711390339222	2.668977799202377	2.9239362481887974	0.8469536347168959	19	+	No Hit	False


class ASB(Adapter):
    # 1-based coordinate system
    ALLOWED_LABELS = ['asb', 'asb_cell_ontology']
    ONTOLOGY_PRIORITY_LIST = ['CL:', 'UBERON:', 'CLO:', 'EFO:']
    CELL_ONTOLOGY_ID_MAPPING_PATH = './data_loading_support_files/ADASTRA_cell_ontologies_mapped_ids.tsv'
    TF_ID_MAPPING_PATH = './data_loading_support_files/ADASTRA_TF_uniprot_accession.tsv'
    SOURCE = 'ADASTRA allele-specific TF binding calls'
    MOTIF_SOURCE = 'HOCOMOCOv11'

    OUTPUT_PATH = './parsed-data'
    SKIP_BIOCYPHER = True

    def __init__(self, filepath, label='asb', dry_run=True):
        if label not in ASB.ALLOWED_LABELS:
            raise ValueError('Ivalid label. Allowed values: ' +
                             ','.join(ASB.ALLOWED_LABELS))

        self.filepath = filepath
        self.label = label
        self.dataset = label
        self.type = 'edge'
        if label == 'asb':
            self.collection = 'variants_proteins'
        else:
            self.collection = 'variants_proteins_terms'

        self.dry_run = dry_run

        self.output_filepath = '{}/{}.json'.format(
            ASB.OUTPUT_PATH,
            self.dataset
        )

        super(ASB, self).__init__()

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

    def process_file(self):
        parsed_data_file = open(self.output_filepath, 'w')
        self.load_tf_uniprot_id_mapping()
        self.load_cell_ontology_id_mapping()

        for filename in os.listdir(self.filepath):
            if '_HUMAN@' in filename:
                tf_name = filename.split('@')[0]
                tf_uniprot_id = self.tf_uniprot_id_mapping.get(tf_name)
                if tf_uniprot_id is None:
                    print('TF uniprot id unavailable, skipping: ' + filename)
                    continue
                # skeletal_muscles@myoblasts in filename -> skeletal_muscles_and_myoblasts in table
                cell_name = '_and_'.join(
                    filename.replace('.tsv', '').split('@')[1:])
                try:
                    cell_ontology_id, cell_gtrd_id, cell_gtrd_name = self.cell_ontology_id_mapping[
                        cell_name]
                except KeyError:
                    print('Cell ontology id unavailable, skipping: ' + filename)
                    continue

                with open(self.filepath + '/' + filename, 'r') as asb:
                    asb_csv = csv.reader(asb, delimiter='\t')
                    next(asb_csv)
                    for row in asb_csv:
                        chr, pos, rsid, ref, alt = row[:5]
                        # some files have decimal '.0' in position column
                        pos = int(float(pos))
                        variant_id = build_variant_id(
                            chr, pos, ref, alt, 'GRCh38'
                        )

                        if self.label == 'asb':
                            # create edges in variants_proteins regardless of cell type
                            # the redundance will be resolved when importing into arangodb
                            _key = variant_id + '_' + tf_uniprot_id
                            _from = 'variants/' + variant_id
                            _to = 'proteins/' + tf_uniprot_id

                            props = {
                                '_key': _key,
                                '_from': _from,
                                '_to': _to,
                                'chr': chr,
                                'rsid': rsid,
                                'motif_fc': row[18],
                                'motif_pos': row[19],
                                'motif_orient': row[20],
                                'motif_conc': row[21],
                                'motif': 'motifs/' + tf_name + '_' + ASB.MOTIF_SOURCE,
                                'source': ASB.SOURCE,
                                'label': 'allele-specific binding',
                                'name': 'modulates binding of',
                                'inverse_name': 'binding modulated by',
                                'biological_process': 'ontology_terms/GO_0051101'
                            }

                        elif self.label == 'asb_cell_ontology':
                            _key = variant_id + '_' + tf_uniprot_id + '_' + cell_name
                            _from = 'variants_proteins/' + variant_id + \
                                '_' + tf_uniprot_id
                            _to = 'ontology_terms/' + cell_ontology_id  # check format, underscored

                            props = {
                                '_key': _key,
                                '_from': _from,
                                '_to': _to,
                                'es_mean_ref': row[10],
                                'es_mean_alt': row[11],
                                'fdrp_bh_ref': row[13],
                                'fdrp_bh_alt': row[15],
                                'biological_context': cell_gtrd_name,
                                'source_url': 'http://gtrd.biouml.org/#!table/gtrd_current.cells/Details/ID=' + cell_gtrd_id
                            }

                        json.dump(props, parsed_data_file)
                        parsed_data_file.write('\n')

        parsed_data_file.close()
        self.save_to_arango()

    def save_to_arango(self):
        if self.dry_run:
            print(self.arangodb()[0])
        else:
            os.system(self.arangodb()[0])

    def arangodb(self):
        return ArangoDB().generate_json_import_statement(self.output_filepath, self.collection, type=self.type)
