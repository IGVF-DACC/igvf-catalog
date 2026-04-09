import { Database } from 'arangojs'
import { DEFAULT_KEEP_ALIVE, DEFAULT_MAX_SOCKETS, DEFAULT_TIMEOUT, envData } from './env'

const dbConfig = envData.database

interface Configuration {
  url: string
  databaseName: string
  auth: {
    username: string
    password: string
  }
  agentOptions?: {
    connections: number
    pipelining: number
    timeout: number
  }
}

const configuration: Configuration = {
  url: dbConfig.connectionUri,
  databaseName: dbConfig.dbName,
  auth: {
    username: dbConfig.auth.username,
    password: dbConfig.auth.password
  },
  agentOptions: {
    connections: dbConfig.agentOptions?.connections ?? DEFAULT_MAX_SOCKETS,
    pipelining: dbConfig.agentOptions?.pipelining ?? DEFAULT_KEEP_ALIVE,
    timeout: dbConfig.agentOptions?.timeout ?? DEFAULT_TIMEOUT
  }
}

export const db = new Database(configuration)
