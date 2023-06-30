import gzip
import csv
import os
import json
import hashlib
from adapters import Adapter
from adapters.helpers import build_variant_id
from db.arango_db import ArangoDB


# GWAS variant to phenotype - v2d_igvf.tsv
# variant_id      mondo_id        efo_id  study_id        lead_chrom      lead_pos        lead_ref        lead_alt        direction       beta    beta_ci_lower   beta_ci_upper   odds_ratio      oddsr_ci_lower  oddsr_ci_upper        pval_mantissa   pval_exponent   pval    ancestry_initial        ancestry_replication    n_cases n_initial       n_replication   pmid    pub_author      pub_date        pub_journal     pub_title             has_sumstats    num_assoc_loci  source  trait_reported  trait_efos      trait_category  tag_chrom       tag_pos tag_ref tag_alt overall_r2      pics_95perc_credset     AFR_1000G_prop  AMR_1000G_prop  EAS_1000G_prop        EUR_1000G_prop  SAS_1000G_prop  log10_ABF       posterior_prob
# 1:1010747:GT:G  NA      EFO_0007010     NEALE2_20003_1140867876 1       1010747 GT      G       -                               0.3464239658215028      0.2372663081628671      0.5058011186869372      4.02417 -8            4.02417e-08     ['European=361141']     []      491.0   361141  0.0             UKB Neale v2    2018-08-01                      True    6       NEALE   Prozac 20mg capsule | treatment/medication code ['EFO_0007010']       measurement     1       988598  A       AG      0.551468126881  True    0.0     0.0     0.0     1.0     0.0     5.112385010047364       0.004867160933888
# 1:1009731:C:T   NA      EFO_0007937     GCST90087821    1       1009731 C       T       +       0.707278        0.5564011777996241      0.8581548222003759                              4.0     -20     4e-20   ['European=5366']     []              5366            PMID:35078996   Gudjonsson A    2022-01-25      Nat Commun      A genome-wide association study of serum proteins reveals shared loci with common diseases.     False         2       GCST    Serum levels of protein ISG15   ['EFO_0007937'] measurement     1       988598  A       AG      0.803520410449  True    0.0     0.0     0.0     1.0     0.0
# 1:1008088:T:C   NA      EFO_0007937     GCST006585_950  1       1008088 T       C       +       0.73554206      0.5305998818099342      0.9404842381900658                              2.0     -12     2e-12   ['European=3200']     []              3200            PMID:30072576   Emilsson V      2018-08-02      Science Co-regulatory networks of human serum proteins link genetics to disease.        False   1       GCST    Blood protein levels [ISG15, 14151_4_3]       ['EFO_0007937'] measurement     1       988598  A       AG      0.825908352025  True    0.0     0.0     0.0     1.0     0.0


# GWAS variant to gene - scored file (v2g_scored_igvf):
# (note: v2g_igvf has the same columns except for the last 4)
# variant_id      gene_id chr_id  position        ref_allele      alt_allele      feature type_id source_id          fpred_labels    fpred_scores    fpred_max_label fpred_max_score qtl_beta        qtl_se  qtl_pval           qtl_score       interval_score  qtl_score_q     interval_score_q        d       distance_score  distance_score_q   overall_score   source_list     source_score_list
# 5:141242639:G:T ENSG00000204961 5       141242639       G       T       MACROPHAGES_M0  pchic   javierre2016       []      []                                                      8.56622816615577                0.7                                0.0663983903420523      ['canonical_tss' 'javierre2016']        [0.2 0.8]
# 5:141242639:G:T ENSG00000204961 5       141242639       G       T       MACROPHAGES_M1  pchic   javierre2016       []      []                                                      9.03867857946432                0.7                                0.0663983903420523      ['canonical_tss' 'javierre2016']        [0.2 0.8]
# 5:141242736:GT:G        ENSG00000253953 5       141242736       GT      G       unspecified     distance           canonical_tss   []      []                                                                                 144962.0        6.898359570094232e-06   0.7     0.0929577464788732      ['canonical_tss' 'javierre2016']   [0.7 0.7]

# Important! We need to handle the case where breaklines happen in the middle of certain lines, like:
# 6:32387828:G:A	ENSG00000237541	6	32387828	G	A	ROSMAP-BRAIN_NAIVE	eqtl	eqtl	[]	[]			0.364989	0.0521153	7.24831e-12	11.139763240771314		0.6					0.4462776659959758	"['sqtl' 'pqtl' 'javierre2016' 'thurman2012' 'jung2019' 'canonical_tss'
# 'eqtl']"	[0.7 0.9 0.7 0.  0.  0.3 0.9]


