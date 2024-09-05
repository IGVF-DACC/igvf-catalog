import json
import os
from typing import Optional

from adapters import Adapter
from db.arango_db import ArangoDB
from adapters.writer import Writer

# Data file for genes_pathways: https://reactome.org/download/current/Ensembl2Reactome_All_Levels.txt
# data format:
# Source database identifier, e.g. UniProt, ENSEMBL, NCBI Gene or ChEBI identifier
# Reactome Pathway Stable identifier
# URL
# Event (Pathway or Reaction) Name
# Evidence Code
# Species

# Example file:
# ENSDART00000193986	R-DRE-5653656	https://reactome.org/PathwayBrowser/#/R-DRE-5653656	Vesicle-mediated transport	IEA	Danio rerio
# ENSG00000000419	R-HSA-162699	https://reactome.org/PathwayBrowser/#/R-HSA-162699	Synthesis of dolichyl-phosphate mannose	TAS	Homo sapiens
# ENSG00000000419	R-HSA-163125	https://reactome.org/PathwayBrowser/#/R-HSA-163125	Post-translational modification: synthesis of GPI-anchored proteins	TAS	Homo sapiens
# ENSG00000000419	R-HSA-1643685	https://reactome.org/PathwayBrowser/#/R-HSA-1643685	Disease	TAS	Homo sapiens
# ENSG00000000419.14	R-HSA-162699	https://reactome.org/PathwayBrowser/#/R-HSA-162699	Synthesis of dolichyl-phosphate mannose	TAS	Homo sapiens

# Data file for parent_pathway_of: https://reactome.org/download/current/ReactomePathwaysRelation.txt
# example file:
# R-BTA-109581	R-BTA-109606
# R-BTA-109581	R-BTA-169911
# R-BTA-109581	R-BTA-5357769
# R-BTA-109581	R-BTA-75153
# R-BTA-109582	R-BTA-140877


class Reactome:

    ALLOWED_LABELS = ['genes_pathways',
                      'parent_pathway_of']

    def __init__(self, filepath, label, dry_run=True, writer: Optional[Writer] = None):
        if label not in Reactome.ALLOWED_LABELS:
            raise ValueError('Ivalid label. Allowed values: ' +
                             ', '.join(Reactome.ALLOWED_LABELS))
        self.filepath = filepath
        self.dataset = label
        self.label = label
        self.dry_run = dry_run
        self.type = 'edge'
        self.writer = writer

    def process_file(self):
        self.writer.open()
        with open(self.filepath) as input:
            _props = {
                'source': 'Reactome',
                'source_url': 'https://reactome.org/',
                'organism': 'Homo sapiens'
            }
            _ids_dict = {}
            for line in input:
                if self.label == 'genes_pathways':
                    data = line.strip().split('\t')
                    pathway_id = data[1]
                    if pathway_id.startswith('R-HSA') and data[0].startswith('ENSG'):
                        ensg_id = data[0].split('.')[0]
                        _id = ensg_id + '_' + pathway_id
                        if _id in _ids_dict:
                            continue
                        _ids_dict[_id] = True
                        _source = 'genes/' + ensg_id
                        _target = 'pathways/' + pathway_id
                        _props.update(
                            {
                                '_key': _id,
                                '_from': _source,
                                '_to': _target,
                                'name': 'belongs to',
                                'inverse_name': 'has part'
                            }
                        )
                        self.writer.write(json.dumps(_props))
                        self.writer.write('\n')
                else:
                    parent, child = line.strip().split('\t')
                    if parent.startswith('R-HSA'):
                        _id = parent + '_' + child
                        _source = 'pathways/' + parent
                        _target = 'pathways/' + child
                        _props.update(
                            {
                                '_key': _id,
                                '_from': _source,
                                '_to': _target,
                                'name': 'parent of',
                                'inverse_name': 'child of'
                            }
                        )
                        self.writer.write(json.dumps(_props))
                        self.writer.write('\n')
        self.writer.close()

    def save_to_arango(self):
        if self.dry_run:
            print(self.arangodb()[0])
        else:
            os.system(self.arangodb()[0])

    def arangodb(self):
        return ArangoDB().generate_json_import_statement(self.writer.destination, self.collection, type=self.type)
