import csv
import gzip
import json
import re
from typing import Dict, Optional, Tuple

from adapters.base import BaseAdapter
from adapters.helpers import build_regulatory_region_id, get_file_fileset_by_accession_in_arangodb
from adapters.gene_validator import GeneValidator
from adapters.writer import Writer

# Example rows from Gersbach's Perturb-seq data
# p_val	avg_log2FC	pct.1	pct.2	p_val_adj	guide_id	target_gene	intended_target_name	intended_target_chr	intended_target_start	intended_target_end
# 0	3.608562048	0.918	0.282	0	BATF3-2	ENSG00000123685	ENSG00000123685	chr1	212699339	212700840
# 0	3.020205154	0.961	0.724	0	KLF2-11	ENSG00000132965	ENSG00000127528	chr19	16323826	16325327
# 0	2.778382681	0.923	0.476	0	KLF2-11	ENSG00000113552	ENSG00000127528	chr19	16323826	16325327
# 0	4.552805504	0.944	0.349	0	KLF2-11	ENSG00000137731	ENSG00000127528	chr19	16323826	16325327
# 0	1.562300285	0.965	0.822	0	MYB-8	ENSG00000197971	ENSG00000118513	chr6	135180514	135182015
# 0	1.846713305	0.998	0.994	0	NFE2L1-12	ENSG00000087460	ENSG00000082641	chr17	48047370	48048871
# 0	4.714580706	0.944	0.474	0	EOMES-8	ENSG00000030582	ENSG00000163508	chr3	27721997	27723498
# 5e-324	2.422421422	0.997	0.966	1.80833e-319	EOMES-8	ENSG00000122862	ENSG00000163508	chr3	27721997	27723498
# 1.70888203873918e-305	2.353451553	0.904	0.498	6.25467914998928e-301	KLF2-11	ENSG00000095794	ENSG00000127528	chr19	16323826	16325327

# Example rows from Gersbach's CRISPR FACS data
# FRACTEL_pval	FRACTEL_pval_fdr_corr	FRACTEL_effect_size	intended_target_name	intended_target_chr	intended_target_start	intended_target_end	readout_gene	readout_gene_symbol
# 0.7264835	0.9994257067617868	0.2254047296279381	ENSG00000188290	chr1	998962	999432	ENSG00000168685	IL7R
# 0.6353328	0.9994257067617868	0.4499883534060434	ENSG00000157933	chr1	2228695	2229735	ENSG00000168685	IL7R
# 0.8264444	0.9994257067617868	0.2234036501031779	ENSG00000197921	chr1	2528745	2529749	ENSG00000168685	IL7R
# 0.0375612	0.7776272999999999	-0.902286973451608	ENSG00000142611	chr1	3385152	3385286	ENSG00000168685	IL7R
# 0.4863262	0.9994257067617868	0.4703859734914864	ENSG00000078900	chr1	3707549	3707791	ENSG00000168685	IL7R
# 0.6627895	0.9994257067617868	-0.4684078131930258	ENSG00000173673	chr1	6244351	6244446	ENSG00000168685	IL7R
# 0.5737245	0.9994257067617868	0.4359202869686309	ENSG00000069812	chr1	6415232	6419153	ENSG00000168685	IL7R
# 0.0163096	0.4615330666666667	0.6634541544827465	ENSG00000204859	chr1	6582058	6582299	ENSG00000168685	IL7R
# 0.6030225	0.9994257067617868	0.40989234019479	ENSG00000041988	chr1	6628499	6628691	ENSG00000168685	IL7R

