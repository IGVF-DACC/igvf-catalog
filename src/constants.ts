import { z } from 'zod'

export const chrEnum = [
  '1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
  '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
  '21', '22', 'x', 'y'
] as const

export const ancestryGroups = [
  'AFR', // African / African American
  'AMI', // Amish
  'AMR', // Latino / Admixed American
  'ASJ', // Ashkenazi Jewish'
  'EAS', // East Asian
  'FIN', // European (Finnish)
  'MID', // Middle Eastern
  'EUR', // European (Non-Finnish)
  'SAS' // South Asian
] as const

export interface configType {
  $id?: string
  $schema?: string
  db_collection_name?: string
  accessible_via?: {
    filter_by_range?: string
    simplified_return?: string
    return?: string
    [key: string]: any
  }
  properties?: Record<string, any>
  required?: string[]
  allOf?: any[]
  type?: string
  [key: string]: any
}

export const QUERY_LIMIT: number = 25
export const PROPERTIES_TO_ZOD_MAPPING: Record<string, z.ZodType> = {
  str: z.string().optional(),
  int: z.number().optional(),
  boolean: z.boolean().optional()
}

export const edgeArangoDB = z.object({
  _key: z.string(),
  _id: z.string(),
  _from: z.string(),
  _to: z.string(),
  _rev: z.string(),
  name: z.string()
})

const pathSchema = z.object({
  vertices: z.array(z.any()),
  edges: z.array(edgeArangoDB)
})
export type PathArangoDB = z.infer<typeof pathSchema>

const edgeSchema = z.object({
  to: z.string(),
  from: z.string(),
  name: z.string()
})
export type Edge = z.infer<typeof edgeSchema>

const pathsSchema = z.object({
  vertices: z.record(z.string(), z.any()),
  paths: z.array(z.array(edgeSchema))
})
export type Paths = z.infer<typeof pathsSchema>
