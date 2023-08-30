import xml.etree.ElementTree as ET
import json
import os

from adapters import Adapter
from db.arango_db import ArangoDB

# The xml file was download from https://www.orphadata.com/genes/
# The disease-gene association elements are under each Disorder element in the tree from the xml file
# Example of one disorder element:
# <Disorder id="17601">
#   <OrphaCode>166024</OrphaCode>
#   <ExpertLink lang="en">http://www.orpha.net/consor/cgi-bin/OC_Exp.php?lng=en&amp;Expert=166024</ExpertLink>
#   <Name lang="en">Multiple epiphyseal dysplasia, Al-Gazali type</Name>
#   ... ... ...
#   <DisorderGeneAssociationList count="1">
#     <DisorderGeneAssociation>
#       <SourceOfValidation>22587682[PMID]</SourceOfValidation>
#       <Gene id="20160">
#         <Name lang="en">kinesin family member 7</Name>
#           ... ... ...
#       </Gene>
#       <DisorderGeneAssociationType id="17949">
#         <Name lang="en">Disease-causing germline mutation(s) in</Name>
#       </DisorderGeneAssociationType>
#       <DisorderGeneAssociationStatus id="17991">
#         <Name lang="en">Assessed</Name>
#       </DisorderGeneAssociationStatus>
#     </DisorderGeneAssociation>
#   </DisorderGeneAssociationList>
# </Disorder>


class Disease(Adapter):
    SOURCE = 'Orphanet'
    SOURCE_URL = 'https://www.orphadata.com/genes/'

    OUTPUT_PATH = './parsed-data'
    SKIP_BIOCYPHER = True

    def __init__(self, filepath, dry_run=True):
        self.filepath = filepath
        self.dataset = 'disease_gene'
        self.collection = 'diseases_genes'
        self.type = 'edge'
        self.dry_run = dry_run
        self.output_filepath = '{}/{}.json'.format(
            Disease.OUTPUT_PATH,
            self.dataset
        )

        super(Disease, self).__init__()

    def process_file(self):
        parsed_data_file = open(self.output_filepath, 'w')

        # the xml file is relatively small, just parse at once here
        # or could return an iterator with ET.iterparse(xmlfile)
        disease_gene_tree = ET.parse(self.filepath)
        root = disease_gene_tree.getroot()
        for elem in root.findall('./DisorderList/Disorder'):
            ontology_id = elem.find('OrphaCode').text
            term_name = elem.find('Name').text
            for assoc in elem.findall('./DisorderGeneAssociationList/DisorderGeneAssociation'):
                source = assoc.find('SourceOfValidation').text
                pmids = []
                if source is not None:
                    # can have multiple e.g. 16150725[PMID]_16150725[PMID]_21771795[PMID]
                    pmids = [pmid.replace('[PMID]', '')
                             for pmid in source.split('_')]

                gene = assoc.find('Gene')
                gene_symbol = gene.find('Symbol').text
                gene_id = None
                for exter_ref in gene.findall('./ExternalReferenceList/ExternalReference'):
                    exter_source = exter_ref.find('Source').text
                    if exter_source == 'Ensembl':
                        gene_id = exter_ref.find('Reference').text

                if gene_id is None:  # ignore genes if no mapping to ensembl id
                    continue

                # other DisorderGeneAssociation attributes
                assoc_type = assoc.find('DisorderGeneAssociationType')
                assoc_type_name = assoc_type.find('Name').text

                assoc_status = assoc.find('DisorderGeneAssociationStatus')
                assoc_status_name = assoc_status.find('Name').text

                _key = 'Orphanet_' + ontology_id + '_' + gene_id

                props = {
                    '_key': _key,
                    '_from': 'ontology_terms/Orphanet_' + ontology_id,
                    '_to': 'genes/' + gene_id,

                    'pmid': pmids,
                    'term_name': term_name,
                    'gene_symbol': gene_symbol,
                    'association_type': assoc_type_name,
                    'association_status': assoc_status_name,
                    'source': Disease.SOURCE,
                    'source_url': Disease.SOURCE_URL
                }

                json.dump(props, parsed_data_file)
                parsed_data_file.write('\n')

        parsed_data_file.close()
        self.save_to_arango()

    def save_to_arango(self):
        if self.dry_run:
            print(self.arangodb()[0])
        else:
            os.system(self.arangodb()[0])

    def arangodb(self):
        return ArangoDB().generate_json_import_statement(self.output_filepath, self.collection, type=self.type)
