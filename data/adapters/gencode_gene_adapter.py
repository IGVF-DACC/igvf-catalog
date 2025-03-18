import gzip
import json
from typing import Optional

from adapters.writer import Writer
import requests

# Example genocde gtf input file:
# ##description: evidence-based annotation of the human genome (GRCh38), version 43 (Ensembl 109)
# ##provider: GENCODE
# ##contact: gencode-help@ebi.ac.uk
# ##format: gtf
# ##date: 2022-11-29
# chr1	HAVANA	gene	11869	14409	.	+	.	gene_id "ENSG00000290825.1"; gene_type "lncRNA"; gene_name "DDX11L2"; level 2; tag "overlaps_pseudogene";
# chr1	HAVANA	transcript	11869	14409	.	+	.	gene_id "ENSG00000290825.1"; transcript_id "ENST00000456328.2"; gene_type "lncRNA"; gene_name "DDX11L2"; transcript_type "lncRNA"; transcript_name "DDX11L2-202"; level 2; transcript_support_level "1"; tag "basic"; tag "Ensembl_canonical"; havana_transcript "OTTHUMT00000362751.1";
# chr1	HAVANA	exon	11869	12227	.	+	.	gene_id "ENSG00000290825.1"; transcript_id "ENST00000456328.2"; gene_type "lncRNA"; gene_name "DDX11L2"; transcript_type "lncRNA"; transcript_name "DDX11L2-202"; exon_number 1; exon_id "ENSE00002234944.1"; level 2; transcript_support_level "1"; tag "basic"; tag "Ensembl_canonical"; havana_transcript "OTTHUMT00000362751.1";
# chr1	HAVANA	exon	12613	12721	.	+	.	gene_id "ENSG00000290825.1"; transcript_id "ENST00000456328.2"; gene_type "lncRNA"; gene_name "DDX11L2"; transcript_type "lncRNA"; transcript_name "DDX11L2-202"; exon_number 2; exon_id "ENSE00003582793.1"; level 2; transcript_support_level "1"; tag "basic"; tag "Ensembl_canonical"; havana_transcript "OTTHUMT00000362751.1";


