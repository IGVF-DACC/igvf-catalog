import { ontologyTermsEdgeRouters } from '../../../datatypeRouters/edges/ontology_terms_ontology_terms'
import * as dbModule from '../../../../database'

jest.mock('../../../../database')

describe('ontologyTermsEdgeRouters', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns class, method and files_filesets for children', async () => {
    const mockResult = [{
      term: {
        uri: 'https://uri/CHILD_1',
        term_id: 'CHILD_1',
        name: 'child term',
        synonyms: [],
        description: '',
        source: 'UBERON',
        subontology: null,
        source_url: 'https://uri/',
        class: 'biological relationship',
        method: null,
        files_filesets: 'files_filesets/IGVFFI7407XTPX'
      },
      relationship_type: 'subclass'
    }]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { ontology_term_id: 'PARENT_1', page: 0 }
    const result: any = await ontologyTermsEdgeRouters.ontologyTermChildren({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(result[0].term.class).toBe('biological relationship')
    expect(result[0].term.method).toBeNull()
    expect(result[0].term.files_filesets).toBe('files_filesets/IGVFFI7407XTPX')
  })

  it('returns class, method and files_filesets for parents', async () => {
    const mockResult = [{
      term: {
        uri: 'https://uri/PARENT_1',
        term_id: 'PARENT_1',
        name: 'parent term',
        synonyms: [],
        description: '',
        source: 'UBERON',
        subontology: null,
        source_url: 'https://uri/',
        class: 'biological relationship',
        method: null,
        files_filesets: 'files_filesets/IGVFFI7407XTPX'
      },
      relationship_type: 'subclass'
    }]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { ontology_term_id: 'CHILD_1', page: 0 }
    const result: any = await ontologyTermsEdgeRouters.ontologyTermParents({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result[0].term.class).toBe('biological relationship')
    expect(result[0].term.files_filesets).toBe('files_filesets/IGVFFI7407XTPX')
  })

  it('returns class, method and files_filesets on transitive-closure path vertices', async () => {
    const mockPaths = [{
      vertices: [
        {
          _key: 'START_1',
          uri: 'https://uri/START_1',
          term_id: 'START_1',
          name: 'start term',
          synonyms: [],
          description: '',
          source: 'UBERON',
          subontology: null,
          class: 'biological relationship',
          method: null,
          files_filesets: 'files_filesets/IGVFFI7407XTPX'
        },
        {
          _key: 'END_1',
          uri: 'https://uri/END_1',
          term_id: 'END_1',
          name: 'end term',
          synonyms: [],
          description: '',
          source: 'UBERON',
          subontology: null,
          class: 'biological relationship',
          method: null,
          files_filesets: 'files_filesets/IGVFFI7407XTPX'
        }
      ],
      edges: [{
        _key: 'e1',
        _id: 'ontology_terms_ontology_terms/e1',
        _from: 'ontology_terms/START_1',
        _to: 'ontology_terms/END_1',
        _rev: 'r1',
        name: 'subclass'
      }]
    }]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockPaths)
    } as any)

    const input = { ontology_term_id_start: 'START_1', ontology_term_id_end: 'END_1' }
    const result: any = await ontologyTermsEdgeRouters.ontologyTermTransitiveClosure({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result.vertices.START_1.class).toBe('biological relationship')
    expect(result.vertices.START_1.method).toBeNull()
    expect(result.vertices.START_1.files_filesets).toBe('files_filesets/IGVFFI7407XTPX')
    expect(result.vertices.END_1.files_filesets).toBe('files_filesets/IGVFFI7407XTPX')
  })
})
