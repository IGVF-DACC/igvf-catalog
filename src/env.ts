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
    connectionUri: z.string(),
    dbName: z.string(),
    auth: z.object({
      username: z.string(),
      password: z.string()
    })
  }),
  openai_api_key: z.string(),
  openai_model: z.string(),
  catalog_llm_query: z.string()
})

let config = envConfig
if (typeof process.env.ENV !== 'undefined') {
  const envPath = '../config/' + process.env.ENV + '.json'
  config = require(envPath)

  // ENV variables are priority and defaults to config file
  if (process.env.ENV === 'production') {
    config.environment = 'production'
    config.host.protocol = process.env.IGVF_CATALOG_PROTOCOL ?? config.host.protocol
    config.host.hostname = process.env.IGVF_CATALOG_HOSTNAME ?? config.host.hostname
    config.host.port = parseInt(process.env.IGVF_CATALOG_PORT ?? DEFAULT_PORT) ?? config.host.port
    config.database.connectionUri = process.env.IGVF_CATALOG_ARANGODB_URI ?? config.database.connectionUri
    config.database.dbName = process.env.IGVF_CATALOG_ARANGODB_DBNAME ?? config.database.dbName
    config.database.auth.username = process.env.IGVF_CATALOG_ARANGODB_USERNAME ?? config.database.auth.username
    config.database.auth.password = process.env.IGVF_CATALOG_ARANGODB_PASSWORD ?? config.database.auth.password
  }
}

const env = envSchema.safeParse(config)

if (!env.success) {
  console.error('❌ Invalid environment config:', JSON.stringify(env.error.format(), null, 2))
  process.exit(1)
}

export const envData = env.data
