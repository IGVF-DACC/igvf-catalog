import { openApiDocument } from '../../../openapi'
import { geneProgramsRouters } from '../../datatypeRouters/nodes/gene_programs'
import { genesGeneProgramsRouters } from '../../datatypeRouters/edges/genes_gene_programs'
import { geneProgramsGeneProgramsRouters } from '../../datatypeRouters/edges/gene_programs_gene_programs'
import { genesGenesEdgeRouters } from '../../datatypeRouters/edges/genes_genes'
import * as dbModule from '../../../database'

jest.mock('../../../database')

const context = {
  source: 'IGVF',
  source_url: 'https://data.igvf.org/',
  files_filesets: 'files_filesets/IGVFFI6502THLB',
  class: 'observed data',
  method: 'Perturb-seq',
  label: 'gene program',
  biosample_term: 'ontology_terms/CL_0000115',
  biological_context: 'endothelial cell',
  treatments_term_ids: ['UniProtKB:P01584'],
  perturbation: 'CRISPR interference'
}
const program = { ...context, _id: 'IGVFFI0156PMEA_GP_1', name: 'GP_1', program_id: 'GP_1', reported_gene_count: 300 }
const call = async (procedure: (opts: any) => Promise<any>, input: any): Promise<any> => await procedure({ input, rawInput: input, ctx: {}, type: 'query', path: '' })
const mockRows = (rows: any[]): void => {
  jest.spyOn(dbModule.db, 'query').mockResolvedValue({ all: jest.fn().mockResolvedValue(rows) } as any)
}
const query = (): string => (dbModule.db.query as jest.Mock).mock.calls[0][0] as string

beforeEach(() => { jest.clearAllMocks(); mockRows([]) })

it('returns program definitions and disambiguates file-local IDs', async () => {
  mockRows([program])
  expect(await call(geneProgramsRouters.genePrograms, { program_id: 'GP_1', files_fileset: 'IGVFFI0156PMEA', page: 1, limit: 10 })).toEqual([program])
  expect(query()).toContain("record.program_id == 'GP_1'")
  expect(query()).toContain("record.files_filesets == 'files_filesets/IGVFFI0156PMEA'")
  expect(query()).toContain('LIMIT 10, 10')
})

it('accepts document IDs and escapes exact text filters', async () => {
  await call(geneProgramsRouters.genePrograms, { id: 'gene_programs/IGVFFI0156PMEA_GP_1', name: "program's name" })
  expect(query()).toContain("record._key == 'IGVFFI0156PMEA_GP_1'")
  expect(query()).toContain("program\\'s name")
})

it('returns membership weights without requiring regulator metrics', async () => {
  const edge = { ...context, _id: 'genes_gene_programs/member', gene: 'genes/ENSG1', gene_program: 'gene_programs/P1', label: 'gene program membership', name: 'is a member of', inverse_name: 'has member', score: 0.5 }
  mockRows([edge])
  expect(await call(genesGeneProgramsRouters.geneProgramsFromGenes, { gene_id: 'ENSG1', label: 'gene program membership', score: 'gte:0.2' })).toEqual([edge])
  expect(query()).toContain('record._from == gene._id')
  expect(query()).toContain('IS_NUMBER(record.score)')
  expect(query()).toContain("record['score'] >= 0.2")
})

it('returns regulation context and metrics with inverse relationship naming', async () => {
  const edge = { ...context, _id: 'genes_gene_programs/regulator', gene: 'genes/ENSG1', gene_program: program, label: 'gene program regulation', name: 'regulated by', inverse_name: 'regulates', log2FC: -0.4, neg_log10_pvalue_adj: null, significant: null, genomic_elements: ['genomic_elements/promoter'] }
  mockRows([edge])
  expect(await call(genesGeneProgramsRouters.genesFromGenePrograms, { gene_program_id: program._id, verbose: 'true', log2FC: 'lt:0' })).toEqual([edge])
  expect(query()).toContain('name: record.inverse_name')
  expect(query()).toContain("record._to == 'gene_programs/IGVFFI0156PMEA_GP_1'")
  expect(query()).toContain('FOR other IN gene_programs')
  expect(query()).toContain('IS_NUMBER(record.log2FC)')
})

it('matches program correlations in either direction and retains null coefficients', async () => {
  const edge = { ...context, _id: 'gene_programs_gene_programs/pair', gene_program_1: 'gene_programs/P1', gene_program_2: 'gene_programs/P2', name: 'correlated with', inverse_name: 'correlated with', label: 'program-program correlation', pearson_correlation: null }
  mockRows([edge])
  expect(await call(geneProgramsGeneProgramsRouters.geneProgramsGenePrograms, { gene_program_id: 'P2', associated_gene_program_id: 'P1' })).toEqual([edge])
  expect(query()).toContain("record._from == 'gene_programs/P2' OR record._to == 'gene_programs/P2'")
  expect(query()).toContain("record._to == 'gene_programs/P1'")
})

