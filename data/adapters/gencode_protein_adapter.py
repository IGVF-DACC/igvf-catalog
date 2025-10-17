import gzip
import json
from typing import Optional
import pickle
import pdb
from Bio import SwissProt

from adapters.writer import Writer
from jsonschema import Draft202012Validator, ValidationError
from schemas.registry import get_schema

# Example genocde gtf input file row with protein_id
# ##description: evidence-based annotation of the human genome (GRCh38), version 43 (Ensembl 109)
# ##provider: GENCODE
# ##contact: gencode-help@ebi.ac.uk
# ##format: gtf
# ##date: 2022-11-29
# chr1	HAVANA	transcript	65419	71585	.	+	.	gene_id "ENSG00000186092.7"; transcript_id "ENST00000641515.2"; gene_type "protein_coding"; gene_name "OR4F5"; transcript_type "protein_coding"; transcript_name "OR4F5-201"; level 2; protein_id "ENSP00000493376.2"; hgnc_id "HGNC:14825"; tag "RNA_Seq_supported_partial"; tag "basic"; tag "Ensembl_canonical"; tag "MANE_Select"; tag "appris_principal_1"; havana_gene "OTTHUMG00000001094.4"; havana_transcript "OTTHUMT00000003223.4";
# chr1	HAVANA	transcript	450740	451678	.	-	.	gene_id "ENSG00000284733.2"; transcript_id "ENST00000426406.4"; gene_type "protein_coding"; gene_name "OR4F29"; transcript_type "protein_coding"; transcript_name "OR4F29-201"; level 2; protein_id "ENSP00000409316.1"; transcript_support_level "NA"; hgnc_id "HGNC:31275"; tag "basic"; tag "Ensembl_canonical"; tag "MANE_Select"; tag "appris_principal_1"; tag "CCDS"; ccdsid "CCDS72675.1"; havana_gene "OTTHUMG00000002860.3"; havana_transcript "OTTHUMT00000007999.3";


