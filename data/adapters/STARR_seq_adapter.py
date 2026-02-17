from concurrent.futures import ThreadPoolExecutor
import csv
import gzip
import hashlib
import json
from typing import Optional

from biocommons.seqrepo import SeqRepo
from ga4gh.vrs.dataproxy import SeqRepoDataProxy
from ga4gh.vrs.extras.translator import AlleleTranslator

from adapters.base import BaseAdapter
from adapters.helpers import bulk_check_variants_in_arangodb, load_variant, get_file_fileset_by_accession_in_arangodb
from adapters.writer import Writer

# Example rows from Gersbach's STARR-seq data
# chr1	13527	13528	NC_000001.11:13527:C:G	228	+	-0.0278029095483658	0.7114327127487537	0.7149746114749761	0.1321046194607542	0.1093490723098078	NaN	NaN	0.228	0.412242	1.84585	-1	G
# chr1	13769	13770	NC_000001.11:13769:C:G	312	+	-0.1017057269649259	0.6019815261720225	0.8937182643437201	0.1321046194607542	0.0	NaN	NaN	0.312	0.219367	1.58841	-1	C	G
# chr1	13867	13868	NC_000001.11:13867:A:G	199	+	-0.0145221575215694	0.5472559328836568	0.7149746114749761	0.0	0.0	NaN	NaN	0.199	0.30534	1.93752	-1	A	G
# chr1	14132	14133	NC_000001.11:14132:G:C	417	+	-0.1750220194242328	0.4925303395952911	0.491545045389046	0.0	0.0	NaN	NaN	0.417	0.202079	1.47554	-1	G	C
# chr1	14646	14647	NC_000001.11:14646:G:C	295	+	-0.0678382669410818	0.8208838993254852	0.8490323511265341	0.0	0.0	NaN	NaN	0.295	0.170571	1.91351	-1	G	C
# chr1	14699	14700	NC_000001.11:14699:G:A	212	+	0.0172948227757965	0.9303350859022164	0.67028869825779	0.0	0.2186981446196156	NaN	NaN	0.212	0.525642	2.52342	-1	G	A
# chr1	14751	14752	NC_000001.11:14751:G:A	205	+	-0.0081315406059707	0.9303350859022164	0.5809168718234181	0.0	0.1093490723098078	NaN	NaN	0.205	0.540865	2.80752	-1	G	A
# chr1	14842	14843	NC_000001.11:14842:G:A	436	+	-0.219595824347398	0.7114327127487537	0.491545045389046	0.528418477843017	0.0	NaN	NaN	0.436	0.0993272	1.37549	-1	G	A
# chr1	15339	15340	NC_000001.11:15339:G:A	281	+	-0.0406237654350125	0.5472559328836568	0.536230958606232	0.1321046194607542	0.1093490723098078	NaN	NaN	0.281	0.299043	1.69411	-1	A
# chr1	15445	15446	NC_000001.11:15445:C:A	204	+	-0.0051104102040069	0.6019815261720225	0.4468591321718601	0.2642092389215085	0.2186981446196156	NaN	NaN	0.204	0.427119	2.02552	-1	A


