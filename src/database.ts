import { createClient } from '@clickhouse/client'
import { envData } from './env'

const dbConfig = envData.database

export const db = createClient({
  url: dbConfig.url,
  database: dbConfig.name,
  username: dbConfig.username,
  password: dbConfig.password,
  request_timeout: 60_000
})
