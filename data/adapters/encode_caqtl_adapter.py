import json
import os
from typing import Optional

from adapters.helpers import build_variant_id, build_regulatory_region_id
from adapters.writer import Writer
from adapters.file_fileset_adapter import FileFileSet

# Example Encode caQTL input file:
# chr1	766454	766455	chr1_766455_T_C	chr1	766455	T	C	1	778381	779150	FALSE	1_778381_779150	C	T	rs189800799	Progenitor
# chr1	766454	766455	chr1_766455_T_C	chr1	766455	T	C	1	778381	779150	FALSE	1_778381_779150	C	T	rs189800799	Neuron
# chr1	1668541	1668542	chr1_1668542_C_T	chr1	1668542	C	T	1	1658831	1659350	FALSE	1_1658831_1659350	T	C	rs72634822	Progenitor
# chr1	1687152	1687153	chr1_1687153_A_G	chr1	1687153	A	G	1	1745801	1746550	FALSE	1_1745801_1746550	A	G	rs28366981	Progenitor

# Columns parsed in ths adapter:
# 1: variant chrom; 3: variant position (1-based); 7: variant ref allele; 8: variant alt allele; 2nd last: rsID
# 9: caPeak chrom; 10: caPeak start; 11: caPeak end;
# last column: cell name


class CAQtl:
    # 1-based coordinate system

    ALLOWED_LABELS = ['genomic_element', 'encode_caqtl']
    CLASS_NAME = 'accessible_dna_element'
    # we can have a map file if loading more datasets in future
    CELL_ONTOLOGY = {
        'Progenitor': {
            'term_id': 'CL_0011020',
            'term_name': 'neural progenitor cell'
        },
        'Neuron': {
            'term_id': 'CL_0000540',
            'term_name': 'neuron'
        },
        'Liver': {
            'term_id': 'UBERON_0002107',
            'term_name': 'liver'
        }
    }
    EDGE_COLLECTION_NAME = 'modulates accessibility of'
    EDGE_COLLECTION_INVERSR_NAME = 'accessibility modulated by'
    EDGE_COLLECTION_METHOD = 'BAO_0040027'  # chromatin acessibility method

    def __init__(self, filepath, source, label, dry_run=True, writer: Optional[Writer] = None, **kwargs):
        if label not in CAQtl.ALLOWED_LABELS:
            raise ValueError('Invalid label. Allowed values: ' +
                             ','.join(CAQtl.ALLOWED_LABELS))

        self.filepath = filepath
        self.file_accession = os.path.basename(self.filepath).split('.')[0]
        self.files_filesets = FileFileSet(self.file_accession)
        self.dataset = label
        self.label = label
        self.source = source
        self.dry_run = dry_run
        self.type = 'edge'
        if (self.label == 'genomic_element'):
            self.type = 'node'
        self.writer = writer

    def process_file(self):
        self.writer.open()
        encode_metadata_props = self.files_filesets.query_fileset_files_props_encode(
            self.file_accession)[0]
        for line in open(self.filepath, 'r'):
            data_line = line.strip().split()

            ocr_chr = 'chr' + data_line[8]
            ocr_pos_start = data_line[9]
            ocr_pos_end = data_line[10]
            genomic_element_id = build_regulatory_region_id(
                ocr_chr, ocr_pos_start, ocr_pos_end, class_name=CAQtl.CLASS_NAME
            )

            if self.label == 'encode_caqtl':
                chr = data_line[0]
                pos = data_line[2]
                ref = data_line[6]
                alt = data_line[7]
                variant_id = build_variant_id(chr, pos, ref, alt)
                cell_name = data_line[-1]

                # there can be same variant -> atac peak in multiple cells in same file, we want to make edges for each cell
                _id = variant_id + '_' + genomic_element_id + \
                    '_' + cell_name + '_' + self.file_accession
                _source = 'variants/' + variant_id
                _target = 'genomic_elements/' + genomic_element_id + '_' + self.file_accession
                _props = {
                    '_key': _id,
                    '_from': _source,
                    '_to': _target,
                    'rsid': data_line[-2],
                    'label': 'caQTL',
                    'method': encode_metadata_props.get('method'),
                    'source': 'ENCODE',
                    'source_url': 'https://www.encodeproject.org/files/' + self.file_accession,
                    'files_filesets': 'files_filesets/' + self.file_accession,
                    'biological_context': CAQtl.CELL_ONTOLOGY[cell_name]['term_name'],
                    'biosample_term': 'ontology_terms/' + CAQtl.CELL_ONTOLOGY[cell_name]['term_id'],
                    'name': CAQtl.EDGE_COLLECTION_NAME,
                    'inverse_name': CAQtl.EDGE_COLLECTION_INVERSR_NAME,
                    'method_term': 'ontology_terms/' + CAQtl.EDGE_COLLECTION_METHOD,
                }

                self.writer.write(json.dumps(_props))
                self.writer.write('\n')

            elif self.label == 'genomic_element':
                _id = genomic_element_id + '_' + self.file_accession
                _props = {
                    '_key': _id,
                    'name': _id,
                    'chr': ocr_chr,
                    'start': int(ocr_pos_start),
                    'end': int(ocr_pos_end),
                    'method': encode_metadata_props.get('method'),
                    'source': 'ENCODE',
                    'source_url': 'https://www.encodeproject.org/files/' + self.file_accession,
                    'files_filesets': 'files_filesets/' + self.file_accession,
                    'type': 'accessible dna elements',
                }

                self.writer.write(json.dumps(_props))
                self.writer.write('\n')
        self.writer.close()
