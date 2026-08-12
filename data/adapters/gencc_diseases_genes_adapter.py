import json
import csv
import os
from typing import Optional
from adapters.base import BaseAdapter
from adapters.writer import Writer
from adapters.helpers import get_gene_map_from_arangodb, get_file_fileset_by_accession_in_arangodb


class GenccDiseasesGenes(BaseAdapter):
    ALLOWED_LABELS = ['disease_gene']
    SOURCE = 'GenCC'
    SOURCE_URL = 'https://thegencc.org/'

    def __init__(self, filepath, label='disease_gene', writer: Optional[Writer] = None, validate=False, **kwargs):
        super().__init__(filepath, label, writer, validate)
        self.file_accession = os.path.basename(filepath).split('.')[0]

    def _get_schema_type(self):
        return 'edges'

    def _get_collection_name(self):
        return 'diseases_genes'

    def parse(self):
        self.writer.add_tag('portal_accessions', self.file_accession)
        file_metadata = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        self.collection_class = file_metadata['class']
        self.method = file_metadata['method']
        self.gene_map = get_gene_map_from_arangodb('hgnc')
        # read the tsv file
        with open(self.filepath, 'r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f, delimiter='\t')
            next(reader)
            for row in reader:
                _key = row[0]
                sgc_id = f'{row[0]}.{row[1]}'
                hgnc_id = row[2]
                gene_ids = self.gene_map.get(hgnc_id)
                if gene_ids is None:
                    print(f'No gene id found for {hgnc_id}')
                    continue
                gene_symbol = row[3]
                # need to replace ":" with "_" in the ontology_term_id
                ontology_term_id = row[4].replace(':', '_')
                _from = f'ontology_terms/{ontology_term_id}'
                term_name = row[5]
                classification = row[9]
                moi_id = row[10]
                moi_name = row[11]
                submitter = row[13]
                pmids = []
                if row[27]:
                    pmids = [pmid.strip()
                             for pmid in row[27].split(',') if pmid.strip()]

                for gene_id in gene_ids:
                    _to = f'genes/{gene_id}'
                    props = {
                        '_key': f'{_key}_{gene_id}',
                        '_from': _from,
                        '_to': _to,
                        'sgc_id': sgc_id,
                        'name': 'associated_with',
                        'inverse_name': 'associated_with',
                        'hgnc': hgnc_id,
                        'gene_symbol': gene_symbol,
                        'term_name': term_name,
                        'classification': classification,
                        'moi_id': moi_id,
                        'moi_name': moi_name,
                        'submitter': submitter,
                        'pmids': pmids,
                        'source': self.SOURCE,
                        'source_url': f'https://thegencc.org/submissions/{sgc_id}',
                        'class': self.collection_class,
                        'method': self.method,
                        'label': self.method,
                        'files_filesets': 'files_filesets/' + self.file_accession,
                    }
                    if self.validate:
                        self.validate_doc(props)
                    self.writer.write(json.dumps(props, ensure_ascii=False))
                    self.writer.write('\n')
