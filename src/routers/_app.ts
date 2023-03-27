import { router } from "../trpc";

import { genericRouters } from "./genericRouters/genericRouters";

import { regions } from "./regionSearch";
import { variantCorrelations } from "./variantCorrelations";
import { eqtls } from "./eqtls";

const customRouters = {
  regions,
  variantCorrelations,
  eqtls,
};

export const appRouter = router({ ...genericRouters, ...customRouters });

export type igvfCatalogRouter = typeof appRouter;
