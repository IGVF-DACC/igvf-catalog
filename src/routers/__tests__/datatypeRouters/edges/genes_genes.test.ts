import { genesGenesEdgeRouters } from '../../../datatypeRouters/edges/genes_genes'
import { db } from '../../../../database'
import { CATALOG_ENDPOINTS } from '../../../../catalogEndpoints'

jest.mock('../../../../database')

const call = async (input: Record<string, unknown>): Promise<any> => await genesGenesEdgeRouters.genesGenes({ input, ctx: {}, type: 'query', path: '', rawInput: input })
const record = {
  _id: 'genes_genes/test',
  gene_1: 'genes/G1',
  gene_2: 'genes/G2',
  name: 'modulates expression of',
  label: 'gene overexpression effect on gene expression',
  method: 'MORF screen',
  class: 'observed data',
  source: 'IGVF',
  transcript: 'transcripts/ENST00000619387',
  morf_id: 'AATF_1',
  log2FC: 1.2,
  significant: true,
  files_filesets: 'files_filesets/IGVFFI6734IWRB',
  transcript_mapping_method: 'supplied ENST'
}

beforeEach(() => {
  jest.spyOn(db, 'query').mockResolvedValue({ all: jest.fn().mockResolvedValue([record]) } as any)
})

it('exposes MORF and its transcript hyperedge from the IGVF gene-gene endpoint', async () => {
  expect(await call({ method: 'MORF screen', transcript_id: 'ENST00000619387.1', significant: 'true', log2FC: 'gte:1', page: 0 })).toEqual([record])
  const query = (db.query as jest.Mock).mock.calls[0][0]
  expect(query).toContain('FOR record IN genes_genes')
  expect(query).toContain("record.transcript == 'transcripts/ENST00000619387'")
  expect(query).toContain('record.significant == true')
  expect(query).toContain("record['log2FC'] >= 1")
  expect(query).toContain("record['morf_id']")
  expect(CATALOG_ENDPOINTS.find(e => e.path === '/genes/genes')?.tag).toBe('IGVF Data')
  expect(CATALOG_ENDPOINTS.some(e => e.path === '/transcripts/genes/effects')).toBe(false)
})

it('preserves source-to-readout direction for IGVF and symmetric lookup for legacy data', async () => {
  await call({ gene_id: 'G1', associated_gene_id: 'G2', page: 0 })
  const query = (db.query as jest.Mock).mock.calls[0][0]
  expect(query).toContain("record._from == gene._id OR (record.source != 'IGVF'")
  expect(query).toContain("record._to == associatedGene._id OR (record.source != 'IGVF'")
  expect(query).toContain("record.source == 'COXPRESdb'")
})

it('expands the transcript link in verbose mode', async () => {
  await call({ morf_id: 'AATF_1', verbose: 'true', page: 0 })
  expect((db.query as jest.Mock).mock.calls[0][0]).toContain('transcriptRecord._id == record.transcript')
})

it('keeps mouse BioGRID queries available', async () => {
  await call({ gene_id: 'ENSMUSG00000000001', organism: 'Mus musculus', page: 0 })
  expect((db.query as jest.Mock).mock.calls[0][0]).toContain('FOR record IN mm_genes_mm_genes')
})

it('rejects unbounded and invalid numeric requests', async () => {
  await expect(call({ page: 0 })).rejects.toThrow('Define a gene')
  await expect(call({ method: 'MORF screen', log2FC: 'not-a-number', page: 0 })).rejects.toThrow('valid number')
})
