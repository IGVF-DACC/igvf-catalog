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


class GersbachE2GPerturbseq:

    ALLOWED_LABELS = [
        'genomic_element',
        'genomic_element_gene'
    ]
    SOURCE = 'IGVF'

    def __init__(self, filepath, label, source_url, writer: Optional[Writer] = None, **kwargs):
        if label not in GersbachE2GPerturbseq.ALLOWED_LABELS:
            raise ValueError('Ivalid label. Allowed values: ' +
                             ','.join(GersbachE2GPerturbseq.ALLOWED_LABELS))
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
            self.file_accession, writer=None, label='igvf_file_fileset')

    def process_file(self):
        self.writer.open()

        file_set_props, _, _ = self.files_filesets.query_fileset_files_props_igvf(
            self.file_accession, replace=False)
        simple_sample_summaries = file_set_props['simple_sample_summaries']
        biosample_term = file_set_props['samples']
        treatments_term_ids = file_set_props['treatments_term_ids']
        method = file_set_props['method']
        genomic_element_to_element_id = {}
        with gzip.open(self.data_file, 'rt') as data_file:
            reader = csv.reader(data_file, delimiter='\t')
            next(reader)
            for row in reader:
                p_val = float(row[0])
                avg_log2FC = float(row[1])
                pct_1 = float(row[2])
                pct_2 = float(row[3])
                p_val_adj = float(row[4])
                target_gene = row[6]
                if not self.gene_validator.validate(target_gene):
                    raise ValueError(
                        f'Promoted gene: {target_gene} is not a valid gene.')
                intended_target_name = row[7]
                if not self.gene_validator.validate(intended_target_name):
                    raise ValueError(
                        f'Promoted gene: {intended_target_name} is not a valid gene.')
                intended_target_chr = row[8]
                intended_target_start = row[9]
                intended_target_end = row[10]
                element_id = build_regulatory_region_id(
                    intended_target_chr, intended_target_start, intended_target_end, 'CRISPR')
                element_coordinates = (
                    intended_target_chr, intended_target_start, intended_target_end, intended_target_name)
                genomic_element_to_element_id[element_coordinates] = element_id

                if self.label == 'genomic_element_gene':
                    element_id = genomic_element_to_element_id[element_coordinates]
                    _id = '_'.join(
                        [element_id, target_gene, self.file_accession])
                    _source = 'genomic_elements/' + element_id + '_' + self.file_accession
                    _props = {
                        '_key': _id,
                        '_from': _source,
                        '_to': 'genes/' + target_gene,
                        'p_val': p_val,
                        'avg_log2FC': avg_log2FC,
                        'pct_1': pct_1,
                        'pct_2': pct_2,
                        'p_val_adj': p_val_adj,
                        'source': GersbachE2GPerturbseq.SOURCE,
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
                    self.writer.write(json.dumps(_props))
                    self.writer.write('\n')

            if self.label == 'genomic_element':
                for genomic_element, element_id in genomic_element_to_element_id.items():
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
                        'source': GersbachE2GPerturbseq.SOURCE,
                        'source_url': self.source_url,
                        'type': 'promoter',
                        'files_filesets': 'files_filesets/' + self.file_accession
                    }
                    self.writer.write(json.dumps(_props))
                    self.writer.write('\n')
        self.writer.close()
