import { chromium, Page } from "playwright";
import { mkdirSync, readFileSync } from "fs";
import { resolve, dirname, join } from "path";
import { fileURLToPath, pathToFileURL } from "url";
import { spawn } from "child_process";

interface Turn {
  turnLabel?: string;
  userMessage?: string;
  assistantText?: string;
  a2uiMessages: unknown[];
}

interface Dialogue {
  dialogue_id: string;
  turns: Turn[];
}

interface RenderPaths {
  dialogueId: string;
  images: string[];
}

interface RenderOptions {
  outputDir: string;
}

const DEFAULT_PORT = 5180;

function parseArgs(args: string[]) {
  const out: Record<string, string> = {};
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (!arg.startsWith("--")) continue;
    const key = arg.slice(2);
    const next = args[i + 1];
    if (next && !next.startsWith("--")) {
      out[key] = next;
      i++;
    } else {
      out[key] = "true";
    }
  }
  return out;
}

function sanitizeId(id: string): string {
  return id.replace(/[^a-zA-Z0-9._-]+/g, "_");
}

function startDevServer(projectDir: string, port: number): Promise<ReturnType<typeof spawn>> {
  return new Promise((resolvePromise, reject) => {
    const child = spawn("npx", ["vite", "--port", String(port)], {
      cwd: projectDir,
      stdio: ["ignore", "pipe", "pipe"],
    });

    let started = false;

    const onData = (data: Buffer) => {
      const text = data.toString();
      if (!started && text.includes("Local:")) {
        started = true;
        resolvePromise(child);
      }
    };

    child.stdout?.on("data", onData);
    child.stderr?.on("data", onData);

    child.on("error", (err) => {
      if (!started) reject(err);
    });

    child.on("exit", (code) => {
      if (!started) reject(new Error(`Dev server exited with code ${code}`));
    });

    setTimeout(() => {
      if (!started) {
        child.kill();
        reject(new Error("Dev server did not start within 30s"));
      }
    }, 30_000);
  });
}

export async function renderDialogue(
  page: Page,
  dialogue: Dialogue,
  options: RenderOptions
): Promise<RenderPaths> {
  const dialogueId = dialogue.dialogue_id || "dialogue";
  const safeId = sanitizeId(dialogueId);
  const dialogueDir = resolve(options.outputDir, safeId);
  mkdirSync(dialogueDir, { recursive: true });

  await page.evaluate(() => (window as any).__A2UI_RENDER__?.reset());

  const images: string[] = [];
  let captureIndex = 0;

  for (let i = 0; i < dialogue.turns.length; i++) {
    const turn = dialogue.turns[i];
    if (!turn?.a2uiMessages || turn.a2uiMessages.length === 0) {
      continue;
    }

    const result = await page.evaluate(
      (messages) => (window as any).__A2UI_RENDER__?.processTurn(messages),
      turn.a2uiMessages
    );

    if (!result?.shouldCapture) {
      continue;
    }

    const filename = `turn_${String(i + 1).padStart(3, "0")}_${String(
      ++captureIndex
    ).padStart(3, "0")}.png`;
    const filePath = resolve(dialogueDir, filename);

    await page.locator("#surface-frame").screenshot({ path: filePath });
    images.push(filePath);
  }

  return { dialogueId, images };
}

async function main() {
  const __dirname = dirname(fileURLToPath(import.meta.url));
  const projectDir = resolve(__dirname, "..");

  const args = parseArgs(process.argv.slice(2));
  if (!args.input) {
    throw new Error("Missing --input. Pass a dialogue JSON file to render.");
  }
  const inputPath = resolve(args.input);
  const outputDir = resolve(args.out || join(projectDir, "output"));
  const limit = args.limit ? Number(args.limit) : undefined;
  const start = args.start ? Number(args.start) : 0;
  const dialogueId = args["dialogue-id"];

  const raw = readFileSync(inputPath, "utf-8");
  const parsed = JSON.parse(raw);
  const dialogues: Dialogue[] = Array.isArray(parsed)
    ? parsed
    : Object.values(parsed);

  const filtered = dialogueId
    ? dialogues.filter((d) => d.dialogue_id === dialogueId)
    : dialogues;

  const sliced = limit ? filtered.slice(start, start + limit) : filtered.slice(start);

  mkdirSync(outputDir, { recursive: true });

  const port = args.port ? Number(args.port) : DEFAULT_PORT;
  const url = `http://localhost:${port}/`;

  const serverProcess = await startDevServer(projectDir, port);

  let browser;
  try {
    browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
      viewport: { width: 1400, height: 900 },
      deviceScaleFactor: 2,
    });

    const page = await context.newPage();
    await page.goto(url, { waitUntil: "networkidle" });
    await page.waitForFunction(
      () => Boolean((window as any).__A2UI_RENDER__),
      {},
      { timeout: 10_000 }
    );

    const results: RenderPaths[] = [];

    for (let i = 0; i < sliced.length; i++) {
      const dialogue = sliced[i];
      const rendered = await renderDialogue(page, dialogue, {
        outputDir,
      });
      results.push(rendered);
      console.log(
        `[render] ${i + 1}/${sliced.length} ${rendered.dialogueId} -> ${rendered.images.length} images`
      );
    }

    await context.close();
    await browser.close();
    browser = null;

    console.log(`[render] Done. Output at ${outputDir}`);
  } finally {
    if (browser) {
      await browser.close().catch(() => {});
    }
    serverProcess.kill();
  }
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((err) => {
    console.error("[render] Error:", err);
    process.exit(1);
  });
}
