import csv
import json
import requests
from adapters.base import BaseAdapter
from adapters.helpers import build_variant_id, load_variant, split_spdi, build_regulatory_region_id, bulk_check_variants_in_arangodb, get_file_fileset_by_accession_in_arangodb
from typing import Optional
from adapters.writer import Writer

# Example lines from file from IGVFFI5288RAAV
# score_threshold:0.7
# chrom   pos     spdi    ref     alt     adipose_tissue.TLand    adrenal_gland.TLand     arterial_blood_vessel.TLand     blood.TLand     blood_vessel.TLand      bone_element.TLand      bone_marrow.TLand       brain.TLand   breast.TLand    colon.TLand     connective_tissue.TLand ear.TLand       embryo.TLand    endocrine_gland.TLand   epithelium.TLand        esophagus.TLand exocrine_gland.TLand    extraembryonic_component.TLandeye.TLand       gonad.TLand     heart.TLand     immune_organ.TLand      intestine.TLand kidney.TLand    large_intestine.TLand   limb.TLand      liver.TLand     lung.TLand      lymph_node.TLand        lymphoid_tissue.TLand mammary_gland.TLand     mouth.TLand     musculature_of_body.TLand       nerve.TLand     ovary.TLand     pancreas.TLand  penis.TLand     placenta.TLand  prostate_gland.TLand    skin_of_body.TLand      skin_of_prepuce_of_penis.TLand        small_intestine.TLand   spinal_cord.TLand       spleen.TLand    stomach.TLand   testis.TLand    thymus.TLand    thyroid_gland.TLand     uterus.TLand    vagina.TLand    vasculature.TLand
# chr1    10177   NC_000001.11:10176:A:C  A       C       0.1831400271272394      0.6202947811906289      0.1713818397296201      0.5319590418262792      0.1887214226011916      0.5697150757753037      0.5944817847083231    0.3798165652335787      0.2366499945896307      0.51613758840727        0.1714446338813601      0.2103713204497768      0.6250809670043544      0.6962094742341552      0.3770141687627178      0.2919829297432562    0.3914762200703769      0.6180625392397199      0.2921097006025599      0.6852627900366929      0.3835844614793865      0.1817349559717954      0.3980199807649946      0.1547105101878795      0.4317338674849454    0.4184735607837286      0.6619531031717406      0.1495047235286212      0.7294814151294535      0.2233437729567862      0.2029287217514218      0.2965866985776438      0.2643061096103022      0.7023333448591672    0.6944922648392122      0.7215973332545919      0.2499557162742658      0.619993093642817       0.3446428161133312      0.1550004226418923      0.3041985699560927      0.2348786043630874      0.1908264837756796    0.7054299579262177      0.1993831275895352      0.4514535816025581      0.5956610996726779      0.4211297027650385      0.1729146052388448      0.304196952748633       0.1693659747753729


class TLandVariantsBiosamples(BaseAdapter):
    ALLOWED_LABELS = ['variant', 'variant_biosample']
    TLAND_BIOSAMPLE_MAPPING_FILE = 'https://api.data.igvf.org/documents/2df9515a-8b3d-4971-9254-ba3fa4e1e37f/@@download/attachment/tland_OntTermRef.json'
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
        self.file_accession = self.filepath.split('/')[-1].split('.')[-2]
        self.source_url = 'https://data.igvf.org/tabular-files/' + self.file_accession + '/'
        self.collection_label = 'predicted variant effect on gene expression'
        if label == 'variant_biosample':
            # Example: {'adipose_tissue.TLand': 'UBERON_0001013', 'adrenal_gland.TLand': 'UBERON_0002369', ... }
            self.tland_biosample_mapping = json.loads(
                requests.get(self.TLAND_BIOSAMPLE_MAPPING_FILE).text)

    def _get_schema_type(self):
        if self.label == 'variant_biosample':
            return 'edges'
        else:
            return 'nodes'

    def _get_collection_name(self):
        if self.label == 'variant_biosample':
            return 'variants_biosamples'
        else:
            return 'variants'

    def process_file(self):
        self.writer.open()
        file_fileset_obj = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        self.method = file_fileset_obj['method']
        self.collection_class = file_fileset_obj['class']
        self.biosample_term = file_fileset_obj['samples'][0]

        with open(self.filepath, 'r') as tland_tsv:
            reader = csv.reader(tland_tsv, delimiter='\t')
            chunk_size = 6500

            # #score_threshold:0.7
            self.score_threshold = float(next(reader)[0].split(':')[1])
            self.header = next(reader)

            chunk = []
            for i, row in enumerate(reader, 1):
                chunk.append(row)
                if i % chunk_size == 0:
                    if self.label == 'variant':
                        self.process_variant_chunk(chunk)
                    elif self.label == 'variant_biosample':
                        self.process_edge_chunk(chunk)
                    chunk = []

            if chunk != []:
                if self.label == 'variant':
                    self.process_variant_chunk(chunk)
                elif self.label == 'variant_biosample':
                    self.process_edge_chunk(chunk)

        self.writer.close()

    def process_variant_chunk(self, chunk):
        loaded_spdis = bulk_check_variants_in_arangodb(
            [row[2] for row in chunk])
        skipped_spdis = []

        unloaded_chunk = []
        for row in chunk:
            if row[2] not in loaded_spdis:
                unloaded_chunk.append(row)

        for row in unloaded_chunk:
            spdi = row[2]
            variant, skipped_message = load_variant(spdi)
            if variant:
                variant.update({
                    'pos': int(variant['pos']),
                    'source': TLandVariantsBiosamples.SOURCE,
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
            [row[2] for row in chunk])

        unloaded_chunk = []
        for row in chunk:
            if row[2] in loaded_spdis:
                unloaded_chunk.append(row)

        for row in unloaded_chunk:
            spdi = row[2]
            chr, pos_start, ref, alt = split_spdi(spdi)
            _id = build_variant_id(chr, pos_start + 1, ref, alt, 'GRCh38')

            for i, score in enumerate(row[5:]):
                if float(score) < self.score_threshold:
                    continue

                real_index = i + 5
                biosample = self.header[real_index]
                biosample_term = self.tland_biosample_mapping.get(biosample)

                edge_key = _id + '_' + biosample_term + '_' + self.file_accession

                edge_props = {
                    '_key': edge_key,
                    '_from': 'variants/' + _id,
                    '_to': 'ontology_terms/' + biosample_term,
                    'label': 'predicted allele-specific binding',
                    'score': float(score),
                    'class': self.collection_class,
                    'method': self.method,
                    'biological_context': biosample.replace('.TLand', '').replace('_', ' '),
                    'biosample_term': 'ontology_terms/' + biosample_term,
                    'name': 'modulates regulatory activity of',
                    'inverse_name': 'regulatory activity modulated by',
                    'source': self.SOURCE,
                    'source_url': self.source_url,
                    'files_filesets': 'files_filesets/' + self.file_accession
                }

                if self.validate:
                    self.validate_doc(edge_props)
                self.writer.write(json.dumps(edge_props) + '\n')
