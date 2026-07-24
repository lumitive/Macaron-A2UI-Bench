# Upstream Notes

This repository vendors selected files from local source trees in order to make the benchmark package independently runnable.

## Dual protocol stacks

The benchmark runs **one stack per invocation**, selected by `--protocol-version` or `PROTOCOL_VERSION`:

| Stack | Default | Lint / schema assets | Renderer harness | Dev port |
|-------|---------|----------------------|------------------|----------|
| **v0.9.1** | yes | `protocol/v0_9_1/` + upstream catalog refs | `render_v091/` | 5174 |
| **v0.8** | legacy comparison | `protocol/v0_8/` + `vendor/a2ui_demo/` | `render/` | 5173 |

Results are written under `results/<protocol-version>/`. The 0.8 stack is retained permanently for version-comparison experiments; it is not removed when 0.9.1 is the default.

## Vendored trees

- `vendor/a2ui_demo/`: validation/schema assets copied from the local `a2ui_demo` checkout (0.8 stack).
- `render/vendor/a2ui/renderers/`: renderer package dependencies copied from the local `A2UI/renderers` checkout (0.8 harness).
- `render/`: **v0.8** renderer harness copied from the local `A2UI-Bench/render` project and adjusted for standalone use.
- `render_v091/`: **v0.9.1** renderer harness (parallel to `render/`; does not replace it).

If you update the vendored code, keep the corresponding upstream licenses and notices intact.
