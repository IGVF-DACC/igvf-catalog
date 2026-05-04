import csv
import gzip
import json
from adapters.base import BaseAdapter
from adapters.helpers import build_variant_id, load_variant, split_spdi, bulk_check_variants_in_arangodb, get_file_fileset_by_accession_in_arangodb
from typing import Optional
from adapters.writer import Writer

# Example lines from ColocBoost file (tab-separated with header):
# VariantChr	VariantStart	VariantEnd	EffectAllele	OtherAllele	SPDI_ID	BiosampleTerm	OntologyTerm	VCP	GeneEnsembl	GeneName	TraitName
# chr1	754503	754504	C	T	NC_000001.11:754503:T:C	UBERON_0001323	EFO_0006340	0.9263	ENSG00000237491	LINC01128	mean arterial pressure


class ColocBoostVariantBiosample(BaseAdapter):
    ALLOWED_LABELS = ['variant', 'variant_biosample']
    SOURCE = 'IGVF'

    def __init__(
        self,
        filepath,
        label='variant_biosample',
        writer: Optional[Writer] = None,
        validate=False,
        **kwargs
    ):
        super().__init__(filepath, label, writer, validate)
        # Extract accession from filename: IGVFFI1234ABCD.tsv.gz -> IGVFFI1234ABCD
        filename = self.filepath.split('/')[-1]
        self.file_accession = filename.split('.')[0]
        self.source_url = 'https://data.igvf.org/tabular-files/' + self.file_accession + '/'
        self.collection_label = 'variant colocalization with molecular trait'

    def _get_schema_type(self):
        if self.label == 'variant_biosample':
            return 'edges'
        return 'nodes'

    def _get_collection_name(self):
        if self.label == 'variant_biosample':
            return 'variants_biosamples'
        return 'variants'

    def process_file(self):
        self.writer.open()
        file_fileset_obj = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        self.method = file_fileset_obj['method']
        self.collection_class = file_fileset_obj['class']

        with gzip.open(self.filepath, 'rt') as colocboost_tsv:
            reader = csv.DictReader(colocboost_tsv, delimiter='\t')
            chunk_size = 6500
            chunk = []
            for i, row in enumerate(reader, 1):
                chunk.append(row)
                if i % chunk_size == 0:
                    if self.label == 'variant':
                        self.process_variant_chunk(chunk)
                    elif self.label == 'variant_biosample':
                        self.process_edge_chunk(chunk)
                    chunk = []
            if chunk:
                if self.label == 'variant':
                    self.process_variant_chunk(chunk)
                elif self.label == 'variant_biosample':
                    self.process_edge_chunk(chunk)

        self.writer.close()

    def process_variant_chunk(self, chunk):
        loaded_spdis = bulk_check_variants_in_arangodb(
            [row['SPDI_ID'] for row in chunk])
        skipped_spdis = []
        unloaded_chunk = [
            row for row in chunk if row['SPDI_ID'] not in loaded_spdis]

        for row in unloaded_chunk:
            spdi = row['SPDI_ID']
            variant, skipped_message = load_variant(spdi)
            if variant:
                variant.update({
                    'source': self.SOURCE,
                    'source_url': self.source_url,
                    'files_filesets': 'files_filesets/' + self.file_accession
                })
                if self.validate:
                    self.validate_doc(variant)
                self.writer.write(json.dumps(variant) + '\n')
            if skipped_message is not None:
                skipped_spdis.append(skipped_message)

        if skipped_spdis:
            self.logger.warning(f'Skipped {len(skipped_spdis)} variants:')
            for skipped in skipped_spdis:
                self.logger.warning(
                    f"  - {skipped['variant_id']}: {skipped['reason']}")
            with open('./skipped_variants.jsonl', 'a') as out:
                for skipped in skipped_spdis:
                    out.write(json.dumps(skipped) + '\n')

    def process_edge_chunk(self, chunk):
        loaded_spdis = bulk_check_variants_in_arangodb(
            [row['SPDI_ID'] for row in chunk])

        for row in chunk:
            spdi = row['SPDI_ID']
            if spdi not in loaded_spdis:
                continue

            chr, pos_start, ref, alt = split_spdi(spdi)
            _id = build_variant_id(chr, pos_start + 1, ref, alt, 'GRCh38')

            # BiosampleTerm per row; comma-separated to support multiple biosamples -> multiple edges
            biosample_terms = [t.strip()
                               for t in row['BiosampleTerm'].split(',') if t.strip()]

            # OntologyTerm column provides per-row phenotype (e.g. EFO_0006340 or EFO:0006340)
            ontology_term_raw = row.get('OntologyTerm', '').strip()
            phenotype = ('ontology_terms/' + ontology_term_raw.replace(':',
                         '_')) if ontology_term_raw else None

            for biosample_term in biosample_terms:
                biosample_term_id = biosample_term.replace(':', '_')
                biosample_ref = 'ontology_terms/' + biosample_term_id
                edge_key = _id + '_' + biosample_term_id + '_' + self.file_accession

                edge_props = {
                    '_key': edge_key,
                    '_from': 'variants/' + _id,
                    '_to': biosample_ref,
                    'biosample_term': biosample_ref,
                    'phenotype': phenotype,
                    'vcp': float(row['VCP']),
                    'gene_ensembl': row.get('GeneEnsembl') or None,
                    'gene_name': row.get('GeneName') or None,
                    'trait_name': row.get('TraitName') or None,
                    'label': self.collection_label,
                    'method': self.method,
                    'class': self.collection_class,
                    'name': 'colocalizes with',
                    'inverse_name': 'colocalized by variant',
                    'source': self.SOURCE,
                    'source_url': self.source_url,
                    'files_filesets': 'files_filesets/' + self.file_accession
                }

                if self.validate:
                    self.validate_doc(edge_props)
                self.writer.write(json.dumps(edge_props) + '\n')
