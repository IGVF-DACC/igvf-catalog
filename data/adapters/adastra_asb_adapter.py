import csv
from adapters import Adapter
from adapters.helpers import build_variant_id

# Example ADASTRA allele-specific binding (ASB) file TF_name@cell_name.tsv (e.g. ATF1_HUMAN@HepG2__hepatoblastoma_.tsv):
# chr	pos	ID	ref	alt	repeat_type	mean_BAD	mean_SNP_per_segment	total_cover	n_aggregated	es_mean_ref	es_mean_altlogitp_ref	fdrp_bh_ref	logitp_alt	fdrp_bh_alt	motif_log_pref	motif_log_palt	motif_fc	motif_pos	motif_orient	motif_conc	novel
# chr11	129321262.0 rs10750410	A	G		1.25	518.5	73.0	2.0	-1.508200583122832	1.5220631227173078	0.9999438590195968	1.0	3.776801544248756e-06	0.0024711390339222	2.668977799202377	2.9239362481887974	0.8469536347168959	19	+	No Hit	False


class ASB(Adapter):
    # 1-based coordinate system

    DATASET = 'asb'

    def __init__(self, filepath, TF_uniprot_id, cell_name):
        self.filepath = filepath
        self.dataset = ASB.DATASET

        super(ASB, self).__init__()

    def get_TF_uniprot_id(self, mapfile='../samples/asb/ADASTRA_TF_uniprot_accession.tsv'):
        TF_name = self.filepath.split('@')[0]
        with open(mapfile, 'r') as TF_uniprot:
            TF_uniprot_csv = csv.reader(TF_uniprot, delimiter='\t')
            next(TF_uniprot_csv)
            for row in TF_uniprot_csv:
                if row[0] == TF_name:
                    return row[1]  # return uniprot id of the TF (i.e. protein)
        return None

    def get_cell_ontology_id(self, mapfile='../samples/asb/ADASTRA_cell_ontologies.tsv'):
        cell_name = self.filepath.split('@')[1].split('.')[0]
        ontology_priority_list = ['CL:', 'UBERON:', 'EFO:']
        with open(mapfile, 'r') as cell_ontology:
            cell_ontology_csv = csv.reader(cell_ontology, delimiter='\t')
            next(cell_ontology_csv)
            for row in cell_ontology_csv:
                if cell_name == row[2]:
                    # ontoloty ids from CL/CL0, UBERON, EFO in column 6,7,8
                    ontology_ids = row[5:8]
                    for collection in ontology_priority_list:
                        for ontology_id in ontology_ids:
                            if ontology_id.startswith(collection):
                                return ontology_id
        return None

    def process_file(self):
        TF_uniprot_id = self.get_TF_uniprot_id()
        cell_ontology_id = self.get_cell_ontology_id()
        if TF_uniprot_id is None:
            print('TF uniprot id unavailable, skipping: ' + self.filepath)
            return
        if cell_ontology_id is None:
            print('cell ontology id unavailable, skipping: ' + self.filepath)
            return

        with open(self.filepath, 'r') as asb:
            asb_csv = csv.reader(asb, delimiter='\t')

            next(asb_csv)

            for row in asb_csv:
                chr, pos, rsid, ref, alt = row[:5]
                # some files have decimal '.0' in position column
                pos = int(pos)
                variant_id = build_variant_id(
                    chr, pos, ref, alt, 'GRCh38'
                )

                try:
                    _id = variant_id + TF_uniprot_id + cell_ontology_id  # needs to change in future
                    _source = 'variants/' + variant_id
                    _target = 'proteins/' + TF_uniprot_id
                    label = 'asb'
                    _props = {
                        'chr': chr,
                        'rsid': rsid,
                        'biological_context': cell_ontology_id,
                        'es_mean_ref': row[10],  # es: effect size
                        'es_mean_alt': row[11],
                        'fdrp_bh_ref': row[13],
                        'fdrp_bh_alt': row[15],
                        'motif_fc': row[18],
                        'motif_pos': row[19],
                        'motif_orient': row[20],
                        'motif_conc': row[21]
                    }

                    yield(_id, _source, _target, label, _props)
                except:
                    print(row)
                    pass
