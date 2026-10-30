"""
MPRA (Massively Parallel Reporter Assay) — unified IGVF and ENCODE adapter.

**Pipelines**
  * **IGVF** — load *MPRA sequence designs* (``reference_filepath``: path or list of paths) once, then an *effect* file
    per run (``filepath``). Designs supply tile metadata (incl. ``allele`` / ``SPDI``);
    effect files are BED; column usage is noted on the methods that read them.
  * **ENCODE** — no designs file. Effect file is BED (optional ``.gz``); 4th column = element
    name.

**Labels (``self.label``)**
  Prefix any label below with ``mm_`` for mouse (GRCm39); unprefixed labels use human (GRCh38).
  * ``genomic_element`` / ``genomic_element_biosample`` — element-level activity. Designs are required
  for IGVF to attribute the element to design file for joining with variant edges.
  * ``variant`` / ``variant_biosample`` / ``genomic_element_from_variant`` — IGVF variant activity.
  Designs are required to map SPDI/variant pos → tile for linking to element edges.

**Assumptions**
  1. **Node _key** — ``build_regulatory_region_id`` + normalized strand token + *accession*.
     ``make_design_key`` (chr, start, end, strand) selects the design name and filters.
     Opposite strands for the same interval become distinct ``genomic_element`` nodes.
  2. **ref vs alt** — ``design_row_allele_role``; rows that *define* the catalog tile are
     those for which ``_design_row_defines_catalog_element`` is true (``ref`` or non-variant
     ``none``). Alt-only design rows do not set ``coords_to_element_name`` or SPDI → tile; they only
     populate allele sets to skip ``ALT_``* effect names for ref-only biosample edges. A
     *single* row with ``[ref, alt]`` is one reference tile (not two elements).
  3. **Significance** — ``minusLog10QValue >= THRESHOLD`` (default 1) when Q is available.
  4. **File exceptions** — accession-scoped, reasoned exclusions under
     ``data_loading_support_files/mpra/<accession>_exception_list.tsv``.

"""

# Example rows from ENCODE lenti-MPRA bed file ENCFF802FUV.bed: (the last two columns are the same for all rows)
# Column 7: activity score (i.e. log2(RNA/DNA)); Column 8: inputCount; Column 9: outputCount
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
import hashlib
import math
from typing import Optional
from collections import defaultdict
import ast
from pathlib import Path

import requests

from adapters.archive_utils import get_file_accession
from adapters.base import BaseAdapter
from adapters.helpers import (
    build_regulatory_region_id,
    bulk_check_variants_in_arangodb,
    load_variant,
    get_file_fileset_by_accession_in_arangodb
)
from adapters.ontology_term_validator import OntologyTermValidator
from adapters.writer import Writer


