import csv
import json
import hashlib
from typing import Optional
from collections import defaultdict
import ast

from adapters.helpers import (
    build_regulatory_region_id,
    bulk_check_variants_in_arangodb,
    load_variant
)
from adapters.writer import Writer
from adapters.file_fileset_adapter import FileFileSet

# Example rows from IGVFFI4914OUJH - MPRA sequence designs
# name	sequence	category	class	source	ref	chr	start	end	strand	variant_class	variant_pos	SPDI	allele	info
# Variant 7193 (chr9:100000294-100000494)	TCCACCCGTCTCGGACTCCCAAAGTGCTGGGATTACAGGCGTGAGCCACGGCGCCCGGCCTGGAGCTTGTGTTACTAAAAGACATGCAAACGCCCTTAACCGCTAAGCTCCTGAGGGGTAACGGTATGCTACAAAAGTGCTTCTGAGCTACTACTCCTGGAGGCTTGGTCCGAGTGACCGCAGCAGTGGGCGCGGTGGAA	variant	test	Supplementary Table S6 from An et al., 2018	GRCh38	chr9	97238011	97238211	+	["SNV"]	[100]	["NC_000009.12:97238111:C:T"]	["ref"]	for questions ask Ahituv lab
# Variant 7194 (chr9:100000294-100000494)	TCCACCCGTCTCGGACTCCCAAAGTGCTGGGATTACAGGCGTGAGCCACGGCGCCCGGCCTGGAGCTTGTGTTACTAAAAGACATGCAAACGCCCTTAACTGCTAAGCTCCTGAGGGGTAACGGTATGCTACAAAAGTGCTTCTGAGCTACTACTCCTGGAGGCTTGGTCCGAGTGACCGCAGCAGTGGGCGCGGTGGAA	variant	test	Supplementary Table S6 from An et al., 2018	GRCh38	chr9	97238011	97238211	+	["SNV"]	[100]	["NC_000009.12:97238111:C:T"]	["alt"]	for questions ask Ahituv lab
# Variant 7195 (chr9:100743726-100743926)	TTTGCCCTGATGCTAAGGATTAATACCACCTCCTCCGGGAGCCATCAGGTTACCACTCTCTAGCACAGAGCTACCACGTTTAAGACTCCTTCAGCACCATCCCCCCTTTTCCTGCACGAGGACACTTGCATGCTGTTTGGTATTAAAAGCCCTCTGCAACTGTTCCCAACCTACAGCACCAAAGTAGCCCCCCACCATG	variant	test	Supplementary Table S6 from An et al., 2018	GRCh38	chr9	97981444	97981642	+	NA	NA	NA	NA	for questions ask Ahituv lab
# Variant 7196 (chr9:100743726-100743926)	TTTGCCCTGATGCTAAGGATTAATACCACCTCCTCCGGGAGCCATCAGGTTACCACTCTCTAGCACAGAGCTACCACGTTTAAGACTCCTTCAGCACCATCCCCCCCTTTTCCTGCACGAGGACACTTGCATGCTGTTTGGTATTAAAAGCCCTCTGCAACTGTTCCCAACCTACAGCACCAAAGTAGCCCCCCACCATG	variant	test	Supplementary Table S6 from An et al., 2018	GRCh38	chr9	97981444	97981642	+	NA	NA	NA	NA	for questions ask Ahituv lab
# Variant 7197 (chr9:100744209-100744409)	GTTCTCATAACCTTAGTTACAGACCTTTTGTAACCCTGAGAACATCTGTCTCCATTTTCCCTTGTCATAAAGACGTCTGCTGAGACTACAAACGGAGTCAGGGAACTACTACCAGAAAGTTTTTCTTTTCCCATATTCCTTCTAAAACTTTCATCTTCAAATGTTAACTCACTCAGTATTTTAAAAGCTGATATATAATT	variant	test	Supplementary Table S6 from An et al., 2018	GRCh38	chr9	97981941	97982141	+	["indel"]	[85]	["NC_000009.12:97982027:TACAAACGGAGTCAGGGAACTACTACCA:"]	["ref"]	for questions ask Ahituv lab
# Variant 7198 (chr9:100744209-100744409)	GTTCTCATAACCTTAGTTACAGACCTTTTGTAACCCTGAGAACATCTGTCTCCATTTTCCCTTGTCATAAAGACGTCTGCTGAGACGAAAGTTTTTCTTTTCCCATATTCCTTCTAAAACTTTCATCTTCAAATGTTAACTCACTCAGTATTTTAAAAGCTGATATATAATT	variant	test	Supplementary Table S6 from An et al., 2018	GRCh38	chr9	97981941	97982141	+	["indel"]	[85]	["NC_000009.12:97982027:TACAAACGGAGTCAGGGAACTACTACCA:"]	["alt"]	for questions ask Ahituv lab
# Variant 7199 (chr9:101568131-101568331)	CTGGGGCTTAAGTCCATGTCTTGTAAGGCCTAATTGCATTTCTCTTTTCTCTGTATCTGAACCTCTATTGAGAAGCATTCCAATTTGGCAAGCGGATCCAAGACATTATGAATTGTAATCCTTGTCTGTTTTCTAATCTGACCGCAGATCTTAAATGTGTTGGGTGTCTGAACAGAGGCCAAAGGGCTCAGGTCCAGACC	variant	test	Supplementary Table S6 from An et al., 2018	GRCh38	chr9	98805848	98806048	+	["SNV"]	[100]	["NC_000009.12:98805948:A:G"]	["ref"]	for questions ask Ahituv lab
# Variant 7200 (chr9:101568131-101568331)	CTGGGGCTTAAGTCCATGTCTTGTAAGGCCTAATTGCATTTCTCTTTTCTCTGTATCTGAACCTCTATTGAGAAGCATTCCAATTTGGCAAGCGGATCCAGGACATTATGAATTGTAATCCTTGTCTGTTTTCTAATCTGACCGCAGATCTTAAATGTGTTGGGTGTCTGAACAGAGGCCAAAGGGCTCAGGTCCAGACC	variant	test	Supplementary Table S6 from An et al., 2018	GRCh38	chr9	98805848	98806048	+	["SNV"]	[100]	["NC_000009.12:98805948:A:G"]	["alt"]	for questions ask Ahituv lab
# Variant 7199 (chr9:101568131-101568331)	CTGGGGCTTAAGTCCATGTCTTGTAAGGCCTAATTGCATTTCTCTTTTCTCTGTATCTGAACCTCTATTGAGAAGCATTCCAATTTGGCAAGCGGATCCAAGACATTATGAATTGTAATCCTTGTCTGTTTTCTAATCTGACCGCAGATCTTAAATGTGTTGGGTGTCTGAACAGAGGCCAAAGGGCTCAGGTCCAGACC	variant	test	Supplementary Table S6 from An et al., 2018	GRCh38	chr9	98805848	98806048	+	["SNV"]	[100]	["NC_000009.12:98805948:A:G"]	["ref"]	for questions ask Ahituv lab
# Variant 7200 (chr9:101568131-101568331)	CTGGGGCTTAAGTCCATGTCTTGTAAGGCCTAATTGCATTTCTCTTTTCTCTGTATCTGAACCTCTATTGAGAAGCATTCCAATTTGGCAAGCGGATCCAGGACATTATGAATTGTAATCCTTGTCTGTTTTCTAATCTGACCGCAGATCTTAAATGTGTTGGGTGTCTGAACAGAGGCCAAAGGGCTCAGGTCCAGACC	variant	test	Supplementary Table S6 from An et al., 2018	GRCh38	chr9	98805848	98806048	+	["SNV"]	[100]	["NC_000009.12:98805948:A:G"]	["alt"]	for questions ask Ahituv lab


