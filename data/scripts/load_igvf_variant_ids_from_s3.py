#!/usr/bin/env python3
"""
Stream variants_* JSONL backup files from S3, filter each record to
source == "IGVF", extract the variant ID from the `_from` field
(collection prefix stripped, e.g. 'variants/12345' -> '12345'), and
bulk-insert the unique IDs into an ArangoDB collection (default:
variants_IGVF).

De-duplication is handled entirely by ArangoDB: each ID is inserted as
{"_key": variant_id}, and bulk inserts use overwrite_mode="ignore" so
duplicate keys are silently skipped by the collection's own unique
primary index -- no need to hold anything in memory or post-process for
uniqueness.

Expects S3 layout like:
    s3://igvf-catalog-parsed-collections/variants_biosamples/*.jsonl
    s3://igvf-catalog-parsed-collections/variants_coding_variants/*.jsonl
    ... etc, one prefix per collection.

Not every file under a prefix need be relevant. Two ways to control
which files get pulled:
  - --file-pattern: a glob restricting filenames when listing a prefix
    (default: *.jsonl)
  - MANIFEST (hardcoded dict near the top of this file): an EXPLICIT
    list of filenames per prefix, bypassing S3 listing entirely for
    those prefixes. Edit it directly, e.g.:
        MANIFEST["variants_biosamples"] = ["part-0001.jsonl", "part-0002.jsonl"]
    Any prefix left as an empty list falls back to --file-pattern
    based listing.

Install dependencies:
    pip install boto3 python-arango --break-system-packages

Usage:
    python3 load_variant_ids_from_s3.py \\
        --bucket igvf-catalog-parsed-collections \\
        --host https://your-arango-host:8529 \\
        --db your_db_name \\
        --username your_user \\
        --password your_password \\
        [--prefixes variants_biosamples,variants_coding_variants,...] \\
        [--target-collection variants_IGVF] \\
        [--file-pattern "*.jsonl"] \\
        [--insert-batch-size 5000] \\
        [--region us-east-1] \\
        [--anonymous]

Run with -h/--help to see all options.
"""

import argparse
import fnmatch
import json
import sys
import time

import boto3
from botocore import UNSIGNED
from botocore.config import Config

from arango import ArangoClient
from arango.http import DefaultHTTPClient


DEFAULT_PREFIXES = [
    'variants_biosamples',
    'variants_coding_variants',
    'variants_genes',
    'variants_phenotypes',
    'variants_proteins',
]

