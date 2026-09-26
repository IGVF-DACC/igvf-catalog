import { genomicElementsGenomicElementsRouters } from '../../../datatypeRouters/edges/genomic_elements_genomic_elements'
import { db } from '../../../../database'

jest.mock('../../../../database')

const call = async (input: any): Promise<any> => await genomicElementsGenomicElementsRouters.genomicElementsFromGenomicElements({ input, ctx: {}, type: 'query', path: '', rawInput: input })

beforeEach(() => {
  jest.clearAllMocks()
  jest.spyOn(db, 'query').mockResolvedValue({ all: jest.fn().mockResolvedValue([]) } as any)
})

it('filters both endpoints and preserves false significance with bound values', async () => {
  await call({ source_element_id: 'promoter', target_element_id: 'genomic_elements/peak', files_fileset: 'IGVFFI2419ZSGC', significant: 'false', biological_context: 'a"\\b', page: 2, limit: 1000 })
  const [query, vars] = (db.query as jest.Mock).mock.calls[0]
  expect(query).toContain('record._from == @_from')
  expect(query).toContain('record._to == @_to')
  expect(query).toContain('SORT record._key')
  expect(query).not.toContain('a"\\b')
  expect(vars).toMatchObject({ _from: 'genomic_elements/promoter', _to: 'genomic_elements/peak', files_filesets: 'files_filesets/IGVFFI2419ZSGC', significant: false, biological_context: 'a"\\b', offset: 1000, limit: 500 })
})

it('combines node overlap and promoter-gene filters before pagination', async () => {
  await call({ source_region: 'chr14:100238144-100239154', target_region: 'chr1:3586345-3586846', promoter_gene_id: 'ENSG00000100811', verbose: 'true', p_value_adj: 'lt:0.1', log2FC: 'lt:0' })
  const [query, vars] = (db.query as jest.Mock).mock.calls[0]
  expect(query).toContain('record.start < 100239154 AND record.end > 100238144')
  expect(query).toContain('record.start < 3586846 AND record.end > 3586345')
  expect(query).toContain('record.promoter_of == @promoterGene')
  expect(query).toContain('record._from IN sourceIDs')
  expect(query).toContain('record._to IN targetIDs')
  expect(query).toContain("record['p_value_adj'] < 0.1")
  expect(query).toContain("record['log2FC'] < 0")
  expect(query).toContain('KEEP(DOCUMENT(record._from)')
  expect(query).toContain("'promoter_of'")
  expect(vars.promoterGene).toBe('genes/ENSG00000100811')
  expect(query.indexOf('record._to IN targetIDs')).toBeLessThan(query.indexOf('LIMIT @offset'))
})

it('returns accessibility metrics and verbose promoter gene links', async () => {
  const element = { _id: 'genomic_elements/promoter', name: 'promoter', chr: 'chr14', start: 1, end: 2, promoter_of: 'genes/ENSG00000100811' }
  const record = { source_genomic_element: element, target_genomic_element: 'genomic_elements/peak', name: 'modulates accessibility of', inverse_name: 'accessibility modulated by', label: 'regulatory element effect on chromatin accessibility', class: 'observed data', method: 'Perturb-seq', source: 'IGVF', source_url: 'https://data.igvf.org/tabular-files/IGVFFI2419ZSGC/', files_filesets: 'files_filesets/IGVFFI2419ZSGC', p_value_adj: 0.07, log2FC: -1.3, significant: false }
  jest.spyOn(db, 'query').mockResolvedValue({ all: jest.fn().mockResolvedValue([record]) } as any)
  expect(await call({ files_fileset: 'IGVFFI2419ZSGC', verbose: 'true' })).toEqual([record])
})

it.each([
  {}, { page: -1, method: 'Perturb-seq' }, { limit: 0, method: 'Perturb-seq' },
  { source_region: 'invalid' }, { source_element_id: '' },
  { method: 'Perturb-seq', p_value_adj: 'lt:0 RETURN 1' }
])('rejects invalid or unbounded inputs: %j', async input => {
  await expect(call(input)).rejects.toThrow()
  expect(db.query).not.toHaveBeenCalled()
})
