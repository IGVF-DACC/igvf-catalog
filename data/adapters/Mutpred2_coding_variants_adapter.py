import gzip
import json
import csv
import os
import re
from typing import Optional

from adapters.base import BaseAdapter
from adapters.helpers import convert_aa_letter_code_and_Met1, convert_aa_to_three_letter, split_spdi, build_variant_coding_variant_key
from adapters.file_fileset_adapter import FileFileSet
from adapters.writer import Writer

# The mapping from a given amino acid change to all possible genetic variants is done via scripts under data/data_loading_support_files/
# run_parallel_mapping_mutpred2.py calls mapping function from enumerate_coding_variants_all_mappings.py to generate a tsv file mutpred2_IGVFFI6893ZOAA_mappings.tsv.gz,
# which was uploaded to s3 bucket s3://igvf-catalog-parsed-collections/coding_variants_enumerated_mappings/

# Example lines from mapping file mutpred2_IGVFFI6893ZOAA_mappings.tsv.gz
# Note the scores (passed threshold) from original data file IGVFFI6893ZOAA.tsv.gz are appended to the last columns, so coding_variants_phenotypes edges can also be loaded from this intermediate file
# ENST00000261590.13	Q873T	DSG2_ENST00000261590.13_p.Q873T_c.2617_2618delinsAC,DSG2_ENST00000261590.13_p.Q873T_c.2617_2619delinsACC,DSG2_ENST00000261590.13_p.Q873T_c.2617_2619delinsACG,DSG2_ENST00000261590.13_p.Q873T_c.2617_2619delinsACT	c.2617_2618delinsAC,c.2617_2619delinsACC,c.2617_2619delinsACG,c.2617_2619delinsACT	\
# NC_000018.10:31546002:CA:AC,NC_000018.10:31546002:CAA:ACC,NC_000018.10:31546002:CAA:ACG,NC_000018.10:31546002:CAA:ACT	NC_000018.10:g.31546003_31546004delinsAC,NC_000018.10:g.31546003_31546005delinsACC,NC_000018.10:g.31546003_31546005delinsACG,NC_000018.10:g.31546003_31546005delinsACT	ACA,ACC,ACG,ACT	1,1,1,1	CAA	ENSP00000261590.8	DSG2_HUMAN \
# 0.279	[{"Property": "Strand", "Posterior Probability": 0.2812593867, "P-value": 0.0075985251, "Affected Position": "-", "Type": "Loss"}, {"Property": "Loop", "Posterior Probability": 0.2645830283, "P-value": 0.0486695275, "Affected Position": "-", "Type": "Loss"}]

# Example lines from original data file IGVFFI6893ZOAA.tsv.gz
# protein_id	transcript_id	gene_id	gene_symbol	Substitution	MutPred2 score	Mechanisms
# ENSP00000261590.8	ENST00000261590.13	ENSG00000046604.15	DSG2	Q873T	0.279	"[{""Property"": ""VSL2B_disorder"", ""Posterior Probability"": 0.137758575, ""P-value"": 0.4708942392, ""Effected Position"": ""S869"", ""Type"": ""Loss""},
# {""Property"": ""B_factor"", ""Posterior Probability"": 0.155336153, ""P-value"": 0.5798113033, ""Effected Position"": ""S878"", ""Type"": ""Gain""}, {""Property"": ""Surface_accessibility"", ...,
# {""Property"": ""Stability"", ""Posterior Probability"": 0.0077869674, ""P-value"": 0.6356068835, ""Effected Position"": ""-"", ""Type"": ""Loss""}]"


