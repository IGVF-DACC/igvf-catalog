import csv
import gzip
import json
import re
from typing import Optional

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
# 0.7264835	0.9994257067617868	0.2254047296279381	ENSG00000188290	chr1	998962	999432	ENSG00000126353	CCR7
# 0.6353328	0.9994257067617868	0.4499883534060434	ENSG00000157933	chr1	2228695	2229735	ENSG00000126353	CCR7
# 0.8264444	0.9994257067617868	0.2234036501031779	ENSG00000197921	chr1	2528745	2529749	ENSG00000126353	CCR7
# 0.0375612	0.7776272999999999	-0.902286973451608	ENSG00000142611	chr1	3385152	3385286	ENSG00000126353	CCR7
# 0.4863262	0.9994257067617868	0.4703859734914864	ENSG00000078900	chr1	3707549	3707791	ENSG00000126353	CCR7
# 0.6627895	0.9994257067617868	-0.4684078131930258	ENSG00000173673	chr1	6244351	6244446	ENSG00000126353	CCR7
# 0.5737245	0.9994257067617868	0.4359202869686309	ENSG00000069812	chr1	6415232	6419153	ENSG00000126353	CCR7
# 0.0163096	0.4615330666666667	0.6634541544827465	ENSG00000204859	chr1	6582058	6582299	ENSG00000126353	CCR7
# 0.6030225	0.9994257067617868	0.40989234019479	ENSG00000041988	chr1	6628499	6628691	ENSG00000126353	CCR7

