import { z } from "zod";
import envConfig from "../config/development.json";

const envSchema = z.object({
  environment: z.string(),
  host: z.object({
    protocol: z.enum(["http", "https"]),
    hostname: z.string(),
    port: z.number(),
  }),
  database: z.object({
    connectionUri: z.string(),
    dbName: z.string(),
    auth: z.object({
      username: z.string(),
      password: z.string(),
    }),
  }),
});

let config = envConfig;
if (typeof process.env.ENV !== "undefined") {
  const envPath = "../config/" + process.env.ENV + ".json";
  config = require(envPath);
}

const env = envSchema.safeParse(config);

if (!env.success) {
  console.error(
    "❌ Invalid environment config:",
    JSON.stringify(env.error.format(), null, 2)
  );
  process.exit(1);
}

export const envData = env.data;
