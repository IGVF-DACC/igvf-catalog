import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { QUERY_LIMIT } from '../../../constants'
import { descriptions } from '../descriptions'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { db } from '../../../database'
import { getSchema } from '../schema'

const MAX_PAGE_SIZE = 500

const filesFilesetsSchema = getSchema('data/schemas/nodes/files_filesets.FileFileSet.json')
const filesFilesetsCollectionName = filesFilesetsSchema.db_collection_name as string

const LABS = [
  'alan-boyle',
  'bill-majoros',
  'charles-gersbach',
  'j-michael-cherry',
  'jesse-engreitz',
  'kushal-dey',
  'lea-starita',
  'mark-craven',
  'nadav-ahituv',
  'predrag-radivojac',
  'roderic-guigo',
  'tim-reddy',
  'zhiping-weng'
] as const

const ASSAYS = [
  'ATAC-seq',
  'CAGE',
  'ChIA-PET',
  'ChIP-seq',
  'CRISPR FACS screen',
  'DNase-seq',
  'HiC',
  'lentiMPRA',
  'Mint-ChIP-seq',
  'MPRA',
  'Perturb-seq',
  'polyA plus RNA-seq',
  'RNA-seq',
  'SGE',
  'STARR-seq',
  'Variant-EFFECTS'
] as const