# Example rows from Quertermous's TAP-seq data
# intended_target_name	guide_id(s)	targeting_chr	targeting_start	targeting_end	type	gene_id	gene_symbol	sceptre_log2_fc	sceptre_p_value	sceptre_adj_p_value	significant	sample_term_name	sample_term_idsample_summary_short	power_at_effect_size_15	notes
# chr4:55181617-55182218	221204_EC_Enhancer_Screen_84, 221204_EC_Enhancer_Screen_85, 221204_EC_Enhancer_Screen_86, 221204_EC_Enhancer_Screen_87, 221204_EC_Enhancer_Screen_88, 221204_EC_Enhancer_Screen_89, 221204_EC_Enhancer_Screen_90, 221204_EC_Enhancer_Screen_91, 221204_EC_Enhancer_Screen_92, 221204_EC_Enhancer_Screen_93, 221204_EC_Enhancer_Screen_94, 221204_EC_Enhancer_Screen_95, 221204_EC_Enhancer_Screen_96, 221204_EC_Enhancer_Screen_97, 221204_EC_Enhancer_Screen_98	chr4	55181617	55182218	targeting	ENSG00000145681	HAPLN1	1.60726510888607	7.25503908439717e-29	3.51143891684823e-26	TRUE	wtc11_d4_ec	NA	ipsc_ec	NA	NA
# chr4:55181617-55182218	221204_EC_Enhancer_Screen_84, 221204_EC_Enhancer_Screen_85, 221204_EC_Enhancer_Screen_86, 221204_EC_Enhancer_Screen_87, 221204_EC_Enhancer_Screen_88, 221204_EC_Enhancer_Screen_89, 221204_EC_Enhancer_Screen_90, 221204_EC_Enhancer_Screen_91, 221204_EC_Enhancer_Screen_92, 221204_EC_Enhancer_Screen_93, 221204_EC_Enhancer_Screen_94, 221204_EC_Enhancer_Screen_95, 221204_EC_Enhancer_Screen_96, 221204_EC_Enhancer_Screen_97, 221204_EC_Enhancer_Screen_98	chr4	55181617	55182218	targeting	ENSG00000128917	DLL4	-0.576747067613555	2.13033821184895e-25	5.15541847267446e-23	TRUE	wtc11_d4_ec	NA	ipsc_ec	NA	NA
# chr4:55181617-55182218	221204_EC_Enhancer_Screen_84, 221204_EC_Enhancer_Screen_85, 221204_EC_Enhancer_Screen_86, 221204_EC_Enhancer_Screen_87, 221204_EC_Enhancer_Screen_88, 221204_EC_Enhancer_Screen_89, 221204_EC_Enhancer_Screen_90, 221204_EC_Enhancer_Screen_91, 221204_EC_Enhancer_Screen_92, 221204_EC_Enhancer_Screen_93, 221204_EC_Enhancer_Screen_94, 221204_EC_Enhancer_Screen_95, 221204_EC_Enhancer_Screen_96, 221204_EC_Enhancer_Screen_97, 221204_EC_Enhancer_Screen_98	chr4	55181617	55182218	targeting	ENSG00000261371	PECAM1	-0.520774246394608	2.01505844276112e-24	3.25096095432128e-22	TRUE	wtc11_d4_ec	NA	ipsc_ec	NA	NA
# chr4:55181617-55182218	221204_EC_Enhancer_Screen_84, 221204_EC_Enhancer_Screen_85, 221204_EC_Enhancer_Screen_86, 221204_EC_Enhancer_Screen_87, 221204_EC_Enhancer_Screen_88, 221204_EC_Enhancer_Screen_89, 221204_EC_Enhancer_Screen_90, 221204_EC_Enhancer_Screen_91, 221204_EC_Enhancer_Screen_92, 221204_EC_Enhancer_Screen_93, 221204_EC_Enhancer_Screen_94, 221204_EC_Enhancer_Screen_95, 221204_EC_Enhancer_Screen_96, 221204_EC_Enhancer_Screen_97, 221204_EC_Enhancer_Screen_98	chr4	55181617	55182218	targeting	ENSG00000125534	PPDPF	0.481123964239175	8.25144540545184e-19	9.98424894059672e-17	TRUE	wtc11_d4_ec	NA	ipsc_ec	NA	NA
# chr4:55181617-55182218	221204_EC_Enhancer_Screen_84, 221204_EC_Enhancer_Screen_85, 221204_EC_Enhancer_Screen_86, 221204_EC_Enhancer_Screen_87, 221204_EC_Enhancer_Screen_88, 221204_EC_Enhancer_Screen_89, 221204_EC_Enhancer_Screen_90, 221204_EC_Enhancer_Screen_91, 221204_EC_Enhancer_Screen_92, 221204_EC_Enhancer_Screen_93, 221204_EC_Enhancer_Screen_94, 221204_EC_Enhancer_Screen_95, 221204_EC_Enhancer_Screen_96, 221204_EC_Enhancer_Screen_97, 221204_EC_Enhancer_Screen_98	chr4	55181617	55182218	targeting	ENSG00000179776	CDH5	-0.365934663367468	1.05516601247984e-18	1.02140070008049e-16	TRUE	wtc11_d4_ec	NA	ipsc_ec	NA	NA

