import csv
import json
from adapters.helpers import bulk_check_variants_in_arangodb, load_variant
from adapters.file_fileset_adapter import FileFileSet
from adapters.gene_validator import GeneValidator
from typing import Optional

from adapters.writer import Writer

# example from IGVFFI9602ILPC
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


class VariantEFFECTSAdapter:
    ALLOWED_LABELS = ['variant', 'variant_gene']
    SOURCE = 'IGVF'
    CHUNK_SIZE = 6500

    def __init__(self, filepath, label, source_url, writer: Optional[Writer] = None, **kwargs):
        if label not in self.ALLOWED_LABELS:
            raise ValueError(
                f'Invalid label. Allowed values: {", ".join(self.ALLOWED_LABELS)}')
        self.filepath = filepath
        self.label = label
        self.source_url = source_url
        self.file_accession = source_url.split('/')[-2]
        self.writer = writer
        self.type = 'node' if label == 'variant' else 'edge'
        self.gene_validator = GeneValidator()

        fileset = FileFileSet(self.file_accession,
                              writer=None, label='igvf_file_fileset')
        props, _, _ = fileset.query_fileset_files_props_igvf(
            self.file_accession, replace=False)
        self.simple_sample_summaries = props['simple_sample_summaries']
        self.biosample_term = props['samples']
        self.treatments_term_ids = props['treatments_term_ids']
        self.method = props['method']

    def process_file(self):
        self.writer.open()

        with open(self.filepath, 'r') as f:
            reader = csv.reader(f, delimiter='\t')
            next(reader)
            chunk = []
            for i, row in enumerate(reader, 1):
                chunk.append(row)
                if i % VariantEFFECTSAdapter.CHUNK_SIZE == 0:
                    self.process_chunk(chunk)
                    chunk = []

            if chunk != []:
                self.process_chunk(chunk)

        self.writer.close()

    def process_chunk(self, chunk):
        spdi_to_variant = {}
        spdi_to_row = {}
        skipped_spdis = []
        for row in chunk:
            gene = row[7]
            if not self.gene_validator.validate(gene):
                raise ValueError(
                    f'{gene} is not a valid gene.')

            spdi = row[0]
            variant, skipped_message = load_variant(spdi)

            if variant:
                normalized_spdi = variant['spdi']
                spdi_to_variant[normalized_spdi] = variant
                if normalized_spdi not in spdi_to_row:
                    spdi_to_row[normalized_spdi] = []
                spdi_to_row[normalized_spdi].append(row)

            if skipped_message is not None:
                skipped_spdis.append(skipped_message)

        if skipped_spdis:
            print(f'Skipped {len(skipped_spdis)} variants:')
            for skipped in skipped_spdis:
                print(f"  - {skipped['variant_id']}: {skipped['reason']}")
            with open('./skipped_variants.jsonl', 'a') as out:
                for skipped in skipped_spdis:
                    out.write(json.dumps(skipped) + '\n')

        loaded_variants = bulk_check_variants_in_arangodb(
            list(spdi_to_variant.keys()))

        if self.label == 'variant':
            self.process_variants(spdi_to_variant, loaded_variants)
        elif self.label == 'variant_gene':
            self.process_edge(spdi_to_row, loaded_variants)

    def process_variants(self, spdi_to_variant, loaded_variants):
        for spdi, variant in spdi_to_variant.items():
            if spdi in loaded_variants:
                continue
            else:
                variant.update({
                    'source': self.SOURCE,
                    'source_url': self.source_url,
                    'files_filesets': f'files_filesets/{self.file_accession}'
                })
                self.writer.write(json.dumps(variant) + '\n')

    def process_edge(self, spdi_to_row, loaded_variants):
        for variant in spdi_to_row:
            if variant in loaded_variants:
                for row in spdi_to_row[variant]:
                    edge_props = {
                        '_key': f'{variant}_{row[7]}_{self.file_accession}',
                        '_from': f'variants/{variant}',
                        '_to': f'genes/{row[7]}',
                        'effect_size': float(row[9]),
                        'log2_fold_change': float(row[10]),
                        'p_nominal_nlog10': float(row[11]),
                        'fdr_nlog10': float(row[12]),
                        'power': float(row[14]) if row[14] else None,
                        'label': f'variant effect on gene expression of {row[7]}',
                        'name': 'modulates expression of',
                        'inverse_name': 'expression modulated by',
                        'source': self.SOURCE,
                        'source_url': self.source_url,
                        'files_filesets': f'files_filesets/{self.file_accession}',
                        'method': self.method,
                        'simple_sample_summaries': self.simple_sample_summaries,
                        'biological_context': self.biosample_term,
                        'treatments_term_ids': self.treatments_term_ids,
                    }

                    self.writer.write(json.dumps(edge_props) + '\n')
