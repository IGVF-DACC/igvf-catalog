import gzip
import json
import csv
import os
import re
from typing import Optional
from helpers import CHR_MAP, split_spdi
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
    SOURCE_URL = 'https://data.igvf.org/tabular-files/IGVFFI6893ZOAA/'
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

    def load_from_mapping_file(self):
        # write all enumerated variants to jsonl files for variants, and variants_coding_variants collections
        # skip checking if they are already loaded since there are > 1,000 million records to check here, will deduplicate when loading them into database
        ### add filter to skip SNVs? - they should already be loaded from dbNSFP ###
        with open(self.MAPPING_FILE, 'rt') as map_file:
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
                            'source_url': self.SOURCE_URL
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
                            'source_url': self.SOURCE_URL
                        }
                        self.writer.write(json.dumps(_props))
                        self.writer.write('\n')
                elif self.label == 'coding_variants':
                    matches = re.findall(
                        r'^([A-Za-z]+)(\d+)([A-Za-z]+)', row['aa_change'])
                    aa_ref, aa_pos, aa_alt = matches[0]
                    _props = {
                        '_key': coding_variant_id,
                        'ref': aa_ref,
                        'alt': aa_alt,
                        'aapos': int(aa_pos),
                        'gene_name': coding_variant_id.split('_')[0],
                        'protein_id': row['protein_id'].split('.')[0],
                        'protein_name': row['protein_name'],
                        # 'hgvsc': coding_variants_enumerated_ids['hgvsc_ids'][i],
                        'hgvsp': 'p.' + row['aa_change'],
                        # 'codonpos': row['codon_positions'][i],
                        'transcript_id': row['transcript_id'].split('.')[0],
                        'source': self.SOURCE,
                        'source_url': self.SOURCE_URL
                    }
                    for i, coding_variant_id in enumerate(coding_variant_ids):
                        _props.update(
                            {'hgvsc': row['hgvsc_ids'].split(',')[i]})
                        _props.update(
                            {'codonpos': row['codon_positions'].split(',')[i]})
                        _props.update(
                            {'codonpos': row['codon_ref'].split(',')[i]})

                        self.writer.write(json.dumps(_props))
                        self.writer.write('\n')
        self.writer.close()

    def process_file(self):
        self.writer.open()

        if self.label in ['variants_coding_variants', 'variants', 'coding_variants']:
            # load directly from mapping file
            self.load_from_mapping_file()
            return
        else:
            # only load rows passing threshold from data file
            with gzip.open(self.filepath, 'rt') as mutpred_file:
                mutpred_csv = csv.reader(mutpred_file, delimiter='\t')
                next(mutpred_csv)
                last_transcript = ''
                exons_coordinates = []
                for row in mutpred_csv:
                    protein_id, transcript_id, gene_id, gene_symbol, hgvsp, score, properties = row
                    # sanity check on protein, transcript, gene fields?
                    # file sorted by transcripts, skip querying exons coordinates if it's the same transcript as last row
                    if transcript_id != last_transcript:
                        exons_coordinates, chrom, chrom_refseq, strand = self.get_exon_coordinates(
                            transcript_id)
                        if chrom is None:
                            print(
                                'Failed to extract exon coordinates for: ' + transcript_id)
                            continue
                        last_transcript = transcript_id
                    # can't skip mapping to genome space for any collection, since coding variants needs hgvsc mapping in id
                    coding_variants_enumerated_ids = enumerate_coding_variants_ids.enumerate_coding_variant(
                        hgvsp, gene_symbol, transcript_id, strand, chrom, chrom_refseq, exons_coordinates, self.seq_reader)
                    if coding_variants_enumerated_ids is None:
                        continue
                    if self.label == 'coding_variants':
                        for i, mutation_id in enumerate(coding_variants_enumerated_ids['mutation_ids']):
                            _props = {
                                '_key': mutation_id,
                                'ref': coding_variants_enumerated_ids['ref_aa'],
                                'alt': coding_variants_enumerated_ids['alt_aa'],
                                'aapos': coding_variants_enumerated_ids['aa_pos'],
                                'gene_name': gene_symbol,
                                'protein_name': '',  # need mapping from ENSP to name here
                                'hgvs': coding_variants_enumerated_ids['hgvsc_ids'][i],
                                'hgvsp': coding_variants_enumerated_ids['hgvsp_id'],
                                'refcodon': coding_variants_enumerated_ids['codon_ref'],
                                # double check calculation on this, reverse strand,
                                'codonpos': coding_variants_enumerated_ids['codon_positions'][i],
                                'transcript_id': transcript_id.split('.')[0],
                                'source': self.SOURCE,
                                'source_url': self.SOURCE_URL
                            }
                            self.writer.write(json.dumps(_props))
                            self.writer.write('\n')

                    elif self.label == 'variants':
                        for i, spdi_id in enumerate(coding_variants_enumerated_ids['spdi_ids']):
                            # add necessary normalization on spdi?
                            # should also check if the enumertated variant is already loaded
                            _props = {
                                '_key': '',  # use functions
                                'name': spdi_id,
                                'pos': '',
                                'ref': '',
                                'alt': '',
                                'variation_type': '',
                                'spdi': spdi_id,
                                'hgvs': coding_variants_enumerated_ids['hgvsg_ids'][i],
                                'organism': 'Homo sapiens',
                                'source': self.SOURCE,
                                'source_url': self.SOURCE_URL
                            }
                            self.writer.write(json.dumps(_props))
                            self.writer.write('\n')

                    elif self.label == 'variants_coding_variants':
                        for i, mutation_id in enumerate(coding_variants_enumerated_ids['mutation_ids']):
                            _props = {
                                '_key': '',  # need coding variant id + variant id
                                '_from': 'variants/' + '',  # add variant id
                                '_to': 'coding_variants/' + mutation_id,
                                'name': 'codes for',
                                'inverse_name': 'encoded by',
                                'chr': '',
                                'pos': '',
                                'ref': '',
                                'alt': '',
                                'source': self.SOURCE,
                                'source_url': self.SOURCE_URL
                            }
                            self.writer.write(json.dumps(_props))
                            self.writer.write('\n')
                    elif self.label == 'coding_variants_phenotypes':
                        ### add some threshold here ###
                        for i, mutation_id in enumerate(coding_variants_enumerated_ids['mutation_ids']):
                            _props = {
                                '_key': mutation_id + self.PHENOTYPE_TERM + self.FILE_ACCESSION,
                                '_from': 'coding_variants/' + mutation_id,
                                '_to': 'ontology_terms/' + self.PHENOTYPE_TERM,
                                'pathogenicity_score': score,
                                'property_scores': properties,  # might need some filtering here
                                # should be only on data edges? (not all coding variants loaded from that file)
                                'files_filesets': 'files_filesets/' + self.FILE_ACCESSION
                            }
                            self.writer.write(json.dumps(_props))
                            self.writer.write('\n')
        self.writer.close()
