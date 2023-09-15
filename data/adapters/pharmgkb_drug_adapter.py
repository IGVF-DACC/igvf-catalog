import os
import json
import csv
import re

from db.arango_db import ArangoDB
from adapters import Adapter
from adapters.helpers import build_variant_id_from_hgvs
from collections import defaultdict

# Variant Annotation files downloaded from https://www.pharmgkb.org/downloads
# Split into three files with most columns in common

# variantAnnotations/var_drug_ann.tsv
# Variant Annotation ID	Variant/Haplotypes	Gene	Drug(s)	PMID	Phenotype Category	Significance	Notes	Sentence	Alleles	Specialty Population	Metabolizer types	isPlural	Is/Is Not associated	Direction of effect	PD/PK terms	Multiple drugs And/or	Population types	Population Phenotypes or diseases	Multiple phenotypes or diseases And/or	Comparison Allele(s) or Genotype(sComparison Metabolizer types
# 1451159680	rs5031016	CYP2A6	warfarin	22248286	Dosage	no	No association was found between this variant and warfarin-maintenance dose. Described as CYP2A6*7 in this study.	Allele G is not associated with increased dose of warfarin in people with an international normalized ratio (INR) of 2.0-3.0 as compared to allele A.	G			Is	Not associated with	increased	dose of		in people with	Other:an international normalized ratio (INR) of 2.0-3.0		A

# variantAnnotations/var_pheno_ann.tsv
# Variant Annotation ID	Variant/Haplotypes	Gene	Drug(s)	PMID	Phenotype Category	Significance	Notes	Sentence	Alleles	Specialty Population	Metabolizer types	isPlural	Is/Is Not associated	Direction of effect	Side effect/efficacy/other	Phenotype	Multiple phenotypes And/or	When treated with/exposed to/when assayed with	Multiple drugs And/or	Population types	Population Phenotypes or diseases	Multiple phenotypes or diseases And/or	Comparison Allele(s) or Genotype(s)	Comparison Metabolizer types
# 982022165	rs45607939	NAT2	sulfamethoxazole / trimethoprim	22850190	Toxicity	no	Minor allele frequencies were compared between cases (with drug-induced hypersensitivity) and controls.	Allele T is not associated with increased risk of Hypersensitivity when treated with sulfamethoxazole / trimethoprim in people with Infection.	T			Is	Not associated with	increased	risk of	Disease:Hypersensitivity		when treated with		in people with	Disease:Infection

# variantAnnotations/var_fa_ann.tsv
# Variant Annotation ID	Variant/Haplotypes	Gene	Drug(s)	PMID	Phenotype Category	Significance	Notes	Sentence	Alleles	Specialty Population	Assay type	Metabolizer types	isPlural	Is/Is Not associated	Direction of effect	Functional terms	Gene/gene product	When treated with/exposed to/when assayed with	Multiple drugs And/or	Cell type	Comparison Allele(s) or Genotype(sComparison Metabolizer types
# 1447990384	rs1065852	CYP2D6	bufuralol	2211621	Metabolism/PK	not stated	In vitro experiments showed a significant decrease in CYP2D6 activity for the variant construct expressed in COS-1 cells as compared to wild-type.	Allele A is associated with decreased activity of CYP2D6 when assayed with bufuralol in COS-1 cells as compared to allele G.	A				Is	Associated with	decreased	activity of	CYP2D6	when assayed with		in COS-1 cells	G
# Other files used from download page:
# variants.tsv: map variant rsID to variant hgvs name
# chemicals.tsv: map drug names to pharmGKB drug IDs (chemicals.tsv contains a larger set than drugs.tsv)
# variantAnnotations/study_parameters.tsv: map pmid to pharmGKB study IDs & parameter sets (each publication can map to multiple study IDs with different parameter sets)
# genes.tsv: map gene symbols to Ensembl IDs


