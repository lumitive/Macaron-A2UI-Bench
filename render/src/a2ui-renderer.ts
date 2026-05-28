import { v0_8 } from "@a2ui/lit";
import "./theme-provider.js";

type A2UIModelProcessorInstance = InstanceType<
  typeof v0_8.Data.A2uiMessageProcessor
>;

interface A2UIThemeProviderElement extends HTMLElement {
  surfaceId: string;
  surface: v0_8.Types.Surface;
  processor: A2UIModelProcessorInstance;
  requestUpdate(): void;
}

/**
 * A2UI Renderer with a single persistent processor for incremental updates
 * across multiple turns. The processor accumulates surface state so that
 * surfaceUpdate messages add/update components incrementally and
 * dataModelUpdate messages patch only changed data.
 *
 * Key insight: processMessages() mutates the Surface object in place
 * (rebuilding componentTree), but Lit only re-renders when property
 * *references* change. So after each turn we must force re-render
 * by destroying and recreating the DOM elements. The processor itself
 * is kept persistent — it accumulates component definitions and data
 * across turns, which is the whole point of incremental updates.
 */
export class A2UIRenderer {
  private processor: A2UIModelProcessorInstance;
  private container: HTMLElement;

  constructor(container: HTMLElement) {
    this.container = container;
    this.processor = v0_8.Data.createSignalA2uiMessageProcessor();
  }

  /**
   * Process a batch of A2UI messages for a single turn.
   * Uses the persistent processor for incremental updates.
   */
  processTurn(a2uiMessages: unknown[]): void {
    if (!a2uiMessages || a2uiMessages.length === 0) {
      return;
    }

    // Check for deleteSurface
    const hasDelete = a2uiMessages.some(
      (msg: any) => msg.deleteSurface !== undefined
    );

    if (hasDelete) {
      this.clear();
      return;
    }

    try {
      this.processor.processMessages(
        a2uiMessages as v0_8.Types.ServerToClientMessage[]
      );
    } catch (error) {
      console.error("[A2UIRenderer] Error processing messages:", error);
    }

    // Rebuild DOM from the current processor state.
    // The processor keeps accumulated state (components + data model),
    // but we must recreate the Lit elements because Lit uses reference
    // equality on the surface object — mutating componentTree in place
    // is invisible to Lit's change detection.
    this.rebuildDOM();
  }

  /**
   * Destroy existing DOM and recreate from current processor surfaces.
   */
  private rebuildDOM(): void {
    this.container.innerHTML = "";

    const surfaces = this.processor.getSurfaces();
    for (const [surfaceId, surface] of surfaces.entries()) {
      const providerEl = document.createElement(
        "a2ui-theme-provider"
      ) as A2UIThemeProviderElement;

      providerEl.surfaceId = surfaceId;
      providerEl.surface = surface;
      providerEl.processor = this.processor;
      providerEl.style.display = "block";

      this.container.appendChild(providerEl);
    }
  }

  /**
   * Clear all rendered surfaces and reset processor.
   */
  clear(): void {
    this.container.innerHTML = "";
    this.processor = v0_8.Data.createSignalA2uiMessageProcessor();
  }
}
