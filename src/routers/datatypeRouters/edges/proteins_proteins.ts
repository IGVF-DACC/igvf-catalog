import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { proteinByIDQuery, proteinFormat } from '../nodes/proteins'
import { descriptions } from '../descriptions'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { commonEdgeParamsFormat, proteinsCommonQueryFormat } from '../params'

const MAX_PAGE_SIZE = 250

const schema = loadSchemaConfig()

const proteinProteinSchema = schema['protein to protein interaction']
const proteinSchema = schema.protein

const sources = z.enum(['IntAct', 'BioGRID', 'BioGRID; IntAct'])

const detectionMethods = z.enum([
  '3D electron microscopy',
  'acetylase assay',
  'adp ribosylase assay',
  'affinity chromatography technology',
  'affinity technology',
  'aggregation assay',
  'amplified luminescent proximity homogeneous assay',
  'ampylation assay',
  'anti bait coimmunoprecipitation',
  'anti tag coimmunoprecipitation',
  'antibody array',
  'array technology',
  'atomic force microscopy',
  'atpase assay',
  'avexis',
  'barcode fusion genetics two hybrid',
  'bead aggregation assay',
  'beta galactosidase complementation',
  'beta lactamase complementation',
  'bimolecular fluorescence complementation',
  'bio-layer interferometry',
  'biochemical',
  'bioluminescence resonance energy transfer',
  'biophysical',
  'biosensor',
  'blue native page',
  'chromatin immunoprecipitation array',
  'chromatin immunoprecipitation assay',
  'chromatography technology',
  'circular dichroism',
  'classical fluorescence spectroscopy',
  'cleavage assay',
  'coimmunoprecipitation',
  'comigration in gel electrophoresis',
  'comigration in non denaturing gel electrophoresis',
  'comigration in sds page',
  'competition binding',
  'confocal microscopy',
  'cosedimentation',
  'cosedimentation in solution',
  'cosedimentation through density gradient',
  'cross-linking study',
  'de-ADP-ribosylation assay',
  'deacetylase assay',
  'decarboxylation assay',
  'demethylase assay',
  'detection by mass spectrometry',
  'deubiquitinase assay',
  'differential scanning calorimetry',
  'dihydrofolate reductase reconstruction',
  'display technology',
  'dynamic light scattering',
  'electron diffraction',
  'electron microscopy',
  'electron microscopy 3D helical reconstruction',
  'electron microscopy 3D single particle reconstruction',
  'electron paramagnetic resonance',
  'electron tomography',
  'electrophoretic mobility shift assay',
  'electrophoretic mobility supershift assay',
  'electrophoretic mobility-based method',
  'enzymatic footprinting',
  'enzymatic study',
  'enzyme linked immunosorbent assay',
  'experimental interaction detection',
  'far western blotting',
  'field flow fractionation',
  'filamentous phage display',
  'filter binding',
  'filter trap assay',
  'fluorescence correlation spectroscopy',
  'fluorescence microscopy',
  'fluorescence polarization spectroscopy',
  'fluorescence recovery after photobleaching',
  'fluorescence technology',
  'fluorescence-activated cell sorting',
  'fluorescent resonance energy transfer',
  'footprinting',
  'force spectroscopy',
  'gal4 vp16 complementation',
  'gdp/gtp exchange assay',
  'glycosylase assay',
  'gtpase assay',
  'homogeneous time resolved fluorescence',
  'hydroxylase assay',
  'imaging technique',
  'immunodepleted coimmunoprecipitation',
  'in-gel kinase assay',
  'inference by socio-affinity scoring',
  'infrared spectroscopy',
  'interaction detection method',
  'interactome parallel affinity capture',
  'ion exchange chromatography',
  'ion mobility mass spectrometry of complexes',
  'isothermal titration calorimetry',
  'kinase homogeneous time resolved fluorescence',
  'kinase scintillation proximity assay',
  'lambda phage display',
  'lambda repressor two hybrid',
  'lex-a dimerization assay',
  'lexa b52 complementation',
  'lexa vp16 complementation',
  'light microscopy',
  'light scattering',
  'lipoprotein cleavage assay',
  'luminescence based mammalian interactome mapping',
  'mammalian protein protein interaction trap',
  'mass spectrometry studies of complexes',
  'mass spectrometry study of hydrogen/deuterium exchange',
  'methyltransferase assay',
  'methyltransferase radiometric assay',
  'microscale thermophoresis',
  'molecular sieving',
  'mrna display',
  'myristoylase assay',
  'neddylase assay',
  'nuclear magnetic resonance',
  'nuclease assay',
  'oxidase assay',
  'oxidoreductase assay',
  'p8 filamentous phage display',
  'palmitoylase assay',
  'peptide array',
  'phage display',
  'phosphatase assay',
  'phosphotransferase assay',
  'polymerization',
  'probe interaction assay',
  'protease accessibility laddering',
  'protease assay',
  'protein array',
  'protein complementation assay',
  'protein cross-linking with a bifunctional reagent',
  'protein kinase assay',
  'protein phosphatase assay',
  'protein three hybrid',
  'proteinchip(r) on a surface-enhanced laser desorption/ionization',
  'proximity labelling technology',
  'proximity ligation assay',
  'proximity-dependent biotin identification',
  'pull down',
  'reverse phase chromatography',
  'reverse ras recruitment system',
  'reverse two hybrid',
  'ribonuclease assay',
  'rna immunoprecipitation',
  'rna interference',
  'sandwich immunoassay',
  'saturation binding',
  'scanning electron microscopy',
  'scintillation proximity assay',
  'small angle neutron scattering',
  'solid phase assay',
  'solid state nmr',
  'solution state nmr',
  'split firefly luciferase complementation',
  'split luciferase complementation',
  'Split renilla luciferase complementation',
  'static light scattering',
  'sumoylase assay',
  'super-resolution microscopy',
  'surface plasmon resonance',
  'surface plasmon resonance array',
  't7 phage display',
  'tandem affinity purification',
  'thermal shift binding',
  'three hybrid',
  'tox-r dimerization assay',
  'transcriptional complementation assay',
  'transmission electron microscopy',
  'two hybrid',
  'two hybrid array',
  'two hybrid bait and prey pooling approach',
  'two hybrid fragment pooling approach',
  'two hybrid pooling approach',
  'two hybrid prey pooling approach',
  'ubiquitin reconstruction',
  'ubiquitinase assay',
  'ultraviolet-visible spectroscopy',
  'unspecified method',
  'validated two hybrid',
  'virotrap',
  'x ray scattering',
  'x-ray crystallography',
  'x-ray fiber diffraction',
  'yeast display',
  'zymography'
])

