import csv
import gzip
import json
from adapters.base import BaseAdapter
from adapters.helpers import build_variant_id, load_variant, split_spdi, bulk_check_variants_in_arangodb, get_file_fileset_by_accession_in_arangodb
from adapters.gene_validator import GeneValidator
from typing import Optional
from adapters.writer import Writer

# Example lines from ColocBoost file IGVFFI7493PNOA:
# VariantChr	VariantStart	VariantEnd	EffectAllele	OtherAllele	SPDI_ID	VCP	GeneEnsembl	GeneName	TraitName	OntologyTerm	BiosampleTermName	UBERONTerm
# chr1	112503772	112503773	T	C	NC_000001.11:112503772:T:C	0.999369103613997	ENSG00000134245	WNT2B	mean arterial pressure	EFO_0006340	tibial nerve	UBERON_0001323
# chr1	112691075	112691076	T	C	NC_000001.11:112691075:T:C	0.105606886580907	ENSG00000155363	MOV10	mean arterial pressure	EFO_0006340	tibial artery;breast;sigmoid colon;gastroesophageal junction;esophagus muscularis;lung;tibial nerve;ovary;stomach;thyroid gland	UBERON_0007610;UBERON_0008367;UBERON_0001159;UBERON_0004550;UBERON_0004648;UBERON_0008952;UBERON_0001323;UBERON_0000992;UBERON_0000945;UBERON_0002046


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
        filename = self.filepath.split('/')[-1]
        self.file_accession = filename.split('.')[0]
        self.source_url = 'https://data.igvf.org/tabular-files/' + self.file_accession + '/'
        self.collection_label = 'predicted variant effect on phenotype'
        self.gene_validator = GeneValidator()

    def _get_schema_type(self):
        if self.label == 'variant_biosample':
            return 'edges'
        return 'nodes'

    def _get_collection_name(self):
        if self.label == 'variant_biosample':
            return 'variants_biosamples'
        return 'variants'

    def process_file(self):
        with self.writer:
            self.parse()

    def parse(self):
        file_fileset_obj = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        self.method = file_fileset_obj['method']
        self.collection_class = file_fileset_obj['class']

        with gzip.open(self.filepath, 'rt') as colocboost_tsv:
            # Some ColocBoost files start with a '# ...' comment line (e.g.
            # '### VCP threshold 0.1') before the real tab-separated header.
            # Drop any such lines so csv.DictReader picks up the actual header.
            lines = (line for line in colocboost_tsv if not line.startswith('#'))
            reader = csv.DictReader(lines, delimiter='\t')
            rows = self.normalize_rows(list(reader))
            rows = self.merge_duplicate_rows(rows)

        chunk_size = 6500
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i:i + chunk_size]
            if self.label == 'variant':
                self.process_variant_chunk(chunk)
            elif self.label == 'variant_biosample':
                self.process_edge_chunk(chunk)

        self.gene_validator.log()

    @staticmethod
    def normalize_rows(rows):
        """
        All ColocBoost files provide multiple biosamples per row via
        semicolon-separated 'UBERONTerm'/'BiosampleTermName' columns, except
        for one file (IGVFFI5870RJQU) which instead provides a single
        biosample per row via a 'BiosampleTerm' column. Normalize that file
        so downstream parsing only has to handle one shape.
        """
        if not rows or 'UBERONTerm' in rows[0]:
            return rows
        for row in rows:
            row['UBERONTerm'] = row.get('BiosampleTerm', '')
        return rows

    @staticmethod
    def merge_duplicate_rows(rows):
        """
        Some ColocBoost files repeat the same (variant, gene, trait) across
        multiple rows with different, overlapping biosample lists and
        different VCP values. Merge those into a single row: union the
        (UBERONTerm, BiosampleTermName) pairs and take the max VCP.
        Files are fairly small so we can do this in memory.

        Rows with mismatched UBERONTerm/BiosampleTermName lengths are passed
        through unmerged so process_edge_chunk's existing length check still
        catches and skips them.
        """
        merged = {}
        order = []
        for row in rows:
            uberon_terms = [t.strip()
                            for t in row['UBERONTerm'].split(';') if t.strip()]
            biosample_names = [
                t.strip() for t in row['BiosampleTermName'].split(';') if t.strip()]

            if len(uberon_terms) != len(biosample_names):
                order.append(object())
                merged[order[-1]] = row
                continue

            key = (row['SPDI_ID'], row['GeneEnsembl'],
                   row['TraitName'], row['OntologyTerm'])
            pairs = list(zip(uberon_terms, biosample_names))

            if key not in merged:
                merged_row = dict(row)
                merged_row['_pairs'] = list(dict.fromkeys(pairs))
                merged[key] = merged_row
                order.append(key)
            else:
                merged_row = merged[key]
                if float(row['VCP']) > float(merged_row['VCP']):
                    merged_row['VCP'] = row['VCP']
                for pair in pairs:
                    if pair not in merged_row['_pairs']:
                        merged_row['_pairs'].append(pair)

        merged_rows = []
        for key in order:
            row = merged[key]
            pairs = row.pop('_pairs', None)
            if pairs is not None:
                row['UBERONTerm'] = ';'.join(p[0] for p in pairs)
                row['BiosampleTermName'] = ';'.join(p[1] for p in pairs)
            merged_rows.append(row)
        return merged_rows

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
            variant_id = build_variant_id(
                chr, pos_start + 1, ref, alt, 'GRCh38')

            # UBERONTerm per row; semicolon-separated for multiple biosamples -> multiple edges
            uberon_terms = [t.strip()
                            for t in row['UBERONTerm'].split(';') if t.strip()]
            biosample_names = [
                t.strip() for t in row['BiosampleTermName'].split(';') if t.strip()]

            # OntologyTerm column provides per-row phenotype (e.g. EFO_0006340 or EFO:0006340)
            ontology_term_raw = row.get('OntologyTerm', '').strip()
            phenotype = ('ontology_terms/' + ontology_term_raw.replace(':',
                         '_')) if ontology_term_raw else None

            if len(uberon_terms) != len(biosample_names):
                self.logger.warning(
                    f'Skipping {spdi}: UBERONTerm count ({len(uberon_terms)}) '
                    f'does not match BiosampleTermName count ({len(biosample_names)})'
                )
                continue

            gene_ensembl_raw = row.get('GeneEnsembl', '').strip()
            gene = None
            if gene_ensembl_raw:
                if not self.gene_validator.validate(gene_ensembl_raw):
                    self.logger.warning(
                        f'Skipping {spdi}: invalid gene ID {gene_ensembl_raw}')
                    continue
                gene = 'genes/' + gene_ensembl_raw

            phenotype_term_id = ontology_term_raw.replace(':', '_')

            for i, uberon_term in enumerate(uberon_terms):
                biosample_term_id = uberon_term.replace(':', '_')
                biosample_ref = 'ontology_terms/' + biosample_term_id
                biological_context = biosample_names[i]
                # one variant can be associated with multiple genes, and multiple phenotypes in one outlier file (IGVFFI5870RJQU)
                # so we need to include gene and phenotype in the edge key to avoid duplicate edges
                edge_key = (
                    variant_id + '_' + biosample_term_id + '_' + gene_ensembl_raw
                    + '_' + phenotype_term_id + '_' + self.file_accession
                )

                edge_props = {
                    '_key': edge_key,
                    '_from': 'variants/' + variant_id,
                    '_to': biosample_ref,
                    'biosample_term': biosample_ref,
                    'biological_context': biological_context,
                    'phenotype': phenotype,
                    'vcp': float(row['VCP']),
                    'gene': gene,
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
