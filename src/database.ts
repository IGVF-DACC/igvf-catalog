import { Database } from "arangojs";
import { envData } from "./env";

const dbConfig = envData.database;

export const db = new Database({
  url: dbConfig.connectionUri,
  databaseName: dbConfig.dbName,
  auth: {
    username: dbConfig.auth.username,
    password: dbConfig.auth.password,
  },
});