const interactionTypes = z.enum([
  'acetylation reaction',
  'adp ribosylation reaction',
  'ampylation reaction',
  'association',
  'atpase reaction',
  'cleavage reaction',
  'colocalization',
  'covalent binding',
  'de-ADP-ribosylation reaction',
  'deacetylation reaction',
  'demethylation reaction',
  'deneddylation reaction',
  'dephosphorylation reaction',
  'deubiquitination reaction',
  'direct interaction',
  'disulfide bond',
  'dna cleavage',
  'enzymatic reaction',
  'glycosylation reaction',
  'gtpase reaction',
  'guanine nucleotide exchange factor reaction',
  'hydroxylation reaction',
  'lipid addition',
  'lipoprotein cleavage reaction',
  'methylation reaction',
  'myristoylation reaction',
  'neddylation reaction',
  'oxidoreductase activity electron transfer reaction',
  'palmitoylation reaction',
  'phosphorylation reaction',
  'phosphotransfer reaction',
  'physical association',
  'proline isomerization  reaction',
  'protein cleavage',
  'proximity',
  'putative self interaction',
  'rna cleavage',
  'self interaction',
  'sumoylation reaction',
  'transglutamination reaction',
  'ubiquitination reaction'
]
)

const proteinsProteinsQueryFormat = proteinsCommonQueryFormat.merge(z.object({
  detection_method: detectionMethods.optional(),
  interaction_type: interactionTypes.optional(),
  pmid: z.string().trim().optional(),
  source: sources.optional()
})).merge(commonEdgeParamsFormat)

