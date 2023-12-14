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

export type configType = Record<string, string | Record<string, string>>

export const schemaConfigFilePath = './data/schema-config.yaml'

export const QUERY_LIMIT: number = 25
export const PROPERTIES_TO_ZOD_MAPPING: Record<string, z.ZodType> = {
  str: z.string().optional(),
  int: z.number().optional(),
  boolean: z.boolean().optional()
}

export const edgeSchemaDB = z.object({
  _key: z.string(),
  _id: z.string(),
  _from: z.string(),
  _to: z.string(),
  _rev: z.string(),
  type: z.string()
})

const pathSchema = z.object({
  vertices: z.array(z.any()),
  edges: z.array(edgeSchemaDB)
})
export type PathDB = z.infer<typeof pathSchema>
