import gzip
import json
import hashlib
import pickle
from typing import Optional

from Bio.UniProt.GOA import gafiterator

from adapters.writer import Writer

# GAF files are defined here: https://geneontology.github.io/docs/go-annotation-file-gaf-format-2.2/
#
# Example:
# !gaf-version: 2.2
# !
# !generated-by: GOC
# !
# !date-generated: 2023-04-02T12:17
# !
# ...
# !
# !=================================
# !
# !Documentation about this header can be found here: https://github.com/geneontology/go-site/blob/master/docs/gaf_validation.md
# !
# UniProtKB	A0A024RBG1	NUDT4B	enables	GO:0003723	GO_REF:0000043	IEA	UniProtKB-KW:KW-0694	F	Diphosphoinositol polyphosphate phosphohydrolase NUDT4B	NUDT4B	protein	taxon:9606	20230306	UniProt
# UniProtKB	A0A024RBG1	NUDT4B	enables	GO:0046872	GO_REF:0000043	IEA	UniProtKB-KW:KW-0479	F	Diphosphoinositol polyphosphate phosphohydrolase NUDT4B	NUDT4B	protein	taxon:9606	20230306	UniProt
# UniProtKB	A0A024RBG1	NUDT4B	located_in	GO:0005829	GO_REF:0000052	IDA		C	Diphosphoinositol polyphosphate phosphohydrolase NUDT4B	NUDT4B	protein	taxon:9606	20161204	HPA
# UniProtKB	A0A075B6H7	IGKV3-7	involved_in	GO:0002250	GO_REF:0000043	IEA	UniProtKB-KW:KW-1064	P	Probable non-functional immunoglobulin kappa variable 3-7	IGKV3-7	protein	taxon:9606	20230306	UniProt
# UniProtKB	A0A075B6H7	IGKV3-7	located_in	GO:0005886	GO_REF:0000044	IEA	UniProtKB-SubCell:SL-0039	C	Probable non-functional immunoglobulin kappa variable 3-7	IGKV3-7	protein	taxon:9606	20230306	UniProt


# RNA Central file example:
#
# URS0000000055	ENSEMBL_GENCODE	ENST00000585414	9606	lncRNA	ENSG00000226803.9
# URS00000000C9	ENSEMBL_GENCODE	ENST00000514011	9606	lncRNA	ENSG00000248309.9
# URS00000000FD	ENSEMBL_GENCODE	ENST00000448543	9606	lncRNA	ENSG00000234279.2
# URS0000000351	ENSEMBL_GENCODE	ENST00000452009	9606	lncRNA	ENSG00000235427.1
# URS00000005D1	ENSEMBL_GENCODE	ENST00000563639	9606	lncRNA	ENSG00000260457.2
# URS0000000787	ENSEMBL_GENCODE	ENST00000452952	9606	lncRNA	ENSG00000206142.9
# URS0000000AA1	ENSEMBL_GENCODE	ENST00000615750	9606	lncRNA	ENSG00000277089.4
# URS0000000C0D	ENSEMBL_GENCODE	ENST00000582841	9606	lncRNA	ENSG00000265443.1
# URS0000000CF3	ENSEMBL_GENCODE	ENST00000414886	9606	lncRNA	ENSG00000226856.9

