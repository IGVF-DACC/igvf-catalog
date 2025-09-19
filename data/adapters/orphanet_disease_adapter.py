import xml.etree.ElementTree as ET
import json
from typing import Optional
from jsonschema import Draft202012Validator, ValidationError
from schemas.registry import get_schema

from adapters.writer import Writer
from adapters.gene_validator import GeneValidator

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


class Disease:
    SOURCE = 'Orphanet'
    SOURCE_URL = 'https://www.orphadata.com/genes/'

    def __init__(self, filepath, dry_run=True, writer: Optional[Writer] = None, validate=False, **kwargs):
        self.filepath = filepath
        self.dataset = 'disease_gene'
        self.label = 'disease_gene'
        self.collection = 'diseases_genes'
        self.type = 'edge'
        self.dry_run = dry_run
        self.writer = writer
        self.gene_validator = GeneValidator()
        self.validate = validate
        if self.validate:
            self.schema = get_schema(
                'edges', 'diseases_genes', self.__class__.__name__)
            self.validator = Draft202012Validator(self.schema)

    def validate_doc(self, doc):
        try:
            self.validator.validate(doc)
        except ValidationError as e:
            raise ValueError(f'Document validation failed: {e.message}')

    def process_file(self):
        self.writer.open()

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
                is_valid_gene_id = self.gene_validator.validate(gene_id)
                if not is_valid_gene_id:
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
                    'name': 'associated_with',
                    'inverse_name': 'associated_with',
                    'pmid': pmids,
                    'term_name': term_name,
                    'gene_symbol': gene_symbol,
                    'association_type': assoc_type_name,
                    'association_status': assoc_status_name,
                    'source': Disease.SOURCE,
                    'source_url': Disease.SOURCE_URL
                }

                if self.validate:
                    self.validate_doc(props)

                self.writer.write(json.dumps(props))
                self.writer.write('\n')

        self.writer.close()
        self.gene_validator.log()
