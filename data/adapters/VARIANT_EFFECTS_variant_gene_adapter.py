import csv
import json
from adapters.helpers import build_variant_id, split_spdi, bulk_check_spdis_in_arangodb, is_variant_snv, get_ref_seq_by_spdi
from adapters.helpers import build_hgvs_from_spdi
from adapters.file_fileset_adapter import FileFileSet
from adapters.gene_validator import GeneValidator
from typing import Optional

from adapters.writer import Writer
# variant	chr	pos	ref	alt	effect_allele	other_allele	gene	gene_symbol	effect_size	log2_fold_change	p_nominal_nlog10	fdr_nlog10	fdr_method	power	VariantID_h19
# NC_000010.11:79347444::CCTCCTCAGG	chr10	79347444		CCTCCTCAGG	CCTCCTCAGG		ENSG00000108179	PPIF	-0.022057224	-0.032178046	1.86224451	1.778299483	Benjamini-Hochberg	0.054202114	chr10:81107199:A>ACCTCCTCAGG
# NC_000010.11:79347444:GG:GGTGTGCGGCGG	chr10	79347444	GG	GGTGTGCGGCGG	GGTGTGCGGCGG	GG	ENSG00000108179	PPIF	-0.408968828	-0.758693872	6.375717904	5.866461092	Benjamini-Hochberg	0.999999871	chr10:81107199:A>AGGTGTGCGGC
# NC_000010.11:79347444::TGATGCAATC	chr10	79347444		TGATGCAATC	TGATGCAATC		ENSG00000108179	PPIF	0.873942851	0.906076956	7.300162274	6.63638802	Benjamini-Hochberg	1	chr10:81107199:A>ATGATGCAATC
# NC_000010.11:79347443:A:ATGTTGCAACA	chr10	79347443	A	ATGTTGCAACA	ATGTTGCAACA	A	ENSG00000108179	PPIF	0.132667302	0.179724161	3.553863762	3.397077705	Benjamini-Hochberg	0.575200705	chr10:81107199:A>ATGTTGCAACA
# NC_000010.11:79347444::TTCAGTTTGG	chr10	79347444		TTCAGTTTGG	TTCAGTTTGG		ENSG00000108179	PPIF	-0.096234355	-0.145979378	0.880457076	0.833234848	Benjamini-Hochberg	0.005869996	chr10:81107199:A>ATTCAGTTTGG
# NC_000010.11:79347440:TA:TACCTGCAGGTA	chr10	79347440	TA	TACCTGCAGGTA	TACCTGCAGGTA	TA	ENSG00000108179	PPIF	-0.50970361	-1.028273956	8.860120914	7.595166283	Benjamini-Hochberg	1	chr10:81107196:T>TACCTGCAGGT
# NC_000010.11:79347442::CTTGCGC	chr10	79347442		CTTGCGC	CTTGCGC		ENSG00000108179	PPIF	0.222274668	0.289568522	8.292429824	7.251037139	Benjamini-Hochberg	1	chr10:81107198:A>CTTGCGCA
# NC_000010.11:79347442::TAAATGAGG	chr10	79347442		TAAATGAGG	TAAATGAGG		ENSG00000108179	PPIF	-0.034044116	-0.049970793	1.401841879	1.342720428	Benjamini-Hochberg	0.02106958	chr10:81107197:A>ATAAATGAGG
# NC_000010.11:79347441:A:ATGAGTTCA	chr10	79347441	A	ATGAGTTCA	ATGAGTTCA	A	ENSG00000108179	PPIF	-0.194725166	-0.312446847	8.772113295	7.591760035	Benjamini-Hochberg	1	chr10:81107197:A>ATGAGTTCA
# NC_000010.11:79347442::TTACGCAAC	chr10	79347442		TTACGCAAC	TTACGCAAC		ENSG00000108179	PPIF	0.181441861	0.240548636	6.970616222	6.412289035	Benjamini-Hochberg	1	chr10:81107197:A>ATTACGCAAC


