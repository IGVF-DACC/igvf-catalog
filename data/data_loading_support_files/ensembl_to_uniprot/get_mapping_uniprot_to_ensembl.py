from Bio import SwissProt
import pickle
import gzip

# generate a mapping for human (combining trembling & sprot collections) from uniprot id -> ENSP ids
# duplicated keys so we can use the output dict for both isoform-agnostic & isoform-specific queries
# e.g. 'P62258-1': ['ENSP00000264335', 'ENSP00000487356'],
# 'P62258-2': ['ENSP00000461762', 'ENSP00000481059'],
# 'P62258': ['ENSP00000264335', 'ENSP00000487356', 'ENSP00000461762', 'ENSP00000481059']
# ...


def get_uniprot_to_ENSP_mapping(sprot_filename, trembl_filename, taxonomy_id):
    uniprot_to_ENSP = {}
    ENSP_sprot_list = []
    # first get mapping from sprot dat file
    with gzip.open(sprot_filename, 'rt') as input_file:
        records = SwissProt.parse(input_file)
        for record in records:
            if record.taxonomy_id == [taxonomy_id]:
                uniprot_id = record.accessions[0]
                uniprot_to_ENSP[uniprot_id] = []
                for cross_reference in record.cross_references:
                    database_name = cross_reference[0]
                    if database_name == 'Ensembl':
                        transcript_id, protein_id, gene_field = cross_reference[1:]
                        protein_key = protein_id.split('.')[0]
                        ENSP_sprot_list.append(protein_id)
                        uniprot_to_ENSP[uniprot_id].append(protein_key)
                        if len(gene_field.split('. ')) != 1:
                            gene_id = gene_field.split('. ')[0]
                            uniprot_id_with_isoform = gene_field.split(
                                '. ')[1].strip('[]')  # with isoform number
                            if uniprot_id_with_isoform.split('-')[0] != uniprot_id:
                                print('ids not matching in isoform: ' +
                                      uniprot_id_with_isoform)
                            else:
                                if uniprot_id_with_isoform in uniprot_to_ENSP:
                                    uniprot_to_ENSP[uniprot_id_with_isoform].append(
                                        protein_key)
                                else:
                                    uniprot_to_ENSP[uniprot_id_with_isoform] = [
                                        protein_key]

    # then add trembling uniprot mappings - skip ENSP already having mapping in sprot file
    with gzip.open(trembl_filename, 'rt') as input_file:
        records = SwissProt.parse(input_file)
        for record in records:
            if record.taxonomy_id == [taxonomy_id]:
                uniprot_id = record.accessions[0]
                uniprot_to_ENSP[uniprot_id] = []
                for cross_reference in record.cross_references:
                    database_name = cross_reference[0]
                    if database_name == 'Ensembl':
                        transcript_id, protein_id, gene_field = cross_reference[1:]
                        protein_key = protein_id.split('.')[0]
                        if protein_key in ENSP_sprot_list:
                            continue
                        uniprot_to_ENSP[uniprot_id].append(protein_key)
                        if len(gene_field.split('. ')) != 1:
                            gene_id = gene_field.split('. ')[0]
                            uniprot_id_with_isoform = gene_field.split(
                                '. ')[1].strip('[]')  # with isoform number
                            if uniprot_id_with_isoform.split('-')[0] != uniprot_id:
                                print('ids not matching in isoform: ' +
                                      uniprot_id_with_isoform)
                            else:
                                if uniprot_id_with_isoform in uniprot_to_ENSP:
                                    uniprot_to_ENSP[uniprot_id_with_isoform].append(
                                        protein_key)
                                else:
                                    uniprot_to_ENSP[uniprot_id_with_isoform] = [
                                        protein_key]

    return uniprot_to_ENSP


# uniprot to ENSP mappings for human
uniprot_to_ENSP = get_uniprot_to_ENSP_mapping(
    'IGVFFI4731NANO.dat.gz', 'IGVFFI8551EYSR.dat.gz', '9606')
outfile = open('uniprot_to_ENSP_human.pkl', 'wb')
pickle.dump(uniprot_to_ENSP, outfile)
outfile.close()
# uniprot to ENSP mappings for mouse
outfile = open('uniprot_to_ENSP_mouse.pkl', 'wb')
pickle.dump(uniprot_to_ENSP_mouse, outfile)
outfile.close()
