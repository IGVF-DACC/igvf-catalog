import csv
import os
import json
import pickle

from db.arango_db import ArangoDB
from adapters import Adapter

# The complex tsv file for human was downloaded from EBI complex portal:http://ftp.ebi.ac.uk/pub/databases/intact/complex/current/complextab/9606.tsv
# An example line with header:
# Complex ac	Recommended name	Aliases for complex	Taxonomy identifier	Identifiers (and stoichiometry) of molecules in complex	Evidence Code	Experimental evidence	Go Annotations	Cross references	Description	Complex properties	Complex assembly	Ligand	Disease	Agonist	Antagonist	Comment	Source	Expanded participant list
# CPX-1	SMAD2-SMAD3-SMAD4 complex	SMAD2/SMAD3/SMAD4 transcription factor complex	9606	P84022(1)|Q13485(1)|Q15796(1)	ECO:0005547(biological system reconstruction evidence based on inference from background scientific knowledge used in manual assertion)	-	\
# GO:0071144(heteromeric SMAD protein complex)|GO:0003690(double-stranded DNA binding)|GO:0003700(DNA-binding transcription factor activity)|GO:0006355(regulation of DNA-templated transcription)|GO:0032924(activin receptor signaling pathway)|GO:0007179(transforming growth factor beta receptor signaling pathway)	\
# reactome:R-HSA-9736938(identity)|reactome:R-HSA-9736929(identity)|pubmed:35359452(see-also)|pubmed:16322555(see-also)|complex portal:CPX-1(complex-primary)|wwpdb:1U7V(subset)	\
# A transcription factor complex which binds to the promoters of target genes and recruits co-activators and histone acetyltransferases, such as p300, CBP and P300/CBP-associated factor, \
# facilitating transcription. In response to TGF-beta/activin-family protein binding, TGF-beta type II receptors phosphorylate TGF-beta type I receptors (ALK4, 5 and 7) which in turn phosphorylates SMAD2 on two Ser-465 and Ser-467, and SMAD3 on Ser-423 and Ser-425. \
# This enables binding to SMAD4 to form heteromeric SMAD complexes that enter the nucleus to initiate gene transcription. Because of their relatively low DNA-binding affinity, SMAD complexes interact with a wide variety of DNA-binding proteins. Crosstalk with other signalling pathways and interaction with other DNA-binding cofactors define the specific binding patterns of SMADs; \
# in addition, interaction with coactivators/corepressors modulates their transcriptional activity.	Preferential formation of the regulatory R-Smad/SMAD4 heterotrimer over the R-Smad homotrimer is largely enthalpy driven, contributed by the unique presence of strong electrostatic interactions within the heterotrimeric interfaces. \
# These electrostatic interactions exist only in the heterotrimer due to specific charged residues in the SMAD4 subunit, Asp-493 and Arg-378, mediating complementary electrostatic interactions with the neighbouring R-Smad subunits.	\
# Heterotrimer	-	-	-	-	-	psi-mi:"MI:0469"(IntAct)	P84022(1)|Q13485(1)|Q15796(1)