# Example rows from IGVFFI1323RCIE - reporter genomic variant effects
# chr9	135961939	135961940	NC_000009.12:135961939:C:T	3	+	0.0040	0.7019	0.4889	0.7251	0.5157	0.1089	0.0436	0.0009	-0.0240	0.0321	100	C	T
# chr9	135962406	135962415	NC_000009.12:135962406:CTTACTTAC:CTTAC	8	+	0.0096	0.6739	0.4672	0.6808	0.4822	0.2451	0.1024	0.0013	-0.0234	0.0425	102	CTTACTTAC	CTTAC
# chr9	136120451	136120452	NC_000009.12:136120451:C:T	13	+	-0.0154	0.6922	0.6222	0.7067	0.6082	0.4623	0.2084	0.0015	-0.0474	0.0166	100	C	T
# chr9	136248440	136248441	NC_000009.12:136248440:T:C	66	+	-0.0768	0.5948	0.3434	0.6516	0.3039	5.9634	4.7221	0.9920	-0.1076	-0.0461	100	T	C
# chr9	136409762	136409763	NC_000009.12:136409762:G:A	0	+	0.0003	0.6667	0.4286	0.6120	0.3810	0.0077	0.0029	0.0009	-0.0276	0.0282	100	G	A
# chr9	136440567	136440568	NC_000009.12:136440567:C:T	31	+	-0.0363	0.5936	0.4647	0.5893	0.4212	1.1282	0.6003	0.0060	-0.0762	0.0036	100	C	T
# chr9	136767461	136767462	NC_000009.12:136767461:G:A	45	+	-0.0522	0.6382	0.4405	0.7456	0.4582	2.0643	1.2851	0.0357	-0.0911	-0.0133	100	G	A
# chr9	136886328	136886329	NC_000009.12:136886328:G:C	2	+	-0.0024	0.6182	1.0241	0.6315	1.0386	0.0928	0.0351	0.0005	-0.0213	0.0166	100	G	C
# chr9	137239310	137239311	NC_000009.12:137239310:T:C	25	+	0.0295	0.6892	0.6271	0.6842	0.6684	1.0221	0.5296	0.0044	-0.0051	0.0641	100	T	C
# chr9	137423283	137423284	NC_000009.12:137423283:T:C	14	+	-0.0164	0.7138	1.3057	0.7387	1.3015	0.4569	0.2065	0.0014	-0.0509	0.0180	100	T	C


