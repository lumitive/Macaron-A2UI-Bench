# Upstream Notes

This repository vendors selected files from local source trees in order to make the benchmark package independently runnable.

- `vendor/a2ui_demo/`: validation/schema assets copied from the local `a2ui_demo` checkout.
- `render/vendor/a2ui/renderers/`: renderer package dependencies copied from the local `A2UI/renderers` checkout.
- `render/`: renderer harness copied from the local `A2UI-Bench/render` project and adjusted for standalone use.

If you update the vendored code, keep the corresponding upstream licenses and notices intact.
