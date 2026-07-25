/**
 * LUMI Carousel MVP: same ChildList layout as Row; reuses the basic Row
 * custom element for render (lint≡render via LUMI catalogId + type name).
 */
import { RowApi } from "@a2ui/web_core/v0_9/basic_catalog";
import type { ComponentApi } from "@a2ui/web_core/v0_9";

export const CarouselApi = {
  name: "Carousel",
  schema: RowApi.schema,
} satisfies ComponentApi;

/** Register as Carousel while rendering with the basic Row element. */
export const A2uiCarousel = {
  ...CarouselApi,
  tagName: "a2ui-basic-row",
};
