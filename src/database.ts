import { Database } from 'arangojs'
import { envData } from './env'
import { Agent } from 'undici'

const dbConfig = envData.database

interface Configuration {
  url: string
  databaseName: string
  auth: {
    username: string
    password: string
  }
  fetchOptions: {
    dispatcher: Agent
  }
}

const configuration: Configuration = {
  url: dbConfig.connectionUri,
  databaseName: dbConfig.dbName,
  auth: {
    username: dbConfig.auth.username,
    password: dbConfig.auth.password
  },
  fetchOptions: {
    dispatcher: new Agent({ pipelining: 0 })
  }
}

export const db = new Database(configuration)