class GAF:
    DATASET = 'gaf'

    # source: https://ftp.ebi.ac.uk/pub/databases/RNAcentral/current_release/id_mapping/database_mappings/ensembl_gencode.tsv
    RNACENTRAL_ID_MAPPING_PATH = './samples/rnacentral_ensembl_gencode.tsv.gz'

    # generated from current proteins collection in the Catalog
    MOUSE_MGI_TO_UNIPROT_PATH = './data_loading_support_files/mgi_to_ensembl.pkl'
    SOURCES = {
        'human': 'http://geneontology.org/gene-associations/goa_human.gaf.gz',
        'human_isoform': 'http://geneontology.org/gene-associations/goa_human_isoform.gaf.gz',
        'mouse': 'https://current.geneontology.org/annotations/mgi.gaf.gz',
        'rna': 'http://geneontology.org/gene-associations/goa_human_rna.gaf.gz'
    }

    def __init__(self, filepath, gaf_type='human', dry_run=True, writer: Optional[Writer] = None, **kwargs):
        if gaf_type not in GAF.SOURCES.keys():
            raise ValueError('Invalid type. Allowed values: ' +
                             ', '.join(GAF.SOURCES.keys()))

        self.filepath = filepath
        self.dataset = GAF.DATASET
        self.label = GAF.DATASET
        self.dry_run = dry_run
        self.type = gaf_type
        self.writer = writer

    def load_rnacentral_mapping(self):
        self.rnacentral_mapping = {}
        with gzip.open(GAF.RNACENTRAL_ID_MAPPING_PATH, 'rt') as mapping_file:
            for annotation in mapping_file:
                mapping = annotation.split('\t')
                self.rnacentral_mapping[mapping[0] +
                                        '_' + mapping[3]] = mapping[2]

    def load_mouse_mgi_to_uniprot(self):
        self.mouse_mgi_mapping = pickle.load(
            open(GAF.MOUSE_MGI_TO_UNIPROT_PATH, 'rb'))

    def process_file(self):
        self.writer.open()

        if self.type == 'rna':
            self.load_rnacentral_mapping()

        self.organism = 'Homo sapiens'
        if self.type == 'mouse':
            self.organism = 'Mus musculus'
            self.load_mouse_mgi_to_uniprot()

        with gzip.open(self.filepath, 'rt') as input_file:
            for annotation in gafiterator(input_file):
                _from = 'ontology_terms/' + \
                    annotation['GO_ID'].replace(':', '_')
                _to = 'proteins/' + annotation['DB_Object_ID']

                if self.type == 'mouse':
                    protein_id = self.mouse_mgi_mapping.get(
                        annotation['DB_Object_ID'])
                    if protein_id is None:
                        continue
                    _to = 'proteins/' + protein_id.replace('UniProtKB:', '')

                if self.type == 'rna':
                    transcript_id = self.rnacentral_mapping.get(
                        annotation['DB_Object_ID'])
                    if transcript_id is None:
                        continue
                    _to = 'transcripts/' + transcript_id

                props = {
                    '_key': hashlib.sha256(str(annotation).encode()).hexdigest(),
                    '_from': _from,
                    '_to': _to,

                    'db': annotation['DB'],
                    'gene_product_id': annotation['DB_Object_ID'],
                    'gene_product_symbol': annotation['DB_Object_Symbol'],
                    'gene_product_name': annotation['DB_Object_Name'],
                    'gene_product_type': annotation['DB_Object_Type'],
                    'qualifier': annotation['Qualifier'],
                    'go_id': annotation['GO_ID'],
                    'db_reference': annotation['DB:Reference'],
                    'evidence': annotation['Evidence'],
                    'with': annotation['With'],
                    'aspect': annotation['Aspect'],
                    'synonyms': annotation['Synonym'],
                    'taxon_id': annotation['Taxon_ID'],
                    'date': annotation['Date'],
                    'assigned_by': annotation['Assigned_By'],
                    'annotation_extension': annotation['Annotation_Extension'],
                    'gene_product_form_id': annotation['Gene_Product_Form_ID'],
                    'organism': self.organism,

                    'source': 'Gene Ontology',
                    'source_url': GAF.SOURCES[self.type]
                }

                if props['aspect'] == 'C':
                    props['name'] = 'is located in'
                    props['inverse_name'] = 'contains'
                elif props['aspect'] == 'P':
                    props['name'] = 'involved in'
                    props['inverse_name'] = 'has component'
                elif props['aspect'] == 'F':
                    props['name'] = 'has the function'
                    props['inverse_name'] = 'is a function of'

                self.writer.write(json.dumps(props))
                self.writer.write('\n')

        self.writer.close()
