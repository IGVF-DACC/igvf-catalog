from Bio import SwissProt
import pickle
import gzip

# generate pkl files containing mapping from ENSP ids to uniprot ids. The pkl files are used when loading proteins collection.


def get_ENSP_to_uniprot_mapping(filename, taxonomy_id):
    '''
    Generate a dict containing mapping from ENSP id to uniprot id from uniprotKB dat file.
    Returns:
        ENSP_to_uniprot (dict): key: ENSP id; value: list of uniprot ids (actually all ENSP within a dat file has only one mapping to a uniprot id)
    '''
    ENSP_to_uniprot = {}
    with gzip.open(filename, 'rt') as input_file:
        records = SwissProt.parse(input_file)
        for record in records:
            if record.taxonomy_id == [taxonomy_id]:
                uniprot_id = record.accessions[0]
                for cross_reference in record.cross_references:
                    database_name = cross_reference[0]
                    if database_name == 'Ensembl':
                        transcript_id, protein_id, gene_field = cross_reference[1:]
                        if len(gene_field.split('. ')) != 1:
                            gene_id = gene_field.split('. ')[0]
                            uniprot_id = gene_field.split('. ')[1].strip('[]')

                        protein_key = protein_id.split('.')[0]
                        if protein_key in ENSP_to_uniprot:
                            print(protein_key +
                                  ' has multiple uniprot id mappings')
                            ENSP_to_uniprot[protein_key].append(uniprot_id)
                        else:
                            ENSP_to_uniprot[protein_key] = [uniprot_id]
    return ENSP_to_uniprot


# human sprot
# wget https://api.data.igvf.org/reference-files/IGVFFI4731NANO/@@download/IGVFFI4731NANO.dat.gz
ENSP_to_uniprot_sprot = get_ENSP_to_uniprot_mapping(
    'IGVFFI4731NANO.dat.gz', '9606')

# human trembl
# wget https://api.data.igvf.org/reference-files/IGVFFI8551EYSR/@@download/IGVFFI8551EYSR.dat.gz
ENSP_to_uniprot_trembl = get_ENSP_to_uniprot_mapping(
    'IGVFFI8551EYSR.dat.gz', '9606')

# mouse sprot
# wget https://api.data.igvf.org/reference-files/IGVFFI3157HIUW/@@download/IGVFFI3157HIUW.dat.gz
ENSP_to_uniprot_sprot_mouse = get_ENSP_to_uniprot_mapping(
    'IGVFFI3157HIUW.dat.gz', '10090')

# mouse trembl
# wget https://api.data.igvf.org/reference-files/IGVFFI6972ORPG/@@download/IGVFFI6972ORPG.dat.gz
ENSP_to_uniprot_trembl_mouse = get_ENSP_to_uniprot_mapping(
    'IGVFFI6972ORPG.dat.gz', '10090')

# dump to pkl files
outfile = open('ENSP_to_uniprot_id_sprot_human.pkl', 'wb')
pickle.dump(ENSP_to_uniprot_sprot, outfile)
outfile.close()
outfile = open('ENSP_to_uniprot_id_trembl_human.pkl', 'wb')
pickle.dump(ENSP_to_uniprot_trembl, outfile)
outfile.close()
outfile = open('ENSP_to_uniprot_id_sprot_mouse.pkl', 'wb')
pickle.dump(ENSP_to_uniprot_sprot_mouse, outfile)
outfile.close()
outfile = open('ENSP_to_uniprot_id_trembl_mouse.pkl', 'wb')
pickle.dump(ENSP_to_uniprot_trembl_mouse, outfile)
outfile.close()