# Example rows from IGVFFI8207IHFY - reporter genomic element effects
# chr9	135962308	135962508	Variant_7027_(chr9:138854152-138854352)	130	+	-0.1796	0.6739	0.4672	0.0000	0.0000
# chr9	136120351	136120551	Variant_7029_(chr9:139012198-139012398)	48	+	-0.0675	0.6922	0.6222	0.0000	0.0000
# chr9	136248340	136248540	Variant_7031_(chr9:139140187-139140387)	172	+	-0.2376	0.5948	0.3434	0.0000	0.0000
# chr9	136409662	136409862	Variant_7033_(chr9:139304115-139304315)	151	+	-0.2085	0.6667	0.4286	0.0000	0.0000
# chr9	136440467	136440667	Variant_7037_(chr9:139334920-139335120)	84	+	-0.1169	0.5936	0.4647	0.0000	0.0000
# chr9	136767361	136767561	Variant_7041_(chr9:139661814-139662014)	130	+	-0.1795	0.6382	0.4405	0.0000	0.0000
# chr9	136886228	136886428	Variant_7043_(chr9:139780681-139780881)	197	+	0.2714	0.6182	1.0241	139.7317	138.3358
# chr9	137239210	137239410	Variant_7045_(chr9:140133663-140133863)	39	+	-0.0548	0.6892	0.6271	0.0000	0.0000
# chr9	137423183	137423383	Variant_7047_(chr9:140317636-140317836)	263	+	0.3619	0.7138	1.3057	86.4719	85.2088
# chrX	55014905	55015105	Positive_1_(chrX:55041339-55041539)	140	+	-0.1937	0.6688	0.4478	0.0000	0.0000


