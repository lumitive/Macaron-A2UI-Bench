# Renderer (A2UI v0.9.1)

Vite + Lit harness for A2UI **v0.9.1** messages. Parallel to `render/` (0.8); does not replace it.

## Upstream pin

See `UPSTREAM_PIN.txt` (same SHA as `protocol/v0_9_1/UPSTREAM_PIN.txt`).

Vendored from [a2ui-project/a2ui](https://github.com/a2ui-project/a2ui):

- `vendor/a2ui/renderers/lit` → `@a2ui/lit`
- `vendor/a2ui/renderers/web_core` → `@a2ui/web_core`
- `vendor/a2ui/specification/{v0_8,v0_9,v1_0}` (schemas copied into web_core at build time)

## Import path (Lit `v0_9`)

Protocol wire format is v0.9.1, but the upstream Lit package export is **`./v0_9`** (there is no `./v0_9_1` module).

| Symbol | Import |
|--------|--------|
| `basicCatalog`, `A2uiSurface` | `@a2ui/lit/v0_9` |
| `MessageProcessor` | `@a2ui/web_core/v0_9` |

Ingest API: `new MessageProcessor([basicCatalog], undefined, { version: "v0.9.1" })` then `processor.processMessages(messages)`. Surfaces render via `<a2ui-surface .surface=${surfaceModel}>`.

Do **not** use `@a2ui/lit/v0_8` or the deprecated root `v0_8` re-export for this harness.

## Setup

```bash
cd render_v091
npm ci
```

## Dev server

Default port **5174** (0.8 harness keeps 5173):

```bash
npm run dev -- --host 127.0.0.1 --port 5174
```

## URL query contract

Compatible with `visual_eval._build_render_url`:

- `a2ui` — JSON-encoded message array
- `maxWidth`, `maxHeight`, `padding` — stage sizing

Automation hook: `window.__A2UI_RENDER__` with `reset()` / `processTurn(messages)`.

## Build

```bash
npm run build
```

## CI note: `@a2ui/web_core/v0_9` resolution

Upstream `web_core` package exports point at `dist/`, which is gitignored in the vendor tree. Fresh CI checkouts therefore cannot resolve `@a2ui/web_core/v0_9`. This bench remaps the `./v0_9` and `./v0_9/basic_catalog` exports in `vendor/a2ui/renderers/web_core/package.json` to the committed TypeScript sources under `src/v0_9/`, and tracks `src/v0_9/schemas/` (normally copy-spec output) so `tsc` can resolve `server_to_client.json` and related imports.
