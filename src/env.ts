import { z } from 'zod'
import envConfig from '../config/development.json'

const DEFAULT_PORT = '2023'
const DEFAULT_MAX_SOCKETS = 5
const DEFAULT_KEEP_ALIVE = 'true'
const DEFAULT_TIMEOUT = 60000

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
    }),
    agentOptions: z.object({
      maxSockets: z.number(),
      keepAlive: z.boolean(),
      timeout: z.number()
    }).optional()
  }),
  catalog_llm_query_service_url: z.string()
})

const config = envConfig

// Support both ENV and NODE_ENV for environment selection
const environment = process.env.ENV ?? process.env.NODE_ENV

if (typeof environment !== 'undefined') {
  config.environment = environment

  // Only load environment variables in production mode (cdk deploy)
  if (environment === 'production') {
    config.host.protocol = process.env.IGVF_CATALOG_PROTOCOL ?? config.host.protocol
    config.host.hostname = process.env.IGVF_CATALOG_HOSTNAME ?? config.host.hostname
    config.host.port = parseInt(process.env.IGVF_CATALOG_PORT ?? DEFAULT_PORT) ?? config.host.port
    config.database.connectionUri = process.env.IGVF_CATALOG_ARANGODB_URI ?? config.database.connectionUri
    config.database.dbName = process.env.IGVF_CATALOG_ARANGODB_DBNAME ?? config.database.dbName
    config.database.auth.username = process.env.IGVF_CATALOG_ARANGODB_USERNAME ?? config.database.auth.username
    config.database.auth.password = process.env.IGVF_CATALOG_ARANGODB_PASSWORD ?? config.database.auth.password
    config.database.agentOptions.maxSockets = process.env.IGVF_CATALOG_ARANGODB_AGENT_MAX_SOCKETS !== undefined ? parseInt(process.env.IGVF_CATALOG_ARANGODB_AGENT_MAX_SOCKETS) : (config.database.agentOptions?.maxSockets ?? DEFAULT_MAX_SOCKETS)
    config.database.agentOptions.keepAlive = process.env.IGVF_CATALOG_ARANGODB_AGENT_KEEP_ALIVE !== undefined ? (process.env.IGVF_CATALOG_ARANGODB_AGENT_KEEP_ALIVE === 'true') : (config.database.agentOptions?.keepAlive ?? DEFAULT_KEEP_ALIVE)
    config.database.agentOptions.timeout = process.env.IGVF_CATALOG_ARANGODB_AGENT_TIMEOUT !== undefined ? parseInt(process.env.IGVF_CATALOG_ARANGODB_AGENT_TIMEOUT) : (config.database.agentOptions?.timeout ?? DEFAULT_TIMEOUT)
    config.catalog_llm_query_service_url = process.env.IGVF_CATALOG_LLM_QUERY_SERVICE_URL ?? config.catalog_llm_query_service_url
  }
}

const env = envSchema.safeParse(config)

if (!env.success) {
  console.error('❌ Invalid environment config:', JSON.stringify(env.error.format(), null, 2))
  process.exit(1)
}

export const envData = env.data