class GencodeGene:
    ALLOWED_KEYS = ['gene_id', 'gene_type', 'gene_name',
                    'transcript_id', 'transcript_type', 'transcript_name', 'hgnc_id', 'mgi_id']
    INDEX = {'chr': 0, 'type': 2, 'coord_start': 3, 'coord_end': 4, 'info': 8}
    ALLOWED_LABELS = [
        'gencode_gene',
        'mm_gencode_gene',
    ]
    ALLOWED_MODE = [
        # output a jsonl file for loading genes into igvfd (without the collections and study_sets properties)
        'igvfd',
        # output a jsonl file with the same properties as on igvfd (from gencode gtf file), also load collections and study_sets properties from igvfd portal
        'catalog'
    ]

    def __init__(self, filepath=None, gene_alias_file_path=None, chr='all', label='gencode_gene', mode='igvfd', writer: Optional[Writer] = None, **kwargs):
        if label not in GencodeGene.ALLOWED_LABELS:
            raise ValueError('Invalid label. Allowed values: ' +
                             ','.join(GencodeGene.ALLOWED_LABELS))
        if mode not in GencodeGene.ALLOWED_MODE:
            raise ValueError('Invalid mode. Allowed values: ' +
                             ','.join(GencodeGene.ALLOWED_MODE))

        self.filepath = filepath
        self.label = label
        self.gene_alias_file_path = gene_alias_file_path
        self.writer = writer
        self.mode = mode
        if self.label == 'gencode_gene':
            self.version = 'v43'
            self.transcript_annotation = 'GENCODE 43'
            self.source_url = 'https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_43/gencode.v43.chr_patch_hapl_scaff.annotation.gtf.gz'
            self.organism = 'Homo sapiens'
            self.assembly = 'GRCh38'
            self.chr_name_mapping_path = './data_loading_support_files/gencode/GCF_000001405.39_GRCh38.p13_assembly_report.txt'
        else:
            self.version = 'vM36'
            self.transcript_annotation = 'GENCODE M36'
            self.source_url = 'https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_mouse/release_M36/gencode.vM36.chr_patch_hapl_scaff.annotation.gtf.gz'
            self.organism = 'Mus musculus'
            self.assembly = 'GRCm39'
            self.chr_name_mapping_path = './data_loading_support_files/gencode/GCF_000001635.27_GRCm39_assembly_report.txt'

    def parse_info_metadata(self, info):
        parsed_info = {}
        for key, value in zip(info, info[1:]):
            if key in GencodeGene.ALLOWED_KEYS:
                parsed_info[key] = value.replace('"', '').replace(';', '')
        return parsed_info

    # the gene alias dict will use both ensembl id and hgnc id (or mgi id for mouse) as key
    def get_collection_alias(self):
        alias_dict = {}
        with gzip.open(self.gene_alias_file_path, 'rt') as input:
            next(input)
            for line in input:
                hgnc = ''
                ensembl = ''
                mgi = ''
                (tax_id, gene_id, symbol, locus_tag, synonyms, dbxrefs, chromosome, map_location, description, type_of_gene, symbol_from_nomenclature_authority,
                 full_name_from_nomenclature_authority, Nomenclature_status, Other_designations, Modification_date, Feature_type) = line.split('\t')
                split_dbxrefs = dbxrefs.split('|')
                for ref in split_dbxrefs:
                    if ref.startswith('HGNC:'):
                        hgnc = ref[5:]
                    elif ref.startswith('Ensembl:'):
                        ensembl = ref[8:]
                    elif ref.startswith('MGI:'):
                        mgi = ref[4:]
                if ensembl or hgnc or mgi:
                    complete_synonyms = []
                    complete_synonyms.append(symbol)
                    for i in synonyms.split('|'):
                        complete_synonyms.append(i)
                    for i in Other_designations.split('|'):
                        complete_synonyms.append(i)
                    complete_synonyms.append(
                        symbol_from_nomenclature_authority)
                    complete_synonyms.append(
                        full_name_from_nomenclature_authority)
                    complete_synonyms = list(set(complete_synonyms))
                    if '-' in complete_synonyms:
                        complete_synonyms.remove('-')
                    alias = {
                        'alias': complete_synonyms,
                        'entrez': 'ENTREZ:' + gene_id  # check if breaks api
                    }
                    if self.label == 'gencode_gene' and hgnc:
                        alias.update(
                            {'hgnc': hgnc}
                        )
                        alias_dict[hgnc] = alias
                    if self.label == 'mm_gencode_gene' and mgi:
                        alias.update(
                            {'mgi': mgi}
                        )
                        alias_dict[mgi] = alias
                    if ensembl:
                        alias_dict[ensembl] = alias
        return alias_dict

    def get_hgnc_id(self, id, info, alias_dict):
        hgnc_id = info.get('hgnc_id')
        if not hgnc_id:
            alias = alias_dict.get(id)
            if alias:
                hgnc_id = alias.get('hgnc')
        return hgnc_id

    def get_mgi_id(self, id, info, alias_dict):
        mgi_id = info.get('mgi_id')
        if not mgi_id:
            alias = alias_dict.get(id)
            if alias:
                mgi_id = alias.get('mgi')
        return mgi_id

    def get_alias_by_id(self, id, hgnc_id, mgi_id, alias_dict):
        for key in [id, hgnc_id, mgi_id]:
            if key in alias_dict:
                return alias_dict[key]
        return None

    def get_additional_props_from_igvfd(self, id):
        igvfd_props = {}
        igvfd_url = 'https://api.data.igvf.org/'
        gene_object = requests.get(
            igvfd_url + id + '/@@object?format=json').json()

        igvfd_props['collections'] = gene_object.get('collections')
        igvfd_props['study_sets'] = gene_object.get('study_sets')
        return igvfd_props

    def load_chr_name_mapping(self):
        self.chr_name_mapping = {}
        with open(self.chr_name_mapping_path, 'r') as mapping_file:
            for row in mapping_file:
                if row.startswith('#'):
                    continue
                mapping_line = row.strip().split('\t')
                self.chr_name_mapping[mapping_line[4]] = mapping_line[-1]

    def process_file(self):
        alias_dict = self.get_collection_alias()
        self.load_chr_name_mapping()
        self.writer.open()
        for line in open(self.filepath, 'r'):
            if line.startswith('#'):
                continue
            split_line = line.strip().split()
            if split_line[GencodeGene.INDEX['type']] == 'gene':
                info = self.parse_info_metadata(
                    split_line[GencodeGene.INDEX['info']:])
                gene_id = info['gene_id']
                id = gene_id.split('.')[0]
                hgnc_id = self.get_hgnc_id(id, info, alias_dict)
                mgi_id = self.get_mgi_id(id, info, alias_dict)
                alias = self.get_alias_by_id(id, hgnc_id, mgi_id, alias_dict)
                chr = split_line[GencodeGene.INDEX['chr']]
                if gene_id.endswith('_PAR_Y'):
                    id = id + '_PAR_Y'
                # map chr name for scaffold/patched regions, use ucsc-style names like chr8_KZ208915v1_fix
                if not chr.startswith('chr'):
                    if chr not in self.chr_name_mapping:
                        print(chr + ' does not have mapped chromosome name.')
                        continue
                    else:
                        # excluding the rows with chromosome name as 'na'
                        if self.chr_name_mapping.get(chr) == 'na':
                            print(chr + ' has illegal mapped chromosome name.')
                            continue
                        else:
                            chr = self.chr_name_mapping.get(chr)
                # the gtf file format is [1-based,1-based], needs to convert to BED format [0-based,1-based]
                start = int(split_line[GencodeGene.INDEX['coord_start']]) - 1
                end = int(split_line[GencodeGene.INDEX['coord_end']])
                if self.mode == 'catalog':
                    to_json = {
                        '_key': id,
                        'gene_id': gene_id,
                        'gene_type': info['gene_type'],
                        'chr': chr,
                        'start': start,
                        'end': end,
                        'symbol': info['gene_name'],
                        'name': info['gene_name'],
                        'source': 'GENCODE',
                        'version': self.version,
                        'source_url': self.source_url,
                        'organism': self.organism
                    }
                    if hgnc_id:
                        to_json.update(
                            {
                                'hgnc': hgnc_id,
                            }
                        )
                    if mgi_id:
                        to_json.update(
                            {
                                'mgi': mgi_id,
                            }
                        )
                    if alias:
                        to_json.update(
                            {
                                # renamed aliases to synonyms (to be consistent with igvfd); # check if breaks api
                                'synonyms': alias['alias'],
                                'entrez': alias['entrez']
                            }
                        )
                    # load collections and study_sets from igvfd portal
                    igvfd_props = self.get_additional_props_from_igvfd(id)
                    to_json.update(igvfd_props)
                    self.writer.write(json.dumps(to_json))
                    self.writer.write('\n')
                else:  # reformat output json to fit igvfd schema
                    dbxrefs = []
                    if hgnc_id:
                        dbxrefs.append(hgnc_id)
                    if mgi_id:
                        dbxrefs.append(mgi_id)
                    if alias and 'entrez' in alias:
                        dbxrefs.append(alias['entrez'])
                    to_json = {
                        'geneid': id,  # without version number
                        'locations': [{'assembly': self.assembly, 'chromosome': chr, 'start': start, 'end': end}],
                        'symbol': info['gene_name'],
                        'taxa': self.organism,
                        'transcriptome_annotation': self.transcript_annotation,
                        'version_number': gene_id.split('.')[-1]
                    }
                    if alias and 'alias' in alias:
                        to_json.update(
                            {
                                'synonyms': alias['alias'],
                            }
                        )
                    # dbxrefs is a required field on igvfd
                    # remove this after schema updated in igvfd
                    if dbxrefs:
                        to_json.update(
                            {
                                'dbxrefs': dbxrefs
                            }
                        )
                        self.writer.write(json.dumps(to_json))
                        self.writer.write('\n')
        self.writer.close()
