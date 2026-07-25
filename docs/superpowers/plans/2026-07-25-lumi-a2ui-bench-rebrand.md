# LUMI-A2UI-Bench Rebrand (Track 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fully rebrand the product from Macaron A2UI Bench to **LUMI-A2UI-Bench** in user-facing names, packages, and docs while preserving heritage paths and upstream licenses.

**Architecture:** Text/metadata rename only—no protocol behavior changes. Keep `vendor/a2ui_demo` on disk; document it as the LUMI 0.8 heritage source. New LUMI 0.9.1 assets land in Track 2 under namespaced paths.

**Tech Stack:** Markdown docs, npm `package.json` / lockfile name fields, GitHub repo metadata via `gh`.

## Global Constraints

- Product name: **LUMI-A2UI-Bench** / **LUMI A2UI Bench** (display).
- Do not invent an `a2ui.org` catalogId for LUMI.
- Do not rewrite upstream Google/A2UI license headers.
- Do not delete 0.8 stack or rename `vendor/a2ui_demo` in this track.
- Spec: `docs/superpowers/specs/2026-07-25-lumi-a2ui-bench-product-design.md`.

---

## File map

| File | Responsibility |
|------|----------------|
| `README.md` | Primary product title + intro |
| `UPSTREAM.md` | Dual-stack notes; brand language |
| `render/package.json`, `render/package-lock.json` | npm package name |
| `render_v091/package.json`, `render_v091/package-lock.json` | npm package name |
| `.github/workflows/ci.yml` | Job display names if Macaron/a2ui-bench branded |
| `docs/superpowers/specs/*.md`, `plans/*.md` | Body text: Macaron-extended → LUMI-extended where product-facing; keep historical “Macaron” in dated Phase-1 titles if needed with a one-line note |
| `docs/compatibility-scorecard.md` | Living D1–D8 table (create) |
| GitHub repo | `gh repo rename` / description (requires owner approval on remote) |

---

### Task 1: Inventory remaining brand strings

- [ ] Run: `rg -n -i 'Macaron|a2ui-bench-render|Macaron-A2UI' --glob '!**/vendor/**' --glob '!**/node_modules/**' --glob '!**/dist/**'`
- [ ] Save hit list in the PR description (paths only).
- [ ] Commit not required yet.

### Task 2: Rename npm packages

- [ ] In `render/package.json` set `"name": "lumi-a2ui-bench-render"`.
- [ ] In `render_v091/package.json` set `"name": "lumi-a2ui-bench-render-v091"`.
- [ ] Update matching `"name"` fields in both `package-lock.json` files (root + `packages[""]`).
- [ ] Run: `cd render && npm run build` and `cd render_v091 && npm run build` (expect pass; name-only).
- [ ] Commit: `chore(brand): rename render packages to lumi-a2ui-bench-*`

### Task 3: README + UPSTREAM + CI display names

- [ ] Change `README.md` H1 to `# LUMI A2UI Bench` and replace product Macaron wording.
- [ ] Add short note: 0.8 heritage catalog lives in `vendor/a2ui_demo` (LUMI 0.8 source); default eval is official basic 0.9.1.
- [ ] Update `UPSTREAM.md` brand language accordingly.
- [ ] Update `.github/workflows/ci.yml` job `name:` fields if they say Macaron or generic only—use `LUMI` where product-facing.
- [ ] Commit: `docs(brand): rebrand README/UPSTREAM/CI to LUMI A2UI Bench`

### Task 4: Docs + scorecard stub

- [ ] Ensure/refresh `docs/compatibility-scorecard.md` (stub may already exist) so D1–D8 (with D6a/D6b) match the product spec baseline and fail-closed claim rules.
- [ ] In prior specs/plans, replace product-facing “Macaron-extended catalog on 0.9.1” follow-ups with “LUMI-extended (Track 2)” pointers to the new product spec (do not rewrite red/blue historical attack text verbatim unless it confuses readers—prefer a header note).
- [ ] Commit: `docs: add compatibility scorecard and LUMI pointers`

### Task 5: GitHub remote rename (operator step)

- [ ] Confirm remote `lumitive/Macaron-A2UI-Bench` (or current).
- [ ] Run (owner): `gh repo rename LUMI-A2UI-Bench --repo lumitive/Macaron-A2UI-Bench` (or UI).
- [ ] Update local remotes: `git remote set-url lumitive git@github.com:lumitive/LUMI-A2UI-Bench.git` (HTTPS variant OK).
- [ ] Verify: `gh repo view lumitive/LUMI-A2UI-Bench --json name,url`.
- [ ] Commit local remote doc note in README badges/links if any hardcode old URL.
- [ ] Commit: `chore(brand): point docs/links at LUMI-A2UI-Bench remote`

### Task 6: Verify + ship

- [ ] `rg -n 'Macaron A2UI Bench|a2ui-bench-render' --glob '!**/vendor/**' --glob '!**/node_modules/**'` → zero product-title hits (historical review memos may remain).
- [ ] CI green on PR.
- [ ] Merge PR.
