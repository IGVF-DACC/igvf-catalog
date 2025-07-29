import gzip
import json
import csv
import os
import re
from typing import Optional
from adapters.helpers import split_spdi
from adapters.file_fileset_adapter import FileFileSet

from adapters.writer import Writer

# The mapping from a given amino acid change to all possible genetic variants is done via scripts under data/data_loading_support_files/
# run_parallel_mapping_mutpred2.py calls mapping function from enumerate_coding_variants_all_mappings.py to generate a tsv file mutpred2_IGVFFI6893ZOAA_mappings.tsv.gz,
# which was uploaded to s3 bucket s3://igvf-catalog-parsed-collections/coding_variants_enumerated_mappings/

# Example lines from mapping file mutpred2_IGVFFI6893ZOAA_mappings.tsv.gz
# ENST00000261590.13	Q873T	DSG2_ENST00000261590.13_p.Q873T_c.2617_2618delinsAC,DSG2_ENST00000261590.13_p.Q873T_c.2617_2619delinsACC,DSG2_ENST00000261590.13_p.Q873T_c.2617_2619delinsACG,DSG2_ENST00000261590.13_p.Q873T_c.2617_2619delinsACT	c.2617_2618delinsAC,c.2617_2619delinsACC,c.2617_2619delinsACG,c.2617_2619delinsACT	\
# NC_000018.10:31546002:CA:AC,NC_000018.10:31546002:CAA:ACC,NC_000018.10:31546002:CAA:ACG,NC_000018.10:31546002:CAA:ACT	NC_000018.10:g.31546003_31546004delinsAC,NC_000018.10:g.31546003_31546005delinsACC,NC_000018.10:g.31546003_31546005delinsACG,NC_000018.10:g.31546003_31546005delinsACT	ACA,ACC,ACG,ACT	1,1,1,1	CAA	ENSP00000261590.8	DSG2_HUMAN

# Example lines from data file IGVFFI6893ZOAA.tsv.gz
# protein_id	transcript_id	gene_id	gene_symbol	Substitution	MutPred2 score	Mechanisms
# ENSP00000261590.8	ENST00000261590.13	ENSG00000046604.15	DSG2	Q873T	0.279	"[{""Property"": ""VSL2B_disorder"", ""Posterior Probability"": 0.137758575, ""P-value"": 0.4708942392, ""Effected Position"": ""S869"", ""Type"": ""Loss""},
# {""Property"": ""B_factor"", ""Posterior Probability"": 0.155336153, ""P-value"": 0.5798113033, ""Effected Position"": ""S878"", ""Type"": ""Gain""}, {""Property"": ""Surface_accessibility"", ...,
# {""Property"": ""Stability"", ""Posterior Probability"": 0.0077869674, ""P-value"": 0.6356068835, ""Effected Position"": ""-"", ""Type"": ""Loss""}]"


