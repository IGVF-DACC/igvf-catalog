import { TRPCError } from '@trpc/server'
import { db } from '../../database'
import { configType } from '../../constants'

export type paramsFormatType = Record<string, string | number | boolean | undefined>

// Range/numeric filter operands (see getFilterStatements) are interpolated directly into
// AQL as bare tokens (unquoted), so a non-numeric value produces invalid/dangerous AQL
// instead of a clean validation error - e.g. `record['x'] == C5X2Cfnl1M75` gets parsed by
// ArangoDB as a collection/view reference and fails with "collection or view not found".
// Guard every such operand here before it reaches string interpolation.
function assertValidNumericOperand (field: string, raw: string | undefined): string {
  if (raw === undefined || raw.trim() === '' || isNaN(Number(raw)) || !isFinite(Number(raw))) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: `${field} must be a valid number. Received: "${raw ?? ''}"`
    })
  }
  return raw
}

export function distanceGeneVariant (geneStart: number, geneEnd: number, variantPos: number): number {
  return Math.min(Math.abs(variantPos - geneStart), Math.abs(variantPos - geneEnd))
}

// Validates page/limit and resolves the effective limit, mutating input by deleting
// `limit` (matching the existing applyLimit/getQueryLimit contract). Negative or
// fractional values are rejected outright rather than silently coerced - a negative
// limit previously slipped past the "cap at maxPageSize" check entirely (-1 <= 500 is
// true) and reached AQL's SLICE, whose negative-length semantics returned far more rows
// than the documented maximum.
export function resolveValidatedLimit (input: paramsFormatType, defaultLimit: number, maxPageSize: number): number {
  const page = input.page as number
  if (!Number.isInteger(page) || page < 0) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: `page must be a non-negative integer. Received: ${String(page)}`
    })
  }

  let limit = defaultLimit
  if (input.limit !== undefined) {
    const rawLimit = input.limit as number
    if (!Number.isInteger(rawLimit) || rawLimit <= 0) {
      throw new TRPCError({
        code: 'BAD_REQUEST',
        message: `limit must be a positive integer. Received: ${String(rawLimit)}`
      })
    }
    limit = rawLimit <= maxPageSize ? rawLimit : maxPageSize
    delete input.limit
  }
  return limit
}

// Some files_filesets.preferred_assay_titles values are a specific sub-type of a broader,
// also-valid preferred_assay_titles value, and callers filtering/grouping by the broader
// term shouldn't have to know about every specific variant - e.g. TAP-seq is a kind of
// Perturb-seq, so a TAP-seq record should surface both terms. Extend this map as more such
// groupings are identified.
const ASSAY_TITLE_GROUPS: Record<string, string[]> = {
  'TAP-seq': ['Perturb-seq']
}

export function expandPreferredAssayTitles (titles: string[] | null | undefined): string[] | null {
  if (titles == null || titles.length === 0) {
    return titles ?? null
  }
  const expanded = new Set(titles)
  titles.forEach(title => {
    ASSAY_TITLE_GROUPS[title]?.forEach(group => expanded.add(group))
  })
  return Array.from(expanded)
}

// Applies expandPreferredAssayTitles to every record in an array fetched from AQL (which
// returns files_filesets.preferred_assay_titles verbatim, un-expanded) that has the field -
// records from sources/paths that never attached it (e.g. verbose-mode object/string unions)
// are left untouched.
export function withExpandedAssayTitles <T> (records: T[]): T[] {
  records.forEach(record => {
    if (record != null && typeof record === 'object' && 'preferred_assay_titles' in record) {
      const typed = record as unknown as { preferred_assay_titles?: string[] | null }
      typed.preferred_assay_titles = expandPreferredAssayTitles(typed.preferred_assay_titles)
    }
  })
  return records
}

// The gene schema's `hgnc` property stores IDs with an `HGNC:` prefix (e.g. `HGNC:4232`),
// but the `hgnc_id` API param accepts the bare number. Any caller that filters on `hgnc`
// directly (rather than delegating to geneSearch()) must apply this same prefixing or the
// filter silently matches nothing.
export function withHgncPrefix (hgncId: string | number): string {
  const value = hgncId.toString()
  return value.startsWith('HGNC') ? value : `HGNC:${value}`
}