# Explicit list of filenames to pull per collection prefix. Fill this in
# directly -- e.g. MANIFEST["variants_biosamples"] = ["part-0001.jsonl",
# "part-0002.jsonl"]. Any prefix left out (or set to an empty list) falls
# back to --file-pattern-based listing of everything under that prefix.
MANIFEST = {
    'variants_biosamples': [
        'bluestarr_variants_biosamples_IGVFFI0818FMCC.jsonl',
        'bluestarr_variants_biosamples_IGVFFI1663LKVQ.jsonl',
        'bluestarr_variants_biosamples_IGVFFI3351LASN.jsonl',
        'bluestarr_variants_biosamples_IGVFFI5288RAAV.jsonl',
        'mpra_variants_biosamples_IGVFFI1323RCIE.jsonl',
        'mpra_variants_biosamples_IGVFFI2950PCZI_20260612.jsonl',
        'mpra_variants_biosamples_IGVFFI4134MFLL_20260612.jsonl',
        'mpra_variants_biosamples_IGVFFI4328UUGV_20260612.jsonl',
        'mpra_variants_biosamples_IGVFFI4378PZYI_20260612.jsonl',
        'mpra_variants_biosamples_IGVFFI4864MRQQ_20260612.jsonl',
        'mpra_variants_biosamples_IGVFFI7899LTDI_20260612.jsonl',
        'mpra_variants_biosamples_IGVFFI9553FYQF_20260612.jsonl',
        'mpra_variants_biosamples_IGVFFI9903YDJU_20260612.jsonl',
        'starr_seq_variants_biosamples_IGVFFI0144WAIH_20260625.jsonl',
        'starr_seq_variants_biosamples_IGVFFI0297DKAZ_20260625.jsonl',
        'starr_seq_variants_biosamples_IGVFFI2306GTSL_20260625.jsonl',
        'starr_seq_variants_biosamples_IGVFFI2408UWDF_20260625.jsonl',
        'starr_seq_variants_biosamples_IGVFFI2997DZFR_20260625.jsonl',
        'starr_seq_variants_biosamples_IGVFFI3264WHFL_20260625.jsonl',
        'starr_seq_variants_biosamples_IGVFFI4012FKNC_20260625.jsonl',
        'starr_seq_variants_biosamples_IGVFFI5057AAGP_20260625.jsonl',
        'starr_seq_variants_biosamples_IGVFFI5688VHRS_20260625.jsonl',
        'starr_seq_variants_biosamples_IGVFFI7256ZPXC_20260625.jsonl',
        'starr_seq_variants_biosamples_IGVFFI7580GCBV_20260625.jsonl',
        'starr_seq_variants_biosamples_IGVFFI7903VFKP_20260625.jsonl',
        'starr_seq_variants_biosamples_IGVFFI8452UFGC_20260625.jsonl',
        'starr_seq_variants_biosamples_IGVFFI9329ALOP_20260625.jsonl',
        'starr_seq_variants_biosamples_IGVFFI9893OTAT_20260625.jsonl'
    ],
    'variants_coding_variants': [
        'variants_coding_variants_vamp.jsonl',
        'variants_coding_variants_mutpred2_IGVFFI6893ZOAA_Met1_patched_20260219.jsonl',
        'variants_coding_variants_ESM_IGVFFI8105TNNO_Met1_patched_20260219.jsonl'
    ],
    'variants_genes': [
        'igvf_crispr_v2g_variant_genes_IGVFFI0524YUIL_06_24_26.jsonl',
        'igvf_crispr_v2g_variant_genes_IGVFFI1254NFRS_06_24_26.jsonl',
        'igvf_crispr_v2g_variant_genes_IGVFFI2440ESUS_06_24_26.jsonl',
        'igvf_crispr_v2g_variant_genes_IGVFFI2542METL_06_24_26.jsonl',
        'igvf_crispr_v2g_variant_genes_IGVFFI2554FKKN_06_24_26.jsonl',
        'igvf_crispr_v2g_variant_genes_IGVFFI3397AYBP_06_24_26.jsonl',
        'igvf_crispr_v2g_variant_genes_IGVFFI4057VSBO_06_24_26.jsonl',
        'igvf_crispr_v2g_variant_genes_IGVFFI4333XLOF_06_24_26.jsonl',
        'igvf_crispr_v2g_variant_genes_IGVFFI4769NVJT_06_24_26.jsonl',
        'igvf_crispr_v2g_variant_genes_IGVFFI4854DWEG_06_24_26.jsonl',
        'igvf_crispr_v2g_variant_genes_IGVFFI5097SDKA_06_24_26.jsonl',
        'igvf_crispr_v2g_variant_genes_IGVFFI5188DBPQ_06_24_26.jsonl',
        'igvf_crispr_v2g_variant_genes_IGVFFI5753CWJL_06_24_26.jsonl',
        'igvf_crispr_v2g_variant_genes_IGVFFI8101RHSC_06_24_26.jsonl',
        'igvf_crispr_v2g_variant_genes_IGVFFI9602ILPC_06_24_26.jsonl',
    ],
    'variants_phenotypes': [
        'variants_phenotypes_SGE_IGVFFI1361XVSO_20251205.jsonl',
        'variants_phenotypes_SGE_IGVFFI2810SLAX_20251205.jsonl',
        'variants_phenotypes_SGE_IGVFFI3125FMNW_20251205.jsonl',
        'variants_phenotypes_SGE_IGVFFI7008EHEH_20251205.jsonl',
        'variants_phenotypes_SGE_IGVFFI9138TFXQ_20251205.jsonl',
        'variants_phenotypes_SGE_IGVFFI9974PZRX_20251205.jsonl',
        'variants_phenotypes_cv2f_IGVFFI0332UGDD_20251205.jsonl',
        'variants_phenotypes_cv2f_IGVFFI1931RMNE_20251205.jsonl',
        'variants_phenotypes_cv2f_IGVFFI3063JRLI_20251205.jsonl',
        'variants_phenotypes_cv2f_IGVFFI3568PHLR_20251205.jsonl',
        'variants_phenotypes_cv2f_IGVFFI4594QVDO_20251205.jsonl',
        'variants_phenotypes_cv2f_IGVFFI5063ALUW_20251205.jsonl',
        'variants_phenotypes_cv2f_IGVFFI6811FTJA_20251205.jsonl',
        'variants_phenotypes_cv2f_IGVFFI7434QTLS_20251205.jsonl',
        'variants_phenotypes_cv2f_IGVFFI8473WYSV_20251205.jsonl',
        'variants_phenotypes_cv2f_IGVFFI8955JXUX_20251205.jsonl'
    ],
    'variants_proteins': [
        'SEMpl_IGVFFI0005WRQP_uniq_20251212.jsonl',
        'SEMpl_IGVFFI0015KDJC_uniq_20251212.jsonl',
        'SEMpl_IGVFFI0028UJBA_uniq_20251212.jsonl',
        'SEMpl_IGVFFI0099VKKV_uniq_20251212.jsonl',
        'SEMpl_IGVFFI0183ELIK_uniq_20251212.jsonl',
        'SEMpl_IGVFFI0192TXRL_uniq_20251212.jsonl',
        'SEMpl_IGVFFI0218RAAG_uniq_20251212.jsonl',
        'SEMpl_IGVFFI0223HERS_uniq_20251212.jsonl',
        'SEMpl_IGVFFI0229OTIW_uniq_20251212.jsonl',
        'SEMpl_IGVFFI0242HHHE_uniq_20251212.jsonl',
        'SEMpl_IGVFFI0263GIKA_uniq_20251212.jsonl',
        'SEMpl_IGVFFI0331TIUV_uniq_20251212.jsonl',
        'SEMpl_IGVFFI0361USLF_uniq_20251212.jsonl',
        'SEMpl_IGVFFI0503EMLJ_uniq_20251212.jsonl',
        'SEMpl_IGVFFI0510SLLZ_uniq_20251212.jsonl',
        'SEMpl_IGVFFI0523FFZM_uniq_20251212.jsonl',
        'SEMpl_IGVFFI0549NNHK_uniq_20251212.jsonl',
        'SEMpl_IGVFFI0555NMDT_uniq_20251212.jsonl',
        'SEMpl_IGVFFI0605BBUI_uniq_20251212.jsonl',
        'SEMpl_IGVFFI0665JZGT_uniq_20251212.jsonl',
        'SEMpl_IGVFFI0750ALAT_uniq_20251212.jsonl',
        'SEMpl_IGVFFI0769GKPS_uniq_20251212.jsonl',
        'SEMpl_IGVFFI0772IVMT_uniq_20251212.jsonl',
        'SEMpl_IGVFFI0778KCQJ_uniq_20251212.jsonl',
        'SEMpl_IGVFFI0808JQIY_uniq_20251212.jsonl',
        'SEMpl_IGVFFI0822XUMX_uniq_20251212.jsonl',
        'SEMpl_IGVFFI0838JPIS_uniq_20251212.jsonl',
        'SEMpl_IGVFFI0846SORV_uniq_20251212.jsonl',
        'SEMpl_IGVFFI0899ZNYF_uniq_20251212.jsonl',
        'SEMpl_IGVFFI0925JFEW_uniq_20251212.jsonl',
        'SEMpl_IGVFFI0926FVAB_uniq_20251212.jsonl',
        'SEMpl_IGVFFI0929ZGGT_uniq_20251212.jsonl',
        'SEMpl_IGVFFI1008APEI_uniq_20251212.jsonl',
        'SEMpl_IGVFFI1110FCWT_uniq_20251212.jsonl',
        'SEMpl_IGVFFI1119TUUD_uniq_20251212.jsonl',
        'SEMpl_IGVFFI1173JCYO_uniq_20251212.jsonl',
        'SEMpl_IGVFFI1173NNHA_uniq_20251212.jsonl',
        'SEMpl_IGVFFI1196VSYT_uniq_20251212.jsonl',
        'SEMpl_IGVFFI1249UMYA_uniq_20251212.jsonl',
        'SEMpl_IGVFFI1249WMDV_uniq_20251212.jsonl',
        'SEMpl_IGVFFI1252JAKC_uniq_20251212.jsonl',
        'SEMpl_IGVFFI1255MQGI_uniq_20251212.jsonl',
        'SEMpl_IGVFFI1315WBKZ_uniq_20251212.jsonl',
        'SEMpl_IGVFFI1325ALFW_uniq_20251212.jsonl',
        'SEMpl_IGVFFI1428VAGK_uniq_20251212.jsonl',
        'SEMpl_IGVFFI1437FXCK_uniq_20251212.jsonl',
        'SEMpl_IGVFFI1449EIUV_uniq_20251212.jsonl',
        'SEMpl_IGVFFI1529NYFP_uniq_20251212.jsonl',
        'SEMpl_IGVFFI1644DRIB_uniq_20251212.jsonl',
        'SEMpl_IGVFFI1645HVHO_uniq_20251212.jsonl',
        'SEMpl_IGVFFI1770WSQY_uniq_20251212.jsonl',
        'SEMpl_IGVFFI1815ZEXL_uniq_20251212.jsonl',
        'SEMpl_IGVFFI1848AIRV_uniq_20251212.jsonl',
        'SEMpl_IGVFFI1953DSSA_uniq_20251212.jsonl',
        'SEMpl_IGVFFI2112SWWC_uniq_20251212.jsonl',
        'SEMpl_IGVFFI2240BDUJ_uniq_20251212.jsonl',
        'SEMpl_IGVFFI2257XYLK_uniq_20251212.jsonl',
        'SEMpl_IGVFFI2290RGGS_uniq_20251212.jsonl',
        'SEMpl_IGVFFI2301QCFS_uniq_20251212.jsonl',
        'SEMpl_IGVFFI2359FSYI_uniq_20251212.jsonl',
        'SEMpl_IGVFFI2438YWOI_uniq_20251212.jsonl',
        'SEMpl_IGVFFI2565SVVP_uniq_20251212.jsonl',
        'SEMpl_IGVFFI2601TECN_uniq_20251212.jsonl',
        'SEMpl_IGVFFI2643ZFXH_uniq_20251212.jsonl',
        'SEMpl_IGVFFI2649RJCG_uniq_20251212.jsonl',
        'SEMpl_IGVFFI2719GLKZ_uniq_20251212.jsonl',
        'SEMpl_IGVFFI2725XPGY_uniq_20251212.jsonl',
        'SEMpl_IGVFFI2835LTLZ_uniq_20251212.jsonl',
        'SEMpl_IGVFFI2842SDNX_uniq_20251212.jsonl',
        'SEMpl_IGVFFI2860ATIO_uniq_20251212.jsonl',
        'SEMpl_IGVFFI2933JDJZ_uniq_20251212.jsonl',
        'SEMpl_IGVFFI2936TOTD_uniq_20251212.jsonl',
        'SEMpl_IGVFFI2943RVII_uniq_20251212.jsonl',
        'SEMpl_IGVFFI3020KKOA_uniq_20251212.jsonl',
        'SEMpl_IGVFFI3060WLBY_uniq_20251212.jsonl',
        'SEMpl_IGVFFI3063GXPH_uniq_20251212.jsonl',
        'SEMpl_IGVFFI3064GQGU_uniq_20251212.jsonl',
        'SEMpl_IGVFFI3075NGPG_uniq_20251212.jsonl',
        'SEMpl_IGVFFI3094STFB_uniq_20251212.jsonl',
        'SEMpl_IGVFFI3116SMJK_uniq_20251212.jsonl',
        'SEMpl_IGVFFI3147FUHR_uniq_20251212.jsonl',
        'SEMpl_IGVFFI3155EURE_uniq_20251212.jsonl',
        'SEMpl_IGVFFI3170UHEL_uniq_20251212.jsonl',
        'SEMpl_IGVFFI3215PNZF_uniq_20251212.jsonl',
        'SEMpl_IGVFFI3223XDNS_uniq_20251212.jsonl',
        'SEMpl_IGVFFI3224CAPC_uniq_20251212.jsonl',
        'SEMpl_IGVFFI3241OYHI_uniq_20251212.jsonl',
        'SEMpl_IGVFFI3465JZBF_uniq_20251212.jsonl',
        'SEMpl_IGVFFI3537RTNM_uniq_20251212.jsonl',
        'SEMpl_IGVFFI3549ZXTE_uniq_20251212.jsonl',
        'SEMpl_IGVFFI3561DGGN_uniq_20251212.jsonl',
        'SEMpl_IGVFFI3594NNNB_uniq_20251212.jsonl',
        'SEMpl_IGVFFI3646GQPY_uniq_20251212.jsonl',
        'SEMpl_IGVFFI3660PBTK_uniq_20251212.jsonl',
        'SEMpl_IGVFFI3667IMKG_uniq_20251212.jsonl',
        'SEMpl_IGVFFI3679JTFF_uniq_20251212.jsonl',
        'SEMpl_IGVFFI3709DGWP_uniq_20251212.jsonl',
        'SEMpl_IGVFFI3774ZXQK_uniq_20251212.jsonl',
        'SEMpl_IGVFFI3843UXMB_uniq_20251212.jsonl',
        'SEMpl_IGVFFI3860MACP_uniq_20251212.jsonl',
        'SEMpl_IGVFFI3875SFVE_uniq_20251212.jsonl',
        'SEMpl_IGVFFI4121DRAZ_uniq_20251212.jsonl',
        'SEMpl_IGVFFI4133DAHD_uniq_20251212.jsonl',
        'SEMpl_IGVFFI4261QMQM_uniq_20251212.jsonl',
        'SEMpl_IGVFFI4368UMHL_uniq_20251212.jsonl',
        'SEMpl_IGVFFI4424FXZD_uniq_20251212.jsonl',
        'SEMpl_IGVFFI4440LLKE_uniq_20251212.jsonl',
        'SEMpl_IGVFFI4574PKNH_uniq_20251212.jsonl',
        'SEMpl_IGVFFI4599KAKQ_uniq_20251212.jsonl',
        'SEMpl_IGVFFI4612CTQT_uniq_20251212.jsonl',
        'SEMpl_IGVFFI4625HCNX_uniq_20251212.jsonl',
        'SEMpl_IGVFFI4634SMEX_uniq_20251212.jsonl',
        'SEMpl_IGVFFI4727IXBE_uniq_20251212.jsonl',
        'SEMpl_IGVFFI4857VJZG_uniq_20251212.jsonl',
        'SEMpl_IGVFFI4858DYHK_uniq_20251212.jsonl',
        'SEMpl_IGVFFI4874THPU_uniq_20251212.jsonl',
        'SEMpl_IGVFFI4981VZMV_uniq_20251212.jsonl',
        'SEMpl_IGVFFI5003LERC_uniq_20251212.jsonl',
        'SEMpl_IGVFFI5015UCGN_uniq_20251212.jsonl',
        'SEMpl_IGVFFI5097LIKG_uniq_20251212.jsonl',
        'SEMpl_IGVFFI5183JEQL_uniq_20251212.jsonl',
        'SEMpl_IGVFFI5213EEGM_uniq_20251212.jsonl',
        'SEMpl_IGVFFI5225ZHMS_uniq_20251212.jsonl',
        'SEMpl_IGVFFI5288ONHJ_uniq_20251212.jsonl',
        'SEMpl_IGVFFI5305BUUY_uniq_20251212.jsonl',
        'SEMpl_IGVFFI5333DXTH_uniq_20251212.jsonl',
        'SEMpl_IGVFFI5441VTHS_uniq_20251212.jsonl',
        'SEMpl_IGVFFI5505ZGHX_uniq_20251212.jsonl',
        'SEMpl_IGVFFI5526HGAK_uniq_20251212.jsonl',
        'SEMpl_IGVFFI5588TUKN_uniq_20251212.jsonl',
        'SEMpl_IGVFFI5599GYKV_uniq_20251212.jsonl',
        'SEMpl_IGVFFI5643VYBU_uniq_20251212.jsonl',
        'SEMpl_IGVFFI5655HZCY_uniq_20251212.jsonl',
        'SEMpl_IGVFFI5659VKUZ_uniq_20251212.jsonl',
        'SEMpl_IGVFFI5678ATEA_uniq_20251212.jsonl',
        'SEMpl_IGVFFI5913KSIS_uniq_20251212.jsonl',
        'SEMpl_IGVFFI5944IXYP_uniq_20251212.jsonl',
        'SEMpl_IGVFFI6002DIKL_uniq_20251212.jsonl',
        'SEMpl_IGVFFI6031TECB_uniq_20251212.jsonl',
        'SEMpl_IGVFFI6044LKYT_uniq_20251212.jsonl',
        'SEMpl_IGVFFI6138ADED_uniq_20251212.jsonl',
        'SEMpl_IGVFFI6207XHHD_uniq_20251212.jsonl',
        'SEMpl_IGVFFI6324SSXZ_uniq_20251212.jsonl',
        'SEMpl_IGVFFI6336TCAK_uniq_20251212.jsonl',
        'SEMpl_IGVFFI6339BAFZ_uniq_20251212.jsonl',
        'SEMpl_IGVFFI6391SGVA_uniq_20251212.jsonl',
        'SEMpl_IGVFFI6465DJCT_uniq_20251212.jsonl',
        'SEMpl_IGVFFI6487PVTW_uniq_20251212.jsonl',
        'SEMpl_IGVFFI6505VPQR_uniq_20251212.jsonl',
        'SEMpl_IGVFFI6513TNQB_uniq_20251212.jsonl',
        'SEMpl_IGVFFI6560OWUF_uniq_20251212.jsonl',
        'SEMpl_IGVFFI6575ZLTY_uniq_20251212.jsonl',
        'SEMpl_IGVFFI6602IFPA_uniq_20251212.jsonl',
        'SEMpl_IGVFFI6639OVYQ_uniq_20251212.jsonl',
        'SEMpl_IGVFFI6654JKUD_uniq_20251212.jsonl',
        'SEMpl_IGVFFI6669ADFN_uniq_20251212.jsonl',
        'SEMpl_IGVFFI6706IYCA_uniq_20251212.jsonl',
        'SEMpl_IGVFFI6750YEUT_uniq_20251212.jsonl',
        'SEMpl_IGVFFI6756NYPI_uniq_20251212.jsonl',
        'SEMpl_IGVFFI6795PLES_uniq_20251212.jsonl',
        'SEMpl_IGVFFI6814YJNI_uniq_20251212.jsonl',
        'SEMpl_IGVFFI6837ZFSA_uniq_20251212.jsonl',
        'SEMpl_IGVFFI6904CLEP_uniq_20251212.jsonl',
        'SEMpl_IGVFFI6923RISY_uniq_20251212.jsonl',
        'SEMpl_IGVFFI6969OPHA_uniq_20251212.jsonl',
        'SEMpl_IGVFFI6992HUWN_uniq_20251212.jsonl',
        'SEMpl_IGVFFI7015OLEU_uniq_20251212.jsonl',
        'SEMpl_IGVFFI7043ZNKL_uniq_20251212.jsonl',
        'SEMpl_IGVFFI7057HTSB_uniq_20251212.jsonl',
        'SEMpl_IGVFFI7086SROC_uniq_20251212.jsonl',
        'SEMpl_IGVFFI7126IDUK_uniq_20251212.jsonl',
        'SEMpl_IGVFFI7128BVKK_uniq_20251212.jsonl',
        'SEMpl_IGVFFI7149DMFN_uniq_20251212.jsonl',
        'SEMpl_IGVFFI7154TQEI_uniq_20251212.jsonl',
        'SEMpl_IGVFFI7193DHHZ_uniq_20251212.jsonl',
        'SEMpl_IGVFFI7362VNGW_uniq_20251212.jsonl',
        'SEMpl_IGVFFI7515WLDL_uniq_20251212.jsonl',
        'SEMpl_IGVFFI7529KNOP_uniq_20251212.jsonl',
        'SEMpl_IGVFFI7611WGCY_uniq_20251212.jsonl',
        'SEMpl_IGVFFI7711IAAN_uniq_20251212.jsonl',
        'SEMpl_IGVFFI7744KFJI_uniq_20251212.jsonl',
        'SEMpl_IGVFFI7766RJHL_uniq_20251212.jsonl',
        'SEMpl_IGVFFI7891XOCU_uniq_20251212.jsonl',
        'SEMpl_IGVFFI7896UGFF_uniq_20251212.jsonl',
        'SEMpl_IGVFFI7924MXSH_uniq_20251212.jsonl',
        'SEMpl_IGVFFI7957CZEM_uniq_20251212.jsonl',
        'SEMpl_IGVFFI7979KDIB_uniq_20251212.jsonl',
        'SEMpl_IGVFFI8085AQOC_uniq_20251212.jsonl',
        'SEMpl_IGVFFI8101CHLZ_uniq_20251212.jsonl',
        'SEMpl_IGVFFI8181UDYU_uniq_20251212.jsonl',
        'SEMpl_IGVFFI8186NSCK_uniq_20251212.jsonl',
        'SEMpl_IGVFFI8253JNZF_uniq_20251212.jsonl',
        'SEMpl_IGVFFI8316ARFX_uniq_20251212.jsonl',
        'SEMpl_IGVFFI8356LQFY_uniq_20251212.jsonl',
        'SEMpl_IGVFFI8471XMZK_uniq_20251212.jsonl',
        'SEMpl_IGVFFI8560JJZN_uniq_20251212.jsonl',
        'SEMpl_IGVFFI8595BDKV_uniq_20251212.jsonl',
        'SEMpl_IGVFFI8595WEZO_uniq_20251212.jsonl',
        'SEMpl_IGVFFI8596FIYT_uniq_20251212.jsonl',
        'SEMpl_IGVFFI8642KPVX_uniq_20251212.jsonl',
        'SEMpl_IGVFFI8775GOTM_uniq_20251212.jsonl',
        'SEMpl_IGVFFI8803YRJY_uniq_20251212.jsonl',
        'SEMpl_IGVFFI8844EMRM_uniq_20251212.jsonl',
        'SEMpl_IGVFFI9070IQTF_uniq_20251212.jsonl',
        'SEMpl_IGVFFI9078AJKM_uniq_20251212.jsonl',
        'SEMpl_IGVFFI9104WCTL_uniq_20251212.jsonl',
        'SEMpl_IGVFFI9131SDMB_uniq_20251212.jsonl',
        'SEMpl_IGVFFI9153FJWU_uniq_20251212.jsonl',
        'SEMpl_IGVFFI9370YOQC_uniq_20251212.jsonl',
        'SEMpl_IGVFFI9386ROUR_uniq_20251212.jsonl',
        'SEMpl_IGVFFI9435JKMR_uniq_20251212.jsonl',
        'SEMpl_IGVFFI9469SOFV_uniq_20251212.jsonl',
        'SEMpl_IGVFFI9517DJFS_uniq_20251212.jsonl',
        'SEMpl_IGVFFI9546GTAT_uniq_20251212.jsonl',
        'SEMpl_IGVFFI9547UXPP_uniq_20251212.jsonl',
        'SEMpl_IGVFFI9548VTEW_uniq_20251212.jsonl',
        'SEMpl_IGVFFI9572ZTGA_uniq_20251212.jsonl',
        'SEMpl_IGVFFI9717LNFQ_uniq_20251212.jsonl',
        'SEMpl_IGVFFI9769XKUE_uniq_20251212.jsonl',
        'SEMpl_IGVFFI9782KUPG_uniq_20251212.jsonl',
        'SEMpl_IGVFFI9884GLDJ_uniq_20251212.jsonl',
        'SEMpl_IGVFFI9949CVXP_uniq_20251212.jsonl',
        'SEMpl_IGVFFI9987BMOI_uniq_20251212.jsonl'
    ]
}