class MPRAAdapter(BaseAdapter):
    """
    IGVF loads a *sequence designs* TSV into the following in-memory structures:

    * ``design_elements`` — set of ``make_design_key`` tuples (chr, start, end, norm strand)
      for rows that *define* the ref/non-variant tile (see
      :meth:`_design_row_defines_catalog_element`). Drives IGVF effect row filtering
      (``genomic_element``: design must have seen this key).
    * ``coords_to_element_name`` — design ``name`` for that key, only from catalog-defining
      rows (alt-only rows do not overwrite).
    * ``design_name_class`` / ``design_name_alleles`` / ``design_element_alleles`` — per
      *normalized* effect BED *name* and per coordinate key: ``class`` string and the set
      of ``ref``/``alt`` tags from the ``allele`` column. Used to skip controls, to require
      ``ref`` for ref-only biosample edges, and to detect ambiguous multi-name regions without
      alleles.
    * ``variant_to_element`` / ``variant_pos_to_element`` — map SPDI (and optional bed
      ``variant_pos``) to the same design keys, **only** from catalog-defining rows, so
      hyper-edges point at the ref tile, not a separate ``alt``-only line.

    The effect file is always ``filepath``; ``get_file_fileset_by_accession_in_arangodb`` ties
    ``file_accession`` to ``files_filesets`` (method, class, biosample, etc.).
    """

    ALLOWED_LABELS = [
        'genomic_element',
        'genomic_element_biosample',
        'variant',
        'genomic_element_from_variant',
        'variant_biosample',
        'mm_genomic_element',
        'mm_genomic_element_biosample',
        'mm_variant',
        'mm_genomic_element_from_variant',
        'mm_variant_biosample'
    ]

    SATMUT_DESIGN_ACCESSIONS = frozenset({'IGVFFI4261NSQZ', 'IGVFFI1789LDNT'})

    # Reviewed IGVF-reformatted ENCODE files repeat reference effects for nearby
    # variants. Collapse only identical emitted records; conflicting scores fail.
    IDENTICAL_ELEMENT_EFFECT_FILES = frozenset({
        'IGVFFI0697ERLC',
        'IGVFFI1403DXAG',
        'IGVFFI1510BIKA',
        'IGVFFI1539EUOM',
        'IGVFFI1657SPYA',
        'IGVFFI1741RWXP',
        'IGVFFI1774BLKA',
        'IGVFFI2065HRKJ',
        'IGVFFI2088BWUT',
        'IGVFFI2612KYGU',
        'IGVFFI3051BDVJ',
        'IGVFFI3067GFJQ',
        'IGVFFI3404GVKG',
        'IGVFFI3512THBD',
        'IGVFFI3759TMLT',
        'IGVFFI4402NIMA',
        'IGVFFI4549EUOM',
        'IGVFFI4580CPIW',
        'IGVFFI4920GDBI',
        'IGVFFI6128ABQP',
        'IGVFFI6430GOGX',
        'IGVFFI6713XUAJ',
        'IGVFFI6745NQHO',
        'IGVFFI6956JADI',
        'IGVFFI6981UWPM',
        'IGVFFI6988MJTJ',
        'IGVFFI7020ICIO',
        'IGVFFI8760OJPL',
        'IGVFFI8768JREA',
        'IGVFFI9022VCNU',
        'IGVFFI9189WMAU',
        'IGVFFI9363OYOI',
        'IGVFFI9704CYED',
        'IGVFFI9835TEFQ',
        'IGVFFI9887JSVV',
    })

    # Library1.4: collapse exact repeats after explicit conflicting-variant exclusions.
    IDENTICAL_VARIANT_EFFECT_FILES = frozenset({'IGVFFI6587LCPK'})

    # Reviewed CD corrections are restricted to these exact effect/design pairs.
    CD_EFFECT_DESIGNS = {'IGVFFI2909LNFX': 'IGVFFI5857RBRC',
                         'IGVFFI4623ATHV': 'IGVFFI5857RBRC'}

    THRESHOLD = 1
    CHUNK_SIZE = 6500
    EXCEPTION_DIR = (Path(__file__).resolve().parents[1] /
                     'data_loading_support_files' / 'mpra')
    # These 12K designs use patch-version names for GRCh38 primary chromosomes.
    DESIGN_ASSEMBLY_ALIASES = {'IGVFFI7237HYCA': {'GRCh38.p13': 'GRCh38'}}

    def __init__(
        self,
        filepath,
        label,
        writer: Optional[Writer] = None,
        reference_filepath: Optional[str | list[str]] = None,
        validate=False,
        **kwargs
    ):
        if label not in self.ALLOWED_LABELS:
            raise ValueError(
                f'Invalid label: {label}. Allowed values: {self.ALLOWED_LABELS}')
        self.effect_label = label.removeprefix('mm_')
        self.file_accession = get_file_accession(filepath)
        if self.file_accession.startswith('ENCFF'):
            self.source = 'ENCODE'
            self.source_url = (
                f'https://www.encodeproject.org/files/{self.file_accession}/'
            )
        elif self.file_accession.startswith('IGVFFI'):
            self.source = 'IGVF'
            self.source_url = (
                f'https://data.igvf.org/tabular-files/{self.file_accession}'
            )
        else:
            raise ValueError(
                f'Unsupported file accession prefix: {self.file_accession}. '
                'Expected ENCFF (ENCODE) or IGVFFI (IGVF).'
            )

        # Raise before super().__init__ so we don't load variant schema when ENCODE has no sequence designs
        if (
            reference_filepath is None
            and self.effect_label in ('variant', 'genomic_element_from_variant', 'variant_biosample')
            and self.source == 'ENCODE'
        ):
            raise ValueError(
                'ENCODE MPRA files do not have MPRA sequence designs. '
                'Use label genomic_element or genomic_element_biosample only.'
            )

        prefix = 'mm_' if label.startswith('mm_') else ''
        self.assembly = 'GRCm39' if prefix else 'GRCh38'
        self.element_collection = f'{prefix}genomic_elements'
        self.variant_collection = f'{prefix}variants'
        self.ontology_term_validator = OntologyTermValidator()
        super().__init__(filepath, label, writer, validate)

        if self.source == 'ENCODE':
            self.igvf_accession = self._resolve_igvf_accession_from_encode_accession(
                self.file_accession)
            self.writer.add_tag('portal_accessions', self.igvf_accession)
        else:
            self.writer.add_tag('portal_accessions', self.file_accession)

        if isinstance(reference_filepath, (list, tuple)) and not reference_filepath:
            raise ValueError('MPRA reference file list must not be empty')
        self.has_sequence_designs = reference_filepath is not None

        self.file_fileset = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)

        self.variant_to_element = defaultdict(set)
        self.variant_pos_to_element = defaultdict(set)
        self.design_elements = set()
        self.coords_to_element_name = {}
        self.design_name_alleles = defaultdict(set)
        self.design_element_alleles = defaultdict(set)
        self.design_name_class = {}
        self.excluded_assembly_design_names = set()
        self.element_design_accessions = {}
        self.reference_sequences = defaultdict(set)
        self.element_design_sources = defaultdict(set)
        paths = list(reference_filepath) if isinstance(reference_filepath, (list, tuple)) else (
            [reference_filepath] if reference_filepath else [])
        if len(paths) != len({get_file_accession(path) for path in paths}):
            raise ValueError('Duplicate MPRA reference accessions')
        self.reference_file_accessions = [
            get_file_accession(path) for path in paths]
        self.multiple_designs = len(paths) > 1
        self.mpra_design_file = None
        self.reference_file_accession = None
        self.reference_source_url = None
        accumulated_exceptions = [set() for _ in range(5)]
        # Preferred owner last; input order never decides shared element ownership.
        for path in sorted(paths, key=lambda p: (get_file_accession(p) == 'IGVFFI3757JVGI', get_file_accession(p))):
            self.mpra_design_file = path
            self.reference_file_accession = get_file_accession(path)
            self.reference_source_url = f'https://data.igvf.org/tabular-files/{self.reference_file_accession}'
            self.writer.add_tag('portal_accessions',
                                self.reference_file_accession)
            current_exceptions = self._load_exceptions()
            (self.excluded_effect_names, self.excluded_variants,
             self.variants_without_reference_element, self.deduplicated_variants,
             self.first_bed_score_variants) = current_exceptions
            for target, values in zip(accumulated_exceptions, current_exceptions):
                target.update(values)
            self.load_mpra_design_mapping(path)
        if not paths:
            accumulated_exceptions = self._load_exceptions()
        (self.excluded_effect_names, self.excluded_variants,
         self.variants_without_reference_element, self.deduplicated_variants,
         self.first_bed_score_variants) = accumulated_exceptions
        if self.excluded_variants & self.variants_without_reference_element:
            raise ValueError(
                'MPRA variant cannot be both excluded and retained without a reference element')
        if self.multiple_designs:
            for key, accessions in self.element_design_sources.items():
                if len(accessions) > 1:
                    sequences = [self.reference_sequences[(
                        key, accession)] for accession in accessions]
                    if any(not seq or seq != sequences[0] for seq in sequences):
                        raise ValueError(
                            f'Conflicting or missing reference sequences across MPRA designs at {key}')
            self.mpra_design_file = paths
            self.reference_file_accession = None
            self.reference_source_url = None

    def _element_owner(self, key):
        return self.element_design_accessions.get(key, self.reference_file_accession or self.file_accession)

    def _reviewed_effect_rows(self, reader):
        """Apply only reviewed CD corrections; never infer mappings for other files."""
        expected_design = self.CD_EFFECT_DESIGNS.get(self.file_accession)
        if expected_design is None:
            yield from reader
            return
        if self.reference_file_accession != expected_design:
            raise ValueError(
                f'{self.file_accession}: CD correction requires {expected_design}')
        by_coordinate = defaultdict(list)
        with self._open_text_file(self.mpra_design_file) as stream:
            for design in csv.DictReader(stream, delimiter='\t'):
                key = self.make_design_key(
                    *(design[k] for k in ('chr', 'start', 'end', 'strand')))
                by_coordinate[key].append(design)
        for row in reader:
            row = list(row)
            if self.file_accession == 'IGVFFI4623ATHV' and self._is_blacklisted_effect_name(row[3]):
                continue
            key = self.make_design_key(row[0], row[1], row[2], row[5])
            candidates = by_coordinate.get(key, [])
            if self.file_accession == 'IGVFFI4623ATHV':
                # Names use old coordinates; match exact current tile and allele suffix.
                allele = row[3].rsplit('_', 1)[-1]
                names = {d['name'] for d in candidates if d['name'].rsplit(
                    '_', 1)[-1] == allele}
                if len(names) != 1:
                    raise ValueError(
                        f'{self.file_accession}: ambiguous CD element {row[3]} at {key}')
                row[3] = names.pop()
            else:
                mappings = {(spdi, int(pos)) for d in candidates
                            for spdi, pos in zip(ast.literal_eval(d['SPDI']), ast.literal_eval(d['variant_pos']))}
                if len(mappings) != 1:
                    raise ValueError(
                        f'{self.file_accession}: ambiguous CD variant {row[3]} at {key}')
                spdi, position = mappings.pop()
                names = {d['name'].rsplit('_', 1)[0] for d in candidates}
                if (row[3] not in names or row[17:19] != spdi.split(':')[2:]
                        or self.safe_int(row[16]) != position - 1):
                    raise ValueError(
                        f'{self.file_accession}: unexpected CD identifier, alleles or position: {row[3]}')
                row[3], row[16] = spdi, str(position)
            yield row

    def _resolve_igvf_accession_from_encode_accession(self, encode_accession, igvf_api_url='https://api.data.igvf.org'):
        response = requests.get(
            f'{igvf_api_url}/search/?type=File&aliases=igvf:{encode_accession}&field=accession')
        response.raise_for_status()
        try:
            return response.json()['@graph'][0]['accession']
        except (KeyError, IndexError) as e:
            raise ValueError(
                f'Failed to resolve IGVF accession from ENCODE accession: {encode_accession}, response: {response.json()}') from e

    @staticmethod
    def _open_text_file(filepath):
        """Stream plain or gzipped effects/designs without extracting a local copy."""
        opener = gzip.open if str(filepath).endswith('.gz') else open
        return opener(filepath, 'rt')

    def _open_file(self):
        return self._open_text_file(self.filepath)

    def _get_schema_type(self):
        if self.effect_label in ['genomic_element_biosample', 'variant_biosample']:
            return 'edges'
        return 'nodes'

    def _get_collection_name(self):
        if self.effect_label == 'variant':
            return self.variant_collection
        if self.effect_label == 'variant_biosample':
            return f'{self.variant_collection}_biosamples'
        if self.effect_label in ['genomic_element', 'genomic_element_from_variant']:
            return self.element_collection
        if self.effect_label == 'genomic_element_biosample':
            return f'{self.element_collection}_biosamples'
        return None

    @staticmethod
    def safe_float(value):
        try:
            parsed = float(value)
            return parsed
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _drop_nonfinite_metrics(props):
        """Preserve records while omitting NaN and infinite numeric fields."""
        return {key: value for key, value in props.items()
                if not (key == 'bed_score' and value is None)
                and not (isinstance(value, float) and not math.isfinite(value))}

    @classmethod
    def safe_int(cls, value):
        parsed = cls.safe_float(value)
        if parsed is None or not math.isfinite(parsed):
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
    def design_row_allele_role(cls, allele_values):
        """Return ``'ref'`` | ``'alt'`` | ``'none'`` for the parsed ``allele`` list.

        ``'ref'`` if the list contains ``ref`` (including mixed ``[ref, alt]`` = one ref tile).
        ``'alt'`` only for alt-only rows. ``'none'`` for missing/empty lists or no ref/alt tokens.
        See module docstring and :meth:`_design_row_defines_catalog_element`.
        """
        if not isinstance(allele_values, list) or not allele_values:
            return 'none'
        s = {
            str(a).strip().lower() for a in allele_values
            if a is not None
        }
        if 'ref' in s:
            return 'ref'
        if 'alt' in s:
            return 'alt'
        return 'none'

    @staticmethod
    def _design_row_defines_catalog_element(name_role):
        """Whether the design row may set ``design_elements``, ``coords_to_element_name``, and SPDI/variant_pos → tile.

        True for **ref** and **non-variant (none)** rows; false for **alt-only** rows. See
        module docstring.
        """
        return name_role in ('ref', 'none')

    def build_mpra_element_node_id(self, chr_, start, end, strand, suffix):
        """Genomic element node _key: coordinates + strand token + suffix."""
        region_id = build_regulatory_region_id(
            chr_, start, end, 'MPRA', assembly=self.assembly)
        return f'{region_id}_{self.strand_token(strand)}_{suffix}'

    def load_mpra_design_mapping(self, mpra_design_file):
        # IGVF designs TSV: per-row `allele` / `SPDI` / `variant_pos` drive the maps in the
        # class docstring. Alt-only rows only contribute to allele *sets*, not to catalog keys.
        pending_alt_spdi_mappings = []
        reference_tiles = set()
        with self._open_text_file(mpra_design_file) as f:
            reader = csv.DictReader(f, delimiter='\t')
            for i, row in enumerate(reader, 1):
                if self._is_blacklisted_effect_name(row.get('name')):
                    continue
                assembly = row.get('ref', self.assembly)
                assembly = self.DESIGN_ASSEMBLY_ALIASES.get(
                    self.reference_file_accession, {}).get(assembly, assembly)
                if assembly not in (self.assembly, '', 'NA'):
                    self.excluded_assembly_design_names.add(
                        self.normalize_design_name(row.get('name')))
                    continue
                try:
                    key = self.make_design_key(
                        row['chr'], row['start'], row['end'], row.get('strand'))
                except Exception:
                    continue

                allele_raw = row.get('allele')
                allele_values = None
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
                name_role = self.design_row_allele_role(allele_values or [])

                if self._design_row_defines_catalog_element(name_role):
                    owner = self.element_design_accessions.get(key)
                    if owner and owner != self.reference_file_accession:
                        if {owner, self.reference_file_accession} != {'IGVFFI5128MGTU', 'IGVFFI3757JVGI'}:
                            raise ValueError(
                                f'Unreviewed overlapping MPRA designs at {key}: {owner}, {self.reference_file_accession}')
                    # Compare fully reference sequences, not mixed ref/alt constructs.
                    if self.multiple_designs and 'alt' not in (allele_values or []):
                        sequence = row.get('sequence')
                        if not sequence:
                            raise ValueError(
                                f'Missing reference sequence at shared-design tile {key}')
                        digest = hashlib.sha256(sequence.encode()).hexdigest()
                        self.reference_sequences[(
                            key, self.reference_file_accession)].add(digest)
                    self.element_design_sources[key].add(
                        self.reference_file_accession)
                    self.element_design_accessions[key] = self.reference_file_accession
                    self.design_elements.add(key)
                    if row.get('name') is not None and str(row.get('name')).strip():
                        self.coords_to_element_name[key] = row.get('name')
                    if name_role == 'ref':
                        reference_tiles.add(key)

                normalized_name = self.normalize_design_name(row.get('name'))
                if normalized_name:
                    self.design_name_class[normalized_name] = (
                        row.get('class') or '').strip().lower()
                if allele_values is not None:
                    for allele in allele_values:
                        if allele is None:
                            continue
                        normalized = str(allele).strip().lower()
                        self.design_element_alleles[key].add(normalized)
                        if normalized_name:
                            self.design_name_alleles[normalized_name].add(
                                normalized)

                if row.get('SPDI') in (None, '', 'NA', 'NaN'):
                    continue
                try:
                    spdi_list = ast.literal_eval(row['SPDI'])
                except (ValueError, SyntaxError) as e:
                    raise ValueError(
                        f"Malformed SPDI at row {i}: {row['SPDI']!r}") from e
                if not isinstance(spdi_list, list):
                    raise ValueError(
                        f'Malformed SPDI at row {i}: expected list, got {type(spdi_list).__name__}'
                    )

                variant_pos_list = None
                variant_pos_raw = row.get('variant_pos')
                if variant_pos_raw not in (None, '', 'NA', 'NaN'):
                    try:
                        variant_pos_list = ast.literal_eval(variant_pos_raw)
                    except (ValueError, SyntaxError) as e:
                        raise ValueError(
                            f'Malformed variant_pos at row {i}: {variant_pos_raw!r}') from e
                    if not isinstance(variant_pos_list, list):
                        raise ValueError(
                            f'Malformed variant_pos at row {i}: expected list, got {type(variant_pos_list).__name__}'
                        )

                if self._design_row_defines_catalog_element(name_role):
                    target_key = key
                elif name_role == 'alt':
                    # Some IGVF design files provide SPDI/variant_pos only on ALT rows.
                    # Defer until we know whether this coordinate key has a ref/none tile.
                    pending_alt_spdi_mappings.append(
                        (key, spdi_list, variant_pos_list)
                    )
                    continue
                else:
                    continue

                for spdi in spdi_list:
                    self.variant_to_element[spdi].add(target_key)

                if variant_pos_list is not None:
                    for spdi, variant_pos in zip(spdi_list, variant_pos_list):
                        pos = self.safe_int(variant_pos)
                        if pos is not None:
                            self.variant_pos_to_element[(
                                spdi, pos)].add(target_key)

        for key, spdi_list, variant_pos_list in pending_alt_spdi_mappings:
            if key not in self.design_elements:
                if self.reference_file_accession not in self.SATMUT_DESIGN_ACCESSIONS:
                    # Only these reviewed SatMut designs encode ALT coordinates
                    # as changed bases. Do not infer tiles for other files.
                    continue
                # ALT coordinates may describe only the changed bases rather
                # than the full reference tile. When there is no exact tile
                # match, require a unique reference tile containing that interval
                # on the same chromosome and strand. This mapping uses reference
                # coordinates, not sequence identity or provenance names, and
                # applies only to the explicitly listed SatMut designs.
                candidates = {
                    tile for tile in reference_tiles
                    if key[0] == tile[0] and key[3] == tile[3]
                    and int(tile[1]) <= int(key[1]) <= int(key[2]) <= int(tile[2])
                }
                if not candidates:
                    # ALT-only designs have no reference element to link to.
                    continue
                if len(candidates) != 1:
                    raise ValueError(
                        f'Expected one reference tile containing variant design {key}; '
                        f'found {len(candidates)} in {self.reference_file_accession}')
                key = candidates.pop()
            for spdi in spdi_list:
                self.variant_to_element[spdi].add(key)
            if variant_pos_list is not None:
                for spdi, variant_pos in zip(spdi_list, variant_pos_list):
                    pos = self.safe_int(variant_pos)
                    if pos is not None:
                        self.variant_pos_to_element[(spdi, pos)].add(key)

    def _load_exceptions(self):
        """Exact identifiers only; a replacement accession never inherits exceptions."""
        exceptions = {'element': set(), 'variant': set(),
                      'variant_without_reference_element': set(),
                      'variant_deduplicate': set(), 'variant_deduplicate_first_bed_score': set()}
        for accession in (self.file_accession, self.reference_file_accession):
            if not accession:
                continue
            path = self.EXCEPTION_DIR / f'{accession}_exception_list.tsv'
            if not path.exists():
                continue
            with path.open() as stream:
                reader = csv.DictReader(stream, delimiter='\t')
                if reader.fieldnames != ['kind', 'identifier', 'reason']:
                    raise ValueError(f'Invalid MPRA exception header: {path}')
                for row in reader:
                    if (row['kind'] not in exceptions or not row['identifier']
                            or not row['reason'] or None in row):
                        raise ValueError(
                            f'Invalid MPRA exception entry in {path}: {row}')
                    exceptions[row['kind']].add(row['identifier'])
        if exceptions['variant'] & exceptions['variant_without_reference_element']:
            raise ValueError(
                'MPRA variant cannot be both excluded and retained without a reference element')
        return tuple(frozenset(exceptions[kind]) for kind in (
            'element', 'variant', 'variant_without_reference_element',
            'variant_deduplicate', 'variant_deduplicate_first_bed_score'))

    def _is_blacklisted_effect_name(self, effect_name):
        return (effect_name or '').strip() in self.excluded_effect_names

    def parse(self):
        # genomic_element_from_variant: dedupe (chr,start,end,strand) across chunks
        self.writer.add_tag('portal_accessions', self.file_accession)
        file_set_accession = self.file_fileset.get('file_set_id')
        if file_set_accession:
            self.writer.add_tag('portal_accessions', file_set_accession)
        self.seen_elements = set()
        self.seen_variant_effects = {}
        self.collection_label_variants_elements = 'variant effect on regulatory element activity'
        self.collection_label_elements_biosamples = (
            'regulatory reference element activity')
        self.collection_class = self.file_fileset.get('class')
        self.method = self.file_fileset.get('method')
        samples = self.file_fileset.get('samples') or []
        raw = samples[0] if samples else None
        # Normalize to full document ID (fileset may give "EFO_0002067" or "ontology_terms/EFO_0002067")
        self.biosample_term = (raw if (raw or '').startswith(
            'ontology_terms/') else f'ontology_terms/{raw}') if raw else None
        self.simple_sample_summaries = self.file_fileset.get(
            'simple_sample_summaries')
        self.treatments_term_ids = self.file_fileset.get(
            'treatments_term_ids')

        if self.effect_label in ('genomic_element_biosample', 'variant_biosample'):
            if not self.ontology_term_validator.ensure(self.biosample_term):
                self.ontology_term_validator.log()
                return

        if self.effect_label in ('genomic_element', 'genomic_element_biosample'):
            self._process_element_effects_file()
            return

        with self._open_file() as f:
            reader = csv.reader(f, delimiter='\t')
            chunk = []
            # in this case the file is always from IGVF so we add the tag
            for i, row in enumerate(self._reviewed_effect_rows(reader), 1):
                if row[3] in self.excluded_variants:
                    continue
                chunk.append(row)
                if i % self.CHUNK_SIZE == 0:
                    self._process_chunk_igvf(chunk)
                    chunk = []
            if chunk:
                self._process_chunk_igvf(chunk)

    def _process_element_effects_file(self):
        """Element-activity BED/TSV: one row per tile × strand in the MPRA output.

        Columns (0-based): 0=chr, 1=start, 2=end, 3=name, 4=bed score, 5=strand, 6=log2FC,
        7=DNA, 8=RNA, 9=``-log10P`` (or -1 if absent), 10=``-log10Q`` (or -1). IGVF joins the
        sequence designs; ENCODE uses col 3 for ``name`` and ``design_elements`` is unused.

        Writes ``genomic_element`` nodes and/or ``genomic_element_biosample`` edges depending on
        ``self.label`` (both branches are in the same loop; only one label per run is active).
        """
        seen_element_ids = set()
        seen_edges = {}
        biosample_term_key = (self.biosample_term or '').split('/')[-1]

        with self._open_file() as f:
            reader = csv.reader(f, delimiter='\t')
            rows = list(self._reviewed_effect_rows(reader))
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
                    chr_, start, end, 'MPRA', assembly=self.assembly)
                element_key = self.make_design_key(chr_, start, end, strand)
                element_id_suffix = self._element_owner(element_key)
                element_id = self.build_mpra_element_node_id(
                    chr_, start, end, strand, element_id_suffix)
                if self.normalize_design_name(row[3]) in self.excluded_assembly_design_names:
                    continue

                if self._is_blacklisted_effect_name(row[3]):
                    continue
                if self.effect_label == 'genomic_element':
                    if self.has_sequence_designs and element_key not in self.design_elements:
                        self.logger.warning(
                            f'Skipping genomic element {(chr_, start, end, strand)} from {self.file_accession}: '
                            f'not present in MPRA sequence designs file {self.reference_file_accession}.'
                        )
                        continue
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
                        'strand': self.normalize_strand(strand),
                        'method': self.method,
                        'type': 'tested elements',
                        'source': self.source,
                        'source_url': f'https://data.igvf.org/tabular-files/{element_id_suffix}' if self.has_sequence_designs else self.source_url,
                        'files_filesets': 'files_filesets/' + element_id_suffix
                    }
                    if self.validate:
                        self.validate_doc(props)
                    self.writer.write(json.dumps(
                        props, allow_nan=False) + '\n')

                elif self.effect_label == 'genomic_element_biosample':
                    if self.has_sequence_designs:
                        normalized_effect_name = self.normalize_design_name(
                            row[3])
                        # Must run before missing-allele handling: blacklisted rows
                        # have no design alleles and share coordinates, which would
                        # otherwise trigger missing_allele_multi_effect.
                        if self._is_blacklisted_effect_name(row[3]):
                            continue
                        effect_class = self.design_name_class.get(
                            normalized_effect_name, '')
                        if 'control' in effect_class and not (
                                self.reference_file_accession in self.SATMUT_DESIGN_ACCESSIONS
                                and 'ref' in self.design_name_alleles.get(normalized_effect_name, set())):
                            # Controls normally do not produce activity edges. The
                            # SatMut WT controls are its five reference test tiles.
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
                        if alleles and 'ref' not in alleles:
                            # Only ref element effects should be loaded.
                            continue
                    if self.has_sequence_designs and element_key not in self.design_elements:
                        raise ValueError(
                            f'{self.file_accession}: element {row[3]!r} has no reference design tile '
                            f'{element_key}; review the input or add a file-specific exclusion.')
                    edge_id = '_'.join(
                        [region_id, self.strand_token(strand), self.file_accession, biosample_term_key])
                    minus_p = self.safe_float(row[9]) if len(
                        row) > 9 and row[9] != '-1' else None
                    minus_q_edge = self.safe_float(row[10]) if len(
                        row) > 10 and row[10] != '-1' else None
                    props = {
                        '_key': edge_id,
                        '_from': f'{self.element_collection}/{element_id}',
                        '_to': self.biosample_term,
                        'strand': strand,
                        'log2FC': self.safe_float(row[6]),
                        'bed_score': self.safe_int(row[4]),
                        'inputCount': self.safe_float(row[7]),
                        'outputCount': self.safe_float(row[8]),
                        'neg_log10_pvalue': minus_p,
                        'neg_log10_pvalue_adj': minus_q_edge,
                        'significant': significant,
                        'class': self.collection_class,
                        'label': self.collection_label_elements_biosamples,
                        'name': 'expression effect in',
                        'inverse_name': 'has expression effect from',
                        'method': self.method,
                        'source': self.source,
                        'source_url': self.source_url,
                        'files_filesets': 'files_filesets/' + self.file_accession,
                        'biological_context': self.simple_sample_summaries[0] if self.simple_sample_summaries else None,
                        'biosample_term': self.biosample_term,
                        'treatments_term_ids': self.treatments_term_ids if self.treatments_term_ids else None,
                    }
                    props = self._drop_nonfinite_metrics(props)
                    if edge_id in seen_edges:
                        if (self.file_accession in self.IDENTICAL_ELEMENT_EFFECT_FILES
                                and seen_edges[edge_id] == props):
                            continue
                        raise ValueError(
                            f'{self.file_accession}: duplicate element effect {edge_id}; '
                            'conflicting or unreviewed duplicate reference scores')
                    seen_edges[edge_id] = props
                    if self.validate:
                        self.validate_doc(props)
                    self.writer.write(json.dumps(
                        props, allow_nan=False) + '\n')

            if missing_allele_multi_effect:
                raise ValueError(
                    'Missing allele annotations for regions with multiple element effects '
                    f'(examples: {missing_allele_multi_effect[:5]})'
                )

    def _process_chunk_igvf(self, chunk):
        if self.effect_label == 'variant':
            self._process_variant_chunk(chunk)
        elif self.effect_label == 'variant_biosample':
            self._process_variant_biosample_chunk(chunk)
        elif self.effect_label == 'genomic_element_from_variant':
            self._process_genomic_element_chunk(chunk)

    def _process_variant_chunk(self, chunk):
        spdis = [row[3] for row in chunk]
        loaded_spdis = bulk_check_variants_in_arangodb(
            spdis, check_by='spdi', excluded_files_filesets=f'files_filesets/{self.file_accession}',
            collection=self.variant_collection)
        for row in chunk:
            spdi = row[3]
            if spdi in loaded_spdis:
                continue
            variant, skipped_message = load_variant(
                spdi, assembly=self.assembly)
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
        """``genomic_element_from_variant``: ``genomic_element`` nodes for coords in ``variant_to_element``.

        Only reported, non-excluded variants contribute nodes. ``self.seen_elements``
        dedupes across chunk invocations.
        """
        keys = set()
        for row in chunk:
            element_coords_set = self.variant_to_element.get(row[3], set())
            for chr_, start, end, strand in element_coords_set:
                keys.add(self.make_design_key(chr_, start, end, strand))

        for key in sorted(keys):
            if key in self.seen_elements:
                continue
            self.seen_elements.add(key)
            chr_, start, end, strand = key
            element_name = self.coords_to_element_name.get(key)
            if element_name is None:
                raise ValueError(
                    f'Missing MPRA sequence design name for {(chr_, start, end, strand)} in {self.reference_file_accession}.')
            owner = self._element_owner(key)
            _id = self.build_mpra_element_node_id(
                chr_, start, end, strand, owner)
            props = {
                '_key': _id,
                'name': element_name,
                'chr': chr_,
                'start': int(start),
                'end': int(end),
                'strand': self.normalize_strand(strand),
                'method': self.method,
                'type': 'tested elements',
                'source': self.source,
                'source_url': f'https://data.igvf.org/tabular-files/{owner}',
                'files_filesets': f'files_filesets/{owner}'
            }
            if self.validate:
                self.validate_doc(props)
            self.writer.write(json.dumps(props, allow_nan=False) + '\n')

    def _process_variant_biosample_chunk(self, chunk):
        """IGVF variant×biosample BED: SPDI in col 3, optional ``variant_pos`` in col 16 for disambiguation of the same variant on different strands."""
        loaded_spdis = bulk_check_variants_in_arangodb(
            [row[3] for row in chunk], collection=self.variant_collection)
        missing_spdis = {row[3] for row in chunk} - set(loaded_spdis)
        if missing_spdis:
            self.logger.error(
                f'{self.file_accession}: skipping variant-biosample edges for '
                f'{len(missing_spdis)} unique variants in this chunk because their '
                f'nodes are missing from {self.variant_collection} in ArangoDB. '
                'Output will be incomplete. Load the variant nodes into ArangoDB '
                'and rerun edge generation; uploading node files to S3 is not sufficient.')
        for row in chunk:
            spdi = row[3]
            if spdi not in loaded_spdis:
                continue
            if (not self.variant_to_element.get(spdi)
                    and spdi not in self.variants_without_reference_element):
                raise ValueError(
                    f'SPDI {spdi} found in variant file but not in MPRA design mapping. '
                    'Ensure all genomic element edges are mapped via the sequence design file.'
                )

            variant, skipped_message = load_variant(
                spdi, assembly=self.assembly)
            if not variant:
                if skipped_message:
                    self.logger.warning(f'Skipped {spdi}: {skipped_message}')
                continue
            variant_id = variant['_key']
            biosample_term_key = (self.biosample_term or '').split('/')[-1]
            bed_variant_pos = self.safe_int(row[16]) if len(row) > 16 else None
            bed_strand = self.normalize_strand(row[5]) if len(row) > 5 else '.'

            mapped_elements = set()
            if bed_variant_pos is not None:
                mapped_elements = self.variant_pos_to_element.get(
                    (spdi, bed_variant_pos), set())
                if len(mapped_elements) > 1:
                    strand_matched = {
                        element for element in mapped_elements
                        if self.normalize_strand(element[3]) == bed_strand
                    }
                    if strand_matched:
                        mapped_elements = strand_matched
            if not mapped_elements:
                mapped_elements = self.variant_to_element.get(spdi, set())

            # Only an explicit file exception permits a missing reference tile.
            for element in mapped_elements or [None]:
                if element is None:
                    element_id = None
                    element_strand = bed_strand
                    element_key = f'no_reference_element_{self.strand_token(bed_strand)}_{bed_variant_pos}'
                else:
                    element_chr, element_start, element_end, element_strand = element
                    element_id = self.build_mpra_element_node_id(
                        element_chr, element_start, element_end, element_strand, self._element_owner(element))
                    element_key = element_id
                edge_key = '_'.join([
                    variant_id,
                    element_key,
                    biosample_term_key,
                    self.file_accession,
                ])

                if len(edge_key) > 255:
                    edge_key = hashlib.sha256(edge_key.encode()).hexdigest()

                minus_q = self.safe_float(row[12])
                edge_props = {
                    '_key': edge_key,
                    '_from': f'{self.variant_collection}/{variant_id}',
                    '_to': self.biosample_term,
                    'genomic_element': f'{self.element_collection}/{element_id}' if element_id else None,
                    'strand': element_strand,
                    'log2FC': self.safe_float(row[6]),
                    'bed_score': self.safe_int(row[4]),
                    'inputCountRef': self.safe_float(row[7]),
                    'outputCountRef': self.safe_float(row[8]),
                    'inputCountAlt': self.safe_float(row[9]),
                    'outputCountAlt': self.safe_float(row[10]),
                    'neg_log10_pvalue': self.safe_float(row[11]),
                    'neg_log10_pvalue_adj': minus_q,
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
                    'biological_context': self.simple_sample_summaries[0] if self.simple_sample_summaries else None,
                    'biosample_term': self.biosample_term,
                    'treatments_term_ids': self.treatments_term_ids or None,
                }

                edge_props = self._drop_nonfinite_metrics(edge_props)
                if (self.file_accession in self.IDENTICAL_VARIANT_EFFECT_FILES
                        or spdi in self.deduplicated_variants
                        or spdi in self.first_bed_score_variants):
                    comparable = {k: v for k, v in edge_props.items()
                                  if k != 'bed_score' or spdi not in self.first_bed_score_variants}
                    if edge_key in self.seen_variant_effects:
                        if self.seen_variant_effects[edge_key] != comparable:
                            raise ValueError(
                                f'{self.file_accession}: conflicting variant effect for {spdi}; '
                                'review and add an explicit variant exclusion')
                        continue
                    self.seen_variant_effects[edge_key] = comparable
                if self.validate:
                    self.validate_doc(edge_props)
                self.writer.write(json.dumps(
                    edge_props, allow_nan=False) + '\n')
