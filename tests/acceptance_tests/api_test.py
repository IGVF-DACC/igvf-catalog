# execute with: $ pytest
# check catalog_api_response_times.txt file for report on response times

import requests
import logging
import http.client as http_client
from datetime import datetime
import pytest

from regulatory_regions import regulatory_regions
from genes import genes
from transcripts import transcripts
from proteins import proteins
from gene_transcripts import genes_transcripts
from transcripts_genes import transcripts_genes
from genes_proteins import genes_proteins
from proteins_genes import proteins_genes
from transcripts_proteins import transcripts_proteins
from proteins_transcripts import proteins_transcripts
from genes_genes import genes_genes
from variants import variants
from eqtls import eqtls
from sqtls import sqtls
from variants_genes import variants_genes
from genes_variants import genes_variants
from phenotypes_variants import phenotypes_variants
from variants_phenotypes import variants_phenotypes
from variants_ld import variants_ld
from motifs import motifs
from diseases_genes import diseases_genes
from genes_diseases import genes_diseases
from ontology_terms import ontology_terms
from complexes import complexes
from complexes_proteins import complexes_proteins
from proteins_complexes import proteins_complexes
from regulatory_regions_genes import regulatory_regions_genes
from genes_regulatory_regions import genes_regulatory_regions

API = 'https://api.catalog.igvf.org/api'

http_client.HTTPConnection.debuglevel = 1

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

requests_log = logging.getLogger('requests.packages.urllib3')
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

requests_report = logging.getLogger('response_times')
requests_report.setLevel(logging.INFO)
requests_report.propagate = True


TESTS = {
    **regulatory_regions,
    **genes,
    **transcripts,
    **proteins,
    **genes_transcripts,
    **transcripts_genes,
    **genes_proteins,
    **proteins_genes,
    **transcripts_proteins,
    **proteins_transcripts,
    **genes_genes,
    **variants,
    **eqtls,
    **sqtls,
    **variants_genes,
    **genes_variants,
    **phenotypes_variants,
    **variants_phenotypes,
    **variants_ld,
    **motifs,
    **diseases_genes,
    **genes_diseases,
    **ontology_terms,
    **complexes,
    **complexes_proteins,
    **proteins_complexes,
    **regulatory_regions_genes,
    **genes_regulatory_regions
}


@pytest.mark.parametrize('endpoint', TESTS.keys())
class TestAPI(object):
    response_times = {}

    def teardown_class(self):
        with open('catalog_api_response_times.txt', 'w') as output:
            output.write(API + '\n')
            output.write(datetime.now().strftime('%d/%m/%Y %H:%M:%S') + '\n')
            for key in TestAPI.response_times.keys():
                output.write(
                    key + '\t' + str(TestAPI.response_times[key]) + 's\n')

    def test_endpoints(self, endpoint):
        url = API + endpoint

        for test in TESTS[endpoint]:
            if test.get('params_url'):
                url = API + endpoint.format(**test['params_url'])

            response = requests.get(url, params=test.get('params'))

            assert response.status_code == 200
            print(response.json())
            assert response.json() == test['response']
            TestAPI.response_times[response.url] = response.elapsed.total_seconds(
            )
