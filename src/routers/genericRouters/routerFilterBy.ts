import { Router } from "./routerFactory";
import { z } from "zod";
import { db } from "../../database";
import { TRPCError } from "@trpc/server";
import { publicProcedure } from "../../trpc";
import {
  configType,
  QUERY_LIMIT,
  PROPERTIES_TO_ZOD_MAPPING,
} from "../../constants";

export class RouterFilterBy implements Router {
  apiName: string;
  apiSpecs: Record<string, string>;
  properties: Record<string, string>;
  filterBy: string[];
  filterByRange: string[];
  fuzzyTextSearch: string[];
  output: string[];
  hasGetByIDEndpoint: boolean;
  dbCollectionName: string;
  dbCollectionPerChromosome: boolean;
  dbReturnStatements: string;

  constructor(schemaObj: configType) {
    this.apiSpecs = schemaObj.accessible_via as Record<string, string>;
    this.apiName = this.apiSpecs.name;
    this.properties = schemaObj.properties as Record<string, string>;
    this.filterBy =
      this.apiSpecs.filter_by?.split(",").map((item: string) => item.trim()) ||
      [];
    this.filterByRange =
      this.apiSpecs.filter_by_range
        ?.split(",")
        .map((item: string) => item.trim()) || [];
    this.output = this.apiSpecs.return
      .split(",")
      .map((item: string) => item.trim());
    this.hasGetByIDEndpoint = this.filterBy.includes("_id");
    this.fuzzyTextSearch =
      this.apiSpecs.fuzzy_text_search
        ?.split(",")
        .map((item: string) => item.trim()) || [];
    this.dbCollectionName = schemaObj.db_collection_name as string;
    this.dbCollectionPerChromosome = !!schemaObj.db_collection_per_chromosome;

    const returns: string[] = [];
    this.output.forEach((field: string) => {
      if (field === "_id") {
        returns.push("_id: record._key");
      } else if (this.properties[field] === "int") {
        returns.push(`${field}: record['${field}:long']`);
      } else {
        returns.push(`'${field}': record['${field}']`);
      }
    });
    this.dbReturnStatements = returns.join(", ");
  }

  getFilterStatements(
    queryParams: Record<string, string | number | undefined>
  ): string {
    const dbFilterBy: string[] = [];

    Object.keys(queryParams).forEach((element: string) => {
      if (queryParams[element] !== undefined) {
        if (this.filterByRange.includes(element)) {
          if (element === "start") {
            dbFilterBy.push(
              `record['start:long'] >= ${queryParams[element] as number}`
            );
          } else if (element === "end") {
            dbFilterBy.push(
              `record['end:long'] <= ${queryParams[element] as number}`
            );
          }
        } else {
          dbFilterBy.push(
            `record.${element} == '${queryParams[element] as string | number}'`
          );
        }
      }
    });

    if (dbFilterBy.length === 0) {
      throw new TRPCError({
        code: "BAD_REQUEST",
        message: "At least one parameter must be defined.",
      });
    }

    return dbFilterBy.join(" and ");
  }

  async getObjects(
    queryParams: Record<string, string | number | undefined>
  ): Promise<any[]> {
    let collectionName = this.dbCollectionName;
    if (this.dbCollectionPerChromosome) {
      collectionName = `${this.dbCollectionName}_${queryParams.chr as string}`;
    }

    let page = 0;
    if (Object.hasOwn(queryParams, "page")) {
      page = parseInt(queryParams.page as string);
    }

    const query = `
      FOR record IN ${collectionName}
      FILTER ${this.getFilterStatements(queryParams)}
      LIMIT ${page}, ${QUERY_LIMIT}
      RETURN { ${this.dbReturnStatements} }
    `;

    const cursor = await db.query(query);
    return await cursor.all();
  }

  resolveTypes(params: string[], addID: boolean): z.ZodType {
    const paramTypes: Record<string, z.ZodType> = {};

    params
      .filter((p) => addID || p !== "_id")
      .forEach((param: string) => {
        paramTypes[param] =
          PROPERTIES_TO_ZOD_MAPPING[this.properties[param]] ??
          z.string().optional();
      });

    return z.object(paramTypes);
  }

  generateRouter(): any {
    const path = `/${this.apiName}` as const;
    const inputFormat = this.resolveTypes(
      [...this.filterBy, ...this.filterByRange],
      false
    );
    const outputFormat = z.array(this.resolveTypes(this.output, true));

    return publicProcedure
      .meta({
        openapi: {
          method: "GET",
          path,
          description: this.apiSpecs.description,
        },
      })
      .input(inputFormat)
      .output(outputFormat)
      .query(async ({ input }) => await this.getObjects(input));
  }
}