const proteinsProteinsFormat = z.object({
  // ignore dbxrefs field to avoid long output
  'protein 1': z.string().or(z.array(proteinFormat.omit({ dbxrefs: true }))),
  'protein 2': z.string().or(z.array(proteinFormat.omit({ dbxrefs: true }))),
  detection_method: z.string(),
  detection_method_code: z.string(),
  interaction_type: z.array(interactionTypes),
  interaction_type_code: z.array(z.string()),
  confidence_value_biogrid: z.number().nullable(),
  confidence_value_intact: z.number().nullable(),
  source: z.string(),
  organism: z.string(),
  pmids: z.array(z.string()),
  name: z.string(),
  inverse_name: z.string()
})

function edgeQuery (input: paramsFormatType): string {
  const query = []

  if (input.pmid !== undefined && input.pmid !== '') {
    const pmidUrl = 'http://pubmed.ncbi.nlm.nih.gov/'
    input.pmid = pmidUrl + (input.pmid as string)
    query.push(`'${input.pmid}' IN record.pmids`)
    delete input.pmid
  }

  if (input.source !== undefined) {
    query.push(`record.source == '${input.source as string}'`)
    delete input.source
  }

  if (input['interaction type'] !== undefined) {
    query.push(`'${input['interaction type'] as string}' in record.interaction_type[*]`)
    delete input['interaction type']
  }

  if (input.detection_method !== undefined) {
    query.push(`record.detection_method == '${input.detection_method as string}'`)
    delete input.detection_method
  }

  if (input.organism !== undefined) {
    query.push(`record.organism == '${input.organism as string}'`)
    delete input.organism
  }

  return query.join(' and ')
}

async function proteinProteinSearch (input: paramsFormatType): Promise<any[]> {
  let nodesFilter = ''
  let nodesQuery = ''

  let proteinFilters = ''
  if (input.protein_id !== undefined) {
    nodesQuery = `LET nodes = ${proteinByIDQuery(input.protein_id as string)}`
    delete input.organism
  } else {
    input.names = input.protein_name
    input.full_names = input.full_name
    delete input.protein_name
    delete input.full_name

    proteinFilters = getFilterStatements(proteinSchema, input)
    if (proteinFilters !== '') {
      nodesQuery = `LET nodes = (
        FOR record in ${proteinSchema.db_collection_name as string}
        FILTER ${proteinFilters}
        RETURN record._id
      )`
    }
  }

  let filter = edgeQuery(input)
  nodesFilter = '(record._from IN nodes OR record._to IN nodes)'
  if (filter !== '') {
    filter = `and ${filter}`
  }

  const page = input.page as number
  const verbose = input.verbose === 'true'

  const sourceVerboseQuery = `
    FOR otherRecord IN ${proteinSchema.db_collection_name as string}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
    RETURN {${getDBReturnStatements(proteinSchema).replaceAll('record', 'otherRecord')}}
  `
  const targetVerboseQuery = `
    FOR otherRecord IN ${proteinSchema.db_collection_name as string}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
    RETURN {${getDBReturnStatements(proteinSchema).replaceAll('record', 'otherRecord')}}
  `

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let filterBy = `${nodesFilter} ${filter}`
  if (filterBy.trim() !== '') {
    filterBy = `FILTER ${filterBy}`
  }

  const query = `
    ${nodesQuery}
    FOR record IN ${proteinProteinSchema.db_collection_name as string}
      ${filterBy}
      SORT record._key
      LIMIT ${page * limit}, ${limit}
      RETURN {
        'protein 1': ${verbose ? `(${sourceVerboseQuery})` : 'record._from'},
        'protein 2': ${verbose ? `(${targetVerboseQuery})` : 'record._to'},
        ${getDBReturnStatements(proteinProteinSchema)},
        'name': record.name,
        'inverse_name': record.inverse_name
      }
    `

  return await (await db.query(query)).all()
}

const proteinsProteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/proteins/proteins', description: descriptions.proteins_proteins } })
  .input(proteinsProteinsQueryFormat)
  .output(z.array(proteinsProteinsFormat))
  .query(async ({ input }) => await proteinProteinSearch(input))

export const proteinsProteinsRouters = {
  proteinsProteins
}
