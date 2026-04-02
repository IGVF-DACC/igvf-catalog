import * as fs from 'fs'
import * as path from 'path'
import { type configType } from '../../constants'
import { db } from '../../database'

// ---------------------------------------------------------------------------
// ClickHouse column / table schema types
// ---------------------------------------------------------------------------

export interface ChColumn {
  name: string
  chType: string
  isPrimaryKey: boolean
}

export interface ChTableSchema {
  tableName: string
  columns: ChColumn[]
  columnsByName: Map<string, ChColumn>
  fkColumns: string[]
}

// ---------------------------------------------------------------------------
// SQL schema parser
// ---------------------------------------------------------------------------

function parseChSqlFile (sqlText: string): ChTableSchema {
  const tableMatch = sqlText.match(/CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+(\S+)/i)
  const tableName = tableMatch?.[1] ?? ''

  const bodyMatch = sqlText.match(/\(\s*\n?(.*)\)/s)
  if (bodyMatch == null) return { tableName, columns: [], columnsByName: new Map(), fkColumns: [] }

  const columns: ChColumn[] = []
  for (let line of bodyMatch[1].split('\n')) {
    line = line.trim().replace(/,\s*$/, '')
    if (line === '') continue

    const isPK = /PRIMARY\s+KEY/i.test(line)
    line = line.replace(/PRIMARY\s+KEY/i, '').trim()

    const m = line.match(/^`([^`]+)`\s+(.+)$/) ?? line.match(/^(\S+)\s+(.+)$/)
    if (m != null) {
      columns.push({ name: m[1], chType: m[2].trim(), isPrimaryKey: isPK })
    }
  }

  const columnsByName = new Map<string, ChColumn>()
  for (const col of columns) columnsByName.set(col.name, col)

  const pkIdx = columns.findIndex(c => c.isPrimaryKey && c.name === 'id')
  const fkColumns = pkIdx >= 0
    ? columns.slice(pkIdx + 1).filter(c => c.name.endsWith('_id')).map(c => c.name)
    : []

  return { tableName, columns, columnsByName, fkColumns }
}

// ---------------------------------------------------------------------------
// Schema registry — loaded once at import time
// ---------------------------------------------------------------------------

const GENERATED_SCHEMAS_DIR = path.join(__dirname, '../../../data/db/generated_schemas')

const chSchemaRegistry = new Map<string, ChTableSchema>()

function loadAllChSchemas (): void {
  if (!fs.existsSync(GENERATED_SCHEMAS_DIR)) return
  for (const file of fs.readdirSync(GENERATED_SCHEMAS_DIR)) {
    if (!file.endsWith('.sql')) continue
    const sqlText = fs.readFileSync(path.join(GENERATED_SCHEMAS_DIR, file), 'utf-8')
    const schema = parseChSqlFile(sqlText)
    if (schema.tableName !== '') {
      chSchemaRegistry.set(schema.tableName, schema)
    }
  }
}

loadAllChSchemas()

export function getChTableSchema (tableName: string): ChTableSchema {
  const schema = chSchemaRegistry.get(tableName)
  if (schema == null) {
    throw new Error(`No ClickHouse schema found for table: ${tableName}`)
  }
  return schema
}

// ---------------------------------------------------------------------------
// JSON schema loader
// ---------------------------------------------------------------------------

const JSON_SCHEMAS_DIR = path.join(__dirname, '../../../data/schemas')

export function loadJsonSchema (relativePath: string): configType {
  const fullPath = path.join(JSON_SCHEMAS_DIR, relativePath)
  return JSON.parse(fs.readFileSync(fullPath, 'utf-8')) as configType
}

// ---------------------------------------------------------------------------
// Parameterized query helper
// ---------------------------------------------------------------------------

export type QueryParams = Record<string, string | number | boolean | string[] | number[]>

export async function chQuery<T = any> (sql: string, params?: QueryParams): Promise<T[]> {
  const resultSet = await db.query({ query: sql, query_params: params, format: 'JSONEachRow' })
  return await resultSet.json()
}

export function sqlInList (ids: string[]): string {
  return ids.map(id => `'${id.replace(/'/g, "\\'")}'`).join(',')
}

// ---------------------------------------------------------------------------
// getChSelectStatements
// ---------------------------------------------------------------------------

export interface ChSelectOptions {
  simplified?: boolean
  extraSelect?: string[]
  skipFields?: string[]
}

export function getChSelectStatements (
  jsonSchema: configType,
  chSchema: ChTableSchema,
  alias: string,
  options?: ChSelectOptions
): string {
  const accessibleVia = jsonSchema.accessible_via
  if (accessibleVia?.return == null) {
    throw new Error(`JSON schema ${jsonSchema.$id ?? '(unknown)'} has no accessible_via.return`)
  }

  let fieldList: string
  if (options?.simplified === true && accessibleVia.simplified_return != null) {
    fieldList = accessibleVia.simplified_return
  } else {
    fieldList = accessibleVia.return
  }

  const fields = fieldList.split(',').map(f => f.trim()).filter(f => f !== '')
  const skipSet = new Set(options?.skipFields ?? [])
  const selects: string[] = []

  for (const field of fields) {
    if (skipSet.has(field)) continue

    if (field === '_id') {
      selects.push(`${alias}.id AS _id`)
    } else if (field === '_from') {
      const fk = chSchema.fkColumns[0]
      if (fk != null) {
        selects.push(`${alias}.${fk} AS _from`)
      }
    } else if (field === '_to') {
      const fk = chSchema.fkColumns[1]
      if (fk != null) {
        selects.push(`${alias}.${fk} AS _to`)
      }
    } else if (chSchema.columnsByName.has(field)) {
      selects.push(`${alias}.${quoteIfNeeded(field)} AS ${quoteIfNeeded(field)}`)
    } else {
      console.warn(`[clickhouse_helpers] Field "${field}" in accessible_via.return not found in SQL schema for ${chSchema.tableName}; skipping`)
    }
  }

  if (options?.extraSelect != null) {
    selects.push(...options.extraSelect)
  }

  return selects.join(', ')
}

