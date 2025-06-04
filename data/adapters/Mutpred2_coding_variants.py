import gzip
import json
import csv
import boto3
import requests
import py2bit
from typing import Optional
from scripts.variants_spdi import CHR_MAP
import data_loading_support_files.enumerate_coding_variants_all_mappings as enumerate_coding_variants_ids

from adapters.writer import Writer
# Example lines from file IGVFFI6893ZOAA
# protein_id	transcript_id	gene_id	gene_symbol	Substitution	MutPred2 score	Mechanisms
# ENSP00000261590.8	ENST00000261590.13	ENSG00000046604.15	DSG2	Q873T	0.279	"[{""Property"": ""VSL2B_disorder"", ""Posterior Probability"": 0.137758575, ""P-value"": 0.4708942392, ""Effected Position"": ""S869"", ""Type"": ""Loss""},
# {""Property"": ""B_factor"", ""Posterior Probability"": 0.155336153, ""P-value"": 0.5798113033, ""Effected Position"": ""S878"", ""Type"": ""Gain""}, {""Property"": ""Surface_accessibility"", ...,
# {""Property"": ""Stability"", ""Posterior Probability"": 0.0077869674, ""P-value"": 0.6356068835, ""Effected Position"": ""-"", ""Type"": ""Loss""}]"


class Mutpred2CodingVariantsScores:
    ALLOWED_LABELs = ['mutpred2_coding_variants', 'mutpred2_enumerated_variants',
                      'mutpred2_coding_variants_variants', 'mutpred2_coding_variants_phenotypes']
    SOURCE = 'IGVF'
    SOURCE_URL = 'https://data.igvf.org/tabular-files/IGVFFI6893ZOAA/'
    GENOME_SEQUENCE_FILE = 'hg38.2bit'  # upload file
    FILE_ACCESSION = 'IGVFFI6893ZOAA'
    PHENOTYPE_TERM = ''

    def __init__(self, filepath=None, label='mutpred2_coding_variants', writer: Optional[Writer] = None, **kwargs):
        if label not in Mutpred2CodingVariantsScores.ALLOWED_LABELs:
            raise ValueError('Invalid label. Allowed values:' +
                             ','.join(Mutpred2CodingVariantsScores.ALLOWED_LABELs))

        self.filepath = filepath
        self.writer = writer
        self.label = label

    # get seq_reader from s3 right now
    # can upload to portal later -> need new enum for file format
    def read_sequence_file(self):
        self.seq_reader = None
        s3 = boto3.client('s3')
        # add check if the file is already existing
        bucket_name = ''
        object_key = ''
        destination_file = Mutpred2CodingVariantsScores.GENOME_SEQUENCE_FILE
        print(
            f'Downloading s3://{bucket_name}/{object_key} to {destination_file}')
        s3.download_file(bucket_name, object_key, destination_file)
        self.seq_reader = py2bit.open(
            Mutpred2CodingVariantsScores.GENOME_SEQUENCE_FILE)

    def get_exon_coordinates(self, transcript_id):
        transcript_id = transcript_id.split('.')[0]
        # double check limit
        query_url = f'https://api-dev.catalog.igvf.org/api/genes-structure?transcript_id={transcript_id}&organism=Homo%20sapiens&limit=1000'
        exons_coordinates = []
        chrom = None
        chrom_refseq = None
        strand = None
        try:
            responses = requests.get(query_url).json()
        # get gene structure from KG; the exon ranges are stored in bed format
            for structure in responses:
                if structure['type'] == 'CDS':
                    if structure['strand'] == '+':
                        exons_coordinates.extend(
                            list(range(structure['start'], structure['end'])))
                    else:  # on reverse strand
                        exons_coordinates.extend(
                            list(reversed(range(structure['start'], structure['end']))))
            chrom = responses[0]['chr']
            chrom_refseq = CHR_MAP['GRCh38'][chrom]
            strand = responses[0]['strand']
        except Exception as e:
            print(f'Error: {e}')

        return exons_coordinates, chrom, chrom_refseq, strand

    def process_file(self):
        self.writer.open()
        self.read_sequence_file()
        if self.seq_reader is None:
            print('Failed to read genome sequence file')
            return
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

                if self.label == 'mutpred2_coding_variants':
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

                elif self.label == 'mutpred2_enumerated_variants':
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

                elif self.label == 'mutpred2_coding_variants_variants':
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
                elif self.label == 'mutpred2_coding_variants_phenotypes':
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
        self.seq_reader.close()
