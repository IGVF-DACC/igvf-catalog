import json
from typing import Optional

from adapters.archive_utils import get_file_accession
from adapters.base import BaseAdapter
from adapters.helpers import get_file_fileset_by_accession_in_arangodb, get_gene_map_from_arangodb
from adapters.writer import Writer

# Sample file:
# DB Class Key	Common Organism Name	NCBI Taxon ID	Symbol	EntrezGene ID	Mouse MGI ID	HGNC ID	OMIM Gene ID	Genetic Location	Genome Coordinates (mouse: GRCm39 human: GRCh38)	Nucleotide RefSeq IDs	Protein RefSeq IDs	SWISS_PROT IDs
# 45916481	mouse, laboratory	10090	Gdnf	14573	MGI:107430			Chr15 3.8 cM	Chr15:7840327-7867056(+)	NM_010275,NM_001301332,NM_001301357,NM_001301333	NP_001288261,NP_034405,NP_001288262,NP_001288286	P48540
# 45916481	human	9606	GDNF	2668		HGNC:4232	OMIM:600837	Chr5 p13.2	Chr5:37812677-37840041(-)	NM_199234,NM_000514,NM_001190468,NM_001190469,NM_001278098,NM_199231	NP_000505,NP_001177397,NP_001177398,NP_001265027,NP_954701,XP_016864826,XP_054208339	P39905
# 45916482	mouse, laboratory	10090	Hoxa4	15401	MGI:96176			Chr6 25.4 cM	Chr6:52166662-52168683(-)	NM_008265	NP_032291	P06798


class MGIHumanMouseOrthologAdapter(BaseAdapter):
    ALLOWED_LABELS = ['human_mm_genes_ortholog']

    def __init__(self, filepath, label='human_mm_genes_ortholog', writer: Optional[Writer] = None, validate=False, **kwargs):
        self.file_accession = get_file_accession(filepath)
        super().__init__(filepath, label, writer, validate)

    def _get_schema_type(self):
        """Return schema type."""
        return 'edges'

    def _get_collection_name(self):
        """Get collection name."""
        return 'genes_mm_genes'

    @staticmethod
    def _entrez_ensembl_map(gene_map):
        return {
            entrez.removeprefix('ENTREZ:'): ensembl_ids
            for entrez, ensembl_ids in gene_map.items()
            if entrez.startswith('ENTREZ:') and ensembl_ids
        }

    @staticmethod
    def _mgi_ensembl_map(gene_map):
        return {
            mgi_id: ensembl_ids
            for mgi_id, ensembl_ids in gene_map.items()
            if ensembl_ids
        }

    def parse(self):
        self.writer.add_tag('portal_accessions', self.file_accession)

        self.file_fileset = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        self.collection_class = self.file_fileset['class']
        self.method = self.file_fileset['method']
        file_set_accession = self.file_fileset.get('file_set_id')
        if file_set_accession:
            self.writer.add_tag('portal_accessions', file_set_accession)

        self.gene_mapping = self._entrez_ensembl_map(
            get_gene_map_from_arangodb('entrez')
        )
        self.mm_gene_mapping = self._mgi_ensembl_map(
            get_gene_map_from_arangodb('mgi', collection='mm_genes')
        )

        orthologs = {}

        for line in open(self.filepath, 'r'):
            if line.startswith('DB'):
                continue

            data_line = line.strip().split('\t')

            if data_line[1].startswith('mouse'):
                mgi_id = data_line[5]
                ensembl_ids = self.mm_gene_mapping.get(mgi_id)
                if not ensembl_ids:
                    self.logger.warning(
                        "Can't process Mouse MGI ID: " + mgi_id)
                    continue
                gene_ids = ['mm_genes/' +
                            ensembl_id for ensembl_id in ensembl_ids]

            elif data_line[1].startswith('human'):
                entrez_id = data_line[4]
                ensembl_ids = self.gene_mapping.get(entrez_id)
                if not ensembl_ids:
                    self.logger.warning(
                        "Can't process Human Entrez ID: " + entrez_id)
                    continue
                gene_ids = ['genes/' +
                            ensembl_id for ensembl_id in ensembl_ids]
            else:
                continue

            ortholog_id = data_line[0]
            if orthologs.get(ortholog_id):
                orthologs[ortholog_id].extend(gene_ids)
            else:
                orthologs[ortholog_id] = gene_ids

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
                            'source_url': 'https://www.informatics.jax.org/downloads/reports/HOM_MouseHumanSequence.rpt',
                            'class': self.collection_class,
                            'method': self.method,
                            'files_filesets': 'files_filesets/' + self.file_accession
                        }
                        if self.validate:
                            self.validate_doc(props)
                        self.writer.write(json.dumps(props))
                        self.writer.write('\n')
