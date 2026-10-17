import { collectionEndpointsRouters } from '../../datatypeRouters/collectionEndpoints'
import { validateCollectionEndpoints, COLLECTION_ENDPOINTS } from '../../../collectionEndpoints'

async function callCollectionEndpoints (input: { collection?: string, type?: 'node' | 'edge' }): Promise<any> {
  return await collectionEndpointsRouters.collectionEndpoints({
    input,
    ctx: {},
    type: 'query',
    path: '',
    rawInput: input
  })
}

describe('collectionEndpointsRouters.collectionEndpoints', () => {
  it('returns the entire mapping when called with no filters', async () => {
    const result = await callCollectionEndpoints({})
    expect(result.length).toBe(Object.keys(COLLECTION_ENDPOINTS).length)
    expect(result).toEqual(
      expect.arrayContaining([{ collection: 'genes', type: 'node', endpoints: ['/genes'] }])
    )
  })

  it('filters by an exact collection name', async () => {
    const result = await callCollectionEndpoints({ collection: 'genomic_elements_genes' })
    expect(result).toEqual([
      {
        collection: 'genomic_elements_genes',
        type: 'edge',
        endpoints: [
          '/genomic-elements/genes',
          '/genes/genomic-elements',
          '/gene-regulatory-network',
          '/enhancer-gene-predictions',
          '/variants/genomic-elements/genes'
        ]
      }
    ])
  })

  it('returns an empty array for an unknown collection', async () => {
    const result = await callCollectionEndpoints({ collection: 'not_a_real_collection' })
    expect(result).toEqual([])
  })

  it('returns an empty endpoints array for a collection with no dedicated endpoint', async () => {
    const result = await callCollectionEndpoints({ collection: 'donors' })
    expect(result).toEqual([{ collection: 'donors', type: 'node', endpoints: [] }])
  })

  it('filters by type only', async () => {
    const result = await callCollectionEndpoints({ type: 'node' })
    expect(result.length).toBeGreaterThan(0)
    expect(result.every((entry: any) => entry.type === 'node')).toBe(true)
  })

  it('combines collection and type filters', async () => {
    const matching = await callCollectionEndpoints({ collection: 'genes', type: 'node' })
    expect(matching).toEqual([{ collection: 'genes', type: 'node', endpoints: ['/genes'] }])

    const mismatched = await callCollectionEndpoints({ collection: 'genes', type: 'edge' })
    expect(mismatched).toEqual([])
  })
})

describe('validateCollectionEndpoints', () => {
  it('does not throw against the real registry.json and catalogEndpoints.ts', () => {
    expect(() => { validateCollectionEndpoints() }).not.toThrow()
  })
})
