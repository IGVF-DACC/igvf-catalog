import gzip
import json
import csv
import os
import re
from typing import Optional
from adapters.helpers import AA_TABLE, split_spdi, build_variant_coding_variant_key
from adapters.file_fileset_adapter import FileFileSet

from adapters.writer import Writer

# works in similar way to mutpred2 adapter
# The mapping from a given amino acid change to all possible genetic variants is done via scripts under data/data_loading_support_files/
# run_parallel_mapping_ESM.py calls mapping function from enumerate_coding_variants_all_mappings.py to generate a tsv file ESM_1v_IGVFFI8105TNNO_mappings.tsv.gz,
# which was uploaded to s3 bucket s3://igvf-catalog-parsed-collections/coding_variants_enumerated_mappings/

# Example lines from mapping file ESM_1v_IGVFFI8105TNNO_mappings.tsv.gz
# Note the scores from original data file IGVFFI8105TNNO.tsv.gz are appended to the last columns, so coding_variants_phenotypes edges can also be loaded from this intermediate file
# ENST00000370460.7	p.Met1Ala	AFF2_ENST00000370460.7_p.Met1Ala_c.1_3delinsGCA,AFF2_ENST00000370460.7_p.Met1Ala_c.1_3delinsGCC,AFF2_ENST00000370460.7_p.Met1Ala_c.1_2delinsGC,AFF2_ENST00000370460.7_p.Met1Ala_c.1_3delinsGCT	c.1_3delinsGCA,c.1_3delinsGCC,c.1_2delinsGC,c.1_3delinsGCT	\
# NC_000023.11:148501097:ATG:GCA,NC_000023.11:148501097:ATG:GCC,NC_000023.11:148501097:AT:GC,NC_000023.11:148501097:ATG:GCT	NC_000023.11:g.148501098_148501100delinsGCA,NC_000023.11:g.148501098_148501100delinsGCC,NC_000023.11:g.148501098_148501099delinsGC,NC_000023.11:g.148501098_148501100delinsGCT \
# GCA,GCC,GCG,GCT	1,1,1,1	ATG	ENSP00000359489.2	AFF2_HUMAN  -5.354976177215576	-4.247730731964111	-5.950134754180908	-5.966752052307129	-5.39961051940918		-5.383840847015381

# Example lines from data file IGVFFI8105TNNO.tsv.gz
# GENCODE.v43.ENSG	GENCODE.v43.ENST	GENCODE.v43.ENSP	HGVS.p	esm1v_t33_650M_UR90S_1	esm1v_t33_650M_UR90S_2	esm1v_t33_650M_UR90S_3	esm1v_t33_650M_UR90S_4	esm1v_t33_650M_UR90S_5	esm1v_t33_650M_UR90S_1_next esm1v_t33_650M_UR90S_2_next	esm1v_t33_650M_UR90S_3_next	esm1v_t33_650M_UR90S_4_next	esm1v_t33_650M_UR90S_5_next	combined_score
# ENSG00000155966.14	ENST00000370460.7	ENSP00000359489.2	ENSP00000359489.2:p.Met1Ala	-5.354976177215576	-4.247730731964111	-5.950134754180908	-5.966752052307129	-5.39961051940918		-5.383840847015381