it('excludes missing coefficients from negative Pearson range queries', async () => {
  await call(geneProgramsGeneProgramsRouters.geneProgramsGenePrograms, { gene_program_id: 'P1', pearson_correlation: 'lt:-0.5' })
  expect(query()).toContain('IS_NUMBER(record.pearson_correlation)')
  expect(query()).toContain("record['pearson_correlation'] < -0.5")
})

it('returns IGVF regulator correlations through genes/genes with their targeted elements', async () => {
  const edge = { ...context, _id: 'genes_genes/pair', gene_1: 'genes/ENSG1', gene_2: 'genes/ENSG2', name: 'correlated with', inverse_name: 'correlated with', label: 'regulator-regulator correlation', pearson_correlation: -0.7, genomic_elements_from: ['genomic_elements/A'], genomic_elements_to: ['genomic_elements/B'] }
  mockRows([edge])
  expect(await call(genesGenesEdgeRouters.genesGenes, { gene_id: 'ENSG1', source: 'IGVF', label: edge.label, method: 'Perturb-seq', files_fileset: 'IGVFFI6502THLB', pearson_correlation: 'lte:-0.5' })).toEqual([edge])
  expect(query()).toContain("record.label == 'regulator-regulator correlation' ?")
  expect(query()).toContain("'genomic_elements_from': record['genomic_elements_from']")
  expect(query()).toContain('record.pearson_correlation != null')
  expect(query()).toContain("record.files_filesets == 'files_filesets/IGVFFI6502THLB'")
})

it.each(['gt:NaN', 'gt:1:2', 'wat:0.5', 'Infinity', ''])('rejects invalid Pearson filter %s before querying', async value => {
  await expect(call(genesGenesEdgeRouters.genesGenes, { gene_id: 'ENSG1', pearson_correlation: value })).rejects.toThrow()
  expect(dbModule.db.query).not.toHaveBeenCalled()
})

it.each([{ page: -1 }, { limit: 0 }, { limit: 101 }, { page: 0.5 }])('rejects invalid program pagination %j', async input => {
  await expect(call(geneProgramsRouters.genePrograms, input)).rejects.toThrow()
  expect(dbModule.db.query).not.toHaveBeenCalled()
})

it('requires endpoint identifiers rather than scanning edge collections', async () => {
  await expect(call(genesGeneProgramsRouters.geneProgramsFromGenes, {})).rejects.toThrow('At least one gene identifier')
  await expect(call(genesGeneProgramsRouters.genesFromGenePrograms, {})).rejects.toThrow('gene_program_id is required')
  await expect(call(geneProgramsGeneProgramsRouters.geneProgramsGenePrograms, {})).rejects.toThrow()
  await expect(call(genesGenesEdgeRouters.genesGenes, { gene_id: '' })).rejects.toThrow('At least one gene')
  expect(dbModule.db.query).not.toHaveBeenCalled()
})

it('registers all gene-program endpoints in OpenAPI', () => {
  for (const path of ['/gene-programs', '/genes/gene-programs', '/gene-programs/genes', '/gene-programs/gene-programs']) {
    expect(openApiDocument.paths[path]?.get).toBeDefined()
    expect(openApiDocument.paths[path]?.get?.tags).toEqual([path === '/gene-programs' ? 'Nodes' : 'IGVF Data'])
  }
})

it('excludes regulator correlations and BioGRID from z-score range filters', async () => {
  await call(genesGenesEdgeRouters.genesGenes, { gene_id: 'ENSG1', z_score: 'lt:1' })
  expect(query()).toContain('record.z_score != null')
})

it('groups genes/genes as bespoke and includes gene-program examples', () => {
  expect(openApiDocument.paths['/genes/genes']?.get?.tags).toEqual(['Bespoke Endpoints'])
  for (const path of ['/gene-programs', '/genes/gene-programs', '/gene-programs/genes', '/gene-programs/gene-programs']) {
    const description = openApiDocument.paths[path]?.get?.description
    expect(description).toContain('Examples by method')
    expect(description).toContain('IGVFFI9532OEFJ')
  }
})

it.each([{ limit: 500 }, { method: 'NotAMethod' }])('rejects invalid genes/genes constraints %j', async input => {
  await expect(call(genesGenesEdgeRouters.genesGenes, { gene_id: 'ENSG1', ...input })).rejects.toThrow()
  expect(dbModule.db.query).not.toHaveBeenCalled()
})

it('publishes bounded limits and method choices for genes/genes', () => {
  const params = openApiDocument.paths['/genes/genes']?.get?.parameters as any[]
  expect(params.find(p => p.name === 'limit').schema.maximum).toBe(100)
  expect(params.find(p => p.name === 'method').schema.enum).toContain('Perturb-seq')
  const response = openApiDocument.paths['/genes/genes']?.get?.responses['200'] as any
  const method = response.content['application/json'].schema.items.properties.method
  expect(method.enum).toEqual(params.find(p => p.name === 'method').schema.enum)
  expect(method.nullable).toBe(true)
})
