import csv
import gzip
import json
from typing import Optional

from adapters.helpers import build_regulatory_region_id
from adapters.file_fileset_adapter import FileFileSet
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


class GersbachE2GCRISPR:

    ALLOWED_LABELS = [
        'genomic_element',
        'genomic_element_gene'
    ]
    SOURCE = 'IGVF'

    def __init__(self, filepath, label, source_url, writer: Optional[Writer] = None, **kwargs):
        if label not in GersbachE2GCRISPR.ALLOWED_LABELS:
            raise ValueError('Ivalid label. Allowed values: ' +
                             ','.join(GersbachE2GCRISPR.ALLOWED_LABELS))
        self.data_file = filepath
        self.label = label
        self.source_url = source_url
        self.file_accession = source_url.split('/')[-2]
        self.dataset = label
        self.type = 'edge'
        if (self.label == 'genomic_element'):
            self.type = 'node'
        self.writer = writer
        self.gene_validator = GeneValidator()
        self.files_filesets = FileFileSet(
            self.file_accession, replace=False, writer=None, label='igvf_file_fileset')

    def process_file(self):
        self.writer.open()

        file_set_props, _, _ = self.files_filesets.query_fileset_files_props_igvf(
            self.file_accession)
        simple_sample_summaries = file_set_props['simple_sample_summaries']
        biosample_term = file_set_props['samples'][0]
        treatments_term_ids = file_set_props['treatments_term_ids']
        method = file_set_props['method']

        genomic_coordinates_to_element_id = {}
        with gzip.open(self.data_file, 'rt') as data_file:
            reader = csv.reader(data_file, delimiter='\t')
            header = next(reader)

            name_to_idx = {h.strip(): i for i, h in enumerate(header)}

            if method == 'Perturb-seq':
                I = {
                    'p_val': name_to_idx['p_val'],
                    'avg_log2FC': name_to_idx['avg_log2FC'],
                    'pct_1': name_to_idx['pct.1'],
                    'pct_2': name_to_idx['pct.2'],
                    'p_val_adj': name_to_idx['p_val_adj'],
                    'target_gene': name_to_idx['target_gene'],
                    'promoter_gene': name_to_idx['intended_target_name'],
                    'chr': name_to_idx['intended_target_chr'],
                    'start': name_to_idx['intended_target_start'],
                    'end': name_to_idx['intended_target_end'],
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
                intended_target_name = row[I['promoter_gene']]
                target_gene = row[I['target_gene']]
                if not self.gene_validator.validate(intended_target_name):
                    raise ValueError(
                        f'Promoter gene: {intended_target_name} is not a valid gene.')
                if not self.gene_validator.validate(target_gene):
                    raise ValueError(
                        f'Targeted gene: {target_gene} is not a valid gene.')

                element_coordinates = (
                    intended_target_chr, intended_target_start, intended_target_end, intended_target_name)
                if element_coordinates not in genomic_coordinates_to_element_id:
                    element_id = build_regulatory_region_id(
                        intended_target_chr, intended_target_start, intended_target_end, 'CRISPR')
                    genomic_coordinates_to_element_id[element_coordinates] = element_id
                else:
                    element_id = genomic_coordinates_to_element_id[element_coordinates]

                if method == 'Perturb-seq':
                    metrics = {
                        'p_val': float(row[I['p_val']]),
                        'avg_log2FC': float(row[I['avg_log2FC']]),
                        'pct_1': float(row[I['pct_1']]),
                        'pct_2': float(row[I['pct_2']]),
                        'p_val_adj': float(row[I['p_val_adj']]),
                    }
                elif method == 'CRISPR FACS screen':
                    metrics = {
                        'p_val': float(row[I['p_val']]),
                        'p_val_adj': float(row[I['p_val_adj']]),
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
                        'source': GersbachE2GCRISPR.SOURCE,
                        'source_url': self.source_url,
                        'files_filesets': 'files_filesets/' + self.file_accession,
                        'label': f'element effect on gene expression of {target_gene}',
                        'name': 'modulates expression of',
                        'inverse_name': 'expression modulated by',
                        'method': method,
                        'simple_sample_summaries': simple_sample_summaries,
                        'biological_context': biosample_term,
                        'treatments_term_ids': treatments_term_ids,
                    }
                    _props.update(metrics)
                    self.writer.write(json.dumps(_props))
                    self.writer.write('\n')

            if self.label == 'genomic_element':
                for genomic_element, element_id in genomic_coordinates_to_element_id.items():
                    source_annotation = 'promoter'
                    if int(genomic_element[2]) - int(genomic_element[1]) == 1:
                        source_annotation = 'transcription start site'
                    _id = element_id + '_' + self.file_accession
                    _props = {
                        '_key': _id,
                        'name': _id,
                        'chr': genomic_element[0],
                        'start': int(genomic_element[1]),
                        'end': int(genomic_element[2]),
                        'promoter_of': f'genes/{genomic_element[3]}',
                        'method': method,
                        'source_annotation': source_annotation,
                        'source': GersbachE2GCRISPR.SOURCE,
                        'source_url': self.source_url,
                        'type': 'tested elements',
                        'files_filesets': 'files_filesets/' + self.file_accession
                    }
                    self.writer.write(json.dumps(_props))
                    self.writer.write('\n')
        self.writer.close()