class GWAS(Adapter):
    SKIP_BIOCYPHER = True
    OUTPUT_PATH = './parsed-data'

    def __init__(self, variants_to_ontology, variants_to_genes, dry_run=True):
        self.to_ontology_filepath = variants_to_ontology
        self.to_genes_filepath = variants_to_genes
        self.dataset = 'gwas_phenotypes'
        self.dry_run = dry_run

        self.output_filepath = '{}/{}-{}.json'.format(
            GWAS.OUTPUT_PATH,
            self.dataset,
            variants_to_ontology.split('/')[-1]
        )

        super(GWAS, self).__init__()

    # trying to capture the breakline problem described in the comments above
    def line_appears_broken(self, row):
        return row[-1].startswith('"[') and not row[-1].endswith(']"')

    def edge_keys(self, row):
        variant_id = 'variants/' + \
            build_variant_id(row[4], row[5], row[6], row[7])

        ontology_term_id = 'ontology_terms/'
        equivalent_term_id = None
        # give preference to MONDO if defined, otherwise, use EFO term
        if row[1] != 'NA':
            ontology_term_id = ontology_term_id + row[1]
            equivalent_term_id = 'ontology_terms/' + row[2]
        else:
            ontology_term_id = ontology_term_id + row[2]

        # MANY records have no ontology term. Ignoring those lines.
        if ontology_term_id == 'ontology_terms/':
            return (None, None, None, None)

        key = hashlib.sha256(
            (variant_id + '_' + ontology_term_id).encode()).hexdigest()

        return (key, variant_id, ontology_term_id, equivalent_term_id)

    def process_file(self):
        header = None
        trying_to_complete_line = None

        print('Collecting genes...')
        genes = self.get_genes_from_variant_to_genes_file()

        print('Collecting tagged variants...')
        tagged = self.get_tagged_variants()

        # Many records are duplicated with different tagged values.
        # We are collecting all tagged values at once.
        # For that, we need to keep track of which keys we already processed to avoid duplicated entries.
        processed_keys = set()

        parsed_data_file = open(self.output_filepath, 'w')

        print('Processing file...')

        for record in open(self.to_ontology_filepath, 'r'):
            if header is None:
                header = record.strip().split('\t')
                continue

            if trying_to_complete_line:
                record = trying_to_complete_line + record
                trying_to_complete_line = None

            row = record.strip().split('\t')

            if self.line_appears_broken(row):
                trying_to_complete_line = record
                continue

            key, variant_id, ontology_term_id, equivalent_term_id = self.edge_keys(
                row)

            if key is None or key in processed_keys:
                continue

            # a few rows are incomplete. Filling empty values with None
            row = row + [None] * (len(header) - len(row))

            props = {
                '_key': key,
                '_from': variant_id,
                '_to': ontology_term_id,
                'genes': genes.get(row[0]),
                'equivalent_ontology_term': equivalent_term_id,
                'study_id': row[3],
                'lead_chrom': row[4],
                'lead_pos': row[5],
                'lead_ref': row[6],
                'lead_alt': row[7],
                'direction': row[8],
                'beta': row[9],
                'beta_ci_lower': row[10],
                'beta_ci_upper': row[11],
                'odds_ratio': row[12],
                'oddsr_ci_lower': row[13],
                'oddsr_ci_upper': row[14],
                'pval_mantissa': row[15],
                'pval_exponent': row[16],
                'pval': row[17],
                'ancestry_initial': row[18],
                'ancestry_replication': row[19],
                'n_cases': row[20],
                'n_initial': row[21],
                'n_replication': row[22],
                'pmid': row[23],
                'pub_author': row[24],
                'pub_date': row[25],
                'pub_journal': row[26],
                'pub_title': row[27],
                'has_sumstats': row[28],
                'num_assoc_loci': row[29],
                'source': row[30],
                'trait_reported': row[31],
                'trait_efos': row[32],
                'trait_category': row[33],
                'tagged': tagged[key],
                'source': 'OpenTargets',
                'version': 'October 2022 (22.10)'
            }

            processed_keys.add(key)
            json.dump(props, parsed_data_file)
            parsed_data_file.write('\n')

        parsed_data_file.close()
        self.save_to_arango()

    def arangodb(self):
        return ArangoDB().generate_json_import_statement(self.output_filepath, 'variants_phenotypes', type='edge')

    def save_to_arango(self):
        if self.dry_run:
            print(self.arangodb()[0])
        else:
            os.system(self.arangodb()[0])

    def get_tagged_variants(self):
        header = None
        trying_to_complete_line = None
        tagged_variants = {}

        for record in open(self.to_ontology_filepath, 'r'):
            if header is None:
                header = record.strip().split('\t')
                continue

            if trying_to_complete_line:
                record = trying_to_complete_line + record
                trying_to_complete_line = None

            row = record.strip().split('\t')

            if self.line_appears_broken(row):
                trying_to_complete_line = record
                continue

            key = self.edge_keys(row)[0]

            if key is None:
                continue

            # a few rows are incomplete. Filling empty values with None
            row = row + [None] * (len(header) - len(row))

            variant = {
                'tag_chrom': row[34],
                'tag_pos': row[35],
                'tag_ref': row[36],
                'tag_alt': row[37],
                'overall_r2': row[38],
                'pics_95perc_credset': row[39],
                'AFR_1000G_prop': row[40],
                'AMR_1000G_prop': row[41],
                'EAS_1000G_prop': row[42],
                'EUR_1000G_prop': row[43],
                'SAS_1000G_prop': row[44],
                'log10_ABF': row[45],
                'posterior_prob': row[46]
            }

            if key not in tagged_variants:
                tagged_variants[key] = [variant]
            else:
                should_add = True
                for tagged in tagged_variants[key]:
                    if tagged == variant:
                        should_add = False
                        break
                if should_add:
                    tagged_variants[key].append(variant)

        return tagged_variants

    def get_genes_from_variant_to_genes_file(self):
        header = None
        trying_to_complete_line = None
        genes = {}

        for record in open(self.to_genes_filepath, 'r'):
            if header is None:
                header = record.strip().split('\t')
                continue

            if trying_to_complete_line:
                record = trying_to_complete_line + record
                trying_to_complete_line = None

            row = record.strip().split('\t')

            if self.line_appears_broken(row):
                trying_to_complete_line = record
                continue

            gene_id = row[1]

            if row[0] not in genes:
                genes[row[0]] = {}

            genes[row[0]]['genes/' + gene_id] = {
                'feature': row[6],
                'type_id': row[7],
                'source_id': row[8]
            }

        return genes
