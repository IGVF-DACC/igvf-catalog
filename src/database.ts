import { Database } from 'arangojs'
import { envData } from './env'

const dbConfig = envData.database

interface Configuration {
  url: string
  databaseName: string
  auth: {
    username: string
    password: string
  }
}

const configuration: Configuration = {
  url: dbConfig.connectionUri,
  databaseName: dbConfig.dbName,
  auth: {
    username: dbConfig.auth.username,
    password: dbConfig.auth.password
  }
}

export const db = new Database(configuration)
