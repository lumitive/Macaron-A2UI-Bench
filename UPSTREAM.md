# Upstream Notes

This repository (**LUMI-A2UI-Bench**) vendors selected files from local source trees in order to make the benchmark package independently runnable.

## Dual protocol stacks

The benchmark runs **one stack per invocation**, selected by `--protocol-version` or `PROTOCOL_VERSION`:

| Stack | Default | Lint / schema assets | Renderer harness | Dev port |
|-------|---------|----------------------|------------------|----------|
| **v0.9.1** | yes | `protocol/v0_9_1/` + upstream catalog refs; optional `--protocol-catalog lumi` | `render_v091/` | 5174 |
| **v0.8** | legacy comparison | `protocol/v0_8/` + `vendor/a2ui_demo/` | `render/` | 5173 |

Results are written under `results/<protocol-version>/`. The 0.8 stack is retained permanently for version-comparison experiments; it is not removed when 0.9.1 is the default.

## Vendored trees

- `vendor/a2ui_demo/`: **LUMI 0.8 heritage source** — validation/schema assets copied from the local `a2ui_demo` checkout (0.8 stack; source for Track 2 LUMI 0.9.1 catalog mapping).
- `render/vendor/a2ui/renderers/`: renderer package dependencies copied from the local `A2UI/renderers` checkout (0.8 harness).
- `render/`: **v0.8** renderer harness (npm package `lumi-a2ui-bench-render`).
- `render_v091/`: **v0.9.1** renderer harness (npm package `lumi-a2ui-bench-render-v091`; parallel to `render/`; does not replace it).

If you update the vendored code, keep the corresponding upstream licenses and notices intact.