# Per-file expectation for which regions the screen perturbs (see data_sources.yaml /
# data_sources_file_fileset.yaml IGVF CRISPR E2G lists). "both" keeps the prior per-row rule:
# coordinates or non-gene intended target -> enhancer; valid ENSG intended target -> promoter.
CRISPR_E2G_TARGETED_ELEMENT_TYPES = {
    # promoter Perturb-seq
    'IGVFFI3069QCRA': 'promoter',  # T-cell CRISPRa
    'IGVFFI5749WPVK': 'promoter',  # T-cell CRISPRi
    'IGVFFI6376HTIF': 'promoter',  # HCASMC Pilot Perturb-seq
    'IGVFFI0206LUDV': 'promoter',  # HCASMC 971-gene Perturb-seq
    # Mixed promoter and enhancer Perturb-seq
    'IGVFFI4544JMWL': 'both',  # Scaled screen
    'IGVFFI0830FXFI': 'both',  # WTC-11 CM TF-Perturb-seq
    'IGVFFI5903QAWP': 'both',  # CRUDO TAP-seq
    # enhancer Perturb-seq
    'IGVFFI6296RCJK': 'enhancer',  # Mechanoenhancer
    'IGVFFI6600VCYY': 'enhancer',  # EC-TAP-seq D0
    'IGVFFI7195XKBC': 'enhancer',  # EC-TAP-seq D2
    'IGVFFI9246AJEK': 'enhancer',  # EC-TAP-seq D4
    'IGVFFI3434YAPX': 'enhancer',  # 9p21 DC-TAP-seq
    'IGVFFI1168JUYR': 'enhancer',  # HCASMC DC-TAP-seq
    # promoter CRISPR FACS screens
    'IGVFFI9100GKNS': 'promoter',
    'IGVFFI6268OASM': 'promoter',
    'IGVFFI1336XWXJ': 'promoter',
    'IGVFFI3089UGHM': 'promoter',
}


# CRUDO TAP-seq (IGVFFI5903QAWP): name_hg38 (duplex chr:start-chr:end or simple chr:start-end),
# type, TargetGeneID; metrics from EnhancerEffect.noAux / pval.EnhancerEffect.noAux / adj.pval.* (or EnhancerEff.*).
# TSS rows: promoter Ensembl id is not in the file — see CRUDO_TSS_PROMOTER_GENE.
CRUDO_TSS_PROMOTER_GENE = {
    'CCND1_TSS': 'ENSG00000110092',
    'KITLG_TSS': 'ENSG00000049130',
    'SSFA2_TSS': 'ENSG00000138434',
    'FAM3C_TSS': 'ENSG00000196937',
    'MYC_TSS': 'ENSG00000136997',
}


# name_hg38 / name-style intervals: either chr:start-chr:end (duplex) or chr:start-end (simple).
_HG38_DUPLEX_INTERVAL_RE = re.compile(
    r'^(?P<c1>chr[^:]+):(?P<s1>\d+)-(?P<c2>chr[^:]+):(?P<s2>\d+)$'
)
_HG38_SIMPLE_INTERVAL_RE = re.compile(
    r'^(?P<c>chr[^:]+):(?P<s1>\d+)-(?P<s2>\d+)$'
)