function quoteIfNeeded (name: string): string {
  if (/^\d/.test(name) || !/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(name)) {
    return `\`${name}\``
  }
  return name
}

// ---------------------------------------------------------------------------
// getChFilterConditions
// ---------------------------------------------------------------------------

const SKIP_PARAMS = new Set(['page', 'limit', 'verbose', 'sort', 'organism'])

export function getChFilterConditions (
  jsonSchema: configType,
  chSchema: ChTableSchema,
  queryParams: Record<string, string | number | boolean | undefined>,
  alias: string,
  params: QueryParams
): string[] {
  const conditions: string[] = []
  const rangeFields = new Set(
    jsonSchema.accessible_via?.filter_by_range?.split(',').map(f => f.trim()).filter(f => f !== '') ?? []
  )

  for (const [key, value] of Object.entries(queryParams)) {
    if (value === undefined || SKIP_PARAMS.has(key)) continue

    if (key === 'intersect') {
      const parts = String(value).split(':')
      const fieldOps = parts[0].split('-')
      const rangeOps = parts[1].split('-')
      conditions.push(`${alias}.${fieldOps[0]} < ${rangeOps[1]} AND ${alias}.${fieldOps[1]} > ${rangeOps[0]}`)
      continue
    }

    const col = chSchema.columnsByName.get(key)

    if (rangeFields.has(key)) {
      const strVal = String(value)
      const paramBase = `_rf_${key}`
      if (strVal.startsWith('range:')) {
        const [lo, hi] = strVal.slice(6).split('-').map(Number)
        params[`${paramBase}_lo`] = lo
        params[`${paramBase}_hi`] = hi
        conditions.push(`${alias}.${quoteIfNeeded(key)} >= {${paramBase}_lo:Float64} AND ${alias}.${quoteIfNeeded(key)} < {${paramBase}_hi:Float64}`)
      } else if (strVal.includes(':')) {
        const [op, num] = strVal.split(':')
        const opMap: Record<string, string> = { gt: '>', gte: '>=', lt: '<', lte: '<=' }
        params[paramBase] = Number(num)
        conditions.push(`${alias}.${quoteIfNeeded(key)} ${opMap[op] ?? '>='} {${paramBase}:Float64}`)
      } else {
        params[paramBase] = Number(strVal)
        conditions.push(`${alias}.${quoteIfNeeded(key)} = {${paramBase}:Float64}`)
      }
      continue
    }

    if (col == null) continue

    const paramName = `_f_${key}`
    const chType = col.chType

    if (chType.startsWith('Array(')) {
      params[paramName] = String(value)
      conditions.push(`has(${alias}.${quoteIfNeeded(key)}, {${paramName}:String})`)
    } else if (/^(Float64|Float32|UInt\d+|Int\d+|Decimal)/.test(chType) || /^Nullable\((Float|UInt|Int|Decimal)/.test(chType)) {
      params[paramName] = Number(value)
      conditions.push(`${alias}.${quoteIfNeeded(key)} = {${paramName}:Float64}`)
    } else {
      params[paramName] = String(value)
      conditions.push(`${alias}.${quoteIfNeeded(key)} = {${paramName}:String}`)
    }
  }

  return conditions
}

// ---------------------------------------------------------------------------
// Startup validation
// ---------------------------------------------------------------------------

function validateSchemas (): void {
  // Intentionally a no-throw check: log warnings only
  const schemaDir = path.join(__dirname, '../../../data/schemas')
  if (!fs.existsSync(schemaDir)) return

  const walkJson = (dir: string): string[] => {
    const results: string[] = []
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      if (entry.isDirectory()) {
        results.push(...walkJson(path.join(dir, entry.name)))
      } else if (entry.name.endsWith('.json')) {
        results.push(path.join(dir, entry.name))
      }
    }
    return results
  }

  for (const jsonPath of walkJson(schemaDir)) {
    try {
      const raw = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'))
      const accessibleReturn = raw.accessible_via?.return as string | undefined
      const tableName = raw.db_collection_name as string | undefined
      if (accessibleReturn == null || tableName == null) continue

      const chSchema = chSchemaRegistry.get(tableName)
      if (chSchema == null) continue

      const fields = accessibleReturn.split(',').map(f => f.trim())
      for (const field of fields) {
        if (field === '_id' || field === '_from' || field === '_to') continue
        if (!chSchema.columnsByName.has(field)) {
          console.warn(`[schema-validation] ${path.basename(jsonPath)}: field "${field}" in accessible_via.return not in ClickHouse table "${tableName}"`)
        }
      }
    } catch {
      // Skip files that fail to parse
    }
  }
}

validateSchemas()
