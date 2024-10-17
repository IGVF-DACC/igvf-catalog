import obonet
import json
from typing import Optional

from adapters.writer import Writer

# cellosaurus.obo is downloaded from: https://ftp.expasy.org/databases/cellosaurus/
# Example node from the obo file:
# [Term]
# id: CVCL_ZW87
# name:017-PC-A
# synonym: "PC-A" RELATED []
# subset: Finite_cell_line
# subset: Female
# xref: Wikidata:Q102111939
# xref: PubMed:27109637
# xref: NCBI_TaxID:9606 ! Homo sapiens (Human)
# comment: "Characteristics: hESC-derived mesenchymal progenitor. Derived from site: In situ; Blastocyst; UBERON=UBERON_0000358."
# relationship: derived_from CVCL_B854 ! ESI-017
# creation_date: 2020-10-29T00:00:00Z


class Cellosaurus:
    SOURCE = 'Cellosaurus'
    SOURCE_URL_PREFIX = 'https://www.cellosaurus.org/'
    NODE_KEYS = ['name', 'synonym', 'subset']
    EDGE_KEYS = ['xref', 'relationship']
    EDGE_TYPES = ['database cross-reference',
                  'originate from same individual as', 'derived from']
    # NBCI TaxID for Human and Mouse
    SPECIES_IDS = ['NCBI_TaxID:9606', 'NCBI_TaxID:10090']

    def __init__(self, filepath, type='node', species_filter=True, writer: Optional[Writer] = None, **kwargs):
        self.filepath = filepath
        self.type = type
        self.species_filter = species_filter
        if type == 'node':
            self.dataset = 'ontology_term'
        else:
            self.dataset = 'ontology_relationship'
        self.label = self.dataset
        self.writer = writer

    def process_file(self):
        self.writer.open()
        graph = obonet.read_obo(self.filepath)
        same_individual_pairs = []

        for node in graph.nodes():
            node_dict = graph.nodes[node]
            # only load cells from organisms in SPECIES_IDS (i.e. Human & Mouse)
            if self.species_filter:
                if node_dict.get('xref'):
                    xrefs = node_dict['xref']
                    if not set(xrefs) & set(Cellosaurus.SPECIES_IDS):
                        continue
                else:
                    continue

            if self.type == 'node':
                synonyms = None
                # e.g. "HL-1 Friendly Myeloma 653" RELATED []
                if node_dict.get('synonyms'):
                    synonyms = [syn.split('"')[1]
                                for syn in node_dict['synonyms']]

                props = {
                    '_key': node,
                    'uri': Cellosaurus.SOURCE_URL_PREFIX + node,
                    'term_id': node,
                    'name': node_dict.get('name', None),
                    'synonyms': synonyms,
                    'source': Cellosaurus.SOURCE,
                    'subset': node_dict.get('subset', None)
                }
                self.save_props(props)

            else:
                if node_dict.get('xref'):
                    edge_type = 'database cross-reference'
                    # could have url for each xref, need some work from cellosaurus_xrefs.txt
                    for xref in node_dict['xref']:
                        if node in xref:  # ignore xref to the same term in another database
                            continue
                        elif xref.startswith('http') or xref.startswith('DOI'):
                            continue
                        xref_key = self.to_key(xref)
                        key = '{}_{}_{}'.format(
                            node,
                            'oboInOwl.hasDbXref',  # using same naming format as the ontology terms from owl files
                            xref_key
                        )

                        props = {
                            '_key': key,
                            '_from': 'ontology_terms/' + node,
                            '_to': 'ontology_terms/' + xref_key,
                            'name': edge_type,
                            'inverse_name': 'database cross-reference',
                            'source': Cellosaurus.SOURCE
                        }

                        self.save_props(props)

                if node_dict.get('relationship'):
                    for relation in node_dict['relationship']:
                        edge_type, to_node_key = relation.split(' ')[:2]
                        if edge_type == 'originate_from_same_individual_as':  # symmetric relationship, check redundancy
                            if '-'.join([to_node_key, node]) in same_individual_pairs:
                                continue
                            else:
                                same_individual_pairs.append(
                                    '-'.join([node, to_node_key]))

                        key = '{}_{}_{}'.format(
                            node,
                            edge_type,
                            to_node_key
                        )

                        props = {
                            '_key': key,
                            '_from': 'ontology_terms/' + node,
                            '_to': 'ontology_terms/' + to_node_key,
                            'name': edge_type.replace('_', ' '),
                            'source': Cellosaurus.SOURCE
                        }

                        inverse_name = 'type of'  # for name = subclass
                        if props['name'] == 'database cross-reference':
                            inverse_name = 'database cross-reference'
                        elif props['name'] == 'derived from':
                            inverse_name = 'derives'
                        elif props['name'] == 'has part':
                            inverse_name = 'part of'
                        elif props['name'] == 'part of':
                            inverse_name = 'has part'
                        elif props['name'] == 'originate from same individual as':
                            inverse_name = 'originate from same individual as'
                        props['inverse_name'] = inverse_name

                        self.save_props(props)

        self.writer.close()

    def save_props(self, props):
        self.writer.write(json.dumps(props))
        self.writer.write('\n')

    def to_key(self, xref):
        key = xref.replace(':', '_').replace('/', '_').replace(' ', '_')
        # remove redanduncy part for terms like CLO:CLO_0001001
        if key.split('_')[0] == key.split('_')[1]:
            key = '_'.join(key.split('_')[1:])

        # keep naming consistent with the existing terms from owl files
        key = key.replace('NCBI_TaxID', 'NCBITaxon')
        key = key.replace('ORDO_', '')
        # there might be other inconsistencies we need to fix

        # fix a rare typo: ORDO:Orphaet_102
        key = key.replace('Orphaet', 'Orphanet')

        return key
