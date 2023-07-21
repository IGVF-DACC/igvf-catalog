import gzip
from Bio import SeqIO
from adapters import Adapter

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

# Data file for parent_pathway_of and child_pathway_of: https://reactome.org/download/current/ReactomePathwaysRelation.txt
# example file:
# R-BTA-109581	R-BTA-109606
# R-BTA-109581	R-BTA-169911
# R-BTA-109581	R-BTA-5357769
# R-BTA-109581	R-BTA-75153
# R-BTA-109582	R-BTA-140877


class Reactome(Adapter):

    ALLOWED_LABELS = ['genes_pathways',
                      'parent_pathway_of', 'child_pathway_of']

    def __init__(self, filepath, label):
        if label not in Reactome.ALLOWED_LABELS:
            raise ValueError('Ivalid label. Allowed values: ' +
                             ', '.join(Reactome.ALLOWED_LABELS))
        self.filepath = filepath
        self.dataset = label
        self.label = label

        super(Reactome, self).__init__()

    def process_file(self):
        with open(self.filepath) as input:
            _props = {
                'source': 'Reactome',
                'source_url': 'https://reactome.org/'
            }
            for line in input:
                if self.label == 'genes_pathways':
                    data = line.strip().split('\t')
                    pathway_id = data[1]
                    if pathway_id.startswith('R-HSA'):
                        ensg_id = data[0].split('.')[0]
                        _id = ensg_id + '_' + pathway_id
                        _source = 'genes/' + ensg_id
                        _target = 'pathways/' + pathway_id
                        yield(_id, _source, _target, self.label, _props)
                else:
                    parent, child = line.strip().split('\t')
                    if parent.startswith('R-HSA'):
                        if self.label == 'parent_pathway_of':
                            _id = parent + '_' + child
                            _source = 'pathways/' + parent
                            _target = 'pathways/' + child
                            _props.update(
                                {
                                    'type': 'parent'
                                }
                            )
                            yield(_id, _source, _target, self.label, _props)
                        elif self.label == 'child_pathway_of':
                            _props.update(
                                {
                                    'type': 'child'
                                }
                            )
                            _id = child + '_' + parent
                            _source = 'pathways/' + child
                            _target = 'pathways/' + parent
                            yield(_id, _source, _target, self.label, _props)