class Mutpred2CodingVariantsScores:
    ALLOWED_LABELs = ['coding_variants', 'variants',
                      'variants_coding_variants', 'coding_variants_phenotypes']
    SOURCE = 'IGVF'
    MAPPING_FILE = 'mutpred2_IGVFFI6893ZOAA_mappings.tsv.gz'
    MAPPING_FILE_HEADER = ['transcript_id', 'aa_change', 'mutation_ids', 'hgvsc_ids', 'spdi_ids',
                           'hgvsg_ids', 'alt_codons', 'codon_positions', 'codon_ref', 'protein_id', 'protein_name']
    PHENOTYPE_TERM = 'GO_0003674'  # Molecular Function

    def __init__(self, filepath=None, label='coding_variants', writer: Optional[Writer] = None, **kwargs):
        if label not in Mutpred2CodingVariantsScores.ALLOWED_LABELs:
            raise ValueError('Invalid label. Allowed values:' +
                             ','.join(Mutpred2CodingVariantsScores.ALLOWED_LABELs))

        self.filepath = filepath
        self.file_accession = os.path.basename(self.filepath).split('.')[0]
        self.source_url = 'https://data.igvf.org/tabular-files/' + self.file_accession
        self.writer = writer
        self.label = label
        self.files_filesets = FileFileSet(self.file_accession)

    def load_coding_variant_mapping(self):
        # load all mappings in a dict, to be used while parsing file for loading edges in coding_variants_phenotypes
        print('Loading coding variant mappings...')
        self.coding_variant_mapping = {}
        with gzip.open(self.MAPPING_FILE, 'rt') as map_file:
            map_csv = csv.DictReader(
                map_file, delimiter='\t', fieldnames=self.MAPPING_FILE_HEADER)
            for row in map_csv:
                # trim version number in ENST
                coding_variant_ids = [
                    re.sub(r'(ENST\d+)\.\d+', r'\1', id) for id in row['mutation_ids'].split(',')]
                self.coding_variant_mapping[row['transcript_id'] +
                                            '_' + row['aa_change']] = coding_variant_ids
        print('Coding variant mappings loaded.')

    def load_from_mapping_file(self):
        # write all enumerated variants to jsonl files for variants, and variants_coding_variants collections
        # skip checking if they are already loaded since there are > 1,000 million records to check here, will deduplicate when loading them into database
        ### add filter to skip SNVs? - they should already be loaded from dbNSFP ###
        with gzip.open(self.MAPPING_FILE, 'rt') as map_file:
            map_csv = csv.DictReader(
                map_file, delimiter='\t', fieldnames=self.MAPPING_FILE_HEADER)
            for row in map_csv:
                # trim version number in ENST
                coding_variant_ids = [
                    re.sub(r'(ENST\d+)\.\d+', r'\1', id) for id in row['mutation_ids'].split(',')]
                variant_ids = row['spdi_ids'].split(',')
                if self.label == 'variants_coding_variants':
                    for coding_variant_id, variant_id in zip(coding_variant_ids, variant_ids):
                        chr, pos, ref, alt = split_spdi(variant_id)
                        _props = {
                            '_key': variant_id + '_' + coding_variant_id,  # double check edge _key
                            '_from': 'variants/' + variant_id,
                            '_to': 'coding_variants/' + coding_variant_id,
                            'name': 'codes for',
                            'inverse_name': 'encoded by',
                            'chr': chr,
                            'pos': pos,  # 0-indexed
                            'ref': ref,
                            'alt': alt,
                            'source': self.SOURCE,
                            'source_url': self.source_url
                        }
                        self.writer.write(json.dumps(_props))
                        self.writer.write('\n')
                elif self.label == 'variants':
                    hgvsg_ids = row['hgvsg_ids'].split(',')
                    for variant_id, hgvsg in zip(variant_ids, hgvsg_ids):
                        chr, pos, ref, alt = split_spdi(variant_id)
                        _props = {
                            '_key': variant_id,  # don't have long spdi to convert
                            'name': variant_id,
                            'chr': chr,
                            'pos': pos,
                            'ref': ref,
                            'alt': alt,
                            'variation_type': 'SNP',
                            'spdi': variant_id,
                            'hgvs': hgvsg,
                            'organism': 'Homo sapiens',
                            'source': self.SOURCE,
                            'source_url': self.source_url
                        }
                        self.writer.write(json.dumps(_props))
                        self.writer.write('\n')
                elif self.label == 'coding_variants':
                    for coding_variant_id in coding_variant_ids:
                        matches = re.findall(
                            r'^([A-Za-z]+)(\d+)([A-Za-z]+)', row['aa_change'])
                        aa_ref, aa_pos, aa_alt = matches[0]
                        _props = {
                            '_key': coding_variant_id,
                            'ref': aa_ref,
                            'alt': aa_alt,
                            'aapos': int(aa_pos),
                            'refcodon': row['codon_ref'],
                            'gene_name': coding_variant_id.split('_')[0],
                            'protein_id': row['protein_id'].split('.')[0],
                            'protein_name': row['protein_name'],
                            'hgvsp': 'p.' + row['aa_change'],
                            'transcript_id': row['transcript_id'].split('.')[0],
                            'source': self.SOURCE,
                            'source_url': self.source_url
                        }
                        for i, coding_variant_id in enumerate(coding_variant_ids):
                            _props.update(
                                {'hgvsc': row['hgvsc_ids'].split(',')[i]})
                            _props.update(
                                {'codonpos': int(row['codon_positions'].split(',')[i])})

                            self.writer.write(json.dumps(_props))
                            self.writer.write('\n')
        self.writer.close()

    def process_file(self):
        self.writer.open()

        if self.label in ['variants_coding_variants', 'variants', 'coding_variants']:
            # load directly from mapping file
            self.load_from_mapping_file()
            return
        elif self.label == 'coding_variants_phenotypes':
            self.igvf_metadata_props = self.files_filesets.query_fileset_files_props_igvf(
                self.file_accession)[0]
            self.load_coding_variant_mapping()

            with gzip.open(self.filepath, 'rt') as mutpred_file:
                mutpred_csv = csv.reader(mutpred_file, delimiter='\t')
                next(mutpred_csv)
                for row in mutpred_csv:
                    mechanisms = json.loads(row[-1])
                    mechanism_prop = []
                    for m in mechanisms:
                        # only load rows with any mechanism has Pr >= 0.25 & Pval < 0.05
                        if m['Posterior Probability'] >= 0.25 and m['P-value'] < 0.05:
                            mechanism_prop.append(m)
                    if mechanism_prop:
                        mapping_key = row[1] + '_' + row[4]
                        if mapping_key not in self.coding_variant_mapping:
                            print(
                                f'Error: No mapped coding variant for {mapping_key}.')
                            continue
                        else:
                            mutation_ids = self.coding_variant_mapping[mapping_key]
                            for mutation_id in mutation_ids:
                                _props = {
                                    '_key': '_'.join([mutation_id, self.PHENOTYPE_TERM, self.file_accession]),
                                    '_from': 'coding_variants/' + mutation_id,
                                    '_to': 'ontology_terms/' + self.PHENOTYPE_TERM,
                                    'pathogenicity_score': float(row[-2]),
                                    'property_scores': mechanism_prop,  # property scores passing threshold
                                    'files_filesets': 'files_filesets/' + self.file_accession,
                                    'method': self.igvf_metadata_props.get('method')
                                }
                                self.writer.write(json.dumps(_props))
                                self.writer.write('\n')
        self.writer.close()
