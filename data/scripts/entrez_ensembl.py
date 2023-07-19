import pickle

# entrez_to_ensembl.pkl is used for coxpresdb data to link entrez gene id to ensembl id
# it is generated using those two files:
# gencode file: https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_43/gencode.v43.chr_patch_hapl_scaff.annotation.gtf.gz
# Homo_sapiens.gene_info.gz file: https://ftp.ncbi.nih.gov/gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz
# every gene has ensembl id in gencode file, every gene has hgnc id if available.
# every gene has entrez gene id in gene_info file, every gene has ensembl id or hgcn id if available
# In coxpresdb data total genes anotated are 16651. 16054 genes can be link to ensembl id.
gene_info_file_path = './scripts/Homo_sapiens.gene_info'
encode_filepath = 'scripts/gencode.v43.chr_patch_hapl_scaff.annotation.gtf'
output_path = './scripts/entrez_to_ensembl.pkl'

entrez_ensemble_dict = {}


def get_hgnc_dict_gencode():
    hgnc_dict_gencode = {}
    for line in open(encode_filepath, 'r'):
        if line.startswith('#'):
            continue
        data_line = line.strip().split()
        if data_line[2] == 'gene':
            ensembl_id = data_line[9][1:-2]
            ensembl_id_no_version = ensembl_id.split('.')[0]
            pair_line = data_line[8:]
            for key, value in zip(pair_line, pair_line[1:]):
                if key == 'hgnc_id':
                    hgnc_id = value.replace('"', '').replace(';', '')
                    hgnc_dict_gencode[hgnc_id] = ensembl_id_no_version
    return hgnc_dict_gencode


hgnc_dict_gencode = get_hgnc_dict_gencode()
with open(gene_info_file_path, 'r') as input:
    next(input)
    for line in input:
        (tax_id, gene_id, symbol, locus_tag, synonyms, dbxrefs, chromosome, map_location, description, type_of_gene, symbol_from_nomenclature_authority,
            full_name_from_nomenclature_authority, Nomenclature_status, Other_designations, Modification_date, Feature_type) = line.split('\t')

        split_dbxrefs = dbxrefs.split('|')
        hgnc = ''
        ensembl = ''
        for ref in split_dbxrefs:
            if ref.startswith('HGNC:'):
                hgnc = ref[5:]
            if ref.startswith('Ensembl:'):
                ensembl = ref[8:]
        if ensembl:
            entrez_ensemble_dict[gene_id] = ensembl
        elif hgnc and hgnc in hgnc_dict_gencode:
            ensembl = hgnc_dict_gencode[hgnc]
            entrez_ensemble_dict[gene_id] = ensembl
with open(output_path, 'wb') as f:
    pickle.dump(entrez_ensemble_dict, f)