class STARRseqVariantBiosample(BaseAdapter):
    ALLOWED_LABELS = ['variant', 'variant_biosample']
    SOURCE = 'IGVF'
    CHUNK_SIZE = 6500
    # variants and variant annotations lower than 0.1 postProbEffect are not loaded
    THRESHOLD = 0.1

    def __init__(
        self,
        filepath,
        label,
        source_url,
        writer: Optional[Writer] = None,
        validate=False,
        excluded_file_accessions=None,
        **kwargs
    ):
        self.source_url = source_url
        self.file_accession = source_url.split('/')[-2]
        self.seqrepo = SeqRepo('/usr/local/share/seqrepo/2024-12-20')
        self.translator = AlleleTranslator(SeqRepoDataProxy(self.seqrepo))
        self.collection_label = 'variant effect on regulatory element activity'
        # Optional list of file accessions whose previously-loaded variants should
        # NOT be considered "already loaded" for this run.
        self.excluded_file_accessions = excluded_file_accessions or []

        super().__init__(filepath, label, writer, validate)

    def _get_schema_type(self):
        """Return schema type based on label."""
        if self.label == 'variant':
            return 'nodes'
        else:
            return 'edges'

    def _get_collection_name(self):
        """Get collection based on label."""
        if self.label == 'variant':
            return 'variants'
        else:
            return 'variants_biosamples'

    def process_file(self):
        file_fileset = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        self.simple_sample_summaries = file_fileset['simple_sample_summaries']
        self.biosample_term = file_fileset['samples']
        self.treatments_term_ids = file_fileset['treatments_term_ids']
        self.method = file_fileset['method']
        self.collection_class = file_fileset['class']
        self.writer.open()

        open_file = gzip.open(self.filepath, 'rt') if self.filepath.endswith(
            '.gz') else open(self.filepath, 'r')
        with open_file as f:
            reader = csv.reader(f, delimiter='\t')
            chunk = []
            for i, row in enumerate(reader, 1):
                postProbEffect = float(row[13])
                if postProbEffect < STARRseqVariantBiosample.THRESHOLD:
                    continue
                chunk.append(row)
                if i % STARRseqVariantBiosample.CHUNK_SIZE == 0:
                    self.process_chunk(chunk)
                    chunk.clear()

            if chunk:
                self.process_chunk(chunk)

        self.writer.close()

    def process_chunk(self, chunk):
        variant_id_to_variant = {}
        variant_id_to_row = {}
        skipped_spdis = []
        to_check = []

        spdi_rows = []
        for row in chunk:
            spdi = row[3]  # "name" column (e.g., NC_000001.11:13527:C:G)
            spdi_rows.append((spdi, row))

        # Parallel load_variant calls
        def wrap(spdi_row):
            spdi, row = spdi_row
            variant, skipped = load_variant(
                spdi, translator=self.translator, seq_repo=self.seqrepo
            )
            return spdi, row, variant, skipped

        with ThreadPoolExecutor(max_workers=8) as executor:
            results = executor.map(wrap, spdi_rows)

        for spdi, row, variant, skipped_message in results:
            if variant:
                variant_id = variant['_key']
                variant_id_to_variant[variant_id] = variant
                if variant_id not in variant_id_to_row:
                    variant_id_to_row[variant_id] = []
                variant_id_to_row[variant_id].append(row)
                to_check.append(variant_id)
            if skipped_message:
                skipped_spdis.append(skipped_message)

        if skipped_spdis:
            self.logger.warning(f'Skipped {len(skipped_spdis)} variants:')
            for skipped in skipped_spdis:
                self.logger.warning(
                    f"  - {skipped['variant_id']}: {skipped['reason']}")
            with open('./skipped_variants.jsonl', 'a') as out:
                for skipped in skipped_spdis:
                    out.write(json.dumps(skipped) + '\n')

        # For STARR-seq reloads we want to *not* treat variants previously loaded
        # from this same STARR-seq fileset as "already loaded", so we can emit
        # updated variant nodes (e.g. when switching identifier schemes to SPDI).
        #
        # IMPORTANT: Only do this for the variant node load. For edge loads we
        # must see already-present variants to emit edges.
        if self.label == 'variant':
            excluded_files_filesets = (
                [f'files_filesets/{acc}' for acc in self.excluded_file_accessions]
                + [f'files_filesets/{self.file_accession}']
            )
            loaded_variants = bulk_check_variants_in_arangodb(
                to_check,
                check_by='_key',
                excluded_files_filesets=excluded_files_filesets,
            )
        else:
            loaded_variants = bulk_check_variants_in_arangodb(
                to_check, check_by='_key')

        if self.label == 'variant':
            self.process_variants(variant_id_to_variant, loaded_variants)
        elif self.label == 'variant_biosample':
            self.process_edge(variant_id_to_row, loaded_variants)

    def process_variants(self, variant_id_to_variant, loaded_variants):
        for variant_id, variant in variant_id_to_variant.items():
            if variant_id in loaded_variants:
                continue
            else:
                variant.update({
                    'source': self.SOURCE,
                    'source_url': self.source_url,
                    'files_filesets': f'files_filesets/{self.file_accession}'
                })
                if self.validate:
                    self.validate_doc(variant)
                self.writer.write(json.dumps(variant) + '\n')

    def process_edge(self, variant_id_to_row, loaded_variants):
        for variant in variant_id_to_row:
            if variant in loaded_variants:
                for row in variant_id_to_row[variant]:
                    _raw_key = f'{variant}_{self.biosample_term[0].split("/")[1]}_{self.file_accession}'
                    _key = _raw_key if len(_raw_key) < 254 else hashlib.sha256(
                        _raw_key.encode()).hexdigest()
                    edge_props = {
                        '_key': _key,
                        '_from': 'variants/' + variant,
                        '_to': self.biosample_term[0],
                        'name': 'modulates expression in',
                        'inverse_name': 'regulatory activity modulated by',
                        'log2FoldChange': float(row[6]),
                        'inputCountRef': float(row[7]),
                        'outputCountRef': float(row[8]),
                        'inputCountAlt': float(row[9]),
                        'outputCountAlt': float(row[10]),
                        'postProbEffect': float(row[13]),
                        'CI_lower_95': float(row[14]),
                        'CI_upper_95': float(row[15]),
                        'label': self.collection_label,
                        'method': self.method,
                        'class': self.collection_class,
                        'source': self.SOURCE,
                        'source_url': self.source_url,
                        'files_filesets': 'files_filesets/' + self.file_accession,
                        'biological_context': self.simple_sample_summaries[0],
                        'biosample_term': self.biosample_term[0],
                        'treatments_term_ids': self.treatments_term_ids if self.treatments_term_ids else None
                    }

                    if self.validate:
                        self.validate_doc(edge_props)
                    self.writer.write(json.dumps(edge_props) + '\n')
