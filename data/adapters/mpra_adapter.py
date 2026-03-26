"""
Unified MPRA adapter for both IGVF and ENCODE MPRA data.

- IGVF: requires reference_filepath (MPRA sequence designs TSV). Supports all labels
  (genomic_element, genomic_element_biosample, variant, genomic_element_from_variant,
  variant_biosample). Input: TSV effect files.
- ENCODE: no MPRA sequence designs reference file. Supports only genomic_element and genomic_element_biosample.
  Input: BED (optionally gzipped). Output format is the same; minusLog10PValue,
  minusLog10QValue, and treatments_term_ids are set to None where not available.
"""

# Example rows from ENCODE lenti-MPRA bed file ENCFF802FUV.bed: (the last two columns are the same for all rows)
# Column 7: activity score (i.e. log2(RNA/DNA)); Column 8: DNA count; Column 9: RNA count
# chr1	10410	10610	HepG2_DNasePeakNoPromoter1	212	+	-0.843	0.307	0.171	-1	-1

# Example rows from IGVFFI4914OUJH - MPRA sequence designs
# name	sequence	category	class	source	ref	chr	start	end	strand	variant_class	variant_pos	SPDI	allele	info
# Variant 7193 (chr9:100000294-100000494)	TCCACCCGTCTCGGACTCCCAAAGTGCTGGGATTACAGGCGTGAGCCACGGCGCCCGGCCTGGAGCTTGTGTTACTAAAAGACATGCAAACGCCCTTAACCGCTAAGCTCCTGAGGGGTAACGGTATGCTACAAAAGTGCTTCTGAGCTACTACTCCTGGAGGCTTGGTCCGAGTGACCGCAGCAGTGGGCGCGGTGGAA	variant	test	Supplementary Table S6 from An et al., 2018	GRCh38	chr9	97238011	97238211	+	["SNV"]	[100]	["NC_000009.12:97238111:C:T"]	["ref"]	for questions ask Ahituv lab
# Variant 7194 (chr9:100000294-100000494)	TCCACCCGTCTCGGACTCCCAAAGTGCTGGGATTACAGGCGTGAGCCACGGCGCCCGGCCTGGAGCTTGTGTTACTAAAAGACATGCAAACGCCCTTAACTGCTAAGCTCCTGAGGGGTAACGGTATGCTACAAAAGTGCTTCTGAGCTACTACTCCTGGAGGCTTGGTCCGAGTGACCGCAGCAGTGGGCGCGGTGGAA	variant	test	Supplementary Table S6 from An et al., 2018	GRCh38	chr9	97238011	97238211	+	["SNV"]	[100]	["NC_000009.12:97238111:C:T"]	["alt"]	for questions ask Ahituv lab
# Variant 7195 (chr9:100743726-100743926)	TTTGCCCTGATGCTAAGGATTAATACCACCTCCTCCGGGAGCCATCAGGTTACCACTCTCTAGCACAGAGCTACCACGTTTAAGACTCCTTCAGCACCATCCCCCCTTTTCCTGCACGAGGACACTTGCATGCTGTTTGGTATTAAAAGCCCTCTGCAACTGTTCCCAACCTACAGCACCAAAGTAGCCCCCCACCATG	variant	test	Supplementary Table S6 from An et al., 2018	GRCh38	chr9	97981444	97981642	+	NA	NA	NA	NA	for questions ask Ahituv lab

# Example rows from IGVFFI1323RCIE - reporter genomic variant effects
# chr9	135961939	135961940	NC_000009.12:135961939:C:T	3	+	0.0040	0.7019	0.4889	0.7251	0.5157	0.1089	0.0436	0.0009	-0.0240	0.0321	100	C	T
# chr9	135962406	135962415	NC_000009.12:135962406:CTTACTTAC:CTTAC	8	+	0.0096	0.6739	0.4672	0.6808	0.4822	0.2451	0.1024	0.0013	-0.0234	0.0425	102	CTTACTTAC	CTTAC
# chr9	136120451	136120452	NC_000009.12:136120451:C:T	13	+	-0.0154	0.6922	0.6222	0.7067	0.6082	0.4623	0.2084	0.0015	-0.0474	0.0166	100	C	T