class Mutpred2CodingVariantsScores(BaseAdapter):
    ALLOWED_LABELS = ['coding_variants', 'variants',
                      'variants_coding_variants', 'coding_variants_phenotypes']
    SOURCE = 'IGVF'
    # all collections will be parsed from this intermediate file
    MAPPING_FILE = 'mutpred2_IGVFFI6893ZOAA_mappings.tsv.gz'
    MAPPING_FILE_HEADER = ['transcript_id', 'aa_change', 'mutation_ids', 'hgvsc_ids', 'spdi_ids',
                           'hgvsg_ids', 'alt_codons', 'codon_positions', 'codon_ref', 'protein_id', 'protein_name', 'Mutpred2 score', 'Mechanisms']
    PHENOTYPE_TERM = 'GO_0003674'  # Molecular Function
    FILE_ACCESSION = 'IGVFFI6893ZOAA'
    PHENOTYPE_EDGE_NAME = 'mutational effect'
    PHENOTYPE_EDGE_INVERSE_NAME = 'altered due to mutation'

    def __init__(self, filepath=None, label='coding_variants', writer: Optional[Writer] = None, validate=False, **kwargs):
        self.source_url = 'https://data.igvf.org/tabular-files/' + self.FILE_ACCESSION
        self.files_filesets = FileFileSet(self.FILE_ACCESSION)

        super().__init__(filepath, label, writer, validate)

    def _get_schema_type(self):
        """Return schema type based on label."""
        if self.label in ['coding_variants', 'variants']:
            return 'nodes'
        else:
            return 'edges'

    def _get_collection_name(self):
        """Get collection based on label."""
        if self.label == 'coding_variants':
            return 'coding_variants'
        elif self.label == 'variants':
            return 'variants'
        elif self.label == 'variants_coding_variants':
            return 'variants_coding_variants'
        elif self.label == 'coding_variants_phenotypes':
            return 'coding_variants_phenotypes'

    def process_file(self):
        self.writer.open()
        # write all enumerated variants to jsonl files for variants, and variants_coding_variants collections
        # skip checking if they are already loaded since there are > 1,000 million records to check here, will deduplicate when loading them into database
        if self.label == 'coding_variants_phenotypes':
            self.igvf_metadata_props = self.files_filesets.query_fileset_files_props_igvf(
                self.FILE_ACCESSION)[0]
        with gzip.open(self.MAPPING_FILE, 'rt') as map_file:
            map_csv = csv.DictReader(
                map_file, delimiter='\t', fieldnames=self.MAPPING_FILE_HEADER)
            for row in map_csv:
                # trim version number in ENST
                mutation_ids = [
                    re.sub(r'(ENST\d+)\.\d+', r'\1', id) for id in row['mutation_ids'].split(',')]
                coding_variant_ids = [convert_aa_letter_code_and_Met1(
                    mutation_id) for mutation_id in mutation_ids]
                variant_ids = row['spdi_ids'].split(',')
                if self.label == 'variants_coding_variants':
                    for coding_variant_id, variant_id in zip(coding_variant_ids, variant_ids):
                        chr, pos, ref, alt = split_spdi(variant_id)
                        _props = {
                            '_key': build_variant_coding_variant_key(variant_id, coding_variant_id),
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
                        if self.validate:
                            self.validate_doc(_props)
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
                            'variation_type': 'SNP' if len(ref) == 1 else 'deletion-insertion',
                            'spdi': variant_id,
                            'hgvs': hgvsg,
                            'organism': 'Homo sapiens',
                            'source': self.SOURCE,
                            'source_url': self.source_url
                        }
                        if self.validate:
                            self.validate_doc(_props)
                        self.writer.write(json.dumps(_props))
                        self.writer.write('\n')
                elif self.label == 'coding_variants':
                    for i, coding_variant_id in enumerate(coding_variant_ids):
                        matches = re.findall(
                            r'^([A-Za-z]+)(\d+)([A-Za-z]+)', row['aa_change'])
                        aa_ref, aa_pos, aa_alt = matches[0]
                        aa_change = convert_aa_to_three_letter(
                            row['aa_change'])
                        if aa_change.startswith('Met1'):
                            aa_change = 'Met1?'  # to match with dbNSFP
                        _props = {
                            '_key': coding_variant_id,
                            'name': coding_variant_id,
                            'ref': aa_ref,
                            'alt': aa_alt,
                            'aapos': int(aa_pos),
                            'refcodon': row['codon_ref'],
                            'gene_name': coding_variant_id.split('_')[0],
                            'protein_id': row['protein_id'].split('.')[0],
                            'protein_name': row['protein_name'],
                            'codonpos': int(row['codon_positions'].split(',')[i]),
                            'hgvsc': row['hgvsc_ids'].split(',')[i].replace('-', '>'),
                            'hgvsp': 'p.' + aa_change,
                            'transcript_id': row['transcript_id'].split('.')[0],
                            'source': self.SOURCE,
                            'source_url': self.source_url,
                        }
                        if self.validate:
                            self.validate_doc(_props)
                        self.writer.write(json.dumps(_props))
                        self.writer.write('\n')
                elif self.label == 'coding_variants_phenotypes':
                    # already did filtering on scores when generating the mapping file: retain predicted mechanisms with Pr >= 0.25 & Pval < 0.05
                    mechanism_props = json.loads(row['Mechanisms'])
                    for coding_variant_id in coding_variant_ids:
                        _props = {
                            '_key': '_'.join([coding_variant_id, self.PHENOTYPE_TERM, self.FILE_ACCESSION]),
                            '_from': 'coding_variants/' + coding_variant_id,
                            '_to': 'ontology_terms/' + self.PHENOTYPE_TERM,
                            'name': self.PHENOTYPE_EDGE_NAME,
                            'inverse_name': self.PHENOTYPE_EDGE_INVERSE_NAME,
                            'pathogenicity_score': float(row['Mutpred2 score']),
                            'property_scores': mechanism_props,  # property scores passing threshold
                            'files_filesets': 'files_filesets/' + self.FILE_ACCESSION,
                            'method': self.igvf_metadata_props.get('method'),
                            'source': self.SOURCE,
                            'source_url': self.source_url
                        }
                        if self.validate:
                            self.validate_doc(_props)
                        self.writer.write(json.dumps(_props))
                        self.writer.write('\n')
        self.writer.close()