class PharmGKB(Adapter):
    SOURCE = 'pharmGKB'
    SOURCE_URL_PREFIX = 'https://www.pharmgkb.org/'
    DRUG_ID_MAPPING_PATH = './data_loading_support_files/pharmGKB_chemicals.tsv'
    VARIANT_ID_MAPPING_PATH = './data_loading_support_files/pharmGKB_variants.tsv'
    STUDY_PARAMETERS_MAPPING_PATH = './data_loading_support_files/pharmGKB_study_parameters.tsv'
    GENE_ID_MAPPING_PATH = './data_loading_support_files/pharmGKB_genes.tsv'
    # The first 11 columns are same across three variant annotation files
    VAR_ANNO_FILE_INDEX = {
        'var_drug': {'multiple_drugs': 16, 'alleles': 9, 'comparison_alleles': 20},
        'var_pheno': {'multiple_drugs': 19, 'alleles': 9, 'comparison_alleles': 23},
        'var_fa': {'multiple_drugs': 19, 'alleles': 9, 'comparison_alleles': 21}
    }
    ALLOWED_LABELS = [
        'drug',
        'variant_drug',
        'variant_drug_gene',
    ]

    SKIP_BIOCYPHER = True
    OUTPUT_PATH = './parsed-data'

    def __init__(self, filepath, label, dry_run=True):
        if label not in PharmGKB.ALLOWED_LABELS:
            raise ValueError('Invalid label. Allowed values: ' +
                             ','.join(PharmGKB.ALLOWED_LABELS))

        self.filepath = filepath
        self.dry_run = dry_run
        self.dataset = label
        self.label = label
        if label == 'drug':
            self.type = 'node'
        else:
            self.type = 'edge'

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
            if self.label == 'variant_drug_gene':
                self.load_gene_id_mapping()
            # one variant can be in multiple rows, save those converted variant ids to speed up
            variant_hgvs_id_converted = {}
            for filename in os.listdir(self.filepath):
                if filename.startswith('var_'):
                    self.file_prefix = '_'.join(filename.split('_')[:2])
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
                                    # print('multiple allele cases: ' + variant_name + ','.join(variant_hgvs_ids))
                                    variant_hgvs_id = self.match_variant_alleles(
                                        variant_hgvs_ids, variant_drug_row)
                                    if variant_hgvs_id is None:
                                        print('no matched alleles for: ' +
                                              variant_name + '\t' + variant_anno_id)
                                        continue
                                else:
                                    variant_hgvs_id = variant_hgvs_ids[0]

                                if variant_hgvs_id_converted.get(variant_hgvs_id) is None:
                                    if '>' in variant_hgvs_id:
                                        variant_id = build_variant_id_from_hgvs(
                                            variant_hgvs_id, False)  # skip validate for simple snvs
                                    else:
                                        variant_id = build_variant_id_from_hgvs(
                                            variant_hgvs_id)
                                        #print ('validated: ' + variant_hgvs_ids[0], variant_name, + '\t' + variant_id)
                                    variant_hgvs_id_converted[variant_hgvs_id] = variant_id
                                else:
                                    variant_id = variant_hgvs_id_converted[variant_hgvs_id]

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
                            # gene info
                            # can be multiple genes split by ', ', or empty str for NA cases
                            gene_symbols = variant_drug_row[2].split(', ')
                            if self.label == 'variant_drug_gene':
                                if not variant_drug_row[2]:
                                    continue

                            # drug info
                            # had to map drug IDs from drug names, but it is error-prone

                            # each row can be associated to multiple drugs, split by ', '
                            # while ', ' can also be in part of a single drug name, e.g. PA10390: sulfonamides, urea derivatives

                            # the multiple_drugs_flag on column 17 indicates if the association applies to each drug individually or in combination
                            # but it is sometimes incorrect
                            # -> equals to 'and' when there's a single drug in column 4, or empty when there are multiple drugs

                            drug_ids = []
                            if not variant_drug_row[3]:
                                continue
                            # add and/or logic?
                            multiple_drugs_flag = variant_drug_row[PharmGKB.VAR_ANNO_FILE_INDEX[self.file_prefix].get(
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
                                    drug_names = drug_name.split(', ')
                                    for drug_name_split in drug_names:
                                        drug_id = self.drug_id_mapping.get(
                                            drug_name_split)
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

                                    if self.label == 'variant_drug':
                                        _from = 'variants/' + variant_id
                                        _to = 'drugs/' + drug_id
                                        props = {
                                            '_key': edge_key,
                                            '_from': _from,
                                            '_to': _to,
                                            'gene_symbol': gene_symbols,
                                            'pmid': variant_drug_row[4],
                                            'study_parameters': study_info,
                                            'phenotype_categories': variant_drug_row[5].split(','),
                                            'source': PharmGKB.SOURCE,
                                            'source_url': PharmGKB.SOURCE_URL_PREFIX + 'variantAnnotation/' + variant_anno_id
                                        }

                                        self.save_props(props)

                                    elif self.label == 'variant_drug_gene':

                                        for gene_symbol in gene_symbols:
                                            gene_id_str = self.gene_id_mapping.get(
                                                gene_symbol)
                                            if gene_id_str is None:
                                                print(gene_symbol +
                                                      ' has no matched gene id.')
                                            # take care of a few genes mapped to multiple Ensembl IDs
                                            # maybe should clear out those cases
                                            else:
                                                gene_ids = gene_id_str.split(
                                                    ', ')
                                                for gene_id in gene_ids:
                                                    _from = 'variants_drugs/' + edge_key
                                                    _to = 'genes/' + gene_id
                                                    second_edge_key = edge_key + '_' + gene_id
                                                    props = {
                                                        '_key': second_edge_key,
                                                        '_from': _from,
                                                        '_to': _to,
                                                        'gene_symbol': gene_symbol,
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

    def load_gene_id_mapping(self):
        # e.g. key: 'ABCB1', value: 'ENSG00000085563'
        # a few genes mapped to multiple Ensembl IDs, e.g. SLCO1B3 -> ENSG00000111700, ENSG00000257046
        self.gene_id_mapping = {}
        with open(PharmGKB.GENE_ID_MAPPING_PATH, 'r') as gene_id_mapfile:
            gene_id_csv = csv.reader(gene_id_mapfile, delimiter='\t')
            next(gene_id_csv)
            for gene_id_row in gene_id_csv:
                if gene_id_row[3]:
                    self.gene_id_mapping[gene_id_row[5]] = gene_id_row[3]

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
                    # print('no position info for variant:' + variant_name)
                    continue
                position_str = variant_row[4].split(
                    ':')[0] + ':g.' + variant_row[4].split(':')[1]
                synonyms = variant_row[-1].split(', ')
                variant_ids = []
                for synonym in synonyms:
                    # might miss some del/ins variants
                    if synonym.startswith(position_str):
                        if 'del' in synonym:
                            if synonym.split('del')[1]:
                                # rs72552763: NC_000006.12:g.160139851_160139853del, NC_000006.12:g.160139851_160139853delGAT are equivalent
                                synonym = synonym.split('del')[0] + 'del'

                        # no alt allele info in ref ids like NC_000003.12:g.183917980=
                        if '=' not in synonym and synonym not in variant_ids:
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
            list)  # key: variant annotation ID
        # each variant annotation entry (from one publication though) can have multiple study parameter sets
        with open(PharmGKB.STUDY_PARAMETERS_MAPPING_PATH, 'r') as study_mapfile:
            next(study_mapfile)
            for line in study_mapfile:
                study_row = line.strip('\n').split('\t')
                variant_anno_id = study_row[1]
                p_value = None
                # don't know why split is not working when last few columns are empty...
                if len(study_row) == 17:
                    p_value = study_row[11]

                self.study_paramters_mapping[variant_anno_id].append({
                    'study_parameter_id': study_row[0],
                    'study_type': study_row[2],
                    'study_cases': study_row[3],
                    'study_controls': study_row[4],
                    'p-value': p_value,
                    'biogeographical_groups': study_row[-1]
                })

    def match_variant_alleles(self, variant_hgvs_ids, variant_drug_row):
        # retrieve the studied alleles for variants with multiple alt alleles
        # alleles, comparison_alleles columns have mixed formats accross entries, e.g. # e.g. A; AA + GG; GG; ...
        # assuming each entry only studied single alt allele
        if '>' in variant_hgvs_ids[0]:  # multiple substitutions
            alleles = []
            all_alleles = variant_drug_row[PharmGKB.VAR_ANNO_FILE_INDEX[self.file_prefix]['alleles']] + \
                variant_drug_row[PharmGKB.VAR_ANNO_FILE_INDEX[self.file_prefix]
                                 ['comparison_alleles']]
            for allele in all_alleles:
                if allele in ['A', 'C', 'G', 'T'] and allele not in alleles:
                    alleles.append(allele)

            for variant_hgvs_id in variant_hgvs_ids:
                if variant_hgvs_id.split('>')[1] in alleles:
                    return variant_hgvs_id
        else:  # skip del/ins with multiple alleles for now
            pass
        return None

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