class VARIANTEFFECTSAdapter:
    ALLOWED_LABELS = ['variant', 'variant_gene']
    SOURCE = 'IGVF'

    def __init__(self, filepath, label, source_url, writer: Optional[Writer] = None, **kwargs):
        if label not in VARIANTEFFECTSAdapter.ALLOWED_LABELS:
            raise ValueError('Invalid label. Allowed values: ' +
                             ','.join(VARIANTEFFECTSAdapter.ALLOWED_LABELS))
        self.filepath = filepath
        self.label = label
        self.source_url = source_url
        self.file_accession = source_url.split('/')[-2]
        self.dataset = label
        self.type = 'edge'
        if (self.label == 'variant'):
            self.type = 'node'
        self.writer = writer
        self.gene_validator = GeneValidator()
        self.files_filesets = FileFileSet(
            self.file_accession, writer=None, label='igvf_file_fileset')
        file_set_props, _, _ = self.files_filesets.query_fileset_files_props_igvf(
            self.file_accession, replace=False)
        self.simple_sample_summaries = file_set_props['simple_sample_summaries']
        self.biosample_term = file_set_props['samples']
        self.treatments_term_ids = file_set_props['treatments_term_ids']
        self.method = file_set_props['method']

    def process_file(self):
        self.writer.open()

        with open(self.filepath, 'r') as bluestarr_tsv:
            reader = csv.reader(bluestarr_tsv, delimiter='\t')
            chunk_size = 6500

            chunk = []
            for i, row in enumerate(reader, 1):
                chunk.append(row)
                if i % chunk_size == 0:
                    if self.label == 'variant':
                        self.process_variant_chunk(chunk)
                    elif self.label == 'variant_gene':
                        self.process_edge_chunk(chunk)
                    chunk = []

            if chunk != []:
                if self.label == 'variant':
                    self.process_variant_chunk(chunk)
                elif self.label == 'variant_gene':
                    self.process_edge_chunk(chunk)

        self.writer.close()

    def process_variant_chunk(self, chunk):
        loaded_spdis = bulk_check_spdis_in_arangodb([row[4] for row in chunk])
        skipped_spdis = []

        unloaded_chunk = []
        for row in chunk:
            if row[0] not in loaded_spdis:
                unloaded_chunk.append(row)

        for row in unloaded_chunk:
            spdi = row[0]
            if not is_variant_snv(spdi):
                skipped_spdis.append({'spdi': spdi, 'reason': 'Not SNV'})
                continue

            ref_genome = get_ref_seq_by_spdi(spdi)
            chr, pos_start, ref, alt = split_spdi(spdi)
            if ref != ref_genome:
                skipped_spdis.append(
                    {'spdi': spdi, 'reason': 'Ref allele mismatch'})
                continue
            if ref not in ['A', 'C', 'T', 'G']:
                skipped_spdis.append(
                    {'spdi': spdi, 'reason': 'Ambigious ref allele'})
                continue
            elif alt not in ['A', 'C', 'T', 'G']:
                skipped_spdis.append(
                    {'spdi': spdi, 'reason': 'Ambigious alt allele'})
                continue

            _id = build_variant_id(chr, pos_start + 1, ref, alt, 'GRCh38')

            variation_type = 'SNP'
            if len(ref) < len(alt):
                variation_type = 'insertion'
            elif len(ref) > len(alt):
                variation_type = 'deletion'

            variant = {
                '_key': _id,
                'name': spdi,
                'chr': chr,
                'pos': pos_start,
                'ref': ref,
                'alt': alt,
                'variation_type': variation_type,
                'spdi': spdi,
                'hgvs': build_hgvs_from_spdi(spdi),
                'organism': 'Homo sapiens',
                'source': self.SOURCE,
                'source_url': self.source_url,
                'files_filesets': 'files_filesets/' + self.file_accession
            }

            self.writer.write(json.dumps(variant) + '\n')

        if skipped_spdis:
            print(f'Skipped {len(skipped_spdis)} variants:')
            for skipped in skipped_spdis:
                print(f"  - {skipped['spdi']}: {skipped['reason']}")
            with open('./skipped_variants.jsonl', 'a') as out:
                for skipped in skipped_spdis:
                    out.write(json.dumps(skipped) + '\n')

    def process_edge_chunk(self, chunk):
        loaded_spdis = bulk_check_spdis_in_arangodb([row[4] for row in chunk])

        unloaded_chunk = []
        for row in chunk:
            if row[0] in loaded_spdis:
                unloaded_chunk.append(row)

        for row in unloaded_chunk:
            spdi = row[0]
            chr, pos_start, ref, alt = split_spdi(spdi)
            variant_id = build_variant_id(
                chr, pos_start + 1, ref, alt, 'GRCh38')

            gene = row[7]
            if not self.gene_validator.validate(gene):
                raise ValueError(
                    f'{gene} is not a valid gene.')

            _id = '_'.join([variant_id, gene, self.file_accession])

            edge_props = {
                '_key': _id,
                '_from': 'variants/' + variant_id,
                '_to': 'genes/' + gene,
                'effect_size': float(row[9]),
                'log2_fold_change': float(row[10]),
                'p_nominal_nlog10': float(row[11]),
                'fdr_nlog10': float(row[12]),
                'fdr_method': float(row[13]),
                'power': float(row[14]),
                'label': f'variant effect on gene expression of {gene}',
                'name': 'modulates expression of',
                'inverse_name': 'expression modulated by',
                'source': VARIANTEFFECTSAdapter.SOURCE,
                'source_url': self.source_url,
                'files_filesets': 'files_filesets/' + self.file_accession,
                'method': self.method,
                'simple_sample_summaries': self.simple_sample_summaries,
                'biological_context': self.biosample_term,
                'treatments_term_ids': self.treatments_term_ids,
            }

            self.writer.write(json.dumps(edge_props) + '\n')
