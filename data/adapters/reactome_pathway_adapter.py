import json
import os
import time
from typing import Optional

import requests
from requests.adapters import HTTPAdapter, Retry
from requests.exceptions import RequestException
from json import JSONDecodeError

from adapters.base import BaseAdapter
from adapters.helpers import get_file_fileset_by_accession_in_arangodb
from adapters.writer import Writer

# This adapter is used to parse Reactome pathway data.
# the input file is last modified on 2026-06-19 and is available at: https://reactome.org/download/current/ReactomePathways.txt
# Example pathway input file:
# R-GGA-199992	trans-Golgi Network Vesicle Budding	Gallus gallus
# R-HSA-164843	2-LTR circle formation	Homo sapiens
# R-HSA-73843	5-Phosphoribose 1-diphosphate biosynthesis	Homo sapiens
# R-HSA-1971475	A tetrasaccharide linker sequence is required for GAG synthesis	Homo sapiens
# R-HSA-5619084	ABC transporter disorders	Homo sapiens


class ReactomePathway(BaseAdapter):

    ALLOWED_LABELS = ['pathway']
    # urllib3 retries on these statuses (includes Cloudflare edge errors)
    HTTP_RETRY_STATUSES = (408, 429, 500, 502, 503,
                           504, 520, 521, 522, 523, 524)
    # Application-level retries for empty/HTML bodies and transient failures
    QUERY_MAX_ATTEMPTS = 5
    QUERY_BACKOFF_SECONDS = 2
    QUERY_TIMEOUT_SECONDS = 30

    def __init__(self, filepath=None, label='pathway', writer: Optional[Writer] = None, validate=False, **kwargs):
        super().__init__(filepath, label, writer, validate)
        self.file_accession = os.path.basename(filepath).split('.')[0]

    def _get_schema_type(self):
        """Return schema type."""
        return 'nodes'

    def _get_collection_name(self):
        """Get collection name."""
        return 'pathways'

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        retries = Retry(
            total=5,
            connect=5,
            read=5,
            backoff_factor=1,
            status_forcelist=self.HTTP_RETRY_STATUSES,
            allowed_methods=frozenset(['GET']),
            raise_on_status=False,
        )
        session.mount('https://', HTTPAdapter(max_retries=retries))
        session.mount('http://', HTTPAdapter(max_retries=retries))
        return session

    def _query_pathway(self, session: requests.Session, pathway_id: str) -> Optional[dict]:
        """Query Reactome ContentService for a pathway, with retries.

        Returns None for HTTP 404 (missing pathway). Raises after exhausting retries.
        """
        query = 'https://reactome.org/ContentService/data/query/' + pathway_id
        last_error: Optional[Exception] = None

        for attempt in range(1, self.QUERY_MAX_ATTEMPTS + 1):
            try:
                response = session.get(
                    query, timeout=self.QUERY_TIMEOUT_SECONDS)
                if response.status_code == 404:
                    self.logger.warning(
                        f'Fail to find pathway {pathway_id}. The source file may be outdated')
                    return None
                if response.status_code != 200:
                    raise RequestException(
                        f'HTTP {response.status_code} for {query}')
                return response.json()
            except (JSONDecodeError, RequestException, requests.Timeout) as e:
                last_error = e
                body_preview = ''
                if 'response' in locals():
                    body_preview = (response.text or '')[:500]
                self.logger.warning(
                    f'Reactome query failed for {pathway_id} '
                    f'(attempt {attempt}/{self.QUERY_MAX_ATTEMPTS}): {e}'
                )
                if attempt < self.QUERY_MAX_ATTEMPTS:
                    time.sleep(self.QUERY_BACKOFF_SECONDS * attempt)
                    continue
                self.logger.error(
                    f'Can not query for {query} after {self.QUERY_MAX_ATTEMPTS} attempts. '
                    f'Body preview={body_preview!r}'
                )
                raise last_error

        raise last_error  # pragma: no cover

    def parse(self):
        self.file_fileset = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        self.collection_class = self.file_fileset['class']
        self.method = self.file_fileset['method']
        self.writer.add_tag('portal_accessions', self.file_accession)
        file_set_accession = self.file_fileset.get('file_set_id')
        if file_set_accession:
            self.writer.add_tag('portal_accessions', file_set_accession)
        session = self._build_session()

        with open(self.filepath) as input:
            for line in input:
                id, name, organism = line.strip().split('\t')
                if organism != 'Homo sapiens':
                    continue

                to_json = {
                    '_key': id,
                    'name': name,
                    'organism': organism,
                    'source': 'Reactome',
                    'source_url': 'https://reactome.org/',
                    'class': self.collection_class,
                    'method': self.method,
                    'label': self.method,
                    'files_filesets': 'files_filesets/' + self.file_accession
                }

                data = self._query_pathway(session, id)
                if data is None:
                    continue

                id_version = data['stIdVersion']
                is_in_disease = data['isInDisease']
                name_aliases = data['name']
                is_top_level_pathway = data['className'] == 'TopLevelPathway'
                to_json.update(
                    {
                        'id_version': id_version,
                        'is_in_disease': is_in_disease,
                        'name_aliases': name_aliases,
                        'is_top_level_pathway': is_top_level_pathway
                    }
                )
                if is_in_disease:
                    disease = data.get('disease')
                    disease_ontology_terms = []
                    for d in disease:
                        disease_ontology_term = 'ontology_terms/' + \
                            d['databaseName'] + '_' + d['identifier']
                        disease_ontology_terms.append(
                            disease_ontology_term)
                    to_json.update(
                        {'disease_ontology_terms': disease_ontology_terms}
                    )
                go_biological_process = data.get('goBiologicalProcess')
                if go_biological_process:
                    to_json.update(
                        {
                            'go_biological_process': 'ontology_terms/' + go_biological_process['databaseName'] + '_' + go_biological_process['accession']
                        }
                    )
                if self.validate:
                    self.validate_doc(to_json)
                self.writer.write(json.dumps(to_json))
                self.writer.write('\n')