class EBIComplex(Adapter):
    ALLOWED_LABELS = ['complex', 'complex_protein',
                      'complex_term', 'complex_complex']
    SOURCE = 'EBI'
    SOURCE_URL = 'https://www.ebi.ac.uk/complexportal/'

    # cross-references to ontology terms we want to load
    XREF_SOURCES = ['efo', 'intact', 'mondo', 'orphanet', 'pubmed']
    # removed biorxiv, -> only one case, and difficult to convert to key id

    # path to pre-calculated dict containing binding regions pulled from api
    LINKED_FEATURE_PATH = './data_loading_support_files/EBI_complex/EBI_complex_linkedFeatures.pkl'

    SKIP_BIOCYPHER = True
    OUTPUT_PATH = './parsed-data'

    def __init__(self, filepath, label='complex', dry_run=True):
        if label not in EBIComplex.ALLOWED_LABELS:
            raise ValueError('Ivalid labelS. Allowed values: ' +
                             ','.join(EBIComplex.ALLOWED_LABELS))

        self.filepath = filepath
        self.label = label
        self.dataset = label
        self.dry_run = dry_run
        if label == 'complex':
            self.type = 'node'
        else:
            self.type = 'edge'

        self.output_filepath = '{}/{}_{}.json'.format(
            EBIComplex.OUTPUT_PATH,
            self.dataset,
            EBIComplex.SOURCE
        )

        super(EBIComplex, self).__init__()

    def process_file(self):
        self.parsed_data_file = open(self.output_filepath, 'w')

        with open(self.filepath, 'r') as complex_file:
            complex_tsv = csv.reader(complex_file, delimiter='\t')
            next(complex_tsv)
            for complex_row in complex_tsv:
                skip_flag = None
                complex_ac = complex_row[0]

                molecules = complex_row[4].split('|')
                for molecule in molecules:
                    if molecule.startswith('CHEBI:') or molecule.startswith('URS'):
                        skip_flag = 1

                # skip lines containing chemicals from CHEBI or RNAs from RNACentral
                # i.e. only load complexes where all participants have uniprot protein ids
                if skip_flag is not None:
                    continue

                go_terms = complex_row[7].split('|')
                xrefs = complex_row[8].split('|')

                if self.label == 'complex':
                    # each molecule/participant in column 5th is mostly a single protein_uniprot_id (stoichiometry), e.g. O60506(0)
                    # but sometimes more complicated:
                    # 1) a molecule set for paralogs grouped in an array, e.g. [O15342,Q8NHE4](1)
                    # 2) have extra str after the uniprot ids, e.g. O60506-1(0) ('-1' for specifying the isoform);
                    # O60895-PRO_0000030172 ('-PRO_0000030172' is the chain id)
                    # 3) another complex accession id, e.g. CPX-973(1).

                    # just load the original str for each molecule in complexes collection

                    alias = [] if complex_row[2] == '-' else complex_row[2].split(
                        '|')
                    experimental_evidence = None if complex_row[6] == '-' else complex_row[6]
                    complex_assembly = [] if complex_row[11] == '-' else complex_row[11]
                    reactome_xref = []
                    for xref in xrefs:
                        if xref.startswith('reactome'):
                            reactome_xref.append(xref.replace('reactome:', ''))

                    props = {
                        '_key': complex_ac,
                        'complex_name': complex_row[1],
                        'alias': alias,
                        'molecules': molecules,
                        'evidence_code': complex_row[5],
                        'experimental_evidence': experimental_evidence,
                        'description': complex_row[9],
                        'complex_assembly': complex_assembly,
                        'complex_source': complex_row[17],
                        'reactome_xref': reactome_xref,
                        'source': EBIComplex.SOURCE,
                        'source_url': EBIComplex.SOURCE_URL
                    }

                    self.save_props(props)

                elif self.label == 'complex_protein':
                    # pre-calculated dict containing binding regions pulled from api
                    self.load_linked_features_dict()
                    # the last column only conteins uniprot ids, and expanded for participant in column 5th if it's a complex
                    for protein_str in complex_row[-1].split('|'):
                        proteins = []
                        stoichiometry = int(
                            protein_str.split('(')[1].replace(')', ''))
                        number_of_paralogs = None
                        paralogs = None
                        # molecule set e.g. [Q96A05,P36543](3)
                        if protein_str.startswith('['):
                            paralogs = protein_str.split(']')[
                                0].replace('[', '').split(',')
                            number_of_paralogs = len(paralogs)
                            proteins.extend(paralogs)
                        else:  # single protein e.g. O60506(0)
                            proteins.append(protein_str.split('(')[0])

                        for protein_id in proteins:
                            _key = complex_ac + '_' + protein_id
                            _from = 'complexes/' + complex_ac
                            _to = 'proteins/' + protein_id

                            try:
                                linked_features = self.linked_features_dict[complex_ac][protein_id]
                            except KeyError:
                                #print (complex_ac, protein_id)
                                linked_features = []

                            props = {
                                '_key': _key,
                                '_from': _from,
                                '_to': _to,
                                'stoichiometry': stoichiometry,
                                'chain_id': self.get_chain_id(protein_id),
                                'isoform_id': self.get_isoform_id(protein_id),
                                'number_of_paralogs': number_of_paralogs,
                                'paralogs': paralogs,
                                'linked_features': linked_features,
                                'source': EBIComplex.SOURCE,
                                'source_url': EBIComplex.SOURCE_URL
                            }
                            self.save_props(props)

                elif self.label == 'complex_term':  # parse cross-references & go annotations
                    for go_term in go_terms:
                        go_term_id = go_term.split('(')[0].replace(':', '_')
                        go_term_name = go_term.split('(')[1].replace(')', '')

                        _key = complex_ac + '_' + go_term_id
                        _from = 'complexes/' + complex_ac
                        _to = 'ontology_terms/' + go_term_id
                        props = {
                            '_key': _key,
                            '_from': _from,
                            '_to': _to,
                            'term_name': go_term_name,
                            'source': EBIComplex.SOURCE,
                            'source_url': EBIComplex.SOURCE_URL
                        }
                        self.save_props(props)

                    for xref in xrefs:
                        for source in EBIComplex.XREF_SOURCES:
                            if xref.startswith(source):
                                if xref.startswith('pubmed'):
                                    xref_term_id = xref.split(
                                        '(')[0].replace(':', '_')
                                else:
                                    xref_term_id = xref.split('(')[0].replace(
                                        source + ':', '').replace(':', '_')

                                _key = complex_ac + '_' + xref_term_id
                                _from = 'complexes/' + complex_ac
                                _to = 'ontology_terms/' + xref_term_id
                                props = {
                                    '_key': _key,
                                    '_from': _from,
                                    '_to': _to,
                                    'source': EBIComplex.SOURCE,
                                    'source_url': EBIComplex.SOURCE_URL
                                }
                                self.save_props(props)

                elif self.label == 'complex_complex':
                    for xref in xrefs:
                        if xref.startswith('complex portal'):
                            if 'complex-primary' not in xref:  # ignore complex-complex between itself
                                xref_term_id = xref.split(
                                    '(')[0].replace('complex portal:', '')
                                # inferred-from / secondary-ac
                                relationship = xref.split(
                                    '(')[1].replace(')', '')

                                _key = complex_ac + '_' + xref_term_id
                                _from = 'complexes/' + complex_ac
                                _to = 'complexes/' + xref_term_id
                                props = {
                                    '_key': _key,
                                    '_from': _from,
                                    '_to': _to,
                                    'relationship': relationship,
                                    'source': EBIComplex.SOURCE,
                                    'source_url': EBIComplex.SOURCE_URL
                                }
                                self.save_props(props)

        self.parsed_data_file.close()
        self.save_to_arango()

    def get_chain_id(self, protein):
        if len(protein.split('-')) > 1:
            if protein.split('-')[1].startswith('PRO_'):
                return protein.split('-')[1]

        return None

    def get_isoform_id(self, protein):
        if len(protein.split('-')) > 1:
            if protein.split('-')[1].isnumeric():
                return protein.split('-')[1]

        return None

    def load_linked_features_dict(self):
        self.linked_features_dict = {}
        with open(EBIComplex.LINKED_FEATURE_PATH, 'rb') as linked_features_file:
            self.linked_features_dict = pickle.load(linked_features_file)

    def save_props(self, props):
        json.dump(props, self.parsed_data_file)
        self.parsed_data_file.write('\n')

    def save_to_arango(self):
        if self.dry_run:
            print(self.arangodb()[0])
        else:
            os.system(self.arangodb()[0])

    def arangodb(self):
        return ArangoDB().generate_json_import_statement(self.output_filepath, self.collection, type=self.type)