FILTER_FIELD = 'source'
FILTER_VALUE = 'IGVF'


def strip_id_prefix(value):
    """Strip the leading 'collection/' prefix from an ArangoDB _from/_to
    style ID, e.g. 'variants/12345' -> '12345'."""
    if value and '/' in value:
        return value.split('/', 1)[1]
    return value


def list_matching_keys(s3, bucket, prefix, file_pattern, manifest=None):
    """Determine which S3 keys to process for one collection prefix.

    If the (hardcoded) manifest has a non-empty entry for this prefix,
    use that explicit list of filenames (joined onto the prefix) instead
    of listing the bucket -- this lets you pick exactly which files to
    pull per folder rather than everything matching a glob. An empty or
    missing entry falls back to pattern-based listing.
    """
    if manifest and manifest.get(prefix):
        filenames = manifest[prefix]
        return [f'{prefix}/{filename}' for filename in filenames]

    keys = []
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix=f'{prefix}/'):
        for obj in page.get('Contents', []):
            key = obj['Key']
            filename = key.rsplit('/', 1)[-1]
            if fnmatch.fnmatch(filename, file_pattern):
                keys.append(key)
    return keys


def iter_jsonl_lines(s3, bucket, key):
    """Stream a plain-text JSONL object from S3 line by line without
    loading the whole file into memory."""
    obj = s3.get_object(Bucket=bucket, Key=key)
    body = obj['Body']  # botocore StreamingBody
    for line in body.iter_lines():
        yield line