const METHOD = [
  'binding effect prediction for AHR using SEMVAR v1.0.0',
  'binding effect prediction for AHR, ARNT, HIF1A using SEMVAR v1.0.0',
  'binding effect prediction for ARID3A using SEMVAR v1.0.0',
  'binding effect prediction for ARNT using SEMVAR v1.0.0',
  'binding effect prediction for ARNTL using SEMVAR v1.0.0',
  'binding effect prediction for ATF1 using SEMVAR v1.0.0',
  'binding effect prediction for ATF2 using SEMVAR v1.0.0',
  'binding effect prediction for ATF2, JUN using SEMVAR v1.0.0',
  'binding effect prediction for ATF3 using SEMVAR v1.0.0',
  'binding effect prediction for ATF4 using SEMVAR v1.0.0',
  'binding effect prediction for ATF4, CREB1 using SEMVAR v1.0.0',
  'binding effect prediction for ATF6 using SEMVAR v1.0.0',
  'binding effect prediction for BACH1 using SEMVAR v1.0.0',
  'binding effect prediction for BACH2 using SEMVAR v1.0.0',
  'binding effect prediction for BATF using SEMVAR v1.0.0',
  'binding effect prediction for BCL11A using SEMVAR v1.0.0',
  'binding effect prediction for BCL6 using SEMVAR v1.0.0',
  'binding effect prediction for BHLHA15 using SEMVAR v1.0.0',
  'binding effect prediction for BHLHE40 using SEMVAR v1.0.0',
  'binding effect prediction for CBFB using SEMVAR v1.0.0',
  'binding effect prediction for CEBPA using SEMVAR v1.0.0',
  'binding effect prediction for CEBPB using SEMVAR v1.0.0',
  'binding effect prediction for CEBPD using SEMVAR v1.0.0',
  'binding effect prediction for CEBPG using SEMVAR v1.0.0',
  'binding effect prediction for CLOCK using SEMVAR v1.0.0',
  'binding effect prediction for CREB1 using SEMVAR v1.0.0',
  'binding effect prediction for CREB3L1 using SEMVAR v1.0.0',
  'binding effect prediction for CREM using SEMVAR v1.0.0',
  'binding effect prediction for CTCF using SEMVAR v1.0.0',
  'binding effect prediction for CUX1 using SEMVAR v1.0.0',
  'binding effect prediction for DBP using SEMVAR v1.0.0',
  'binding effect prediction for E2F1 using SEMVAR v1.0.0',
  'binding effect prediction for E2F1, RB1, TFDP1 using SEMVAR v1.0.0',
  'binding effect prediction for E2F1, TFDP1 using SEMVAR v1.0.0',
  'binding effect prediction for E2F1, TFDP2 using SEMVAR v1.0.0',
  'binding effect prediction for E2F2 using SEMVAR v1.0.0',
  'binding effect prediction for E2F3 using SEMVAR v1.0.0',
  'binding effect prediction for E2F4 using SEMVAR v1.0.0',
  'binding effect prediction for E2F4, TFDP1 using SEMVAR v1.0.0',
  'binding effect prediction for E2F4, TFDP2 using SEMVAR v1.0.0',
  'binding effect prediction for E2F5 using SEMVAR v1.0.0',
  'binding effect prediction for E2F6 using SEMVAR v1.0.0',
  'binding effect prediction for E2F7 using SEMVAR v1.0.0',
  'binding effect prediction for EBF1 using SEMVAR v1.0.0',
  'binding effect prediction for EGR1 using SEMVAR v1.0.0',
  'binding effect prediction for ELF1 using SEMVAR v1.0.0',
  'binding effect prediction for ELF2 using SEMVAR v1.0.0',
  'binding effect prediction for ELF3 using SEMVAR v1.0.0',
  'binding effect prediction for ELF4 using SEMVAR v1.0.0',
  'binding effect prediction for ELK1 using SEMVAR v1.0.0',
  'binding effect prediction for ELK4 using SEMVAR v1.0.0',
  'binding effect prediction for ESR1 using SEMVAR v1.0.0',
  'binding effect prediction for ESRRA using SEMVAR v1.0.0',
  'binding effect prediction for ETS1 using SEMVAR v1.0.0',
  'binding effect prediction for ETV1 using SEMVAR v1.0.0',
  'binding effect prediction for ETV4 using SEMVAR v1.0.0',
  'binding effect prediction for ETV5 using SEMVAR v1.0.0',
  'binding effect prediction for ETV6 using SEMVAR v1.0.0',
  'binding effect prediction for FEZF1 using SEMVAR v1.0.0',
  'binding effect prediction for FOS using SEMVAR v1.0.0',
  'binding effect prediction for FOSL1 using SEMVAR v1.0.0',
  'binding effect prediction for FOSL2 using SEMVAR v1.0.0',
  'binding effect prediction for FOXA1 using SEMVAR v1.0.0',
  'binding effect prediction for FOXA2 using SEMVAR v1.0.0',
  'binding effect prediction for FOXA3 using SEMVAR v1.0.0',
  'binding effect prediction for FOXC1 using SEMVAR v1.0.0',
  'binding effect prediction for FOXJ2 using SEMVAR v1.0.0',
  'binding effect prediction for FOXJ3 using SEMVAR v1.0.0',
  'binding effect prediction for FOXK1 using SEMVAR v1.0.0',
  'binding effect prediction for FOXM1 using SEMVAR v1.0.0',
  'binding effect prediction for FOXO1 using SEMVAR v1.0.0',
  'binding effect prediction for FOXP1 using SEMVAR v1.0.0',
  'binding effect prediction for FOXP2 using SEMVAR v1.0.0',
  'binding effect prediction for FOXQ1 using SEMVAR v1.0.0',
  'binding effect prediction for GABPA using SEMVAR v1.0.0',
  'binding effect prediction for GATA1 using SEMVAR v1.0.0',
  'binding effect prediction for GATA2 using SEMVAR v1.0.0',
  'binding effect prediction for GATA3 using SEMVAR v1.0.0',
  'binding effect prediction for GATA4 using SEMVAR v1.0.0',
  'binding effect prediction for GFI1 using SEMVAR v1.0.0',
  'binding effect prediction for GFI1B using SEMVAR v1.0.0',
  'binding effect prediction for GRHL2 using SEMVAR v1.0.0',
  'binding effect prediction for HINFP using SEMVAR v1.0.0',
  'binding effect prediction for HLF using SEMVAR v1.0.0',
  'binding effect prediction for HLTF using SEMVAR v1.0.0',
  'binding effect prediction for HNF1A using SEMVAR v1.0.0',
  'binding effect prediction for HNF1B using SEMVAR v1.0.0',
  'binding effect prediction for HNF4A using SEMVAR v1.0.0',
  'binding effect prediction for HNF4A, NR2F2 using SEMVAR v1.0.0',
  'binding effect prediction for HNF4G using SEMVAR v1.0.0',
  'binding effect prediction for HOXA10 using SEMVAR v1.0.0',
  'binding effect prediction for HOXA9 using SEMVAR v1.0.0',
  'binding effect prediction for HOXB7 using SEMVAR v1.0.0',
  'binding effect prediction for HSF1 using SEMVAR v1.0.0',
  'binding effect prediction for HSF2 using SEMVAR v1.0.0',
  'binding effect prediction for IKZF1 using SEMVAR v1.0.0',
  'binding effect prediction for IRF9 using SEMVAR v1.0.0',
  'binding effect prediction for JUN using SEMVAR v1.0.0',
  'binding effect prediction for JUNB using SEMVAR v1.0.0',
  'binding effect prediction for JUND using SEMVAR v1.0.0',
  'binding effect prediction for KLF1 using SEMVAR v1.0.0',
  'binding effect prediction for KLF12 using SEMVAR v1.0.0',
  'binding effect prediction for KLF14 using SEMVAR v1.0.0',
  'binding effect prediction for KLF5 using SEMVAR v1.0.0',
  'binding effect prediction for KLF7 using SEMVAR v1.0.0',
  'binding effect prediction for KLF8 using SEMVAR v1.0.0',
  'binding effect prediction for KLF9 using SEMVAR v1.0.0',
  'binding effect prediction for LEF1 using SEMVAR v1.0.0',
  'binding effect prediction for MAX using SEMVAR v1.0.0',
  'binding effect prediction for MAX, MYC using SEMVAR v1.0.0',
  'binding effect prediction for MBD2 using SEMVAR v1.0.0',
  'binding effect prediction for MECOM using SEMVAR v1.0.0',
  'binding effect prediction for MEF2A using SEMVAR v1.0.0',
  'binding effect prediction for MEF2B using SEMVAR v1.0.0',
  'binding effect prediction for MEF2C using SEMVAR v1.0.0',
  'binding effect prediction for MEF2D using SEMVAR v1.0.0',
  'binding effect prediction for MEIS1 using SEMVAR v1.0.0',
  'binding effect prediction for MEIS2 using SEMVAR v1.0.0',
  'binding effect prediction for MITF using SEMVAR v1.0.0',
  'binding effect prediction for MXI1 using SEMVAR v1.0.0',
  'binding effect prediction for MYB using SEMVAR v1.0.0',
  'binding effect prediction for MYC using SEMVAR v1.0.0',
  'binding effect prediction for MZF1 using SEMVAR v1.0.0',
  'binding effect prediction for NANOG using SEMVAR v1.0.0',
  'binding effect prediction for NEUROD1 using SEMVAR v1.0.0',
  'binding effect prediction for NFATC3 using SEMVAR v1.0.0',
  'binding effect prediction for NFE2 using SEMVAR v1.0.0',
  'binding effect prediction for NFE2L2 using SEMVAR v1.0.0',
  'binding effect prediction for NFIA using SEMVAR v1.0.0',
  'binding effect prediction for NFIC using SEMVAR v1.0.0',
  'binding effect prediction for NFIL3 using SEMVAR v1.0.0',
  'binding effect prediction for NFKB1 using SEMVAR v1.0.0',
  'binding effect prediction for NFYA using SEMVAR v1.0.0',
  'binding effect prediction for NFYB using SEMVAR v1.0.0',
  'binding effect prediction for NFYC using SEMVAR v1.0.0',
  'binding effect prediction for NKX3-1 using SEMVAR v1.0.0',
  'binding effect prediction for NR2C1 using SEMVAR v1.0.0',
  'binding effect prediction for NR2C2 using SEMVAR v1.0.0',
  'binding effect prediction for NR2F1 using SEMVAR v1.0.0',
  'binding effect prediction for NR2F2 using SEMVAR v1.0.0',
  'binding effect prediction for NR3C1 using SEMVAR v1.0.0',
  'binding effect prediction for NR5A1 using SEMVAR v1.0.0',
  'binding effect prediction for NR5A2 using SEMVAR v1.0.0',
  'binding effect prediction for NRF1 using SEMVAR v1.0.0',
  'binding effect prediction for ONECUT1 using SEMVAR v1.0.0',
  'binding effect prediction for OSR2 using SEMVAR v1.0.0',
  'binding effect prediction for OTX2 using SEMVAR v1.0.0',
  'binding effect prediction for OVOL1 using SEMVAR v1.0.0',
  'binding effect prediction for PATZ1 using SEMVAR v1.0.0',
  'binding effect prediction for PBX1 using SEMVAR v1.0.0',
  'binding effect prediction for PBX2 using SEMVAR v1.0.0',
  'binding effect prediction for PBX3 using SEMVAR v1.0.0',
  'binding effect prediction for PKNOX1 using SEMVAR v1.0.0',
  'binding effect prediction for POU2F1 using SEMVAR v1.0.0',
  'binding effect prediction for POU2F2 using SEMVAR v1.0.0',
  'binding effect prediction for POU5F1 using SEMVAR v1.0.0',
  'binding effect prediction for PPARA using SEMVAR v1.0.0',
  'binding effect prediction for PPARG using SEMVAR v1.0.0',
  'binding effect prediction for PRDM1 using SEMVAR v1.0.0',
  'binding effect prediction for PRDM6 using SEMVAR v1.0.0',
  'binding effect prediction for RBPJ using SEMVAR v1.0.0',
  'binding effect prediction for REL using SEMVAR v1.0.0',
  'binding effect prediction for RELA using SEMVAR v1.0.0',
  'binding effect prediction for RELB using SEMVAR v1.0.0',
  'binding effect prediction for RFX3 using SEMVAR v1.0.0',
  'binding effect prediction for RUNX1 using SEMVAR v1.0.0',
  'binding effect prediction for RUNX3 using SEMVAR v1.0.0',
  'binding effect prediction for RXRA using SEMVAR v1.0.0',
  'binding effect prediction for RXRB using SEMVAR v1.0.0',
  'binding effect prediction for SF1 using SEMVAR v1.0.0',
  'binding effect prediction for SIX1 using SEMVAR v1.0.0',
  'binding effect prediction for SMAD2 using SEMVAR v1.0.0',
  'binding effect prediction for SMAD3 using SEMVAR v1.0.0',
  'binding effect prediction for SMAD4 using SEMVAR v1.0.0',
  'binding effect prediction for SMARCA5 using SEMVAR v1.0.0',
  'binding effect prediction for SNAI2 using SEMVAR v1.0.0',
  'binding effect prediction for SOX13 using SEMVAR v1.0.0',
  'binding effect prediction for SOX5 using SEMVAR v1.0.0',
  'binding effect prediction for SP1 using SEMVAR v1.0.0',
  'binding effect prediction for SPI1 using SEMVAR v1.0.0',
  'binding effect prediction for SPIB using SEMVAR v1.0.0',
  'binding effect prediction for SREBF1 using SEMVAR v1.0.0',
  'binding effect prediction for SREBF2 using SEMVAR v1.0.0',
  'binding effect prediction for SRF using SEMVAR v1.0.0',
  'binding effect prediction for SRY using SEMVAR v1.0.0',
  'binding effect prediction for STAT1 using SEMVAR v1.0.0',
  'binding effect prediction for STAT3 using SEMVAR v1.0.0',
  'binding effect prediction for STAT5A using SEMVAR v1.0.0',
  'binding effect prediction for STAT5B using SEMVAR v1.0.0',
  'binding effect prediction for STAT6 using SEMVAR v1.0.0',
  'binding effect prediction for TAF1 using SEMVAR v1.0.0',
  'binding effect prediction for TAL1 using SEMVAR v1.0.0',
  'binding effect prediction for TAL1, TCF3 using SEMVAR v1.0.0',
  'binding effect prediction for TAL1, TCF4 using SEMVAR v1.0.0',
  'binding effect prediction for TBP using SEMVAR v1.0.0',
  'binding effect prediction for TBX21 using SEMVAR v1.0.0',
  'binding effect prediction for TCF12 using SEMVAR v1.0.0',
  'binding effect prediction for TCF3 using SEMVAR v1.0.0',
  'binding effect prediction for TCF4 using SEMVAR v1.0.0',
  'binding effect prediction for TCF7 using SEMVAR v1.0.0',
  'binding effect prediction for TCF7L2 using SEMVAR v1.0.0',
  'binding effect prediction for TEAD1 using SEMVAR v1.0.0',
  'binding effect prediction for TEAD4 using SEMVAR v1.0.0',
  'binding effect prediction for TFAP2B using SEMVAR v1.0.0',
  'binding effect prediction for TFAP2E using SEMVAR v1.0.0',
  'binding effect prediction for TFAP4 using SEMVAR v1.0.0',
  'binding effect prediction for TFDP1 using SEMVAR v1.0.0',
  'binding effect prediction for TFE3 using SEMVAR v1.0.0',
  'binding effect prediction for TGIF2 using SEMVAR v1.0.0',
  'binding effect prediction for THRA using SEMVAR v1.0.0',
  'binding effect prediction for USF1 using SEMVAR v1.0.0',
  'binding effect prediction for YY1 using SEMVAR v1.0.0',
  'binding effect prediction for ZBTB14 using SEMVAR v1.0.0',
  'binding effect prediction for ZBTB33 using SEMVAR v1.0.0',
  'binding effect prediction for ZBTB48 using SEMVAR v1.0.0',
  'binding effect prediction for ZBTB7A using SEMVAR v1.0.0',
  'binding effect prediction for ZEB1 using SEMVAR v1.0.0',
  'binding effect prediction for ZFX using SEMVAR v1.0.0',
  'binding effect prediction for ZNF18 using SEMVAR v1.0.0',
  'binding effect prediction for ZNF217 using SEMVAR v1.0.0',
  'binding effect prediction for ZNF281 using SEMVAR v1.0.0',
  'binding effect prediction for ZSCAN4 using SEMVAR v1.0.0',
  'candidate Cis-Regulatory Elements',
  'caQTLs',
  'CRISPR FACS screen',
  'element gene regulatory interaction predictions using Distal regulation ENCODE-rE2G',
  'element gene regulatory interaction predictions using EPIraction',
  'element gene regulatory interactions using DistalRegulationCRISPRdata',
  'functional effect prediction on scope of genome-wide using cV2F v1.0.0',
  'functional effect prediction on scope of genome-wide using ESM-1v variant scoring workflow v1.0.0',
  'functional effect prediction on scope of loci using BlueSTARR v0.1.1',
  'functional effect prediction using MutPred2 v0.0.0.0',
  'GRCh38 elements',
  'lentiMPRA',
  'MPRA',
  'Perturb-seq',
  'SGE',
  'STARR-seq',
  'Variant-EFFECTS'
] as const

