import csv
from collections import defaultdict
import json
import os
from typing import Optional

from adapters.archive_utils import get_file_accession
from adapters.base import BaseAdapter
from adapters.helpers import get_gene_map_from_arangodb, get_file_fileset_by_accession_in_arangodb
from adapters.ontology_term_validator import OntologyTermValidator
from adapters.writer import Writer

# CRISPRGeneDependency.csv is downloaded from DepMap portal: https://depmap.org/portal/download/all/
# The original matrix in file is organized as ModelID (rows) X Gene (columns).
# The transpose of the original matrix is loaded here for easier processing.
#
# Portal files (example):
#   IGVFFI8832ZBCC — CRISPRGeneDependency_transposed.csv (dependency matrix)
#   IGVFFI6415FDRI — Model.csv (cell-line metadata / RRID mapping)
#
# Example of part of the loading matrix:
# Gene,ACH-000001,ACH-000004,ACH-000005,ACH-000007,ACH-000009,ACH-000011,ACH-000012,ACH-000013,ACH-000014
# A1BG (1),0.0553211648540664,0.0234180490346237,0.0595523208289766,0.0238795185094775,0.0276524140275033,0.011752429730298,0.0543502827694051,0.0124079166941024,0.040318101157517
# A1CF (29974),0.01403856306881,0.0487237248460492,0.0254784832528157,0.0350823083989964,0.0748604776571315,0.0185146565164343,0.0124800836750166,0.0565492355005334,0.060836485655342
#
# Example of part of Model.csv (columns used by the adapter; file has additional metadata columns):
# ModelID,CellLineName,DepmapModelType,OncotreeCode,RRID,...
# ACH-000001,NIH:OVCAR-3,HGSOC,HGSOC,CVCL_0465,...
# ACH-000004,HEL,AMLNOS,AMLNOS,CVCL_0001,...
# ACH-000005,HEL 92.1.7,AML,AML,CVCL_2481,...
#
# Gene rows are "SYMBOL (ENTREZ_ID)". Ensembl ids are resolved from the genes
# collection in order: entrez (ENTREZ:{id}), then name for symbols still
# unmapped, then synonyms for symbols still unmapped.


