import { z } from 'zod'
import envConfig from '../config/development.json'

const DEFAULT_PORT = '2023'

const envSchema = z.object({
  environment: z.string(),
  host: z.object({
    protocol: z.enum(['http', 'https']),
    hostname: z.string(),
    port: z.number()
  }),
  database: z.object({
    url: z.string(),
    name: z.string(),
    username: z.string(),
    password: z.string()
  }),
  catalog_llm_query_service_url: z.string()
})

const config = envConfig

// Support both ENV and NODE_ENV for environment selection
const environment = process.env.ENV ?? process.env.NODE_ENV

if (typeof environment !== 'undefined') {
  config.environment = environment

  if (environment === 'production') {
    config.host.protocol = process.env.IGVF_CATALOG_PROTOCOL ?? config.host.protocol
    config.host.hostname = process.env.IGVF_CATALOG_HOSTNAME ?? config.host.hostname
    config.host.port = parseInt(process.env.IGVF_CATALOG_PORT ?? DEFAULT_PORT) ?? config.host.port
    config.database.url = process.env.IGVF_CATALOG_CLICKHOUSE_URL ?? config.database.url
    config.database.name = process.env.IGVF_CATALOG_CLICKHOUSE_DBNAME ?? config.database.name
    config.database.username = process.env.IGVF_CATALOG_CLICKHOUSE_USERNAME ?? config.database.username
    config.database.password = process.env.IGVF_CATALOG_CLICKHOUSE_PASSWORD ?? config.database.password
    config.catalog_llm_query_service_url = process.env.IGVF_CATALOG_LLM_QUERY_SERVICE_URL ?? config.catalog_llm_query_service_url
  }
}

const env = envSchema.safeParse(config)

if (!env.success) {
  console.error('Invalid environment config:', JSON.stringify(env.error.format(), null, 2))
  process.exit(1)
}

export const envData = env.data
