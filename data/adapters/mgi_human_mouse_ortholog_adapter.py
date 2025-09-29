import json
import pickle
from typing import Optional
from jsonschema import Draft202012Validator, ValidationError
from schemas.registry import get_schema

from adapters.writer import Writer

# Sample file:
# DB Class Key	Common Organism Name	NCBI Taxon ID	Symbol	EntrezGene ID	Mouse MGI ID	HGNC ID	OMIM Gene ID	Genetic Location	Genome Coordinates (mouse: GRCm39 human: GRCh38)	Nucleotide RefSeq IDs	Protein RefSeq IDs	SWISS_PROT IDs
# 45916481	mouse, laboratory	10090	Gdnf	14573	MGI:107430			Chr15 3.8 cM	Chr15:7840327-7867056(+)	NM_010275,NM_001301332,NM_001301357,NM_001301333	NP_001288261,NP_034405,NP_001288262,NP_001288286	P48540
# 45916481	human	9606	GDNF	2668		HGNC:4232	OMIM:600837	Chr5 p13.2	Chr5:37812677-37840041(-)	NM_199234,NM_000514,NM_001190468,NM_001190469,NM_001278098,NM_199231	NP_000505,NP_001177397,NP_001177398,NP_001265027,NP_954701,XP_016864826,XP_054208339	P39905
# 45916482	mouse, laboratory	10090	Hoxa4	15401	MGI:96176			Chr6 25.4 cM	Chr6:52166662-52168683(-)	NM_008265	NP_032291	P06798


class MGIHumanMouseOrthologAdapter:
    LABEL = 'human_mm_genes_ortholog'
    MGI_ENSEMBL_FILEPATH = 'data_loading_support_files/MRK_ENSEMBL.rpt'
    HUMAN_ENTREZ_TO_ENSEMBL_FILEPATH = './data_loading_support_files/entrez_to_ensembl.pkl'

    def __init__(self, filepath, dry_run=True, writer: Optional[Writer] = None, validate=False, **kwargs):
        self.filepath = filepath
        self.label = MGIHumanMouseOrthologAdapter.LABEL
        self.dataset = self.label
        self.dry_run = dry_run
        self.type = 'edge'
        self.writer = writer
        self.validate = validate
        if self.validate:
            self.schema = get_schema(
                'edges', 'genes_mm_genes', self.__class__.__name__)
            self.validator = Draft202012Validator(self.schema)

    def validate_doc(self, doc):
        try:
            self.validator.validate(doc)
        except ValidationError as e:
            raise ValueError(f'Document validation failed: {e.message}')

    def load_entrz_ensembl_mapping(self):
        with open(MGIHumanMouseOrthologAdapter.HUMAN_ENTREZ_TO_ENSEMBL_FILEPATH, 'rb') as f:
            self.gene_mapping = pickle.load(f)

    def load_mgi_ensembl_mapping(self):
        self.mm_gene_mapping = {}
        for line in open(MGIHumanMouseOrthologAdapter.MGI_ENSEMBL_FILEPATH, 'r'):
            data_line = line.strip().split('\t')
            self.mm_gene_mapping[data_line[0]] = data_line[5]

    def process_file(self):
        self.writer.open()
        self.load_mgi_ensembl_mapping()
        self.load_entrz_ensembl_mapping()

        orthologs = {}

        for line in open(self.filepath, 'r'):
            if line.startswith('DB'):
                continue

            data_line = line.strip().split('\t')

            if data_line[1].startswith('mouse'):
                mgi_id = data_line[5]

                gene_id = self.mm_gene_mapping.get(mgi_id)
                if gene_id is None:
                    print("Can't process Mouse MGI ID: " + mgi_id)
                    continue
                else:
                    gene_id = 'mm_genes/' + gene_id

            elif data_line[1].startswith('human'):
                entrez_id = data_line[4]

                gene_id = self.gene_mapping.get(entrez_id)
                if gene_id is None:
                    print("Can't process Human Entrez ID: " + entrez_id)
                    continue
                else:
                    gene_id = 'genes/' + gene_id

            ortholog_id = data_line[0]
            if orthologs.get(ortholog_id):
                orthologs[ortholog_id].append(gene_id)
            else:
                orthologs[ortholog_id] = [gene_id]

        for key in orthologs:
            if len(orthologs[key]) <= 1:
                continue
            else:
                human_genes = []
                mouse_genes = []

                for gene in orthologs[key]:
                    if gene.startswith('mm'):
                        mouse_genes.append(gene)
                    else:
                        human_genes.append(gene)

                for human_gene in human_genes:
                    for mm_gene in mouse_genes:
                        _from = human_gene
                        _to = mm_gene
                        id = (_to + '_' + _from).replace('/', '_')

                        props = {
                            '_key': id,
                            '_from': _from,
                            '_to': _to,
                            'name': 'homologous to',
                            'inverse_name': 'homologous to',
                            'relationship': 'ontology_terms/NCIT_C79968',
                            'source': 'MGI',
                            'source_url': 'https://www.informatics.jax.org/downloads/reports/HOM_MouseHumanSequence.rpt'
                        }
                        if self.validate:
                            self.validate_doc(props)
                        self.writer.write(json.dumps(props))
                        self.writer.write('\n')
        self.writer.close()
