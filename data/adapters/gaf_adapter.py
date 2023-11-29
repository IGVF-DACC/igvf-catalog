import os
import gzip
import json
import hashlib

from Bio.UniProt.GOA import gafiterator

from adapters import Adapter
from db.arango_db import ArangoDB

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

class GAF(Adapter):
    SKIP_BIOCYPHER = True
    DATASET = 'gaf'
    OUTPUT_PATH = './parsed-data'
    RNACENTRAL_ID_MAPPING_PATH = './samples/rnacentral_ensembl_gencode.tsv.gz'
    SOURCES = {
        'human': 'http://geneontology.org/gene-associations/goa_human.gaf.gz',
        'human_isoform': 'http://geneontology.org/gene-associations/goa_human_isoform.gaf.gz',
        'rna': 'http://geneontology.org/gene-associations/goa_human_rna.gaf.gz',
        'rnacentral': 'https://ftp.ebi.ac.uk/pub/databases/RNAcentral/current_release/id_mapping/database_mappings/ensembl_gencode.tsv'
    }

    def __init__(self, filepath, gaf_type='human', dry_run=True):
        if gaf_type not in GAF.SOURCES.keys():
            raise ValueError('Ivalid type. Allowed values: ' +
                             ', '.join(GAF.SOURCES.keys()))

        self.filepath = filepath
        self.dataset = GAF.DATASET
        self.dry_run = dry_run
        self.type = gaf_type
        self.output_filepath = '{}/{}-{}.json'.format(
            GAF.OUTPUT_PATH,
            self.dataset,
            filepath.split('/')[-1]
        )

        super(GAF, self).__init__()

    def load_rnacentral_mapping(self):
        self.rnacentral_mapping = {}
        with gzip.open(GAF.RNACENTRAL_ID_MAPPING_PATH, 'rt') as mapping_file:
            for annotation in mapping_file:
                mapping = annotation.split('\t')
                self.rnacentral_mapping[mapping[0] +
                                        '_' + mapping[3]] = mapping[2]

    def process_file(self):
        parsed_data_file = open(self.output_filepath, 'w')

        if self.type == 'rna':
            self.load_rnacentral_mapping()

        with gzip.open(self.filepath, 'rt') as input_file:
            for annotation in gafiterator(input_file):
                _from = 'ontology_terms/' + \
                    annotation['GO_ID'].replace(':', '_')
                _to = 'proteins/' + annotation['DB_Object_ID']

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
                    'db_object_id': annotation['DB_Object_ID'],
                    'db_object_symbol': annotation['DB_Object_Symbol'],
                    'qualifier': annotation['Qualifier'],
                    'go_id': annotation['GO_ID'],
                    'db_reference': annotation['DB:Reference'],
                    'evidence': annotation['Evidence'],
                    'with': annotation['With'],
                    'aspect': annotation['Aspect'],
                    'db_object_name': annotation['DB_Object_Name'],
                    'synonyms': annotation['Synonym'],
                    'db_object_type': annotation['DB_Object_Type'],
                    'taxon_id': annotation['Taxon_ID'],
                    'date': annotation['Date'],
                    'assigned_by': annotation['Assigned_By'],
                    'annotation_extension': annotation['Annotation_Extension'],
                    'gene_product_form_id': annotation['Gene_Product_Form_ID'],

                    'source': 'Gene Ontology',
                    'source_url': GAF.SOURCES[self.type]
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
        return ArangoDB().generate_json_import_statement(self.output_filepath, 'go_terms_genes', type='edges')