const SOFTWARE = [
  'BCalm',
  'BEDTools',
  'bigWigAverageOverBed',
  'BlueSTARR',
  'cV2F',
  'Distal regulation ENCODE-rE2G',
  'DistalRegulationCRISPRdata',
  'EPIraction',
  'ESM-1v variant scoring workflow',
  'FRACTEL',
  'MPRAflow tsv-to-bed',
  'MutPred2',
  'SEMVAR',
  'SGE Pipeline'
] as const

const SOURCE = ['ENCODE', 'IGVF'] as const

const CLASS = ['prediction', 'experiment', 'integrative analysis'] as const

const filesFilesetsQueryFormat = z.object({
  file_fileset_id: z.string().optional(),
  fileset_id: z.string().optional(),
  lab: z.enum(LABS).optional(),
  preferred_assay_title: z.enum(ASSAYS).optional(),
  method: z.enum(METHOD).optional(),
  donor_id: z.string().optional(),
  sample_term: z.string().optional(),
  sample_summary: z.string().optional(),
  software: z.enum(SOFTWARE).optional(),
  source: z.enum(SOURCE).optional(),
  class: z.enum(CLASS).optional(),
  page: z.number().default(0),
  limit: z.number().optional()
// eslint-disable-next-line @typescript-eslint/naming-convention
}).transform(({ preferred_assay_title, fileset_id, file_fileset_id, donor_id, sample_term, sample_summary, ...rest }) => ({
  _key: file_fileset_id,
  file_set_id: fileset_id,
  preferred_assay_titles: preferred_assay_title,
  donors: donor_id,
  samples: sample_term,
  simple_sample_summaries: sample_summary,
  ...rest
}))

