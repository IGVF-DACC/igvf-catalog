import os
import json
import csv
import re

from db.arango_db import ArangoDB
from adapters import Adapter
from adapters.helpers import build_variant_id_from_hgvs
from collections import defaultdict
## description on files ##


class PharmGKB(Adapter):
    SOURCE = 'pharmGKB'
    SOURCE_URL_PREFIX = 'https://www.pharmgkb.org/'
    DRUG_ID_MAPPING_PATH = './data_loading_support_files/pharmGKB_chemicals.tsv'
    VARIANT_ID_MAPPING_PATH = './data_loading_support_files/pharmGKB_variants.tsv'
    STUDY_PARAMETERS_MAPPING_PATH = './data_loading_support_files/pharmGKB_study_parameters.tsv'
    # The first 11 columns are same across three variant annotation files
    VAR_ANNO_FILE_INDEX = {
        'var_drug': {'multiple_drugs': 16, 'alleles': 9, 'Comparison_alleles': 20},
        'var_pheno': {'multiple_drugs': 17, 'alleles': 9, 'Comparison_alleles': 23},
        'var_fa': {'multiple_drugs': 19, 'alleles': 9, 'Comparison_alleles': 21}
    }

    SKIP_BIOCYPHER = True
    OUTPUT_PATH = './parsed-data'

    def __init__(self, filepath, type='node', dry_run=True):
        self.filepath = filepath
        self.type = type
        self.dry_run = dry_run
        if type == 'node':
            self.dataset = 'drug'
        else:
            self.dataset = 'variant_drug'

        self.output_filepath = '{}/{}_{}.json'.format(
            PharmGKB.OUTPUT_PATH,
            self.dataset,
            PharmGKB.SOURCE
        )

        super(PharmGKB, self).__init__()

    def process_file(self):
        self.parsed_data_file = open(self.output_filepath, 'w')

        if self.type == 'node':
            with open(PharmGKB.DRUG_ID_MAPPING_PATH, 'r') as drug_file:
                drug_csv = csv.reader(drug_file, delimiter='\t')
                next(drug_csv)
                for drug_row in drug_csv:
                    _key = drug_row[0]
                    drug_name = drug_row[1]
                    xrefs = drug_row[6].split(',')
                    drug_ontology_terms = []
                    for xref in xrefs:
                        # only load ontology terms from Chebi for now
                        if xref.startswith('ChEBI:'):
                            drug_ontology_terms.append(
                                xref.replace('ChEBI:CHEBI:', 'CHEBI_'))

                    props = {
                        '_key': _key,
                        'drug_name': drug_name,
                        'drug_ontology_terms': ['ontology_terms/' + term for term in drug_ontology_terms],
                        'source': PharmGKB.SOURCE,
                        'source_url': PharmGKB.SOURCE_URL_PREFIX + 'chemical/' + _key
                    }

                    self.save_props(props)

            self.parsed_data_file.close()
            self.save_to_arango()

        else:
            self.load_drug_id_mapping()
            self.load_variant_id_mapping()
            self.load_study_paramters_mapping()
            # one variant can be in multiple rows, save those converted variant ids to speed up
            variant_hgvs_id_converted = {}
            for filename in os.listdir(self.filepath):
                if filename.startswith('var_drug'):
                    # if filename.startswith('var_'):
                    file_prefix = '_'.join(filename.split('_')[:2])
                    print('Loading:' + filename)
                    with open(self.filepath + '/' + filename, 'r') as variant_drug_file:
                        variant_drug_csv = csv.reader(
                            variant_drug_file, delimiter='\t')
                        next(variant_drug_csv)
                        for variant_drug_row in variant_drug_csv:
                            variant_name = variant_drug_row[1]
                            # ignore haplotypes like CYP3A4*1, CYP3A4*17, only consider those with rsIDs
                            if not variant_name.startswith('rs'):
                                continue
                            # variant info
                            variant_anno_id = variant_drug_row[0]
                            variant_name = variant_drug_row[1]
                            variant_hgvs_ids = self.variant_id_mapping.get(
                                variant_name)
                            if variant_hgvs_ids is None:
                                print(variant_name +
                                      ' has no matched variant id.')
                                continue
                            else:
                                if len(variant_hgvs_ids) > 1:
                                    print('multiple allele cases: ' +
                                          variant_name + ','.join(variant_hgvs_ids))
                                    ### add multiple alleles checking part! ###
                                    continue
                                else:
                                    if variant_hgvs_id_converted.get(variant_hgvs_ids[0]) is None:
                                        variant_id = build_variant_id_from_hgvs(
                                            variant_hgvs_ids[0])
                                        variant_hgvs_id_converted[variant_hgvs_ids[0]
                                                                  ] = variant_id

                                    else:
                                        variant_id = variant_hgvs_id_converted[variant_hgvs_ids[0]]

                                    if variant_id is None:
                                        print(variant_name +
                                              ' failed converting hgvs id.')
                                        continue

                            # study info
                            study_info = self.study_paramters_mapping.get(
                                variant_anno_id)
                            if study_info is None:
                                print(variant_anno_id +
                                      ' has no matched study info.')
                                continue

                            # drug info
                            # had to map drug IDs from drug names, which is error-prone

                            # each row can be associated to multiple drugs, split by ', '
                            # while ', ' can also be in part of a single drug name, e.g. PA10390: sulfonamides, urea derivatives

                            # the multiple_drugs_flag on column 17 indicates if the association applies to each drug individually or in combination
                            # but it is sometimes incorrect
                            # -> equals to 'and' when there's a single drug in column 4, or empty when there are multiple drugs

                            drug_ids = []
                            if not variant_drug_row[3]:
                                continue
                            # add and/or logic?
                            multiple_drugs_flag = variant_drug_row[PharmGKB.VAR_ANNO_FILE_INDEX[file_prefix].get(
                                'multiple_drugs')]

                            if multiple_drugs_flag and ', ' in variant_drug_row[3]:
                                # retrieve drug names for rows with double quotes
                                # e.g. '"interferon alfa-2a, recombinant", "interferon alfa-2b, recombinant", "ribavirin"'
                                drug_names = [d.replace('"', '') for d in re.findall(
                                    "(\\\".*?\\\")", variant_drug_row[3])]
                                # otherwise, no double quotes just split by ', '
                                if not drug_names:
                                    drug_names = variant_drug_row[3].split(
                                        ', ')
                                for drug_name in drug_names:
                                    drug_id = self.drug_id_mapping.get(
                                        drug_name)
                                    if drug_id is None:
                                        print(drug_name +
                                              ' has no matched drug id.')
                                    else:
                                        drug_ids.append(drug_id)
                            else:
                                drug_name = variant_drug_row[3]
                                drug_id = self.drug_id_mapping.get(drug_name)
                                if drug_id is not None:
                                    drug_ids.append(drug_id)
                                elif ', ' in drug_name:  # try split the drug names by comma, for cases with likely mis-labeled multiple_drugs_flag
                                    drug_names = drug_names.split(', ')
                                    for drug_name in drug_names:
                                        drug_id = self.drug_id_mapping.get(
                                            drug_name)
                                        if drug_id is None:
                                            print(drug_name +
                                                  ' has no matched drug id.')
                                        else:
                                            drug_ids.append(drug_id)

                            if len(drug_ids) == 0:
                                continue
                            else:
                                for drug_id in drug_ids:
                                    edge_key = variant_anno_id + '_' + drug_id
                                    _from = 'variants/' + variant_id
                                    _to = 'drugs/' + drug_id
                                    props = {
                                        '_key': edge_key,
                                        '_from': _from,
                                        '_to': _to,
                                        'gene': variant_drug_row[2],
                                        'pmid': variant_drug_row[4],
                                        'study_parameter_id': study_info['study_parameter_id'],
                                        'p_value': study_info['p_value'],
                                        'study_cases': study_info['study_cases'],
                                        'biogeographical_groups': study_info['biogeographical_groups'],
                                        'phenotype_categories': variant_drug_row[5].split(','),
                                        'source': PharmGKB.SOURCE,
                                        'source_url': PharmGKB.SOURCE_URL_PREFIX + 'variantAnnotation/' + variant_anno_id
                                    }

                                    self.save_props(props)

            self.parsed_data_file.close()
            self.save_to_arango()

    def load_drug_id_mapping(self):
        # e.g. key: '17-alpha-dihydroequilenin sulfate', value: 'PA166238901'
        self.drug_id_mapping = {}
        with open(PharmGKB.DRUG_ID_MAPPING_PATH, 'r') as drug_id_mapfile:
            next(drug_id_mapfile)
            for line in drug_id_mapfile:
                drug_row = line.strip('\n').split('\t')
                self.drug_id_mapping[drug_row[1]] = drug_row[0]

    def load_variant_id_mapping(self):
        # e.g. key: 'rs1000002', value: 'NC_000003.12:g.183917980C>T'
        self.variant_id_mapping = {}
        with open(PharmGKB.VARIANT_ID_MAPPING_PATH, 'r') as variant_id_mapfile:
            next(variant_id_mapfile)
            for line in variant_id_mapfile:
                variant_row = line.strip('\n').split('\t')
                # i.e. dbSNP id, which is unique for each row
                variant_name = variant_row[1]
                # no ref/alt allele in this column, need to match with ids in synonyms
                if ':' not in variant_row[4]:
                    print('no position info for variant:' + variant_name)
                    continue
                position_str = variant_row[4].split(
                    ':')[0] + ':g.' + variant_row[4].split(':')[1]
                synonyms = variant_row[-1].split(', ')
                variant_ids = []
                for synonym in synonyms:
                    # might miss some del/ins variants
                    if synonym.startswith(position_str):
                        if '=' not in synonym:  # no alt allele info in ref ids like NC_000003.12:g.183917980=
                            variant_ids.append(synonym)

                if len(variant_ids) < 1:
                    # print(variant_name + ' has no hgvs id.')
                    continue
                # elif len(variant_ids) > 1:
                    #print(variant_name + ' has multipe hgvs ids.')

                # multiple ids for variants with multiple alternative alleles
                self.variant_id_mapping[variant_name] = variant_ids

    def load_study_paramters_mapping(self):
        self.study_paramters_mapping = defaultdict(
            lambda: defaultdict(list))  # key: variant annotation ID
        # each variant annotation entry (from one publication though) can have multiple study parameter sets
        with open(PharmGKB.STUDY_PARAMETERS_MAPPING_PATH, 'r') as study_mapfile:
            next(study_mapfile)
            for line in study_mapfile:
                study_row = line.strip('\n').split('\t')
                variant_anno_id = study_row[1]
                # don't know why split is not working when last few columns are empty...
                if len(study_row) < 17:
                    self.study_paramters_mapping[variant_anno_id]['p_value'].append(
                        '')
                else:
                    self.study_paramters_mapping[variant_anno_id]['p_value'].append(
                        study_row[11])

                self.study_paramters_mapping[variant_anno_id]['study_parameter_id'].append(
                    study_row[0])
                self.study_paramters_mapping[variant_anno_id]['study_cases'].append(
                    study_row[3])
                self.study_paramters_mapping[variant_anno_id]['biogeographical_groups'].append(
                    study_row[-1])

    def save_props(self, props):
        json.dump(props, self.parsed_data_file)
        self.parsed_data_file.write('\n')

    def save_to_arango(self):
        if self.dry_run:
            print(self.arangodb()[0])
        else:
            os.system(self.arangodb()[0])

    def arangodb(self):
        return ArangoDB().generate_json_import_statement(self.output_filepath, self.collection, type=self.type)
