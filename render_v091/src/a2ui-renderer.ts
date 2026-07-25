import { A2uiSurface, basicCatalog } from "@a2ui/lit/v0_9";
import type { LitComponentApi } from "@a2ui/lit/v0_9";
import { MessageProcessor } from "@a2ui/web_core/v0_9";
import { lumiCatalog } from "./lumi/catalog";

// Ensure <a2ui-surface> (and basic catalog custom elements) are registered.
void A2uiSurface;
void basicCatalog;
void lumiCatalog;

type SurfaceElement = InstanceType<typeof A2uiSurface>;

/**
 * A2UI v0.9.1 renderer with a persistent MessageProcessor for incremental
 * updates across turns. Uses upstream Lit export `@a2ui/lit/v0_9` (not v0_8,
 * not a fictional v0_9_1 module) plus MessageProcessor from web_core.
 *
 * Registers both official basic and LUMI catalogs so createSurface.catalogId
 * can select either.
 *
 * Unlike 0.8, surfaces are reactive SurfaceModel instances. We still rebuild
 * the host DOM after each turn so newly created surfaces appear and deleted
 * ones disappear for Playwright capture.
 */
export class A2UIRenderer {
  private processor: MessageProcessor<LitComponentApi>;
  private container: HTMLElement;

  constructor(container: HTMLElement) {
    this.container = container;
    this.processor = this.createProcessor();
  }

  private createProcessor(): MessageProcessor<LitComponentApi> {
    return new MessageProcessor([basicCatalog, lumiCatalog], undefined, {
      version: "v0.9.1",
    });
  }

  /**
   * Process a batch of A2UI messages for a single turn.
   * Uses the persistent processor for incremental updates.
   */
  processTurn(a2uiMessages: unknown[]): void {
    if (!a2uiMessages || a2uiMessages.length === 0) {
      return;
    }

    // Mirror 0.8 harness: any deleteSurface short-circuits to a full clear.
    const hasDelete = a2uiMessages.some(
      (msg: any) => msg.deleteSurface !== undefined
    );

    if (hasDelete) {
      this.clear();
      return;
    }

    try {
      this.processor.processMessages(a2uiMessages as any);
    } catch (error) {
      console.error("[A2UIRenderer] Error processing messages:", error);
    }

    this.rebuildDOM();
  }

  private rebuildDOM(): void {
    this.container.innerHTML = "";

    for (const [surfaceId, surface] of this.processor.model.surfacesMap.entries()) {
      const surfaceEl = document.createElement("a2ui-surface") as SurfaceElement;
      surfaceEl.surface = surface;
      surfaceEl.dataset.surfaceId = surfaceId;
      surfaceEl.style.display = "block";
      this.container.appendChild(surfaceEl);
    }
  }

  /**
   * Clear all rendered surfaces and reset processor.
   */
  clear(): void {
    this.container.innerHTML = "";
    this.processor.model.dispose();
    this.processor = this.createProcessor();
  }
}