def process_collection(s3, bucket, prefix, file_pattern, arango_collection,
                       insert_batch_size, stats, manifest=None):
    """Stream all matching JSONL files for one collection prefix, filter
    records, and batch-insert unique variant IDs into ArangoDB."""
    keys = list_matching_keys(s3, bucket, prefix, file_pattern, manifest)
    source_desc = 'hardcoded MANIFEST' if manifest and manifest.get(
        prefix) else f"pattern '{file_pattern}'"
    print(f'\n{prefix}: {len(keys)} file(s) selected via {source_desc} under s3://{bucket}/{prefix}/')

    if not keys:
        return

    start = time.perf_counter()
    scanned = 0
    matched = 0
    inserted = 0
    batch = []

    def flush_batch():
        nonlocal inserted
        if not batch:
            return
        result = arango_collection.insert_many(
            batch, overwrite_mode='ignore', silent=True
        )
        inserted += len(batch)
        batch.clear()
        return result

    for i, key in enumerate(keys, start=1):
        print(f'  [{i}/{len(keys)}] {key}', flush=True)
        file_scanned = 0
        file_matched = 0
        try:
            for raw_line in iter_jsonl_lines(s3, bucket, key):
                if not raw_line:
                    continue
                file_scanned += 1
                try:
                    doc = json.loads(raw_line)
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    print(
                        f'    !! skipping unparsable line: {e}', file=sys.stderr)
                    continue

                if (
                    doc.get(FILTER_FIELD) == FILTER_VALUE
                ):
                    variant_id = strip_id_prefix(doc.get('_from'))
                    if variant_id:
                        file_matched += 1
                        batch.append({'_key': variant_id})
                        if len(batch) >= insert_batch_size:
                            flush_batch()
        except Exception as e:
            print(f'    !! ERROR reading {key}: {e}', file=sys.stderr)
            continue

        scanned += file_scanned
        matched += file_matched
        print(
            f'    -> scanned {file_scanned:,} records, matched {file_matched:,}')

    flush_batch()
    elapsed = time.perf_counter() - start

    stats.append(
        {
            'collection': prefix,
            'files': len(keys),
            'scanned': scanned,
            'matched': matched,
            'inserted_attempted': inserted,
            'elapsed': elapsed,
        }
    )
    print(
        f'  {prefix} done: {scanned:,} scanned, {matched:,} matched, '
        f'{inserted:,} insert attempts in {elapsed:.1f}s'
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description='Stream variants_* JSONL backups from S3, filter to '
        'IGVF observed-data records, and load unique variant IDs into '
        'an ArangoDB collection.'
    )
    parser.add_argument('--bucket', required=True, help='S3 bucket name')
    parser.add_argument(
        '--prefixes',
        default=','.join(DEFAULT_PREFIXES),
        help='Comma-separated list of S3 key prefixes / collection folder '
        f"names (default: {','.join(DEFAULT_PREFIXES)})",
    )
    parser.add_argument(
        '--file-pattern',
        default='*.jsonl',
        help='Glob pattern to restrict which filenames are processed '
        'under each prefix when no MANIFEST entry exists for it '
        '(default: *.jsonl)',
    )
    parser.add_argument('--region', default=None, help='AWS region (optional)')
    parser.add_argument(
        '--anonymous',
        action='store_true',
        help='Use anonymous/unsigned S3 access (for public buckets, no '
        'AWS credentials needed)',
    )

    parser.add_argument('--host', required=True, help='ArangoDB host URL')
    parser.add_argument('--db', dest='db_name',
                        required=True, help='Database name')
    parser.add_argument('--username', required=True, help='ArangoDB username')
    parser.add_argument('--password', required=True, help='ArangoDB password')
    parser.add_argument(
        '--target-collection',
        default='variants_IGVF',
        help='ArangoDB collection to insert unique variant IDs into '
        '(default: variants_IGVF). Created automatically if missing.',
    )
    parser.add_argument(
        '--insert-batch-size',
        type=int,
        default=5000,
        help='Number of documents per insert_many() call (default: 5000)',
    )
    parser.add_argument(
        '--request-timeout',
        type=float,
        default=120,
        help='HTTP request timeout in seconds for ArangoDB calls (default: 120)',
    )
    return parser.parse_args()