class ESM1vCodingVariantsScores:
    ALLOWED_LABELs = ['coding_variants', 'variants',
                      'variants_coding_variants', 'coding_variants_phenotypes']
    SOURCE = 'IGVF'
    MAPPING_FILE = 'ESM_1v_IGVFFI8105TNNO_mappings.tsv.gz'
    MAPPING_FILE_HEADER = ['transcript_id', 'aa_change', 'mutation_ids', 'hgvsc_ids', 'spdi_ids',
                           'hgvsg_ids', 'alt_codons', 'codon_positions', 'codon_ref', 'protein_id', 'protein_name', 'esm1v_t33_650M_UR90S_1', 'esm1v_t33_650M_UR90S_2', 'esm1v_t33_650M_UR90S_3', 'esm1v_t33_650M_UR90S_4', 'esm1v_t33_650M_UR90S_5', 'esm1v_t33_650M_UR90S_1_next', 'esm1v_t33_650M_UR90S_2_next', 'esm1v_t33_650M_UR90S_3_next', 'esm1v_t33_650M_UR90S_4_next', 'esm1v_t33_650M_UR90S_5_next', 'combined_score']
    PHENOTYPE_TERM = 'GO_0003674'  # Molecular Function, double check
    FILE_ACCESSION = 'IGVFFI8105TNNO'

    def __init__(self, filepath=None, label='coding_variants', writer: Optional[Writer] = None, **kwargs):
        if label not in ESM1vCodingVariantsScores.ALLOWED_LABELs:
            raise ValueError('Invalid label. Allowed values:' +
                             ','.join(ESM1vCodingVariantsScores.ALLOWED_LABELs))

        self.filepath = filepath
        self.source_url = 'https://data.igvf.org/tabular-files/' + self.FILE_ACCESSION
        self.writer = writer
        self.label = label
        self.files_filesets = FileFileSet(self.FILE_ACCESSION)

    def process_file(self):
        self.writer.open()
        if self.label == 'coding_variants_phenotypes':
            self.igvf_metadata_props = self.files_filesets.query_fileset_files_props_igvf(
                self.FILE_ACCESSION)[0]
            # write all enumerated variants to jsonl files for variants, and variants_coding_variants collections
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
                        self.writer.write(json.dumps(_props))
                        self.writer.write('\n')
                elif self.label == 'coding_variants':
                    for i, coding_variant_id in enumerate(coding_variant_ids):
                        matches = re.findall(
                            r'^([A-Za-z]+)(\d+)([A-Za-z]+)', row['aa_change'].split('.')[1])
                        aa_ref, aa_pos, aa_alt = matches[0]
                        _props = {
                            '_key': coding_variant_id,
                            'ref': AA_TABLE[aa_ref],
                            'alt': AA_TABLE[aa_alt],
                            'aapos': int(aa_pos),
                            'refcodon': row['codon_ref'],
                            'gene_name': coding_variant_id.split('_')[0],
                            'protein_id': row['protein_id'].split('.')[0],
                            'protein_name': row['protein_name'],
                            'codonpos': int(row['codon_positions'].split(',')[i]),
                            'hgvsc': row['hgvsc_ids'].split(',')[i].replace('-', '>'),
                            'hgvsp': row['aa_change'],
                            'transcript_id': row['transcript_id'].split('.')[0],
                            'source': self.SOURCE,
                            'source_url': self.source_url

                        }
                        self.writer.write(json.dumps(_props))
                        self.writer.write('\n')
                elif self.label == 'coding_variants_phenotypes':
                    score = float(row['combined_score'])
                    # only load rows with score < log(0.5)
                    if score < -0.6931:
                        for coding_variant_id in coding_variant_ids:
                            _props = {
                                '_key': '_'.join([coding_variant_id, self.PHENOTYPE_TERM, self.FILE_ACCESSION]),
                                '_from': 'coding_variants/' + coding_variant_id,
                                '_to': 'ontology_terms/' + self.PHENOTYPE_TERM,
                                'esm_1v_score': score,  # property scores passing threshold
                                'files_filesets': 'files_filesets/' + self.FILE_ACCESSION,
                                'method': self.igvf_metadata_props.get('method')
                            }
                            for field in self.MAPPING_FILE_HEADER:
                                # also load intermediate scores from model for now, could skip if not useful
                                if field.startswith('esm1v'):
                                    prop = {}
                                    value = row[field]
                                    prop[field] = float(
                                        value) if value != '' else None
                                    _props.update(prop)

                            self.writer.write(json.dumps(_props))
                            self.writer.write('\n')
        self.writer.close()