class IGVFMPRAAdapter:
    ALLOWED_LABELS = [
        'genomic_element',
        'genomic_element_biosample',
        'variant',
        'genomic_element_from_variant',
        'variant_genomic_element']

    SOURCE = 'IGVF'
    THRESHOLD = 1
    CHUNK_SIZE = 6500

    def __init__(self, filepath, label, source_url, reference_filepath, reference_source_url, writer: Optional[Writer] = None, **kwargs):
        if label not in self.ALLOWED_LABELS:
            raise ValueError('Invalid label. Allowed values: ' +
                             ', '.join(self.ALLOWED_LABELS))

        self.writer = writer
        self.label = label

        self.filepath = filepath
        self.source_url = source_url
        self.file_accession = source_url.split('/')[-2]
        self.files_filesets = FileFileSet(
            self.file_accession, writer=None, label='igvf_file_fileset')

        self.mpra_design_file = reference_filepath
        self.reference_source_url = reference_source_url
        self.reference_file_accession = reference_source_url.split('/')[-2]
        self.reference_files_filesets = FileFileSet(
            self.reference_file_accession, writer=None, label='igvf_file_fileset')

        props, _, _ = self.files_filesets.query_fileset_files_props_igvf(
            self.file_accession)
        self.method = props.get('method')
        self.biosample_term = props.get('samples')
        self.simple_sample_summaries = props.get('simple_sample_summaries')
        self.treatments_term_ids = props.get('treatments_term_ids')

        self.variant_to_element = defaultdict(set)
        self.design_elements = set()
        self.load_mpra_design_mapping(self.mpra_design_file)

    def load_mpra_design_mapping(self, mpra_design_file):
        with open(mpra_design_file, 'r') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for i, row in enumerate(reader, 1):
                try:
                    key = (row['chr'], row['start'], row['end'])
                    self.design_elements.add(key)
                except Exception:
                    pass

                if row['SPDI'] in (None, '', 'NA', 'NaN'):
                    continue
                try:
                    spdi_list = ast.literal_eval(row['SPDI'])
                except (ValueError, SyntaxError) as e:
                    raise ValueError(
                        f"Malformed SPDI at row {i}: {row['SPDI']!r}") from e

                for spdi in spdi_list:
                    self.variant_to_element[spdi].add(key)

    def process_file(self):
        self.writer.open()
        with open(self.filepath, 'r') as f:
            reader = csv.reader(f, delimiter='\t')
            chunk = []
            for i, row in enumerate(reader, 1):
                if self.label in ['variant', 'variant_genomic_element', 'genomic_element_from_variant']:
                    minusLog10QValue = float(row[12])
                else:
                    minusLog10QValue = float(row[10])
                if minusLog10QValue < IGVFMPRAAdapter.THRESHOLD:
                    continue
                chunk.append(row)
                if i % IGVFMPRAAdapter.CHUNK_SIZE == 0:
                    self.process_chunk(chunk)
                    chunk = []
            if chunk:
                self.process_chunk(chunk)
        self.writer.close()

    def process_chunk(self, chunk):
        if self.label == 'variant':
            self.process_variant_chunk(chunk)
        elif self.label == 'variant_genomic_element':
            self.process_variant_element_chunk(chunk)
        elif self.label in ['genomic_element', 'genomic_element_from_variant']:
            self.process_genomic_element_chunk(chunk)
        elif self.label == 'genomic_element_biosample':
            self.process_element_biosample_chunk(chunk)

    def process_variant_chunk(self, chunk):
        spdis = [row[3] for row in chunk]
        loaded_spdis = bulk_check_variants_in_arangodb(spdis, check_by='spdi')
        for row in chunk:
            spdi = row[3]
            if spdi in loaded_spdis:
                continue
            variant, skipped_message = load_variant(spdi)
            if variant:
                variant.update({
                    'source': self.SOURCE,
                    'source_url': self.source_url,
                    'files_filesets': f'files_filesets/{self.file_accession}'
                })
                self.writer.write(json.dumps(variant) + '\n')
            elif skipped_message:
                print(f'Skipped {spdi}: {skipped_message}')
                with open('./skipped_variants.jsonl', 'a') as out:
                    out.write(json.dumps(skipped_message) + '\n')

    def process_genomic_element_chunk(self, chunk):
        props, _, _ = self.reference_files_filesets.query_fileset_files_props_igvf(
            self.reference_file_accession)
        method = props.get('method')

        if self.label == 'genomic_element_from_variant':
            seen = set()
            for element_coords_set in self.variant_to_element.values():
                for chr, start, end in element_coords_set:
                    key = (chr, start, end)
                    if key in seen:
                        continue
                    seen.add(key)
                    region_id = build_regulatory_region_id(
                        chr, start, end, 'MPRA')
                    _id = f'{region_id}_{self.reference_file_accession}'
                    props = {
                        '_key': _id,
                        'name': _id,
                        'chr': chr,
                        'start': int(start),
                        'end': int(end),
                        'method': method,
                        'type': 'tested elements',
                        'source': self.SOURCE,
                        'source_url': self.reference_source_url,
                        'files_filesets': f'files_filesets/{self.reference_file_accession}'
                    }
                    self.writer.write(json.dumps(props) + '\n')
        else:
            for row in chunk:
                chr, start, end = row[0], row[1], row[2]
                if (chr, start, end) not in self.design_elements:
                    raise ValueError(
                        f'Genomic element {(chr, start, end)} from {self.file_accession} is not present in the MPRA sequence designs file {self.reference_file_accession}.')
                region_id = build_regulatory_region_id(chr, start, end, 'MPRA')
                _id = f'{region_id}_{self.reference_file_accession}'
                props = {
                    '_key': _id,
                    'name': _id,
                    'chr': chr,
                    'start': int(start),
                    'end': int(end),
                    'method': method,
                    'type': 'tested elements',
                    'source': self.SOURCE,
                    'source_url': self.source_url,
                    'files_filesets': f'files_filesets/{self.reference_file_accession}'
                }
                self.writer.write(json.dumps(props) + '\n')

    def process_variant_element_chunk(self, chunk):
        loaded_spdis = bulk_check_variants_in_arangodb(
            [row[3] for row in chunk])
        for row in chunk:
            spdi = row[3]
            if spdi not in loaded_spdis:
                continue
            if spdi not in self.variant_to_element:
                raise ValueError(
                    f'SPDI {spdi} found in variant file but not in MPRA design mapping. '
                    'Ensure all genomic element edges are mapped via the sequence design file.'
                )

            variant, skipped_message = load_variant(spdi)
            if not variant:
                if skipped_message:
                    print(f'Skipped {spdi}: {skipped_message}')
                continue
            variant_id = variant['_key']

            for element_chr, element_start, element_end in self.variant_to_element[spdi]:
                element_id = build_regulatory_region_id(
                    element_chr, element_start, element_end, 'MPRA') + f'_{self.reference_file_accession}'
                edge_key = f'{variant_id}_{element_id}_{self.file_accession}'

                edge_props = {
                    '_key': edge_key,
                    '_from': f'variants/{variant_id}',
                    '_to': f'genomic_elements/{element_id}',
                    'bed_score': int(row[4]),
                    'activity_score': float(row[6]),  # log2FoldChange
                    'DNA_count_ref': float(row[7]),
                    'RNA_count_ref': float(row[8]),
                    'DNA_count_alt': float(row[9]),
                    'RNA_count_ref': float(row[10]),
                    'minusLog10PValue': float(row[11]),
                    'minusLog10QValue': float(row[12]),
                    'postProbEffect': float(row[13]),
                    'CI_lower_95': float(row[14]),
                    'CI_upper_95': float(row[15]),
                    'label': 'effect on regulatory function',
                    'name': 'modulates regulatory activity of',
                    'inverse_name': 'regulatory activity modulated by',
                    'method': self.method,
                    'source': self.SOURCE,
                    'source_url': self.source_url,
                    'files_filesets': 'files_filesets/' + self.file_accession,
                    'simple_sample_summaries': self.simple_sample_summaries,
                    'biological_context': self.biosample_term[0],
                    'treatments_term_ids': self.treatments_term_ids or None,
                }

                self.writer.write(json.dumps(edge_props) + '\n')

    def process_element_biosample_chunk(self, chunk):
        for row in chunk:
            chr, start, end = row[0], row[1], row[2]
            region_id = build_regulatory_region_id(chr, start, end, 'MPRA')
            element_id = f'{region_id}_{self.reference_file_accession}'
            edge_id = f'{region_id}_{self.file_accession}_{self.biosample_term[0].split("/")[1]}'

            props = {
                '_key': edge_id,
                '_from': f'genomic_elements/{element_id}',
                '_to': self.biosample_term[0],
                'bed_score': int(row[4]),
                'strand': row[5],
                'activity_score': float(row[6]),  # log2FoldChange
                'DNA_count': float(row[7]),
                'RNA_count': float(row[8]),
                'minusLog10PValue': float(row[9]),
                'minusLog10QValue': float(row[10]),
                'label': 'effect on regulatory function',
                'name': 'expression effect in',
                'inverse_name': 'has expression effect from',
                'method': self.method,
                'source': self.SOURCE,
                'source_url': self.source_url,
                'files_filesets': f'files_filesets/{self.file_accession}',
                'simple_sample_summaries': self.simple_sample_summaries,
                'biological_context': self.biosample_term[0],
                'treatments_term_ids': self.treatments_term_ids if self.treatments_term_ids else None,
            }
            self.writer.write(json.dumps(props) + '\n')