def main():
    args = parse_args()
    prefixes = [p.strip() for p in args.prefixes.split(',') if p.strip()]

    s3_config = Config(signature_version=UNSIGNED) if args.anonymous else None
    s3 = boto3.client('s3', region_name=args.region, config=s3_config)

    http_client = DefaultHTTPClient()
    http_client.request_timeout = args.request_timeout
    client = ArangoClient(hosts=args.host, http_client=http_client)
    db = client.db(args.db_name, username=args.username,
                   password=args.password)

    if not db.has_collection(args.target_collection):
        print(f"Creating collection '{args.target_collection}' ...")
        db.create_collection(args.target_collection)
    arango_collection = db.collection(args.target_collection)

    stats = []
    overall_start = time.perf_counter()
    for prefix in prefixes:
        process_collection(
            s3,
            args.bucket,
            prefix,
            args.file_pattern,
            arango_collection,
            args.insert_batch_size,
            stats,
            manifest=MANIFEST,
        )
    overall_elapsed = time.perf_counter() - overall_start

    print('\nSummary:')
    for s in stats:
        print(
            f"  {s['collection']}: {s['files']} file(s), "
            f"{s['scanned']:,} scanned, {s['matched']:,} matched, "
            f"{s['elapsed']:.1f}s"
        )

    total_matched = sum(s['matched'] for s in stats)
    print(f'\nTotal records matched (pre-dedup): {total_matched:,}')
    print(f'Total wall time: {overall_elapsed:.1f}s')

    final_count = arango_collection.count()
    print(
        f"Final unique document count in '{args.target_collection}': {final_count:,}")


if __name__ == '__main__':
    main()
