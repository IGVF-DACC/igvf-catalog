import csv
import json
import hashlib
from typing import Optional
import os

import obonet
from adapters.base import BaseAdapter
from adapters.writer import Writer
from adapters.helpers import (
    get_file_fileset_by_accession_in_arangodb,
    get_protein_map_from_arangodb,
)

# Example lines in merged_PPI.UniProt.csv (and merged_PPI_mouse.UniProt.csv for mouse):
# Protein ID 1,Protein ID 2,PMID,Detection Method,Detection Method (PSI-MI),Interaction Type,Interaction Type (PSI-MI),Confidence Value (biogrid),Confidence Value (intact),Source
# P0CL82,P36888,[28625976],genetic interference,MI:0254,sensu biogrid,MI:2371,,,BioGRID
# Q9Y243,Q9Y6H6,[33961781],affinity chromatography technology,MI:0004,physical association,MI:0915,0.990648979,,BioGRID


class ProteinsInteraction(BaseAdapter):
    INTERACTION_MI_CODE_PATH = './data_loading_support_files/Biogrid_gene_gene/psi-mi.obo'
    ALLOWED_LABELS = ['protein_protein_human', 'protein_protein_mouse']

    def __init__(self, filepath, label='protein_protein_human', writer: Optional[Writer] = None, validate=False, **kwargs):
        self.file_accession = os.path.basename(filepath).split('.')[0]
        self.source_url = 'https://data.igvf.org/reference-files/' + self.file_accession
        if label == 'protein_protein_mouse':
            self.organism = 'Mus musculus'
        else:
            self.organism = 'Homo sapiens'
        super().__init__(filepath, label, writer, validate)

    def _get_schema_type(self):
        """Return schema type."""
        return 'edges'

    def _get_collection_name(self):
        """Get collection name."""
        return 'proteins_proteins'

    def load_MI_code_mapping(self):
        # get mapping for MI code -> name from obo file (e.g. MI:2370 -> synthetic lethality (sensu BioGRID))
        self.MI_code_mapping = {}
        graph = obonet.read_obo(self.INTERACTION_MI_CODE_PATH)
        for node in graph.nodes():
            self.MI_code_mapping[node] = graph.nodes[node]['name']

    def parse(self):
        self.file_fileset = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        self.collection_class = self.file_fileset['class']
        self.writer.add_tag('portal_accessions', self.file_accession)
        file_set_accession = self.file_fileset.get('file_set_id')
        if file_set_accession:
            self.writer.add_tag('portal_accessions', file_set_accession)
        self.logger.info('Loading MI code mappings')
        self.load_MI_code_mapping()
        self.ensembls = get_protein_map_from_arangodb(organism=self.organism)
        ensembl_unmatched = 0

        with open(self.filepath, 'r') as interaction_file:
            interaction_csv = csv.reader(interaction_file)
            next(interaction_csv)
            for row in interaction_csv:
                # skip detection method = 'genetic interference', they need to be in genes_genes
                if row[3] == 'genetic interference':
                    continue

                protein_from = row[0]
                protein_to = row[1]

                ensembl_ids_from = self.ensembls.get(
                    protein_from) or self.ensembls.get(protein_from.split('-')[0])
                ensembl_ids_to = self.ensembls.get(
                    protein_to) or self.ensembls.get(protein_to.split('-')[0])

                if ensembl_ids_from is None or ensembl_ids_to is None:
                    ensembl_unmatched += 1
                    continue

                for protein_from_ensembl in ensembl_ids_from:
                    for protein_to_ensembl in ensembl_ids_to:
                        pmid_url = 'http://pubmed.ncbi.nlm.nih.gov/'
                        pmids = [pmid.replace("'", '') for pmid in row[2].replace(
                            '[', '').replace(']', '').split(', ')]

                        # load each combination of protein pairs + detection method + pmids as individual edges
                        # some pairs have a long list of pmids
                        _key = hashlib.sha256('_'.join(
                            [protein_from_ensembl, protein_to_ensembl, row[4].replace(':', '_')] + pmids).encode()).hexdigest()
                        interaction_type_code = row[6].split('; ')
                        interaction_type = sorted([self.MI_code_mapping.get(
                            code) for code in interaction_type_code])
                        # collection method should be a string of interaction type separated by ', '
                        collection_method = ', '.join(interaction_type)
                        detection_method = self.MI_code_mapping.get(row[4])
                        source = row[-1]
                        if source == 'IntAct; BioGRID':
                            source = 'BioGRID; IntAct'

                        props = {
                            '_key': _key,
                            '_from': 'proteins/' + protein_from_ensembl,
                            '_to': 'proteins/' + protein_to_ensembl,
                            'detection_method': detection_method,
                            'detection_method_code': row[4],
                            'interaction_type': interaction_type,
                            'interaction_type_code': interaction_type_code,
                            'confidence_value_biogrid': float(row[7]) if row[7] else None,
                            'confidence_value_intact': float(row[-2]) if row[-2] else None,
                            'source': source,
                            'pmids': [pmid_url + pmid for pmid in pmids],
                            'organism': self.organism,
                            'name': 'physically interacts with',
                            'inverse_name': 'physically interacts with',
                            'molecular_function': 'ontology_terms/GO_0005515',
                            'method': collection_method,
                            'label': detection_method,
                            'class': self.collection_class,
                            'source_url': self.source_url,
                            'files_filesets': 'files_filesets/' + self.file_accession
                        }
                        if self.validate:
                            self.validate_doc(props)
                        self.writer.write(json.dumps(props))
                        self.writer.write('\n')

        if ensembl_unmatched != 0:
            self.logger.warning(
                f'{ensembl_unmatched} unmatched uniprot -> ensembl ids')
