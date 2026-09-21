import * as fs from 'fs'
import * as os from 'os'
import * as path from 'path'
import { getSchema } from '../schema'

const root = path.resolve(__dirname, '../../../..')
let directory: string

beforeAll(() => {
  directory = fs.mkdtempSync(path.join(os.tmpdir(), 'catalog-schema-'))
  fs.writeFileSync(path.join(directory, 'mixins.json'), JSON.stringify({
    metadata: {
      sample: { $ref: '#/definitions/a~1b~0c%20d' }
    },
    definitions: {
      'a/b~c d': { description: 'Shared sample description' }
    }
  }))
})

afterAll(() => {
  fs.rmSync(directory, { recursive: true, force: true })
})

function load (schema: any): any {
  const file = path.join(directory, 'schema.json')
  fs.writeFileSync(file, JSON.stringify(schema))
  return getSchema(path.relative(root, file))
}

test('resolves grouped fragments, nested local references and escaped pointer tokens', () => {
  const schema = load({
    allOf: [
      { properties: { $ref: 'mixins.json#/metadata' } },
      { properties: { sample: { type: ['string', 'null'] } }, required: ['sample'] }
    ]
  })
  expect(schema.properties).toEqual({
    sample: { description: 'Shared sample description', type: ['string', 'null'] }
  })
  expect(schema.required).toEqual(['sample'])
})

test('imports an individual property without adding other fields', () => {
  expect(load({ properties: { sample: { $ref: 'mixins.json#/metadata/sample' } } }).properties)
    .toEqual({ sample: { description: 'Shared sample description' } })
})

test('reports missing fragments', () => {
  expect(() => load({ $ref: 'mixins.json#/missing' }))
    .toThrow('Unresolved schema reference: mixins.json#/missing')
})

test('rejects unsupported named fragments', () => {
  expect(() => load({ $ref: 'mixins.json#metadata' }))
    .toThrow('Unsupported schema reference: mixins.json#metadata')
})

test('merges mixins composed by a base schema before child overrides', () => {
  const schema = load({
    allOf: [
      {
        allOf: [
          { properties: { $ref: 'mixins.json#/metadata' } },
          { properties: { sample: { type: 'string' } }, required: ['sample'] }
        ]
      },
      { properties: { sample: { enum: ['K562'] } }, required: ['sample'] }
    ]
  })
  expect(schema.properties.sample).toEqual({
    description: 'Shared sample description', type: 'string', enum: ['K562']
  })
  expect(schema.required).toEqual(['sample'])
})