class GencodeProtein:

    ALLOWED_ORGANISMS = ['HUMAN', 'MOUSE']
    ALLOWED_LABELS = ['gencode_protein', 'gencode_translates_to']
    ALLOWED_KEYS = ['gene_id', 'gene_type', 'gene_name',
                    'transcript_id', 'transcript_type', 'transcript_name', 'protein_id']

    INDEX = {'chr': 0, 'type': 2, 'coord_start': 3, 'coord_end': 4, 'info': 8}

    def __init__(self, filepath=None, label='gencode_protein', uniprot_sprot_file_path=None, uniprot_trembl_file_path=None, organism='HUMAN', writer: Optional[Writer] = None, validate=False, **kwargs):

        self.filepath = filepath
        self.writer = writer
        self.uniprot_sprot_file_path = uniprot_sprot_file_path
        self.uniprot_trembl_file_path = uniprot_trembl_file_path
        self.label = label
        self.validate = validate
        if self.validate:
            if self.label == 'gencode_protein':
                self.schema = get_schema(
                    'nodes', 'proteins', self.__class__.__name__)
            elif self.label == 'gencode_translates_to':
                self.schema = get_schema(
                    'edges', 'transcripts_proteins', self.__class__.__name__)
            self.validator = Draft202012Validator(self.schema)

        if organism not in GencodeProtein.ALLOWED_ORGANISMS:
            raise ValueError('Invalid label. Allowed values: ' +
                             ','.join(GencodeProtein.ALLOWED_ORGANISMS))
        if label not in GencodeProtein.ALLOWED_LABELS:
            raise ValueError('Invalid label. Allowed values: ' +
                             ', '.join(GencodeProtein.ALLOWED_LABELS))
        if organism == 'HUMAN':
            self.version = 'v43'
            self.source_url = 'https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_43/gencode.v43.chr_patch_hapl_scaff.annotation.gtf.gz'
            self.ensembl_to_sprot_mapping_path = './data_loading_support_files/ensembl_to_uniprot/ENSP_to_uniprot_id_sprot_human.pkl'
            self.ensembl_to_trembl_mapping_path = './data_loading_support_files/ensembl_to_uniprot/ENSP_to_uniprot_id_trembl_human.pkl'
            self.organism = 'Homo sapiens'
            self.taxonomy_id = '9606'
            self.transcript_endpoint = 'transcripts/'
            self.chr_name_mapping_path = './data_loading_support_files/gencode/GCF_000001405.39_GRCh38.p13_assembly_report.txt'
        else:
            self.version = 'vM36'
            self.source_url = 'https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_mouse/release_M36/gencode.vM36.chr_patch_hapl_scaff.annotation.gtf.gz'
            self.ensembl_to_sprot_mapping_path = './data_loading_support_files/ensembl_to_uniprot/ENSP_to_uniprot_id_sprot_mouse.pkl'
            self.ensembl_to_trembl_mapping_path = './data_loading_support_files/ensembl_to_uniprot/ENSP_to_uniprot_id_trembl_mouse.pkl'
            self.chr_name_mapping_path = './data_loading_support_files/gencode/GCF_000001635.27_GRCm39_assembly_report.txt'
            self.organism = 'Mus musculus'
            self.transcript_endpoint = 'mm_transcripts/'
            self.taxonomy_id = '10090'

        self.load_chr_name_mapping()

    def validate_doc(self, doc):
        try:
            self.validator.validate(doc)
        except ValidationError as e:
            raise ValueError(f'Document validation failed: {e.message}')

    def parse_info_metadata(self, info):
        parsed_info = {}
        print(info)
        for key, value in zip(info, info[1:]):
            print(key, value)
            if key in GencodeProtein.ALLOWED_KEYS:
                parsed_info[key] = value.replace('"', '').replace(';', '')
            elif key == 'tag' and value == '"MANE_Select";':
                parsed_info['MANE_Select'] = True
        if 'MANE_Select' not in parsed_info:
            parsed_info['MANE_Select'] = False
        print(parsed_info)
        return parsed_info

    def get_dbxrefs(self, cross_references):
        dbxrefs = []
        for cross_reference in cross_references:
            database_name = cross_reference[0]
            if database_name == 'EMBL':
                for id in cross_reference[1:3]:
                    if id != '-':
                        dbxrefs.append({
                            'name': database_name,
                            'id': id
                        })
            # Ensembl cross references pregenerated in pkl file, skip it here
            elif database_name in ['RefSeq', 'MANE-Select']:
                for item in cross_reference[1:]:
                    if item != '-':
                        id = item.split('. ')[0]
                        dbxrefs.append({
                            'name': database_name,
                            'id': id
                        })
            else:
                dbxrefs.append({
                    'name': cross_reference[0],
                    'id': cross_reference[1]
                })
        dbxrefs.sort(key=lambda x: x['name'])
        return dbxrefs

    def get_full_name(self, description):
        rec_name = None
        description_list = description.split(';')
        for item in description_list:
            if item.startswith('RecName: Full=') or item.startswith('SubName: Full='):
                rec_name = item[14:]
                if ' {' in rec_name:
                    rec_name = rec_name[0: rec_name.index(' {')]
                break
        return rec_name

    def get_uniprot_xrefs(self, uniprot_file_path):
        # get full name and dbxrefs from uniprot dat file
        uniprot_dict = {}
        print('loading dbxrefs from ' + uniprot_file_path)
        with gzip.open(uniprot_file_path, 'rt') as uniprot_file:
            records = SwissProt.parse(uniprot_file)
            for record in records:
                if record.taxonomy_id == [self.taxonomy_id]:
                    uniprot_id = record.accessions[0]
                    dbxrefs = self.get_dbxrefs(record.cross_references)
                    full_name = self.get_full_name(record.description)
                    uniprot_json = {
                        'name': record.entry_name,
                        'dbxrefs': dbxrefs
                    }
                    if full_name:
                        uniprot_json['full_name'] = full_name
                    uniprot_dict[uniprot_id] = uniprot_json
        return uniprot_dict

    def load_chr_name_mapping(self):
        self.chr_name_mapping = {}
        with open(self.chr_name_mapping_path, 'r') as mapping_file:
            for row in mapping_file:
                if row.startswith('#'):
                    continue
                mapping_line = row.strip().split('\t')
                self.chr_name_mapping[mapping_line[4]] = mapping_line[-1]

    def process_file(self):
        self.writer.open()
        # first get ENSP -> uniprot id mapping pregenerated from uniprot dat files
        if self.label == 'gencode_protein':
            ensp_to_sprot_mapping = {}
            ensp_to_trembl_mapping = {}
            with open(self.ensembl_to_sprot_mapping_path, 'rb') as sprot_mapping_file:
                ensp_to_sprot_mapping = pickle.load(sprot_mapping_file)
            with open(self.ensembl_to_trembl_mapping_path, 'rb') as trembl_mapping_file:
                ensp_to_trembl_mapping = pickle.load(trembl_mapping_file)

            # get full name/name/dbxrefs from uniprot dat files
            uniprot_properties_sprot = self.get_uniprot_xrefs(
                self.uniprot_sprot_file_path)
            uniprot_properties_trembl = self.get_uniprot_xrefs(
                self.uniprot_trembl_file_path)

        for line in open(self.filepath, 'r'):
            if line.startswith('#'):
                continue
            split_line = line.strip().split()
            if split_line[GencodeProtein.INDEX['type']] == 'transcript':
                data = split_line[:GencodeProtein.INDEX['info']]
                info = self.parse_info_metadata(
                    split_line[GencodeProtein.INDEX['info']:])
                if 'protein_id' in info:
                    protein_id = info['protein_id']
                    id = protein_id.split('.')[0]
                    transcript_id = info['transcript_id'].split('.')[0]
                    # excluding the rows with no mapping to ucsc-style chromosome names or mapped chromosome name is 'na'
                    chr = data[GencodeProtein.INDEX['chr']]
                    if not chr.startswith('chr'):
                        if chr not in self.chr_name_mapping:
                            print(chr + ' does not have mapped chromosome name.')
                            continue
                    else:
                        if self.chr_name_mapping.get(chr) == 'na':
                            print(chr + ' has illegal mapped chromosome name.')
                            continue

                    if self.label == 'gencode_protein':
                        to_json = {
                            '_key': id,
                            'name': info['gene_name'],
                            'protein_id': protein_id,  # ENSP with version number
                            'MANE_Select': info['MANE_Select'],
                            'source': 'GENCODE',
                            'version': self.version,
                            'source_url': self.source_url,
                            'organism': self.organism
                        }
                        # prioritize sprot collection annotation: if the ENSP has mapping in both collections (sprot & trembl), use the one in sprot
                        if id in ensp_to_sprot_mapping:
                            # id can contain isoform number at the end, e.g. Q6UWL6-5
                            # checked for human proteins, each ENSP id only maps to one uniprot id within either sprot or trembl collection
                            # but mouse porteins have cases where one ENSP id maps to multiple uniprot ids within a collection
                            # so need to store mapped uniprot fields in arrays
                            uniprot_ids = ensp_to_sprot_mapping[id]
                            # merge dbxrefs lists from multiple uniprot entries
                            # dedupliate if there's overlapping dbxref across uniprot entries
                            dbxrefs_merged = []
                            for uniprot_id in uniprot_ids:
                                dbxrefs = uniprot_properties_sprot[uniprot_id.split(
                                    '-')[0]].get('dbxrefs', [])
                                if dbxrefs_merged:
                                    dbxrefs_merged_tuple = [
                                        tuple([d['name'], d['id']]) for d in dbxrefs_merged]
                                    for dbxref in dbxrefs:
                                        if tuple([dbxref['name'], dbxref['id']]) not in dbxrefs_merged_tuple:
                                            dbxrefs_merged.append(dbxref)
                                else:
                                    dbxrefs_merged = dbxrefs

                            to_json.update({
                                'uniprot_collection': 'Swiss-Prot',
                                'uniprot_ids': uniprot_ids,
                                'uniprot_names': [uniprot_properties_sprot[uniprot_id.split('-')[0]].get('name') for uniprot_id in uniprot_ids],
                                'dbxrefs': dbxrefs_merged,
                                'full_names': [uniprot_properties_sprot[uniprot_id.split('-')[0]].get('full_name') for uniprot_id in uniprot_ids]

                            })
                        elif id in ensp_to_trembl_mapping:
                            uniprot_ids = ensp_to_trembl_mapping[id]
                            dbxrefs_merged = []
                            for uniprot_id in uniprot_ids:
                                dbxrefs = uniprot_properties_trembl[uniprot_id.split(
                                    '-')[0]].get('dbxrefs', [])
                                if dbxrefs_merged:
                                    dbxrefs_merged_tuple = [
                                        tuple([d['name'], d['id']]) for d in dbxrefs_merged]
                                    for dbxref in dbxrefs:
                                        if tuple([dbxref['name'], dbxref['id']]) not in dbxrefs_merged_tuple:
                                            dbxrefs_merged.append(dbxref)
                            uniprot_ids = ensp_to_trembl_mapping[id]
                            to_json.update({
                                'uniprot_collection': 'TrEMBL',
                                'uniprot_ids': uniprot_ids,
                                'uniprot_names': [uniprot_properties_trembl[uniprot_id.split('-')[0]].get('name') for uniprot_id in uniprot_ids],
                                'dbxrefs': dbxrefs_merged,
                                'full_names': [uniprot_properties_trembl[uniprot_id.split('-')[0]].get('full_name') for uniprot_id in uniprot_ids]
                            })
                    else:
                        to_json = {
                            '_from': self.transcript_endpoint + transcript_id,
                            '_to': 'proteins/' + id,
                            'source': 'GENCODE',
                            'version': self.version,
                            'source_url': self.source_url,
                            'organism': self.organism,
                            'name': 'translates to',
                            'inverse_name': 'translated from',
                            'biological_process': 'ontology_terms/GO_0006412'
                        }

                    if self.validate:
                        self.validate_doc(to_json)

                    self.writer.write(json.dumps(to_json))
                    self.writer.write('\n')
        self.writer.close()
