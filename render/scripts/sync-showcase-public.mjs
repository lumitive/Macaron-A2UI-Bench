import { cp, mkdir, rm } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

async function main() {
  const scriptDir = dirname(fileURLToPath(import.meta.url));
  const renderDir = resolve(scriptDir, "..");
  const sourceDir = resolve(renderDir, "public/showcase");
  const targetDir = resolve(renderDir, "dist/showcase");

  await rm(targetDir, { recursive: true, force: true });
  await mkdir(targetDir, { recursive: true });
  await cp(sourceDir, targetDir, { recursive: true });

  console.log(`Synced showcase public assets to ${targetDir}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