class DepMap(BaseAdapter):
    ALLOWED_LABELS = ['depmap']
    SOURCE = 'DepMap'
    SOURCE_URL = 'https://depmap.org/portal/'
    SOURCE_FILE = 'CRISPRGeneDependency.csv'
    CUTOFF = 0.5  # only load genes with dependency scores greater or equal to 0.5 for each cell
    # Model.csv column headers -> edge property names
    MODEL_COLUMN_HEADERS = {
        'biological_context': 'CellLineName',
        'cell_ontology_id': 'RRID',
        'model_type': 'DepmapModelType',
        'oncotree_code': 'OncotreeCode',
    }

    def __init__(
        self,
        filepath,
        reference_filepath,
        label='depmap',
        writer: Optional[Writer] = None,
        validate=False,
        **kwargs
    ):
        self.ontology_term_validator = OntologyTermValidator()
        self.reference_filepath = reference_filepath
        super().__init__(filepath, label, writer, validate)
        self.file_accession = get_file_accession(filepath)
        self.model_file_accession = os.path.basename(
            self.reference_filepath).split('.')[0]

    def _get_schema_type(self):
        """Return schema type."""
        return 'edges'

    def _get_collection_name(self):
        """Get collection name."""
        return 'genes_biosamples'

    def parse(self):
        self.writer.add_tag('portal_accessions', self.file_accession)
        self.writer.add_tag('portal_accessions', self.model_file_accession)
        self.file_fileset = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        self.collection_class = self.file_fileset['class']
        self.method = self.file_fileset['method']
        file_set_accession = self.file_fileset.get('file_set_id')
        if file_set_accession:
            self.writer.add_tag('portal_accessions', file_set_accession)

        self.load_cell_ontology_id_mapping()
        self.load_gene_id_mapping()

        with open(self.filepath, 'r') as depmap_file:
            # read model ids on the first row
            model_ids = next(depmap_file).strip().split(',')[1:]
            # record the column index of each model ID (start from 2nd column)
            model_ids_column_mapping = {}
            ontology_term_keys = set()
            for column_index, model_id in enumerate(model_ids):
                model_ids_column_mapping[column_index] = model_id
                model_props = self.cell_ontology_id_mapping[model_id]
                # check CVCL / Oncotree mapping for all models once first
                cell_ontology_id = model_props.get('cell_ontology_id')
                if not cell_ontology_id:
                    self.logger.warning(
                        'Cell ontology unavailable for model id ' + model_id)
                else:
                    ontology_term_keys.add(cell_ontology_id)
                oncotree_code = model_props.get('oncotree_code')
                if not oncotree_code:
                    self.logger.warning(
                        'Oncotree code unavailable for model id ' + model_id)
                else:
                    # Match Oncotree _key ('/' is illegal in ArangoDB keys)
                    ontology_term_keys.add(
                        'Oncotree_' + oncotree_code.replace('/', '_'))

            self.ontology_term_validator.preload(
                ontology_term_keys, resolve_via_ols=True)

            for line in depmap_file:
                gene, *values = line.strip().split(',')
                gene_ids = self._gene_ids_for_label(gene)
                if gene_ids is None:
                    self.logger.warning('no gene id mapping for ' + gene)
                    continue

                for value_index, value in enumerate(values):
                    if not value:  # skip NA values
                        continue
                    # only load gene-cell pairs with values >= cutoff (0.5)
                    elif float(value) >= DepMap.CUTOFF:
                        gene_model_id = model_ids_column_mapping[value_index]
                        model_props = self.cell_ontology_id_mapping[gene_model_id]
                        cell_ontology_id = model_props.get('cell_ontology_id')
                        if not cell_ontology_id:  # no CVCL id provided for this model
                            continue
                        oncotree_code = model_props.get('oncotree_code')
                        if not oncotree_code:
                            continue
                        resolved_cell_ontology_id = self.ontology_term_validator.resolve(
                            cell_ontology_id)
                        if not resolved_cell_ontology_id:
                            continue
                        cancer_term_key = 'Oncotree_' + \
                            oncotree_code.replace('/', '_')
                        resolved_cancer_term = self.ontology_term_validator.resolve(
                            cancer_term_key)
                        if not resolved_cancer_term:
                            continue

                        for gene_id in gene_ids:
                            _id = gene_id + '_' + resolved_cell_ontology_id
                            _source = 'genes/' + gene_id
                            _target = 'ontology_terms/' + resolved_cell_ontology_id

                            _props = {
                                '_key': _id,
                                '_from': _source,
                                '_to': _target,
                                'biological_context': model_props['biological_context'],
                                'model_id': gene_model_id,
                                'model_type': model_props['model_type'],
                                'cancer_term': 'ontology_terms/' + resolved_cancer_term,
                                'gene_dependency': float(value),
                                'source': DepMap.SOURCE,
                                'source_url': DepMap.SOURCE_URL,
                                'source_file': DepMap.SOURCE_FILE,
                                'name': 'essential in',
                                'inverse_name': 'dependent on',
                                'class': self.collection_class,
                                'method': self.method,
                                'label': self.method,
                                'files_filesets': 'files_filesets/' + self.file_accession,
                            }
                            if self.validate:
                                self.validate_doc(_props)
                            self.writer.write(json.dumps(_props))
                            self.writer.write('\n')

        self.ontology_term_validator.log()

    def load_cell_ontology_id_mapping(self):
        # key: DepMap Model ID; value: ontology ids (i.e. CVCL ids) and properties of each cell
        # need to take care of comma inside double quotes, e.g. ACH-000082,PT-noCCE4,"G-292, clone A141B1",...
        self.cell_ontology_id_mapping = defaultdict(dict)
        with open(self.reference_filepath, 'r') as cell_ontology_id_mapping_file:
            cell_ontology_csv = csv.reader(cell_ontology_id_mapping_file)
            header = next(cell_ontology_csv)
            header_index = {name: i for i, name in enumerate(header)}
            column_index_mapping = {
                prop: header_index[header_name]
                for prop, header_name in self.MODEL_COLUMN_HEADERS.items()
            }
            for cell_ontology_row in cell_ontology_csv:
                model_id = cell_ontology_row[header_index['ModelID']]
                for prop, column_index in column_index_mapping.items():
                    self.cell_ontology_id_mapping[model_id][prop] = cell_ontology_row[column_index]

    @staticmethod
    def _parse_gene_label(gene_label):
        """Return (symbol, ENTREZ:id or None) from a DepMap gene column.

        Example: ``CFAP90 (134121)`` -> ``('CFAP90', 'ENTREZ:134121')``.
        """
        symbol = gene_label.split(' ', 1)[0]
        entrez_id = None
        if gene_label.endswith(')') and '(' in gene_label:
            entrez_number = gene_label[gene_label.rfind('(') + 1:-1]
            if entrez_number.isdigit() and entrez_number != '0':
                entrez_id = 'ENTREZ:' + entrez_number
        return symbol, entrez_id

    def _gene_labels_in_file(self):
        """Return unique (symbol, ENTREZ:id or None) pairs from the gene column."""
        gene_labels = set()
        with open(self.filepath, 'r') as depmap_file:
            next(depmap_file)  # skip header row of model ids
            for line in depmap_file:
                gene_label = line.split(',', 1)[0]
                gene_labels.add(self._parse_gene_label(gene_label))
        return gene_labels

    def load_gene_id_mapping(self):
        # One map. Entrez keys are ENTREZ:{id}; name and synonym keys are symbols.
        # The gene column is read once. Name, then synonym, run only for symbols
        # whose Entrez id was not in the previous map.
        gene_labels = self._gene_labels_in_file()
        self.gene_id_mapping = get_gene_map_from_arangodb('entrez')

        unmatched_symbols = {
            symbol for symbol, entrez_id in gene_labels
            if not entrez_id or entrez_id not in self.gene_id_mapping
        }
        if unmatched_symbols:
            name_map = get_gene_map_from_arangodb('name')
            still_unmatched = set()
            for symbol in unmatched_symbols:
                gene_keys = name_map.get(symbol)
                if gene_keys:
                    self.gene_id_mapping[symbol] = gene_keys
                else:
                    still_unmatched.add(symbol)
            unmatched_symbols = still_unmatched

        if unmatched_symbols:
            synonym_map = get_gene_map_from_arangodb('synonyms')
            for symbol in unmatched_symbols:
                gene_keys = synonym_map.get(symbol)
                if gene_keys:
                    self.gene_id_mapping[symbol] = gene_keys

    def _gene_ids_for_label(self, gene_label):
        symbol, entrez_id = self._parse_gene_label(gene_label)
        if entrez_id and entrez_id in self.gene_id_mapping:
            return self.gene_id_mapping[entrez_id]
        return self.gene_id_mapping.get(symbol)