// String filter values are interpolated directly into single-quoted AQL literals (see
// getFilterStatements). An unescaped `'` in a value like gene_name or biological_context
// closes the literal early, letting the rest of the value be parsed as AQL - breaking the
// query or, worse, changing the predicate it evaluates. Escape backslashes and single
// quotes before interpolation, mirroring AQL's own string-escaping rules.
export function escapeAqlString (value: string | number): string {
  return value.toString().replace(/\\/g, '\\\\').replace(/'/g, "\\'")
}

export function validRegion (region: string): string[] | null {
  const regex: RegExp = /(chr\w+):(\d*)-(\d*)/

  if (regex.test(region)) {
    const breakdown = regex.exec(region)
    if (breakdown === null || breakdown.length < 4) {
      return null
    }
    const start = parseInt(breakdown[2])
    const end = parseInt(breakdown[3])
    if (start < end) {
      return breakdown
    }
  }

  return null
}

export function preProcessRegionParam (input: paramsFormatType, singleFieldRangeQueryDB: string | null = null, regionParamPrefix: string = ''): paramsFormatType {
  const newInput = { ...input } // cloning object

  let chrField = 'chr'
  let startField = 'start'
  let endField = 'end'
  let regionField = 'region'

  if (regionParamPrefix !== '') {
    chrField = `${regionParamPrefix}_${chrField}`
    startField = `${regionParamPrefix}_${startField}`
    endField = `${regionParamPrefix}_${endField}`
    regionField = `${regionParamPrefix}_${regionField}`
  }

  if (input[regionField] !== undefined) {
    const breakdown = validRegion(input[regionField] as string)

    if (breakdown != null) {
      newInput[chrField] = breakdown[1]

      if (singleFieldRangeQueryDB !== null) {
        newInput[singleFieldRangeQueryDB] = `range:${breakdown[2]}-${breakdown[3]}`
      } else {
        newInput.intersect = `${startField}-${endField}:${breakdown[2]}-${breakdown[3]}`
      }

      // eslint-disable-next-line @typescript-eslint/no-dynamic-delete
      delete newInput[regionField]
    } else {
      throw new TRPCError({
        code: 'BAD_REQUEST',
        message: 'Region format invalid. Please use the format as the example: "chr2:12345-54321". The end position must be greater than the start position.'
      })
    }
  }
  return newInput
}

// takes a list of ids and builds a dictionary where keys are ids and values are simplified objects from database
export async function verboseItems (ids: string[], schema: configType): Promise<Record<string, any>> {
  const verboseQuery = `
    FOR record in ${schema.db_collection_name as string}
    FILTER record._id in @ids
    RETURN {
      ${getDBReturnStatements(schema, true, '', [], false)}
    }`

  const objs = await (await db.query(verboseQuery, { ids: Array.from(ids) })).all()

  if (objs.length > 0) {
    const items: Record<string, any> = {}

    objs.forEach((obj: Record<string, any>) => {
      items[obj._id] = obj
    })
    return items
  } else {
    return {}
  }
}

// Generates aql RETURN statement, for the `return` list in a schema
// Example:
// for return statement based on schema: "return: _id, pos, name"
// outputs: "{ id: record._key, pos: record.pos, name: record.name }"
//
// Optional `returnKeyByField`: maps each field name from the schema return list to the JSON key
// in the response (DB attribute stays the same). Example: { db_field: 'api_field' }.
// Does not apply to `_id` (same as before: `_id: record._key` when `changeId` is true, else `'_id': record['_id']`).
export function getDBReturnStatements (
  schema: configType,
  simplified: boolean = false,
  extraReturn: string = '',
  skipFields: string[] = [],
  changeId: boolean = true,
  returnKeyByField?: Record<string, string>
): string {
  let schemaReturns = (schema.accessible_via as Record<string, string>).return.split(',').map((item: string) => item.trim())
  if (simplified && (schema.accessible_via as Record<string, string>).simplified_return) {
    schemaReturns = (schema.accessible_via as Record<string, string>).simplified_return.split(',').map((item: string) => item.trim())
  }

  const returns: string[] = []

  const filteredReturnFields = schemaReturns.filter(item => !skipFields.includes(item))
  filteredReturnFields.forEach((field: string) => {
    if (field === '_id' && changeId) {
      returns.push('_id: record._key')
    } else if (field === '_id') {
      returns.push(`'${field}': record['${field}']`)
    } else {
      const jsonKey = returnKeyByField?.[field] ?? field
      returns.push(`'${jsonKey}': record['${field}']`)
    }
  })

  if (extraReturn !== '') {
    returns.push(extraReturn)
  }

  return returns.join(', ')
}

// Generates aql FILTER parameters based on queryParams received from user
// Example:
// for the schema: 'coding_variants' and queryParams: { aaapos: "intersect:123-321", gene_name: "ACT1" }
// outpus: "record['aaapos:int'] >= 123 AND record['aaapos:int'] <= 321 AND record.gene_name == 'ACT1'"
export function getFilterStatements (
  schema: configType,
  queryParams: Record<string, string | number | boolean | undefined>,
  joinBy: string = 'and'
): string {
  const dbFilterBy: string[] = []

  Object.keys(queryParams).forEach((element: string) => {
    // reserved parameters for pagination and verbose mode
    if (element === 'page' || element === 'sort' || element === 'verbose' || element === 'limit') {
      return
    }

    if (queryParams[element] !== undefined) {
      const filterByRangeFields = (schema.accessible_via as Record<string, string>).filter_by_range?.split(',').map((item: string) => item.trim()) || []
      // 'interesect' is a reserved parameter for intersectional region search
      // 'annotation.af_ and bravo' are special cases for variant data
      if (filterByRangeFields.includes(element) || element === 'intersect' || element.startsWith('annotations.af_') || element.startsWith('annotations.bravo')) {
        const value = queryParams[element]?.toString()
        let stringOperator = null
        let operand = value as unknown as number

        if (value?.includes(':')) {
          const pair = value.split(':')
          stringOperator = pair[0]
          operand = pair[1] as unknown as number
        }

        // e.g: input['intersect'] = 'start-end:12345-54321'
        if (element === 'intersect') {
          const rangeValue = value?.split(':') as string[]
          const fieldOperands = rangeValue[0].split('-')
          const rangeOperands = rangeValue[1].split('-')
          assertValidNumericOperand(element, rangeOperands[0])
          assertValidNumericOperand(element, rangeOperands[1])

          // fieldOperands come from the DB field names this function itself builds
          // (see preProcessRegionParam), never raw user input - but since they're
          // interpolated as bare property names (unescapable), verify they're real
          // schema fields rather than trusting that invariant to hold forever.
          const schemaFields = schema.properties ? Object.keys(schema.properties) : []
          if (!schemaFields.includes(fieldOperands[0]) || !schemaFields.includes(fieldOperands[1])) {
            throw new TRPCError({
              code: 'BAD_REQUEST',
              message: `intersect must reference valid fields on the collection. Received: "${fieldOperands.join('-')}"`
            })
          }

          // e.g.:fieldOperands[0] = start, fieldOperands[1] = end
          // e.g.:rangeOperands[0] = 12345, rangeOperands[1] = 54321
          dbFilterBy.push(`record.${fieldOperands[0]} < ${rangeOperands[1]} AND record.${fieldOperands[1]} > ${rangeOperands[0]}`)
          return
        }

        if (stringOperator === 'range') {
          const rangeValue = value?.split(':') as string[]
          const rangeOperands = rangeValue[1].split('-')
          assertValidNumericOperand(element, rangeOperands[0])
          assertValidNumericOperand(element, rangeOperands[1])
          dbFilterBy.push(`record.${element} >= ${rangeOperands[0]} and record.${element} < ${rangeOperands[1]}`)
          return
        }

        let operator
        switch (stringOperator) {
          case 'gt':
            operator = '>'
            break
          case 'gte':
            operator = '>='
            break
          case 'lt':
            operator = '<'
            break
          case 'lte':
            operator = '<='
            break
          default:
            operator = '=='
        }
        assertValidNumericOperand(element, operand as unknown as string)
        dbFilterBy.push(`record['${element}'] ${operator} ${operand}`)
      } else {
        if (element === 'dbxrefs') {
          dbFilterBy.push(`'${escapeAqlString(queryParams[element] as string | number)}' in record.${element}[*].id`)
        } else if (schema.properties && Object.keys(schema.properties).includes(element) && ((schema.properties)[element].type === 'array' || (schema.properties)[element].type.includes('array'))) {
          dbFilterBy.push(`'${escapeAqlString(queryParams[element] as string | number)}' in record.${element}`)
        } else if (schema.properties && Object.keys(schema.properties).includes(element) && ((schema.properties)[element].type === 'integer' || (schema.properties)[element].type === 'number' || (schema.properties)[element].type.includes('integer') || (schema.properties)[element].type.includes('number'))) {
          assertValidNumericOperand(element, queryParams[element]?.toString())
          dbFilterBy.push(`record.${element} == ${queryParams[element] as string | number}`)
        } else if (schema.properties && Object.keys(schema.properties).includes(element) && ((schema.properties)[element].type === 'boolean' || (schema.properties)[element].type.includes('boolean'))) {
          dbFilterBy.push(`record.${element} == ${queryParams[element] as string}`)
        } else {
          dbFilterBy.push(`record.${element} == '${escapeAqlString(queryParams[element] as string | number)}'`)
        }
      }
    }
  })
  return dbFilterBy.join(` ${joinBy} `) // default: 'and'
}
