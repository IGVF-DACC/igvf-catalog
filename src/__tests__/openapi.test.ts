import { openApiDocument } from '../openapi'
import { CATALOG_ENDPOINTS } from '../catalogEndpoints'

jest.mock('../database')

// Importing the full OpenAPI document exercises startup-time route registration,
// which isolated router tests and TypeScript compilation do not cover.
it('generates the OpenAPI document with every registered endpoint', () => {
  expect(Object.keys(openApiDocument.paths)).toEqual(CATALOG_ENDPOINTS.map(endpoint => endpoint.path))
  expect(openApiDocument.paths['/genomic-elements/genomic-elements']?.get?.tags).toEqual(['IGVF Data'])
})