# I keys that map row columns but are not numeric edge metrics.
_IGVF_E2G_LAYOUT_KEYS = frozenset({
    'readout_gene', 'promoter_gene', 'chr', 'start', 'end',
    'name_hg38', 'element_type',
})


class IGVFE2GCRISPR(BaseAdapter):

    ALLOWED_LABELS = [
        'genomic_element',
        'genomic_element_gene'
    ]
    SOURCE = 'IGVF'
    COLLECTION_LABEL = 'regulatory element effect on gene expression'

    @staticmethod
    def _normalize_ensembl_gene_id(gene_id: str) -> str:
        if not gene_id:
            return gene_id
        normalized = gene_id.strip().rstrip(');,')
        # Accept IDs like ENSG00000174038.13 by stripping version suffix.
        normalized = re.sub(
            r'^(ENSG[0-9]{11}(?:_PAR_Y)?)\.[0-9]+$',
            r'\1',
            normalized
        )
        return normalized

    @staticmethod
    def _parse_bool(value):
        if value is None:
            return None
        normalized = str(value).strip().lower()
        if normalized in {'true', 't', '1'}:
            return True
        if normalized in {'false', 'f', '0'}:
            return False
        return None

    def _targeted_element_mode(self) -> str:
        mode = CRISPR_E2G_TARGETED_ELEMENT_TYPES.get(self.file_accession)
        if mode is None:
            self.logger.warning(
                'No CRISPR_E2G_TARGETED_ELEMENT_TYPES entry for accession %s; '
                'using "both" (per-row ENSG vs coordinate heuristic). Add this file to the map in '
                'igvf_E2G_CRISPR_adapter.py.',
                self.file_accession,
            )
            return 'both'
        return mode

    def _promoter_gene_and_source_annotation(
        self,
        targeted_mode: str,
        intended_target_name: str,
        intended_target_gene_raw: str,
    ) -> Optional[Tuple[Optional[str], str]]:
        """
        Returns (promoter_gene, source_annotation) or None if the row should be skipped.
        """
        if targeted_mode == 'enhancer':
            return (None, 'enhancer')
        if targeted_mode == 'promoter':
            if not isinstance(intended_target_name, str) or not re.match(
                r'^ENSG[0-9]{11}(?:_PAR_Y)?$', intended_target_name
            ):
                self.logger.warning(
                    'Skipping row: file %s is promoter-targeted but intended_target_name '
                    '"%s" is not a valid Ensembl gene id pattern.',
                    self.file_accession,
                    intended_target_gene_raw,
                )
                return None
            if not self.gene_validator.validate(intended_target_name):
                self.logger.warning(
                    'Skipping row: intended promoter gene "%s" is not a valid gene after '
                    'normalization ("%s").',
                    intended_target_gene_raw,
                    intended_target_name,
                )
                return None
            return (intended_target_name, 'promoter')
        # targeted_mode == 'both'
        promoter_gene = None
        source_annotation = 'enhancer'
        if isinstance(intended_target_name, str) and re.match(
            r'^ENSG[0-9]{11}(?:_PAR_Y)?$', intended_target_name
        ):
            if self.gene_validator.validate(intended_target_name):
                promoter_gene = intended_target_name
                source_annotation = 'promoter'
            else:
                self.logger.warning(
                    'Skipping row: intended promoter gene "%s" is not a valid gene after '
                    'normalization ("%s").',
                    intended_target_gene_raw,
                    intended_target_name,
                )
                return None
        return (promoter_gene, source_annotation)

    @staticmethod
    def _parse_element_coordinates_hg38(name_hg38: str) -> Tuple[str, str, str]:
        s = (name_hg38 or '').strip()
        m = _HG38_DUPLEX_INTERVAL_RE.match(s)
        if m:
            c1, s1, c2, s2 = m['c1'], m['s1'], m['c2'], m['s2']
            if c1 != c2:
                raise ValueError(
                    f'name_hg38 spans two chromosomes: {name_hg38!r}')
            i1, i2 = int(s1), int(s2)
            if i1 <= i2:
                return c1, s1, s2
            return c1, s2, s1
        m = _HG38_SIMPLE_INTERVAL_RE.match(s)
        if m:
            c, s1, s2 = m['c'], m['s1'], m['s2']
            i1, i2 = int(s1), int(s2)
            if i1 <= i2:
                return c, s1, s2
            return c, s2, s1
        raise ValueError(f'Unrecognized name_hg38 interval: {name_hg38!r}')

    def _gene_raw_from_name_hg38_row(
        self,
        row,
        name_idx: int,
        type_idx: Optional[int],
    ) -> Tuple[str, str, str, str]:
        name_cell = row[name_idx]
        chr_, start, end = self._parse_element_coordinates_hg38(name_cell)
        row_type = (
            row[type_idx].strip()
            if type_idx is not None and type_idx < len(row)
            else ''
        )
        if row_type in CRUDO_TSS_PROMOTER_GENE:
            gene_raw = CRUDO_TSS_PROMOTER_GENE[row_type]
        else:
            gene_raw = name_cell
        return chr_, start, end, gene_raw

    @staticmethod
    def _perturb_seq_negative_control(row: list, type_col: Optional[int]) -> bool:
        if type_col is None or type_col >= len(row):
            return False
        return row[type_col].strip() == 'negative_control'

    def _resolve_explicit_interval(
        self,
        row: list,
        col: Dict[str, Optional[int]],
    ) -> Optional[Tuple[str, str, str, str]]:
        ci, si, ei, pi = col['chr'], col['start'], col['end'], col['promoter_gene']
        if ci is None or si is None or ei is None:
            return None
        if ci >= len(row) or si >= len(row) or ei >= len(row):
            return None
        c_raw, s_raw, e_raw = row[ci].strip(), row[si].strip(), row[ei].strip()
        if not (c_raw and s_raw and e_raw):
            return None
        if pi is None or pi >= len(row):
            self.logger.warning(
                'Skipping row in %s: explicit coordinates require '
                'intended_target_name column.',
                self.file_accession,
            )
            return None
        return (c_raw, s_raw, e_raw, row[pi])

    def _resolve_name_hg38_interval(
        self,
        row: list,
        col: Dict[str, Optional[int]],
    ) -> Optional[Tuple[str, str, str, str]]:
        ni = col['name_hg38']
        if ni is None or ni >= len(row) or not row[ni].strip():
            return None
        try:
            return self._gene_raw_from_name_hg38_row(
                row, ni, col['element_type'])
        except ValueError as err:
            self.logger.warning(
                'Skipping row in %s: %s',
                self.file_accession,
                err,
            )
            return None

    def _resolve_perturb_seq_element(
        self,
        row: list,
        col: Dict[str, Optional[int]],
    ) -> Optional[Tuple[str, str, str, str]]:
        explicit = self._resolve_explicit_interval(row, col)
        if explicit is not None:
            return explicit
        from_name = self._resolve_name_hg38_interval(row, col)
        if from_name is not None:
            return from_name
        self.logger.warning(
            'Skipping row in %s: missing coordinates (chr/start/end or name_hg38).',
            self.file_accession,
        )
        return None

    @staticmethod
    def _perturb_seq_columns(name_to_idx: Dict[str, int]) -> Dict[str, Optional[int]]:
        def pick(*candidates: str) -> Optional[int]:
            for name in candidates:
                if name in name_to_idx:
                    return name_to_idx[name]
            return None

        return {
            'p_value': pick(
                'EnhancerEff.pval',
                'p_val',
                'sceptre_p_value',
                'pval.EnhancerEffect.noAux',
            ),
            'p_value_adj': pick(
                'EnhancerEff.pval.adj',
                'p_val_adj',
                'sceptre_adj_p_value',
                'adj.pval.EnhancerEffect.noAux',
            ),
            'effect_size': pick('EnhancerEff', 'EnhancerEffect.noAux'),
            'log2FC': pick('avg_log2FC', 'sceptre_log2_fc'),
            'pct_1': pick('pct.1'),
            'pct_2': pick('pct.2'),
            'readout_gene': pick(
                'TargetGeneID', 'target_gene', 'ensembl_id', 'gene_id'),
            'promoter_gene': pick('intended_target_name'),
            'significant': pick('significant', 'Significant'),
            'name_hg38': pick('name_hg38'),
            'element_type': pick('type'),
            'chr': pick('intended_target_chr', 'targeting_chr'),
            'start': pick('intended_target_start', 'targeting_start'),
            'end': pick('intended_target_end', 'targeting_end'),
        }

    def _metrics_from_row(
        self,
        row: list,
        colmap: Dict[str, Optional[int]],
    ) -> dict:
        metrics = {}
        for key, col_idx in colmap.items():
            if key in _IGVF_E2G_LAYOUT_KEYS or col_idx is None:
                continue
            if col_idx >= len(row):
                continue
            cell = row[col_idx].strip()
            if key == 'significant':
                significant = self._parse_bool(row[col_idx])
                if significant is not None:
                    metrics[key] = significant
            elif cell:
                try:
                    metrics[key] = float(cell)
                except ValueError:
                    self.logger.warning(
                        'Skipping metric %s in %s: not a float (%r).',
                        key,
                        self.file_accession,
                        row[col_idx],
                    )
        return metrics

    def __init__(self, filepath, label, source_url, writer: Optional[Writer] = None, validate=False, **kwargs):
        self.source_url = source_url
        self.file_accession = source_url.split('/')[-2]
        self.gene_validator = GeneValidator()

        super().__init__(filepath, label, writer, validate)

    def _get_schema_type(self):
        """Return schema type based on label."""
        if self.label == 'genomic_element':
            return 'nodes'
        else:
            return 'edges'

    def _get_collection_name(self):
        """Get collection based on label."""
        if self.label == 'genomic_element':
            return 'genomic_elements'
        else:
            return 'genomic_elements_genes'

    def process_file(self):
        self.writer.open()
        file_fileset = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        method = file_fileset['method']
        crispr_modality = file_fileset.get('crispr_modality')
        targeted_element_mode = self._targeted_element_mode()
        genomic_coordinates_to_element_id = {}
        with gzip.open(self.filepath, 'rt') as data_file:
            reader = csv.reader(data_file, delimiter='\t')
            header = next(reader)
            name_to_idx = {h.strip(): i for i, h in enumerate(header)}

            if method == 'Perturb-seq':
                colmap = self._perturb_seq_columns(name_to_idx)
            elif method == 'CRISPR screen':
                colmap = {
                    'p_value': name_to_idx['FRACTEL_pval'],
                    'p_value_adj': name_to_idx['FRACTEL_pval_fdr_corr'],
                    'effect_size': name_to_idx['FRACTEL_effect_size'],
                    'readout_gene': name_to_idx['readout_gene'],
                    'promoter_gene': name_to_idx['intended_target_name'],
                    'chr': name_to_idx['intended_target_chr'],
                    'start': name_to_idx['intended_target_start'],
                    'end': name_to_idx['intended_target_end'],
                }
            else:
                raise ValueError(f'Method: {method} is unsupported.')

            for row in reader:
                if not row:
                    continue

                if method == 'Perturb-seq':
                    if self._perturb_seq_negative_control(row, colmap['element_type']):
                        continue
                    interval = self._resolve_perturb_seq_element(row, colmap)
                    if interval is None:
                        continue
                    (
                        intended_target_chr,
                        intended_target_start,
                        intended_target_end,
                        intended_target_gene_raw,
                    ) = interval
                    read_idx = colmap['readout_gene']
                    if read_idx is None or read_idx >= len(row):
                        self.logger.warning(
                            'Skipping row in %s: missing readout gene column.',
                            self.file_accession,
                        )
                        continue
                    readout_gene_raw = row[read_idx]
                else:
                    intended_target_chr = row[colmap['chr']]
                    intended_target_start = row[colmap['start']]
                    intended_target_end = row[colmap['end']]
                    intended_target_gene_raw = row[colmap['promoter_gene']]
                    readout_gene_raw = row[colmap['readout_gene']]

                intended_target_name = self._normalize_ensembl_gene_id(
                    intended_target_gene_raw)
                readout_gene = self._normalize_ensembl_gene_id(
                    readout_gene_raw)
                if not self.gene_validator.validate(readout_gene):
                    self.logger.warning(
                        'Skipping row: readout gene "%s" is not a valid gene after '
                        'normalization ("%s").',
                        readout_gene_raw,
                        readout_gene,
                    )
                    continue
                resolved = self._promoter_gene_and_source_annotation(
                    targeted_element_mode,
                    intended_target_name,
                    intended_target_gene_raw,
                )
                if resolved is None:
                    continue
                promoter_gene, source_annotation = resolved

                element_coordinates = (
                    intended_target_chr,
                    intended_target_start,
                    intended_target_end,
                    promoter_gene,
                    source_annotation,
                )
                if element_coordinates not in genomic_coordinates_to_element_id:
                    element_id = build_regulatory_region_id(
                        intended_target_chr,
                        intended_target_start,
                        intended_target_end,
                        'CRISPR',
                    )
                    genomic_coordinates_to_element_id[element_coordinates] = element_id
                else:
                    element_id = genomic_coordinates_to_element_id[
                        element_coordinates]

                metrics = self._metrics_from_row(row, colmap)

                if self.label == 'genomic_element_gene':
                    _id = '_'.join(
                        [element_id, readout_gene, self.file_accession])
                    _source = (
                        'genomic_elements/' + element_id + '_' + self.file_accession
                    )
                    _props = {
                        '_key': _id,
                        '_from': _source,
                        '_to': 'genes/' + readout_gene,
                        'source': IGVFE2GCRISPR.SOURCE,
                        'source_url': self.source_url,
                        'files_filesets': 'files_filesets/' + self.file_accession,
                        'label': self.COLLECTION_LABEL,
                        'class': file_fileset['class'],
                        'name': 'modulates expression of',
                        'inverse_name': 'expression modulated by',
                        'method': method,
                        'crispr_modality': crispr_modality,
                        'biological_context': file_fileset['simple_sample_summaries'][0],
                        'biosample_term': file_fileset['samples'][0],
                        'treatments_term_ids': file_fileset['treatments_term_ids'],
                    }
                    _props.update(metrics)
                    if self.validate:
                        self.validate_doc(_props)
                    self.writer.write(json.dumps(_props))
                    self.writer.write('\n')

            if self.label == 'genomic_element':
                for genomic_element, element_id in genomic_coordinates_to_element_id.items():
                    source_annotation = genomic_element[4]
                    promoter_gene = genomic_element[3]
                    _id = element_id + '_' + self.file_accession
                    _props = {
                        '_key': _id,
                        'name': _id,
                        'chr': genomic_element[0],
                        'start': int(genomic_element[1]),
                        'end': int(genomic_element[2]),
                        'method': method,
                        'source_annotation': source_annotation,
                        'source': IGVFE2GCRISPR.SOURCE,
                        'source_url': self.source_url,
                        'type': 'tested elements',
                        'files_filesets': 'files_filesets/' + self.file_accession
                    }
                    if source_annotation == 'promoter':
                        if not promoter_gene:
                            raise ValueError(
                                f'Promoter element {_id} is missing promoter_gene.')
                        _props['promoter_of'] = f'genes/{promoter_gene}'
                    if self.validate:
                        self.validate_doc(_props)
                    self.writer.write(json.dumps(_props))
                    self.writer.write('\n')
        self.writer.close()
