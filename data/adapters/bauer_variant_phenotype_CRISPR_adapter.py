import csv
import json
from adapters.helpers import bulk_check_variants_in_arangodb, load_variant
from adapters.file_fileset_adapter import FileFileSet
from typing import Optional

from adapters.writer import Writer

# example from IGVFFI4039BVDA
# variant,num,neg|score,neg|p-value,neg|fdr,neg|rank,neg|goodsgrna,neg|lfc,pos|score,pos|p-value,pos|fdr,pos|rank,pos|goodsgrna,pos|lfc
# NC_000023.11:56828728:T:C,5,1.0602e-12,2.219e-06,0.001238,1,4,-1.6533,0.94703,0.85192,1.0,1675,0,-1.6533
# NC_000023.11:57404273:T:C,6,2.6262e-08,2.219e-06,0.001238,2,6,-1.4426,1.0,1.0,1.0,2127,0,-1.4426
# NC_000023.11:8888590:T:C,6,3.0591e-08,2.219e-06,0.001238,3,6,-1.5609,0.99999,0.99997,1.0,2125,0,-1.5609
# NC_000023.11:56922647:T:C,6,1.6958e-07,2.219e-06,0.001238,4,5,-1.2206,0.98712,0.94621,1.0,1916,0,-1.2206
# SMC1A,5,6.0631e-07,6.6569e-06,0.002122,5,4,-1.3593,0.47237,0.41143,0.875029,1023,1,-1.3593
# NC_000023.11:109880401:A:G,6,1.1591e-06,6.6569e-06,0.002122,6,6,-2.0214,0.99998,0.99991,1.0,2121,0,-2.0214
# NC_000023.11:66111415:G:A,6,1.2941e-06,6.6569e-06,0.002122,7,5,-1.3132,0.98905,0.95106,1.0,1934,0,-1.3132
# NC_000023.11:48650391:G:A,6,2.3724e-06,1.9971e-05,0.00495,8,5,-0.98956,0.80078,0.73248,1.0,1388,1,-0.98956
# NC_000023.11:153275074:A:G,6,2.8066e-06,1.9971e-05,0.00495,9,6,-1.4282,1.0,0.99999,1.0,2126,0,-1.4282


class BauerVariantPhenotypeAdapter:
    ALLOWED_LABELS = ['variant', 'variant_phenotype']
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
            reader = csv.reader(f, delimiter=',')
            next(reader)
            chunk = []
            for i, row in enumerate(reader, 1):
                chunk.append(row)
                if i % BauerVariantPhenotypeAdapter.CHUNK_SIZE == 0:
                    self.process_chunk(chunk)
                    chunk = []
            if chunk != []:
                self.process_chunk(chunk)

        self.writer.close()

    def process_chunk(self, chunk):
        variant_id_to_variant = {}
        variant_id_row = {}
        skipped_spdis = []
        for row in chunk:
            spdi = row[0]
            variant, skipped_message = load_variant(spdi)

            if variant:
                variant_id = variant['_key']
                variant_id_to_variant[variant_id] = variant
                if variant_id not in variant_id_row:
                    variant_id_row[variant_id] = []
                variant_id_row[variant_id].append(row)

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
            list(variant_id_to_variant.keys()))

        if self.label == 'variant':
            self.process_variants(variant_id_to_variant, loaded_variants)
        elif self.label == 'variant_phenotype':
            self.process_edge(variant_id_row, loaded_variants)

    def process_variants(self, spdi_to_variant, loaded_variants):
        for variant_id, variant in spdi_to_variant.items():
            if variant_id in loaded_variants:
                continue
            else:
                variant.update({
                    'source': self.SOURCE,
                    'source_url': self.source_url,
                    'files_filesets': f'files_filesets/{self.file_accession}'
                })
                self.writer.write(json.dumps(variant) + '\n')

    def process_edge(self, variant_id_row, loaded_variants):
        for variant_id in variant_id_row:
            if variant_id in loaded_variants:
                for row in variant_id_row[variant_id]:
                    edge_props = {
                        '_key': f'{variant_id}_GO_0030218_{self.file_accession}',
                        '_from': f'variants/{variant_id}',
                        '_to': f'ontology_terms/GO_0030218',
                        'neg|lfc': float(row[7]),
                        'pos|lfc': float(row[13]),
                        'label': f'variant effect on erythrocyte differentiation',
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
