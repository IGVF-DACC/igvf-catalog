import csv
import json
from adapters.base import BaseAdapter
from adapters.helpers import build_variant_id, split_spdi, build_regulatory_region_id, bulk_check_variants_in_arangodb, get_file_fileset_by_accession_in_arangodb
from typing import Optional
from adapters.writer import Writer

# Example lines from file from IGVFFI5288RAAV
# chr10	10457	10458	0.1230434926260573	NC_000010.11:10457:T:C
# chr10	10468	10469	0.12064427634610851	NC_000010.11:10468:T:C
# chr10	10552	10553	0.1257567042681801	NC_000010.11:10552:C:A
# chr10	10776	10787	-0.19332494419402918	NC_000010.11:10776:AGGCGCGGAGG:A
# chr10	11396	11397	-0.14256330079878898	NC_000010.11:11396:G:C
# chr10	13342	13343	0.21266985444695388	NC_000010.11:13342:G:A
# chr10	18929	18930	0.1042946029753749	NC_000010.11:18929:C:A
# chr10	28566	28567	-0.3547333768296781	NC_000010.11:28566:G:A
# chr10	35882	35883	0.1866702247789206	NC_000010.11:35882:T:C
# chr10	43093	43094	-0.21362561394303198	NC_000010.11:43093:C:T


class BlueSTARRVariantBiosample(BaseAdapter):
    SOURCE = 'IGVF'
    ELEMENT_FILE_ACCESSION = 'ENCFF420VPZ'  # CCRE from ENCODE
    ACCESSION_WITH_CCRES = 'IGVFFI1663LKVQ'

    # Accessions:
    # IGVFFI3351LASN
    # IGVFFI1663LKVQ
    # IGVFFI5288RAAV
    # IGVFFI0818FMCC

    def __init__(
        self,
        filepath,
        label='variant_biosample',
        writer: Optional[Writer] = None,
        validate=False,
        **kwargs
    ):
        # Initialize base adapter first
        super().__init__(filepath, label, writer, validate)
        self.file_accession = self.filepath.split('/')[-1].split('.')[-2]
        self.source_url = 'https://data.igvf.org/tabular-files/' + self.file_accession + '/'
        self.collection_label = 'predicted variant effect on gene expression'

    def _get_schema_type(self):
        return 'edges'

    def _get_collection_name(self):
        return 'variants_biosamples'

    def process_file(self):
        self.writer.open()
        file_fileset_obj = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        self.method = file_fileset_obj['method']
        self.collection_class = file_fileset_obj['class']
        self.biosample_term = file_fileset_obj['samples'][0]
        self.biological_context = file_fileset_obj['simple_sample_summaries'][0]

        with open(self.filepath, 'r') as bluestarr_tsv:
            reader = csv.reader(bluestarr_tsv, delimiter='\t')
            chunk_size = 6500

            chunk = []
            for i, row in enumerate(reader, 1):
                chunk.append(row)
                if i % chunk_size == 0:
                    self.process_edge_chunk(chunk)
                    chunk = []

            if chunk != []:
                self.process_edge_chunk(chunk)

        self.writer.close()

    def process_edge_chunk(self, chunk):
        loaded_spdis = bulk_check_variants_in_arangodb(
            [row[4] for row in chunk])

        unloaded_chunk = []
        for row in chunk:
            if row[4] in loaded_spdis:
                unloaded_chunk.append(row)

        for row in unloaded_chunk:
            spdi = row[4]
            chr, pos_start, ref, alt = split_spdi(spdi)
            _id = build_variant_id(chr, pos_start + 1, ref, alt, 'GRCh38')

            genomic_element_id = None
            if self.file_accession == BlueSTARRVariantBiosample.ACCESSION_WITH_CCRES:
                genomic_element_id = 'genomic_elements/' + build_regulatory_region_id(
                    row[0], row[1], row[2], 'candidate_cis_regulatory_element') + '_' + BlueSTARRVariantBiosample.ELEMENT_FILE_ACCESSION

            edge_key = _id + '_' + self.biosample_term + '_' + self.file_accession

            edge_props = {
                '_key': edge_key,
                '_from': 'variants/' + _id,
                '_to': 'ontology_terms/' + self.biosample_term,
                'genomic_element': genomic_element_id,
                'log2FC': float(row[3]),
                'class': self.collection_class,
                'label': self.collection_label,
                'method': self.method,
                'biological_context': self.biological_context,
                'biosample_term': self.biosample_term,
                'name': 'modulates regulatory activity of',
                'inverse_name': 'regulatory activity modulated by',
                'source': self.SOURCE,
                'source_url': self.source_url,
                'files_filesets': 'files_filesets/' + self.file_accession
            }

            if self.validate:
                self.validate_doc(edge_props)

            self.writer.write(json.dumps(edge_props) + '\n')