# Example rows from IGVFFI8207IHFY - reporter genomic element effects
# chr9	135962308	135962508	Variant_7027_(chr9:138854152-138854352)	130	+	-0.1796	0.6739	0.4672	0.0000	0.0000
# chr9	136120351	136120551	Variant_7029_(chr9:139012198-139012398)	48	+	-0.0675	0.6922	0.6222	0.0000	0.0000
# chr9	136248340	136248540	Variant_7031_(chr9:139140187-139140387)	172	+	-0.2376	0.5948	0.3434	0.0000	0.0000

import csv
import gzip
import json
from typing import Optional
from collections import defaultdict
import ast

from adapters.base import BaseAdapter
from adapters.helpers import (
    build_regulatory_region_id,
    bulk_check_variants_in_arangodb,
    load_variant,
    get_file_fileset_by_accession_in_arangodb
)
from adapters.writer import Writer


class MPRAAdapter(BaseAdapter):
    ALLOWED_LABELS = [
        'genomic_element',
        'genomic_element_biosample',
        'variant',
        'genomic_element_from_variant',
        'variant_biosample'
    ]

    THRESHOLD = 1
    CHUNK_SIZE = 6500
    BLACKLISTED_EFFECT_NAMES = {
        # Cardiac/neuro design bug: ALT-only entries with no reference design and not explicitly designated as alts.
        'cardiac_neuro_cava_random:alt_kansl1|ensg00000120071.15|eh38e3227108_rev_tile1-1_kansl1|ensg00000120071.15|eh38e3227108|17-46152590-g-c',
        'cardiac_neuro_cava_random:alt_kansl1|ensg00000120071.15|eh38e3227108_rev_tile1-1_kansl1|ensg00000120071.15|eh38e3227108|17-46152590-g-t',
        'cardiac_neuro_cava_random:alt_kansl1|ensg00000120071.15|eh38e3227108_rev_tile1-1_kansl1|ensg00000120071.15|eh38e3227108|17-46152592-g-c',
    }

    def __init__(
        self,
        filepath,
        label,
        source_url,
        writer: Optional[Writer] = None,
        reference_filepath: Optional[str] = None,
        reference_source_url: Optional[str] = None,
        validate=False,
        **kwargs
    ):
        # Raise before super().__init__ so we don't load variant schema when ENCODE has no sequence designs
        if reference_filepath is None and label in ('variant', 'genomic_element_from_variant', 'variant_biosample'):
            if 'encodeproject.org' in (source_url or ''):
                raise ValueError(
                    'ENCODE MPRA files do not have MPRA sequence designs. '
                    'Use label genomic_element or genomic_element_biosample only.'
                )

        super().__init__(filepath, label, writer, validate)
        self.source_url = source_url
        self.file_accession = source_url.rstrip('/').split('/')[-1]

        if 'encodeproject.org' in source_url:
            self.source = 'ENCODE'
        elif 'data.igvf.org' in source_url:
            self.source = 'IGVF'
        else:
            raise ValueError(f'Invalid source URL: {source_url}')

        self.has_sequence_designs = reference_filepath is not None

        self.files_filesets = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)

        self.variant_to_element = defaultdict(set)
        self.design_elements = set()
        self.coords_to_element_name = {}
        self.design_name_alleles = defaultdict(set)
        self.design_element_alleles = defaultdict(set)
        self.design_name_class = {}
        if self.has_sequence_designs:
            self.mpra_design_file = reference_filepath
            self.reference_source_url = reference_source_url or ''
            self.reference_file_accession = (
                reference_source_url or '').rstrip('/').split('/')[-1]
            self.load_mpra_design_mapping(self.mpra_design_file)
        else:
            self.mpra_design_file = None
            self.reference_source_url = None
            self.reference_file_accession = None

    def _open_file(self):
        """Open file as text, handling optional gzip."""
        if self.filepath.endswith('.gz'):
            return gzip.open(self.filepath, 'rt')
        return open(self.filepath, 'r')

    def _get_schema_type(self):
        if self.label in ['genomic_element_biosample', 'variant_biosample']:
            return 'edges'
        return 'nodes'

    def _get_collection_name(self):
        if self.label == 'variant':
            return 'variants'
        if self.label == 'variant_biosample':
            return 'variants_biosamples'
        if self.label in ['genomic_element', 'genomic_element_from_variant']:
            return 'genomic_elements'
        if self.label == 'genomic_element_biosample':
            return 'genomic_elements_biosamples'
        return None

    @staticmethod
    def safe_float(value):
        try:
            parsed = float(value)
            return None if parsed != parsed else parsed
        except (TypeError, ValueError):
            return None

    @classmethod
    def safe_int(cls, value):
        parsed = cls.safe_float(value)
        if parsed is None:
            return None
        return int(parsed) if parsed.is_integer() else None

    @staticmethod
    def normalize_design_name(name):
        if not name:
            return ''
        return ' '.join(str(name).replace('_', ' ').strip().lower().split())

    @staticmethod
    def normalize_strand(strand):
        value = (strand or '').strip()
        if value in ('+', '-'):
            return value
        return '.'

    @classmethod
    def strand_token(cls, strand):
        normalized = cls.normalize_strand(strand)
        if normalized == '+':
            return 'plus'
        if normalized == '-':
            return 'minus'
        return 'na'

    @classmethod
    def make_design_key(cls, chr_, start, end, strand):
        return (chr_, start, end, cls.normalize_strand(strand))

    @classmethod
    def build_mpra_element_node_id(cls, chr_, start, end, suffix):
        """Genomic element node _key: coordinates + suffix only (strand lives on edges)."""
        region_id = build_regulatory_region_id(chr_, start, end, 'MPRA')
        return f'{region_id}_{suffix}'

    def load_mpra_design_mapping(self, mpra_design_file):
        with open(mpra_design_file, 'r') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for i, row in enumerate(reader, 1):
                try:
                    key = self.make_design_key(
                        row['chr'], row['start'], row['end'], row.get('strand'))
                    self.design_elements.add(key)
                    # MPRA sequence designs TSV has a "name" column; we use it as the element node name.
                    self.coords_to_element_name[key] = row.get('name')
                except Exception:
                    pass

                allele_raw = row.get('allele')
                normalized_name = self.normalize_design_name(row.get('name'))
                if normalized_name:
                    self.design_name_class[normalized_name] = (
                        row.get('class') or '').strip().lower()
                if allele_raw not in (None, '', 'NA', 'NaN'):
                    try:
                        allele_values = ast.literal_eval(allele_raw)
                    except (ValueError, SyntaxError) as e:
                        raise ValueError(
                            f'Malformed allele at row {i}: {allele_raw!r}') from e
                    if not isinstance(allele_values, list):
                        raise ValueError(
                            f'Malformed allele at row {i}: expected list, got {type(allele_values).__name__}'
                        )
                    normalized_alleles = set()
                    for allele in allele_values:
                        if allele is None:
                            continue
                        normalized = str(allele).strip().lower()
                        normalized_alleles.add(normalized)
                        self.design_element_alleles[key].add(normalized)
                        if normalized_name:
                            self.design_name_alleles[normalized_name].add(
                                normalized)
                    if 'ref' in normalized_alleles and 'alt' in normalized_alleles:
                        raise ValueError(
                            f'Malformed allele at row {i}: unexpected mixed allele values {allele_values!r}'
                        )

                if row.get('SPDI') in (None, '', 'NA', 'NaN'):
                    continue
                try:
                    spdi_list = ast.literal_eval(row['SPDI'])
                except (ValueError, SyntaxError) as e:
                    raise ValueError(
                        f"Malformed SPDI at row {i}: {row['SPDI']!r}") from e

                for spdi in spdi_list:
                    self.variant_to_element[spdi].add(key)

    @classmethod
    def _is_blacklisted_effect_name(cls, effect_name):
        return (effect_name or '').strip().lower() in cls.BLACKLISTED_EFFECT_NAMES

    def process_file(self):
        self.seen_elements = set()
        self.collection_label_variants_elements = 'variant effect on regulatory element activity'
        self.collection_label_elements_biosamples = 'regulatory element activity'
        self.collection_class = self.files_filesets.get('class')
        self.method = self.files_filesets.get('method')
        samples = self.files_filesets.get('samples') or []
        raw = samples[0] if samples else None
        # Normalize to full document ID (fileset may give "EFO_0002067" or "ontology_terms/EFO_0002067")
        self.biosample_term = (raw if (raw or '').startswith(
            'ontology_terms/') else f'ontology_terms/{raw}') if raw else None
        self.simple_sample_summaries = self.files_filesets.get(
            'simple_sample_summaries') or []
        self.treatments_term_ids = self.files_filesets.get(
            'treatments_term_ids')

        if self.label in ('genomic_element', 'genomic_element_biosample'):
            self._process_element_effects_file()
            return

        self.writer.open()
        with self._open_file() as f:
            reader = csv.reader(f, delimiter='\t')
            chunk = []
            for i, row in enumerate(reader, 1):
                chunk.append(row)
                if i % self.CHUNK_SIZE == 0:
                    self._process_chunk_igvf(chunk)
                    chunk = []
            if chunk:
                self._process_chunk_igvf(chunk)
        self.writer.close()

    def _process_element_effects_file(self):
        """Process BED/TSV element effects (same format for IGVF and ENCODE). Writes genomic_element and/or genomic_element_biosample."""
        self.writer.open()
        seen_element_ids = set()
        biosample_term_key = (self.biosample_term or '').split('/')[-1]
        # Element id suffix: design file accession when we have sequence designs (IGVF), else effect file accession (ENCODE)
        element_id_suffix = self.reference_file_accession if self.has_sequence_designs else self.file_accession

        with self._open_file() as f:
            reader = csv.reader(f, delimiter='\t')
            rows = list(reader)
            effect_counts_by_region = defaultdict(int)
            for row in rows:
                effect_counts_by_region[self.make_design_key(
                    row[0], row[1], row[2], row[5])] += 1

            missing_allele_multi_effect = []
            for row in rows:
                chr_, start, end, strand = row[0], row[1], row[2], row[5]
                minus_q = self.safe_float(row[10]) if len(
                    row) > 10 and row[10] != '-1' else None
                significant = minus_q is not None and minus_q >= self.THRESHOLD
                region_id = build_regulatory_region_id(
                    chr_, start, end, 'MPRA')
                element_id = self.build_mpra_element_node_id(
                    chr_, start, end, element_id_suffix)
                element_key = self.make_design_key(chr_, start, end, strand)

                if self.label == 'genomic_element':
                    if self.has_sequence_designs and element_key not in self.design_elements:
                        raise ValueError(
                            f'Genomic element {(chr_, start, end, strand)} from {self.file_accession} is not present in the MPRA sequence designs file {self.reference_file_accession}.')
                    if self.has_sequence_designs and self._is_blacklisted_effect_name(row[3]):
                        # Ignore known bad design entries.
                        continue
                    if element_id in seen_element_ids:
                        continue
                    seen_element_ids.add(element_id)
                    if self.has_sequence_designs:
                        # IGVF sequence designs TSV first column is the element design name
                        element_name = self.coords_to_element_name.get(
                            element_key)
                        if element_name is None:
                            raise ValueError(
                                f'Missing MPRA sequence design name for {(chr_, start, end, strand)} in {self.reference_file_accession}.')
                    else:
                        # ENCODE MPRA BED 4th column is the element name/design identifier
                        element_name = row[3]
                    props = {
                        '_key': element_id,
                        'name': element_name,
                        'chr': chr_,
                        'start': int(start),
                        'end': int(end),
                        'method': self.method,
                        'type': 'tested elements',
                        'source': self.source,
                        'source_url': self.source_url,
                        'files_filesets': 'files_filesets/' + element_id_suffix
                    }
                    if self.validate:
                        self.validate_doc(props)
                    self.writer.write(json.dumps(props) + '\n')

                elif self.label == 'genomic_element_biosample':
                    if self.has_sequence_designs:
                        normalized_effect_name = self.normalize_design_name(
                            row[3])
                        effect_class = self.design_name_class.get(
                            normalized_effect_name, '')
                        if 'control' in effect_class:
                            # Controls can be present without allele values and
                            # should not produce genomic_element_biosample edges.
                            continue
                        # Prefer design-name mapping when available; fallback to
                        # coordinate mapping for legacy files.
                        alleles = self.design_name_alleles.get(
                            normalized_effect_name, set())
                        if not alleles:
                            if effect_counts_by_region[element_key] > 1:
                                missing_allele_multi_effect.append(
                                    (element_key, row[3]))
                                continue
                            alleles = self.design_element_alleles.get(
                                element_key, set())
                        if self._is_blacklisted_effect_name(row[3]):
                            # Ignore known bad design entries.
                            continue
                        if alleles and 'ref' not in alleles:
                            # Only ref element effects should be loaded.
                            continue
                    edge_id = '_'.join(
                        [region_id, self.strand_token(strand), self.file_accession, biosample_term_key])
                    minus_p = self.safe_float(row[9]) if len(
                        row) > 9 and row[9] != '-1' else None
                    minus_q_edge = self.safe_float(row[10]) if len(
                        row) > 10 and row[10] != '-1' else None
                    props = {
                        '_key': edge_id,
                        '_from': 'genomic_elements/' + element_id,
                        '_to': self.biosample_term,
                        'strand': strand,
                        'log2FC': self.safe_float(row[6]),
                        'bed_score': self.safe_int(row[4]),
                        'DNA_count': self.safe_float(row[7]),
                        'RNA_count': self.safe_float(row[8]),
                        'minusLog10PValue': minus_p,
                        'minusLog10QValue': minus_q_edge,
                        'significant': significant,
                        'class': self.collection_class,
                        'label': self.collection_label_elements_biosamples,
                        'name': 'expression effect in',
                        'inverse_name': 'has expression effect from',
                        'method': self.method,
                        'source': self.source,
                        'source_url': self.source_url,
                        'files_filesets': 'files_filesets/' + self.file_accession,
                        'biological_context': (self.simple_sample_summaries or [''])[0],
                        'biosample_term': self.biosample_term,
                        'treatments_term_ids': self.treatments_term_ids if self.treatments_term_ids else None,
                    }
                    if self.validate:
                        self.validate_doc(props)
                    self.writer.write(json.dumps(props) + '\n')

            if missing_allele_multi_effect:
                raise ValueError(
                    'Missing allele annotations for regions with multiple element effects '
                    f'(examples: {missing_allele_multi_effect[:5]})'
                )

        self.writer.close()

    def _process_chunk_igvf(self, chunk):
        if self.label == 'variant':
            self._process_variant_chunk(chunk)
        elif self.label == 'variant_biosample':
            self._process_variant_biosample_chunk(chunk)
        elif self.label == 'genomic_element_from_variant':
            self._process_genomic_element_chunk(chunk)

    def _process_variant_chunk(self, chunk):
        spdis = [row[3] for row in chunk]
        loaded_spdis = bulk_check_variants_in_arangodb(
            spdis, check_by='spdi', excluded_files_filesets=f'files_filesets/{self.file_accession}')
        for row in chunk:
            spdi = row[3]
            if spdi in loaded_spdis:
                continue
            variant, skipped_message = load_variant(spdi)
            if variant:
                variant.update({
                    'source': self.source,
                    'source_url': self.source_url,
                    'files_filesets': f'files_filesets/{self.file_accession}'
                })
                self.writer.write(json.dumps(variant) + '\n')
            elif skipped_message:
                self.logger.warning(f'Skipped {spdi}: {skipped_message}')
                with open('./skipped_variants.jsonl', 'a') as out:
                    out.write(json.dumps(skipped_message) + '\n')

    def _process_genomic_element_chunk(self, chunk):
        """Emit genomic_element nodes from variant->element mapping (genomic_element_from_variant label only)."""
        coord_to_strands = defaultdict(set)
        for element_coords_set in self.variant_to_element.values():
            for chr_, start, end, strand in element_coords_set:
                coord_to_strands[(chr_, start, end)].add(strand)

        for coord_key in sorted(coord_to_strands.keys()):
            if coord_key in self.seen_elements:
                continue
            self.seen_elements.add(coord_key)
            chr_, start, end = coord_key
            strands = coord_to_strands[coord_key]
            element_name = None
            for strand in sorted(strands):
                element_name = self.coords_to_element_name.get(
                    self.make_design_key(chr_, start, end, strand))
                if element_name:
                    break
            if element_name is None:
                raise ValueError(
                    f'Missing MPRA sequence design name for {coord_key} in {self.reference_file_accession}.')
            _id = self.build_mpra_element_node_id(
                chr_, start, end, self.reference_file_accession)
            props = {
                '_key': _id,
                'name': element_name,
                'chr': chr_,
                'start': int(start),
                'end': int(end),
                'method': self.method,
                'type': 'tested elements',
                'source': self.source,
                'source_url': self.reference_source_url,
                'files_filesets': f'files_filesets/{self.reference_file_accession}'
            }
            if self.validate:
                self.validate_doc(props)
            self.writer.write(json.dumps(props) + '\n')

    def _process_variant_biosample_chunk(self, chunk):
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
                    self.logger.warning(f'Skipped {spdi}: {skipped_message}')
                continue
            variant_id = variant['_key']
            biosample_term_key = (self.biosample_term or '').split('/')[-1]

            for element_chr, element_start, element_end, element_strand in self.variant_to_element[spdi]:
                element_id = self.build_mpra_element_node_id(
                    element_chr, element_start, element_end, self.reference_file_accession)
                # Strand distinguishes edges when node id is coord-only.
                edge_key = '_'.join([
                    variant_id,
                    element_id,
                    self.strand_token(element_strand),
                    biosample_term_key,
                    self.file_accession,
                ])

                minus_q = self.safe_float(row[12])
                edge_props = {
                    '_key': edge_key,
                    '_from': f'variants/{variant_id}',
                    '_to': self.biosample_term,
                    'genomic_element': f'genomic_elements/{element_id}',
                    'bed_score': self.safe_int(row[4]),
                    'log2FC': self.safe_float(row[6]),
                    'DNA_count_ref': self.safe_float(row[7]),
                    'RNA_count_ref': self.safe_float(row[8]),
                    'DNA_count_alt': self.safe_float(row[9]),
                    'RNA_count_alt': self.safe_float(row[10]),
                    'minusLog10PValue': self.safe_float(row[11]),
                    'minusLog10QValue': minus_q,
                    'significant': minus_q is not None and minus_q >= self.THRESHOLD,
                    'postProbEffect': self.safe_float(row[13]),
                    'CI_lower_95': self.safe_float(row[14]),
                    'CI_upper_95': self.safe_float(row[15]),
                    'class': self.collection_class,
                    'label': self.collection_label_variants_elements,
                    'name': 'modulates regulatory activity of',
                    'inverse_name': 'regulatory activity modulated by',
                    'method': self.method,
                    'source': self.source,
                    'source_url': self.source_url,
                    'files_filesets': 'files_filesets/' + self.file_accession,
                    'biological_context': (self.simple_sample_summaries or [''])[0],
                    'biosample_term': self.biosample_term,
                    'treatments_term_ids': self.treatments_term_ids or None,
                }

                if self.validate:
                    self.validate_doc(edge_props)
                self.writer.write(json.dumps(edge_props) + '\n')
