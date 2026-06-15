import gzip
import csv
import json
from typing import Optional

from adapters.base import BaseAdapter
from adapters.helpers import build_regulatory_region_id, get_file_fileset_by_accession_in_arangodb
from adapters.writer import Writer
from adapters.gene_validator import GeneValidator

# data files from: https://api.data.igvf.org/multireport/?type=TabularFile&file_format=tsv&lab.title=Jesse+Engreitz%2C+Stanford&filtered=true&status!=revoked&field=%40id&field=catalog_class&field=catalog_collections&field=collections&content_type=element+to+gene+interactions&limit=100&accession!=IGVFFI3412RLDF
# file example:
# # Source: scE2G
# # Version: v1.2.0
# # ModelType: multiome_powerlaw_v3
# # VirtualSampleTermName: jesse-engreitz:encode-10x-adrenal_medulla_chromaffin_cell
# # ScoreThreshold: 0.177
# ElementChr	ElementStart	ElementEnd	ElementName	ElementClass	GeneSymbol	GeneEnsemblID	GeneTSS	CellType	CellTypeOntologyTerm	CellTypeOntologyTermName	Score	RNA_pseudobulkTPM
# chr1	169893055	169894554	chr1:169893055-169894554	promoter	SCYL3	ENSG00000000457	169893959	Adrenal medulla chromaffin cell	CL:0000336	Adrenal medulla chromaffin cell	0.996889932534048	22.8574991753656
#
# Three header formats are supported:
# 1. Standard (13 columns): includes ElementClass, Score, RNA_pseudobulkTPM
# 2. Extended (16 columns): standard plus SampleOntologyTerm, SampleOntologyTermName, Qualifier
# 3. Alternate (12 columns): no ElementClass or RNA_pseudobulkTPM; uses SampleSummaryShort


class scE2G(BaseAdapter):
    ALLOWED_LABELS = [
        'genomic_element_gene',  # genomic_element --(edge)--> gene
        'genomic_element'
    ]
    SOURCE = 'IGVF'
    COLLECTION_LABEL = 'predicted regulatory element effect on gene expression'
    TYPE = 'accessible dna elements'
    DEFAULT_ELEMENT_CLASS = 'enhancer'

    def __init__(self, filepath, label, writer: Optional[Writer] = None, validate=False, **kwargs):
        self.file_accession = filepath.split('/')[-1].split('.')[0]
        self.source_url = 'https://data.igvf.org/tabular-files/' + self.file_accession
        super().__init__(filepath, label, writer, validate)
        if label == 'genomic_element_gene':
            self.gene_validator = GeneValidator()

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

    def _read_header_map(self, reader):
        for row in reader:
            if row and row[0].startswith('#'):
                continue
            if not row:
                continue
            return {column: index for index, column in enumerate(row)}
        raise ValueError(f'No header found in {self.filepath}')

    def _get_column_value(self, row, header_map, column_name):
        index = header_map.get(column_name)
        if index is None:
            return None
        return row[index]

    def _get_element_class(self, row, header_map):
        element_class = self._get_column_value(row, header_map, 'ElementClass')
        if element_class:
            return element_class
        return self.DEFAULT_ELEMENT_CLASS

    def _get_rna_pseudobulk_tpm(self, row, header_map):
        value = self._get_column_value(row, header_map, 'RNA_pseudobulkTPM')
        if value in (None, ''):
            return None
        return float(value)

    def process_file(self):
        self.writer.open()
        file_fileset = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        method = file_fileset.get('method')
        collection_class = file_fileset.get('class')
        with gzip.open(self.filepath, 'rt') as f:
            reader = csv.reader(f, delimiter='\t')
            header_map = self._read_header_map(reader)
            for row in reader:
                if not row:
                    continue
                chr = row[header_map['ElementChr']]
                start = row[header_map['ElementStart']]
                end = row[header_map['ElementEnd']]
                element_class_name = self._get_element_class(row, header_map)
                regulatory_element_id = build_regulatory_region_id(
                    chr, start, end, class_name=element_class_name) + '_' + self.file_accession

                if self.label == 'genomic_element_gene':
                    if not file_fileset.get('simple_sample_summaries'):
                        cell_type = row[10]
                        cell_type_term_id = row[9].replace(':', '_')
                        cell_type_term_endpoint = f'ontology_terms/{cell_type_term_id}'
                    else:
                        cell_type = file_fileset.get(
                            'simple_sample_summaries')[0]
                        cell_type_term_endpoint = file_fileset.get('samples')[
                            0]
                        cell_type_term_id = cell_type_term_endpoint.split(
                            '/')[-1]
                    gene_id = row[header_map['GeneEnsemblID']]
                    is_valid_gene_id = self.gene_validator.validate(gene_id)
                    if not is_valid_gene_id:
                        self.logger.warning(
                            f'Skipping row: gene "{gene_id}" is not a valid gene.')
                        continue
                    transcription_start_site = int(row[header_map['GeneTSS']])
                    score = float(row[header_map['Score']])
                    rna_pseudobulk_tpm = self._get_rna_pseudobulk_tpm(
                        row, header_map)
                    key = f'{regulatory_element_id}_{gene_id}_{cell_type_term_id}'
                    props = {
                        '_key': key,
                        '_from': f'genomic_elements/{regulatory_element_id}',
                        '_to': f'genes/{gene_id}',
                        'transcription_start_site': transcription_start_site,
                        'score': score,
                        'rna_pseudobulk_tpm': rna_pseudobulk_tpm,
                        'cell_type': cell_type,
                        'cell_type_term': cell_type_term_endpoint,
                        'files_filesets': 'files_filesets/' + self.file_accession,
                        'label': self.COLLECTION_LABEL,
                        'method': method,
                        'class': collection_class,
                        'source': self.SOURCE,
                        'source_url': self.source_url,
                        'name': 'regulates',
                        'inverse_name': 'regulated by'
                    }
                else:
                    props = {
                        '_key': regulatory_element_id,
                        'name': regulatory_element_id,
                        'chr': chr,
                        'start': int(start),
                        'end': int(end),
                        'source_annotation': element_class_name,
                        'type': self.TYPE,
                        'method': method,
                        'source': self.SOURCE,
                        'source_url': self.source_url,
                        'files_filesets': 'files_filesets/' + self.file_accession
                    }
                if self.validate:
                    self.validate_doc(props)
                self.writer.write(json.dumps(props))
                self.writer.write('\n')

        self.writer.close()
        if self.label == 'genomic_element_gene':
            self.gene_validator.log()
