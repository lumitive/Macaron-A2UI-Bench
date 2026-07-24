import { A2UIRenderer } from "./a2ui-renderer.js";

const surfaceContainerEl = document.getElementById("surface-container");
const surfaceFrameEl = document.getElementById("surface-frame");
if (!surfaceContainerEl) {
  throw new Error("Missing #surface-container element");
}
if (!surfaceFrameEl) {
  throw new Error("Missing #surface-frame element");
}

const surfaceContainer = surfaceContainerEl;
const surfaceFrame = surfaceFrameEl;

const renderer = new A2UIRenderer(surfaceContainer);

function hasDelete(messages: unknown[]): boolean {
  return messages.some((msg: any) => msg?.deleteSurface !== undefined);
}

function waitForFrames(count = 2): Promise<void> {
  return new Promise((resolve) => {
    const step = (remaining: number) => {
      if (remaining <= 0) {
        resolve();
        return;
      }
      requestAnimationFrame(() => step(remaining - 1));
    };
    step(count);
  });
}

const renderApi = {
  reset(): void {
    renderer.clear();
  },
  async processTurn(messages: unknown[]): Promise<{ shouldCapture: boolean }> {
    if (!messages || messages.length === 0) {
      return { shouldCapture: false };
    }

    const deleted = hasDelete(messages);
    renderer.processTurn(messages);
    await waitForFrames(2);

    return { shouldCapture: !deleted };
  },
};

// @ts-ignore - exposed for Playwright automation
window.__A2UI_RENDER__ = renderApi;

function setRenderStatus(status: string, detail = ""): void {
  document.body.setAttribute("data-render-status", status);
  document.body.setAttribute("data-render-detail", detail);
}

function parsePositiveNumber(raw: string | null, fallback: number): number {
  const value = raw == null ? NaN : Number(raw);
  return Number.isFinite(value) && value > 0 ? value : fallback;
}

async function bootstrapQueryRender(): Promise<void> {
  const params = new URLSearchParams(window.location.search);
  const rawA2ui = params.get("a2ui");
  if (!rawA2ui) {
    return;
  }

  setRenderStatus("loading");
  try {
    const stageWidth = parsePositiveNumber(params.get("maxWidth"), 420);
    const stageMaxHeight = parsePositiveNumber(params.get("maxHeight"), 1600);
    const stagePadding = parsePositiveNumber(params.get("padding"), 24);

    surfaceFrame.style.width = `${stageWidth}px`;
    surfaceFrame.style.maxWidth = `${stageWidth}px`;
    surfaceFrame.style.padding = `${stagePadding}px`;
    surfaceFrame.style.minHeight = "0";
    surfaceFrame.style.maxHeight = `${stageMaxHeight}px`;

    const parsed = JSON.parse(rawA2ui);
    if (!Array.isArray(parsed)) {
      throw new Error("'a2ui' must decode to an array.");
    }

    renderApi.reset();
    const result = await renderApi.processTurn(parsed);
    await waitForFrames(2);

    if (!result.shouldCapture || surfaceContainer.children.length === 0) {
      throw new Error("No renderable surface was produced.");
    }

    setRenderStatus("ready");
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error);
    setRenderStatus("error", detail);
    console.error("[render-query]", error);
  }
}

void bootstrapQueryRender();
