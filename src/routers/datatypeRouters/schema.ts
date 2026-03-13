import * as fs from 'fs'
import * as path from 'path'
import { configType } from '../../constants'

/**
 * Resolve $ref references in a schema
 */
function resolveRefs (schema: any, basePath: string): any {
  if (!schema || typeof schema !== 'object') {
    return schema
  }

  if (Array.isArray(schema)) {
    return schema.map(item => resolveRefs(item, basePath))
  }

  // Handle $ref
  if (schema.$ref) {
    const refPath = path.join(basePath, schema.$ref)
    const refContent = fs.readFileSync(refPath, 'utf8')
    const refSchema = JSON.parse(refContent)
    // Recursively resolve refs in the referenced schema
    return resolveRefs(refSchema, path.dirname(refPath))
  }

  // Recursively resolve refs in nested objects
  const resolved: any = {}
  for (const [key, value] of Object.entries(schema)) {
    resolved[key] = resolveRefs(value, basePath)
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
  for (const schemaItem of schema.allOf) {
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
  const basePath = path.dirname(fullPath)
  const resolvedSchema = resolveRefs(schema, basePath)

  // Merge allOf if present
  const finalSchema = mergeAllOfSchema(resolvedSchema)

  return finalSchema
}