const filesFilesetsFormat = z.object({
  _id: z.string(),
  file_set_id: z.string(),
  lab: z.string(),
  preferred_assay_titles: z.array(z.string()).nullish(),
  assay_term_ids: z.array(z.string()).nullish(),
  method: z.string(),
  class: z.string(),
  software: z.array(z.string()).nullish(),
  samples: z.array(z.string()).nullish(),
  sample_ids: z.array(z.string()).nullish(),
  simple_sample_summaries: z.array(z.string()).nullish(),
  donors: z.array(z.string()).nullish(),
  source: z.string()
})

async function filesFilesetsSearch (input: paramsFormatType): Promise<any[]> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  if (input.samples !== undefined) {
    input.samples = `ontology_terms/${input.samples as string}`
  }

  if (input.donors !== undefined) {
    input.donors = `donors/${input.donors as string}`
  }

  let filterBy = ''
  const filterSts = getFilterStatements(filesFilesetsSchema, input)
  if (filterSts !== '') {
    filterBy = `FILTER ${filterSts}`
  }

  const query = `
    FOR record IN ${filesFilesetsCollectionName}
    ${filterBy}
    SORT record._key
    LIMIT ${input.page as number * limit}, ${limit}
    RETURN { ${getDBReturnStatements(filesFilesetsSchema)} }
  `

  return await (await db.query(query)).all()
}

const filesFilesets = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/files-filesets', description: descriptions.files_fileset } })
  .input(filesFilesetsQueryFormat)
  .output(z.array(filesFilesetsFormat))
  .query(async ({ input }) => await filesFilesetsSearch(input))

export const filesFilesetsRouters = {
  filesFilesets
}
