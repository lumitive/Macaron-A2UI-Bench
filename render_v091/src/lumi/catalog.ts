import { Catalog } from "@a2ui/web_core/v0_9";
import { basicCatalog } from "@a2ui/lit/v0_9";
import type { LitComponentApi } from "@a2ui/lit/v0_9";
import { A2uiCarousel } from "./carousel";

export const LUMI_CATALOG_ID = "lumi.ai:a2ui:lumi-catalog";

/**
 * LUMI catalog: official basic types + Carousel (MVP unique).
 * Passed alongside basicCatalog so MessageProcessor can resolve either catalogId.
 */
export const lumiCatalog = new Catalog<LitComponentApi>(
  LUMI_CATALOG_ID,
  [...basicCatalog.components.values(), A2uiCarousel as LitComponentApi],
  [...basicCatalog.functions.values()],
);
