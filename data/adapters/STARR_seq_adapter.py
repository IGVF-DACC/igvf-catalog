from concurrent.futures import ThreadPoolExecutor
import csv
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
# chrom	chromStart	chromEnd	name	score	strand	log2FoldChange	inputCountRef	outputCountRef	inputCountAlt	outputCountAlt	minusLog10PValue	minusLog10QValue	postProbEffect	CI_lower_95	CI_upper_95	variantPos	refAllele	altAllele
# chr1	13833	13834	NC_000001.11:13833:C:T	350	+	0.1053361347394244	1.1178449514319324	1.0921171037854174	0	0.2149853195124717			0.35	0.620196	4.98262	-1	C	T
# chr1	14264	14265	NC_000001.11:14264:C:T	196	+	-0.001248471	0.5788839927058221	0.8904954846250326	0	0.085994128			0.196	0.420745	2.70963	-1	C	T
# chr1	14470	14471	NC_000001.11:14470:G:A	221	+	-0.030633972	0.7984606795942375	0.8232882782382377	0.1013695533505425	0.085994128			0.221	0.280078	1.73764	-1	G	A
# chr1	14792	14793	NC_000001.11:14792:G:A	285	+	0.051253758	0.8783067475536612	0.5376576510943594	0	0.085994128			0.285	0.538601	5.691	-1	G	A
# chr1	15189	15190	NC_000001.11:15189:C:T	174	+	-0.00039391	0.6387685436753899	0.7056756670613465	0.050684777	0.128991192			0.174	0.454782	1.97316	-1	C	T
# chr1	15777	15778	NC_000001.11:15777:A:G	139	+	0.018235348	0.4391533737768306	0.5376576510943594	0	0.085994128			0.139	0.543171	2.39533	-1	A	G
# chr1	16101	16102	NC_000001.11:16101:T:G	183	+	-0.012858891	0.3992303397971187	0.5712612542877568	0	0.085994128			0.183	0.489794	1.80506	-1	T	G
# chr1	16280	16281	NC_000001.11:16280:T:C	165	+	-0.002886834	0.4391533737768306	0.7896846750448403	0.050684777	0.2149853195124717			0.165	0.516841	2.67298	-1	T	C
# chr1	16949	16950	NC_000001.11:16949:A:C	192	+	-0.016602482	1.1777295024015002	0.5040540479009619	0.60821732	0.2579823834149661			0.192	0.573042	1.67965	-1	A	C
# chr1	17005	17006	NC_000001.11:17005:A:G	299	+	0.094992695	1.7765750120971782	0.6048648574811543	0.050684777	0.128991192			0.299	0.544042	3.77914	-1	A	G
# chr1	17020	17021	NC_000001.11:17020:G:A	209	+	-0.017787266	1.6168828761783307	0.5712612542877568	0.8616412034796114	0.2579823834149661			0.209	0.513392	1.55285	-1	G	A
# chr1	17222	17223	NC_000001.11:17222:A:G	457	+	-0.266156311	1.317460121330492	0.554459453	1.926021513660308	0.3869735751224492			0.457	0.357333	1.17642	-1	A	G
# chr1	17385	17386	NC_000001.11:17385:G:A	222	+	0.014391003	1.6168828761783307	0.5880630558844554	0	0.042997064			0.222	0.45808	3.30742	-1	G	A


class STARRseqVariantBiosample(BaseAdapter):
    ALLOWED_LABELS = ['variant', 'variant_biosample']
    SOURCE = 'IGVF'
    CHUNK_SIZE = 6500
    # variants and variant annotations lower than 0.1 postProbEffect are not loaded
    THRESHOLD = 0.1

    def __init__(self, filepath, label, source_url, writer: Optional[Writer] = None, validate=False, **kwargs):
        self.source_url = source_url
        self.file_accession = source_url.split('/')[-2]
        self.seqrepo = SeqRepo('/usr/local/share/seqrepo/2024-12-20')
        self.translator = AlleleTranslator(SeqRepoDataProxy(self.seqrepo))
        self.collection_label = 'variant effect on regulatory element activity'

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

        with open(self.filepath, 'r') as f:
            reader = csv.reader(f, delimiter='\t')
            next(reader)
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

        vcf_rows = []
        for row in chunk:
            chr = row[0][3:]
            vcf = f'{chr}-{row[1]}-{row[17]}-{row[18]}'
            vcf_rows.append((vcf, row))

        # Parallel load_variant calls
        def wrap(vcf_row):
            vcf, row = vcf_row
            variant, skipped = load_variant(
                vcf, translator=self.translator, seq_repo=self.seqrepo)
            return vcf, row, variant, skipped

        with ThreadPoolExecutor(max_workers=8) as executor:
            results = executor.map(wrap, vcf_rows)

        for vcf, row, variant, skipped_message in results:
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
