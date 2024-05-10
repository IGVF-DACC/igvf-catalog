import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { proteinFormat } from '../nodes/proteins'
import { descriptions } from '../descriptions'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'

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
  'anti bait coimmunoprecipitation',
  'anti tag coimmunoprecipitation',
  'antibody array',
  'array technology',
  'atomic force microscopy',
  'atpase assay',
  'barcode fusion genetics two hybrid',
  'bead aggregation assay',
  'beta galactosidase complementation',
  'beta lactamase complementation',
  'bimolecular fluorescence complementation',
  'bio-layer interferometry',
  'biochemical',
  'bioid',
  'bioluminescence resonance energy transfer',
  'biophysical',
  'biosensor',
  'blue native page',
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
  'hydroxylase assay',
  'imaging technique',
  'immunodepleted coimmunoprecipitation',
  'in-gel kinase assay',
  'inference by socio-affinity scoring',
  'infrared spectroscopy',
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
  'protease accessibility laddering',
  'protease assay',
  'protein array',
  'protein complementation assay',
  'protein cross-linking with a bifunctional reagent',
  'protein kinase assay',
  'protein phosphatase assay',
  'protein three hybrid',
  'proximity labelling technology',
  'proximity ligation assay',
  'proximity-dependent biotin identification',
  'pull down',
  'r',
  'reverse phase chromatography',
  'reverse ras recruitment system',
  'reverse two hybrid',
  'rna immunoprecipitation',
  'rna interference',
  'sandwich immunoassay',
  'saturation binding',
  'scanning electron microscopy',
  'scintillation proximity assay',
  'solid phase assay',
  'solid state nmr',
  'solution state nmr',
  'split firefly luciferase complementation',
  'split luciferase complementation',
  'Split renilla luciferase complementation',
  'static light scattering',
  'sumoylase assay',
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
  'direct interaction',
  'physical association',
  'acetylation reaction',
  'adp ribosylation reaction',
  'association',
  'covalent binding',
  'methylation reaction',
  'phosphorylation reaction',
  'ubiquitination reaction',
  'colocalization',
  'disulfide bond',
  'enzymatic reaction',
  'hydroxylation reaction',
  'atpase reaction',
  'dephosphorylation reaction',
  'proximity',
  'self interaction',
  'cleavage reaction',
  'protein cleavage',
  'rna cleavage',
  'de-ADP-ribosylation reaction',
  'deacetylation reaction',
  'demethylation reaction',
  'deubiquitination reaction',
  'deneddylation reaction',
  'neddylation reaction',
  'palmitoylation reaction',
  'sumoylation reaction',
  'guanine nucleotide exchange factor reaction',
  'glycosylation reaction',
  'gtpase reaction',
  'lipoprotein cleavage reaction',
  'proline isomerization  reaction',
  'dna cleavage',
  'oxidoreductase activity electron transfer reaction',
  'phosphotransfer reaction',
  'putative self interaction'
])

const proteinsProteinsQueryFormat = z.object({
  protein_id: z.string().trim().optional(),
  name: z.string().trim().optional(),
  'detection method': detectionMethods.optional(),
  'interaction type': interactionTypes.optional(),
  pmid: z.string().trim().optional(),
  source: sources.optional(),
  organism: z.enum(['Mus musculus', 'Homo sapiens']).default('Homo sapiens'),
  page: z.number().default(0),
  verbose: z.enum(['true', 'false']).default('false')
})

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
  pmids: z.array(z.string())
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
    query.push(`record.source == '${input.source}'`)
    delete input.source
  }

  if (input['interaction type'] !== undefined) {
    query.push(`'${input['interaction type']}' in record.interaction_type[*]`)
    delete input['interaction type']
  }

  if (input['detection method'] !== undefined) {
    query.push(`record.detection_method == '${input['detection method']}'`)
    delete input['detection method']
  }

  if (input.organism !== undefined) {
    query.push(`record.organism == '${input.organism}'`)
    delete input['detection method']
  }

  return query.join(' and ')
}

async function proteinProteinSearch (input: paramsFormatType): Promise<any[]> {
  console.log(input)
  let proteinFilters = ''
  if (input.protein_id !== undefined) {
    proteinFilters = `record._id == 'proteins/${input.protein_id as string}'`
    delete input.protein_id
  } else {
    proteinFilters = getFilterStatements(proteinSchema, { name: input.name })
  }
  console.log('proteinFilters', proteinFilters)

  const page = input.page as number
  const verbose = input.verbose === 'true'

  let nodesFilter = ''
  let nodesQuery = ''
  let filter = edgeQuery(input)
  console.log('filter', filter)

  if (proteinFilters !== '') {
    nodesQuery = `LET nodes = (
      FOR record in ${proteinSchema.db_collection_name as string}
      FILTER ${proteinFilters}
      RETURN record._id
    )`
    nodesFilter = '(record._from IN nodes OR record._to IN nodes)'
    if (filter !== '') {
      filter = `and ${filter}`
    }
  }

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
        ${getDBReturnStatements(proteinProteinSchema)}
      }
    `
  console.log(query)
  return await (await db.query(query)).all()
}

const proteinsProteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/proteins/proteins', description: descriptions.proteins_proteins } })
  .input(proteinsProteinsQueryFormat.merge(z.object({ limit: z.number().optional() })))
  .output(z.array(proteinsProteinsFormat))
  .query(async ({ input }) => await proteinProteinSearch(input))

export const proteinsProteinsRouters = {
  proteinsProteins
}
