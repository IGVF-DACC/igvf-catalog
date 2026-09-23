import * as fs from 'fs'
import * as path from 'path'
import { configType } from '../../constants'

const SCHEMA_ROOT = path.join(__dirname, '../../..', 'data/schemas')

/**
 * Resolve $ref references in a schema
 */
function resolveRefs (schema: any, documentPath: string): any {
  if (!schema || typeof schema !== 'object') {
    return schema
  }

  if (Array.isArray(schema)) {
    return schema.map(item => resolveRefs(item, documentPath))
  }

  // Handle $ref; sibling keywords are kept and override the resolved target
  // (JSON Schema 2020-12 allows keywords alongside $ref).
  if (schema.$ref) {
    const reference = schema.$ref as string
    const [file, fragment] = reference.split('#')
    const refPath = file ? path.resolve(path.dirname(documentPath), file) : documentPath
    const refContent = fs.readFileSync(refPath, 'utf8')
    let refSchema = JSON.parse(refContent)
    if (fragment) {
      const pointer = decodeURIComponent(fragment)
      if (!pointer.startsWith('/')) {
        throw new Error(`Unsupported schema reference: ${reference}`)
      }
      for (const token of pointer.slice(1).split('/')) {
        const key = token.replace(/~1/g, '/').replace(/~0/g, '~')
        if (refSchema === null || typeof refSchema !== 'object' ||
            !Object.prototype.hasOwnProperty.call(refSchema, key)) {
          throw new Error(`Unresolved schema reference: ${reference}`)
        }
        refSchema = refSchema[key]
      }
    }
    const resolvedRef = resolveRefs(refSchema, refPath)
    const siblings: any = {}
    for (const [key, value] of Object.entries(schema)) {
      if (key === '$ref') {
        continue
      }
      siblings[key] = resolveRefs(value, documentPath)
    }
    if (Object.keys(siblings).length === 0) {
      return resolvedRef
    }
    if (resolvedRef !== null && typeof resolvedRef === 'object' && !Array.isArray(resolvedRef)) {
      return { ...resolvedRef, ...siblings }
    }
    return resolvedRef
  }

  // Recursively resolve refs in nested objects
  const resolved: any = {}
  for (const [key, value] of Object.entries(schema)) {
    resolved[key] = resolveRefs(value, documentPath)
  }
  return resolved
}

/**
 * Merge allOf schemas into a single schema.
 *
 * For properties: Child definitions are MERGED with base definitions.
 * - Base defines: {type, description}
 * - Child adds: {enum, pattern, example}
 * - Result: {type, description, enum, pattern, example}
 */
function mergeAllOfSchema (schema: any): any {
  if (!schema || typeof schema !== 'object' || !schema.allOf) {
    return schema
  }

  // Start with an empty merged schema
  const merged: any = {}

  // Merge each schema in allOf sequentially
  for (const item of schema.allOf) {
    const schemaItem = mergeAllOfSchema(item)
    // Merge properties (deep merge for each property)
    if (schemaItem.properties) {
      if (!merged.properties) {
        merged.properties = {}
      }

      for (const [propName, propValue] of Object.entries(schemaItem.properties)) {
        if (!(propName in merged.properties)) {
          // New property, add it directly (deep copy if object)
          merged.properties[propName] = typeof propValue === 'object' && propValue !== null
            ? { ...propValue }
            : propValue
        } else {
          // Property exists, merge the definitions
          const existingProp = merged.properties[propName]
          if (typeof existingProp === 'object' && typeof propValue === 'object' &&
              existingProp !== null && propValue !== null) {
            // Deep merge: child's values override/extend base's values
            merged.properties[propName] = { ...existingProp, ...propValue }
          } else {
            // Not an object, just replace
            merged.properties[propName] = propValue
          }
        }
      }
    }

    // Merge required (combine and deduplicate)
    if (schemaItem.required) {
      if (!merged.required) {
        merged.required = []
      }
      merged.required = Array.from(new Set([...merged.required, ...schemaItem.required]))
    }

    // Copy or override other properties
    for (const [key, value] of Object.entries(schemaItem)) {
      if (key !== 'properties' && key !== 'required') {
        merged[key] = value
      }
    }
  }

  // Add top-level properties from the original schema (except allOf)
  const result: any = {}
  for (const [key, value] of Object.entries(schema)) {
    if (key !== 'allOf') {
      result[key] = value
    }
  }

  // Update with merged properties
  Object.assign(result, merged)

  return result
}

/**
 * Load and process a schema file. example: 'data/schemas/nodes/genes.GencodeGene.json'
 * Resolves $ref references and merges allOf
 * returns the schema as a configType type
 */
export function getSchema (schemaFilePath: string): configType {
  const fullPath = path.join(__dirname, '../../..', schemaFilePath)
  const schemaContent = fs.readFileSync(fullPath, 'utf8')
  const schema = JSON.parse(schemaContent)

  // Resolve $ref references
  const resolvedSchema = resolveRefs(schema, fullPath)

  // Merge allOf if present
  const finalSchema = mergeAllOfSchema(resolvedSchema)

  return finalSchema
}

function extractEnumValues (schema: configType, fieldName: string): string[] {
  const fieldSchema = schema?.properties?.[fieldName]
  const enumValues = fieldSchema?.enum
  if (Array.isArray(enumValues)) {
    return enumValues.filter((value): value is string => typeof value === 'string')
  }
  const itemEnumValues = fieldSchema?.items?.enum
  if (Array.isArray(itemEnumValues)) {
    return itemEnumValues.filter((value): value is string => typeof value === 'string')
  }
  return []
}

export function getEnumValues (schemaFilePath: string, fieldName: string): string[] {
  const schema = getSchema(schemaFilePath)
  return extractEnumValues(schema, fieldName)
}

export function getEnumValuesOrThrow (schemaFilePath: string, fieldName: string): [string, ...string[]] {
  const enumValues = getEnumValues(schemaFilePath, fieldName)
  if (enumValues.length === 0) {
    throw new Error(`No enum values found for ${fieldName} in ${schemaFilePath}`)
  }
  return enumValues as [string, ...string[]]
}

export function getCollectionEnumValues (
  schemaType: 'edges' | 'nodes',
  collectionName: string,
  fieldName: string
): string[] {
  const schemaDir = path.join(SCHEMA_ROOT, schemaType)
  const schemaFiles = fs.readdirSync(schemaDir).filter((file) => file.endsWith('.json'))
  const values = new Set<string>()

  for (const file of schemaFiles) {
    const schemaPath = `data/schemas/${schemaType}/${file}`
    const schema = getSchema(schemaPath)
    if (schema.db_collection_name !== collectionName) {
      continue
    }
    for (const value of extractEnumValues(schema, fieldName)) {
      values.add(value)
    }
  }

  return Array.from(values).sort()
}

export function getCollectionEnumValuesOrThrow (
  schemaType: 'edges' | 'nodes',
  collectionName: string,
  fieldName: string
): [string, ...string[]] {
  const enumValues = getCollectionEnumValues(schemaType, collectionName, fieldName)
  if (enumValues.length === 0) {
    throw new Error(`No enum values found for ${fieldName} in ${schemaType}/${collectionName}`)
  }
  return enumValues as [string, ...string[]]
}