# Example rows from Quertermous's TAP-seq data
# intended_target_name	Intended_target_gene_id	guide_id(s)	targeting_chr	targeting_start	targeting_end	gene_id	gene_symbol	sceptre_log2_fc	sceptre_p_value	sceptre_adj_p_value	significant	type
# POLR3D	ENSG00000168495	POLR3D_1,POLR3D_2,POLR3D_3	chrX	100627108	100639991	ENSG00000000003	TSPAN6	0	1	1	FALSE	Indirect_targeting
# SNRPD2	ENSG00000125743	SNRPD2_1,SNRPD2_2,SNRPD2_3	chrX	100627108	100639991	ENSG00000000003	TSPAN6	0	1	1	FALSE	Indirect_targeting
# PSMA5	ENSG00000143106	PSMA5_1,PSMA5_2,PSMA5_3	chrX	100627108	100639991	ENSG00000000003	TSPAN6	0	1	1	FALSE	Indirect_targeting
# SRSF3	ENSG00000112081	SRSF3_1,SRSF3_2,SRSF3_3	chrX	100627108	100639991	ENSG00000000003	TSPAN6	0	1	1	FALSE	Indirect_targeting
# RPS7	ENSG00000171863	RPS7_1,RPS7_2,RPS7_3	chrX	100627108	100639991	ENSG00000000003	TSPAN6	0	1	1	FALSE	Indirect_targeting
# MAN2A2	ENSG00000196547	MAN2A2_1,MAN2A2_2,MAN2A2_3	chrX	100627108	100639991	ENSG00000000003	TSPAN6	0	1	1	FALSE	Indirect_targeting
# PPA1	ENSG00000180817	PPA1_1,PPA1_2,PPA1_3	chrX	100627108	100639991	ENSG00000000003	TSPAN6	0	1	1	FALSE	Indirect_targeting
# RPS6	ENSG00000137154	RPS6_1,RPS6_2,RPS6_3	chrX	100627108	100639991	ENSG00000000003	TSPAN6	0	1	1	FALSE	Indirect_targeting
# NSRP1	ENSG00000126653	NSRP1_1,NSRP1_2,NSRP1_3	chrX	100627108	100639991	ENSG00000000003	TSPAN6	0	1	1	FALSE	Indirect_targeting


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
        genomic_coordinates_to_element_id = {}
        with gzip.open(self.filepath, 'rt') as data_file:
            reader = csv.reader(data_file, delimiter='\t')
            header = next(reader)

            name_to_idx = {h.strip(): i for i, h in enumerate(header)}

            def get_column_index(*column_names):
                for column_name in column_names:
                    if column_name in name_to_idx:
                        return name_to_idx[column_name]
                raise KeyError(
                    f"Missing expected column. Tried: {', '.join(column_names)}")

            def get_optional_column_index(*column_names):
                for column_name in column_names:
                    if column_name in name_to_idx:
                        return name_to_idx[column_name]
                return None

            if method in ['Perturb-seq', 'TAP-seq', 'Parse Perturb-seq']:
                I = {
                    'p_val': get_column_index('p_val', 'sceptre_p_value'),
                    'log2_fc': get_column_index('avg_log2FC', 'sceptre_log2_fc'),
                    'pct_1': get_optional_column_index('pct.1'),
                    'pct_2': get_optional_column_index('pct.2'),
                    'p_val_adj': get_column_index('p_val_adj', 'sceptre_adj_p_value'),
                    'target_gene': get_column_index('target_gene', 'ensembl_id', 'gene_id'),
                    'promoter_gene': get_column_index(
                        'Intended_target_gene_id',
                        'intended_target_name'
                    ),
                    'chr': get_column_index('intended_target_chr', 'targeting_chr'),
                    'start': get_column_index('intended_target_start', 'targeting_start'),
                    'end': get_column_index('intended_target_end', 'targeting_end'),
                }
            elif method == 'CRISPR FACS screen':
                I = {
                    'p_val': name_to_idx['FRACTEL_pval'],
                    'p_val_adj': name_to_idx['FRACTEL_pval_fdr_corr'],
                    'effect_size': name_to_idx['FRACTEL_effect_size'],
                    'target_gene': name_to_idx['readout_gene'],
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

                intended_target_chr = row[I['chr']]
                intended_target_start = row[I['start']]
                intended_target_end = row[I['end']]
                intended_target_name = self._normalize_ensembl_gene_id(
                    row[I['promoter_gene']])
                target_gene_raw = row[I['target_gene']]
                target_gene = self._normalize_ensembl_gene_id(target_gene_raw)
                if not self.gene_validator.validate(target_gene):
                    self.logger.warning(
                        f'Skipping row: targeted gene "{target_gene_raw}" is not a valid gene after normalization ("{target_gene}").')
                    continue
                promoter_gene = None
                source_annotation = 'enhancer'
                if self.gene_validator.validate(intended_target_name):
                    promoter_gene = intended_target_name
                    source_annotation = 'promoter'

                element_coordinates = (
                    intended_target_chr, intended_target_start, intended_target_end, promoter_gene, source_annotation)
                if element_coordinates not in genomic_coordinates_to_element_id:
                    element_id = build_regulatory_region_id(
                        intended_target_chr, intended_target_start, intended_target_end, 'CRISPR')
                    genomic_coordinates_to_element_id[element_coordinates] = element_id
                else:
                    element_id = genomic_coordinates_to_element_id[element_coordinates]

                if method in ['Perturb-seq', 'TAP-seq']:
                    metrics = {
                        'p_value': float(row[I['p_val']]),
                        'log2FC': float(row[I['log2_fc']]),
                        'p_value_adj': float(row[I['p_val_adj']]),
                    }
                    if I['pct_1'] is not None:
                        metrics['pct_1'] = float(row[I['pct_1']])
                    if I['pct_2'] is not None:
                        metrics['pct_2'] = float(row[I['pct_2']])
                elif method == 'CRISPR FACS screen':
                    metrics = {
                        'p_value': float(row[I['p_val']]),
                        'p_value_adj': float(row[I['p_val_adj']]),
                        'effect_size': float(row[I['effect_size']])
                    }

                if self.label == 'genomic_element_gene':
                    _id = '_'.join(
                        [element_id, target_gene, self.file_accession])
                    _source = 'genomic_elements/' + element_id + '_' + self.file_accession
                    _props = {
                        '_key': _id,
                        '_from': _source,
                        '_to': 'genes/' + target_gene,
                        'source': IGVFE2GCRISPR.SOURCE,
                        'source_url': self.source_url,
                        'files_filesets': 'files_filesets/' + self.file_accession,
                        'label': self.COLLECTION_LABEL,
                        'class': file_fileset['class'],
                        'name': 'modulates expression of',
                        'inverse_name': 'expression modulated by',
                        'method': method,
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
                    if genomic_element[3]:
                        _props['promoter_of'] = f'genes/{genomic_element[3]}'
                    if self.validate:
                        self.validate_doc(_props)
                    self.writer.write(json.dumps(_props))
                    self.writer.write('\n')
        self.writer.close()
