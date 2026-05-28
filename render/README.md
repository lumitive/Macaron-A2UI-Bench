# Renderer

Bundled A2UI renderer project used by the optional visual evaluation pipeline.

## Setup

```bash
cd render
npm install
```

## Start Dev Server

```bash
npm run dev -- --host 127.0.0.1 --port 5173
```

## Render a Dialogue JSON File

```bash
npm run render -- --input /path/to/dialogues.json --out ./output
```

`--input` is required. `--out` defaults to `./output`.

The visual-eval scripts in the repository only require the dev server to be running; you do not need to use `scripts/render.ts` unless you want standalone screenshot generation.
