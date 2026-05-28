import { copyFile, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { basename, dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const SCENARIO_DEFS = {
  S1: "Emotional support and strategy branching",
  S2: "Behavior change and commitment facilitation",
  S3: "Slot filling and process advancement",
  S4: "Candidate result display and comparison",
  S5: "Transaction closure and failure recovery",
};

const SOURCE_LABELS = {
  annomi: "AnnoMI",
  esconv: "ESConv",
  multiwoz: "MultiWOZ",
  sgd: "Schema-Guided Dialogue",
};

const DIFFICULTY_LABELS = {
  atomic: "Atomic",
  depth: "Depth rollout",
  width: "Multi-domain width",
};

const OUTPUT_SLUG = "qwen-235b-rl";

const PRIMARY_MODEL = {
  slug: "qwen-235b-rl-50step",
  title: "Qwen-235B RL Visual Showcase",
  modelLabel: "Qwen/Qwen3-235B-A22B-Instruct-2507 @ rl-periodic-step-000050",
  heroTitle: "Qwen-235B RL-50step turns long dialogue context into renderable cards, and now the page shows exactly how it compares against GPT-5.4 full prompting.",
  resultsDir: "results/qwen-235b-rl-50step",
  visualDirName: "visual_compare_kimi25_rerun",
};

const COMPARE_MODEL = {
  slug: "openai__gpt-5.4",
  modelLabel: "OpenAI GPT-5.4 (full prompt)",
  shortLabel: "GPT-5.4 full",
  resultsDir: "results/openai__gpt-5.4",
  visualDirName: "visual_compare_kimi25_rerun",
};

function padStep(stepIdx) {
  return String(stepIdx + 1).padStart(2, "0");
}

async function readJson(path) {
  return JSON.parse(await readFile(path, "utf-8"));
}

function buildTaskIndex(taskResults) {
  const index = new Map();

  for (const task of taskResults) {
    const base = {
      taskId: task.task_id,
      source: task.source,
      sourceLabel: SOURCE_LABELS[task.source] ?? task.source,
      scenarioId: task.scenario_id,
      scenarioLabel: SCENARIO_DEFS[task.scenario_id] ?? task.scenario_id,
      difficulty: task.difficulty_level,
      intentType: task.intent_type,
      expectedPattern: task.expected_pattern,
    };

    if (task.difficulty_level === "depth" && Array.isArray(task.model_output.steps)) {
      const stepCount = task.model_output.steps.length;
      for (const step of task.model_output.steps) {
        const targetId = `${task.task_id}__step${padStep(step.step_idx)}`;
        index.set(targetId, {
          ...base,
          targetId,
          userMessage: step.step_meta.user_message,
          dialogueContext: [],
          textResponse: step.model_output.text_response,
          stepIdx: step.step_idx,
          stepCount,
          stepLabel: `Step ${step.step_idx + 1} / ${stepCount}`,
          a2uiPretty: JSON.stringify(step.model_output.a2ui_messages ?? [], null, 2),
        });
      }
      continue;
    }

    index.set(task.task_id, {
      ...base,
      targetId: task.task_id,
      userMessage: "",
      dialogueContext: [],
      textResponse: task.model_output.text_response ?? "",
      stepIdx: null,
      stepCount: 1,
      stepLabel: DIFFICULTY_LABELS[task.difficulty_level] ?? task.difficulty_level,
      a2uiPretty: JSON.stringify(task.model_output.a2ui_messages ?? [], null, 2),
    });
  }

  return index;
}

function normalizeVisual(visualEval) {
  return {
    mean: visualEval.mean,
    v1: visualEval.scores.V1,
    v2: visualEval.scores.V2,
    v3: visualEval.scores.V3,
    overallNote: visualEval.overall_note ?? "",
    issues: visualEval.issues_detected ?? [],
    reasons: visualEval.reasons ?? {},
  };
}

function average(values) {
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : 0;
}

async function copyScreenshot(row, outputDir, bucketName) {
  const screenshotFile = basename(row.screenshot_path);
  const targetPath = join(outputDir, bucketName, screenshotFile);
  await copyFile(row.screenshot_path, targetPath);
  return `/showcase/${OUTPUT_SLUG}/images/${bucketName}/${screenshotFile}`;
}

function buildFeaturedIds(entries) {
  const featured = [];
  const used = new Set();
  const bySource = new Map();

  for (const entry of entries) {
    const bucket = bySource.get(entry.source) ?? [];
    bucket.push(entry);
    bySource.set(entry.source, bucket);
  }

  for (const [source, bucket] of bySource) {
    bucket
      .sort((a, b) => {
        const deltaA = a.delta?.mean ?? -Infinity;
        const deltaB = b.delta?.mean ?? -Infinity;
        return deltaB - deltaA || b.visual.mean - a.visual.mean;
      })
      .slice(0, source === "multiwoz" ? 4 : 3)
      .forEach((entry) => {
        if (!used.has(entry.id)) {
          used.add(entry.id);
          featured.push(entry.id);
        }
      });
  }

  for (const entry of entries) {
    if (featured.length >= 14) {
      break;
    }
    if (!used.has(entry.id)) {
      used.add(entry.id);
      featured.push(entry.id);
    }
  }

  return featured.slice(0, 14);
}

function buildCounts(entries) {
  return {
    sources: Object.fromEntries(
      Object.entries(
        entries.reduce((acc, entry) => {
          acc[entry.source] = (acc[entry.source] ?? 0) + 1;
          return acc;
        }, {}),
      ).sort((a, b) => b[1] - a[1]),
    ),
    scenarios: Object.fromEntries(
      Object.entries(
        entries.reduce((acc, entry) => {
          acc[entry.scenarioId] = (acc[entry.scenarioId] ?? 0) + 1;
          return acc;
        }, {}),
      ).sort(),
    ),
    difficulties: Object.fromEntries(
      Object.entries(
        entries.reduce((acc, entry) => {
          acc[entry.difficulty] = (acc[entry.difficulty] ?? 0) + 1;
          return acc;
        }, {}),
      ).sort((a, b) => b[1] - a[1]),
    ),
  };
}

function buildCompareSummary(entries) {
  const overlapEntries = entries.filter((entry) => entry.compare);
  const deltaMean = overlapEntries.map((entry) => entry.delta.mean);
  const deltaV1 = overlapEntries.map((entry) => entry.delta.v1);
  const deltaV2 = overlapEntries.map((entry) => entry.delta.v2);
  const deltaV3 = overlapEntries.map((entry) => entry.delta.v3);
  const compareMean = overlapEntries.map((entry) => entry.compare.visual.mean);
  const compareV1 = overlapEntries.map((entry) => entry.compare.visual.v1);
  const compareV2 = overlapEntries.map((entry) => entry.compare.visual.v2);
  const compareV3 = overlapEntries.map((entry) => entry.compare.visual.v3);

  return {
    label: COMPARE_MODEL.modelLabel,
    overlapCount: overlapEntries.length,
    missingCount: entries.length - overlapEntries.length,
    avgCompareVisualMean: average(compareMean),
    avgCompareVisualDims: {
      V1: average(compareV1),
      V2: average(compareV2),
      V3: average(compareV3),
    },
    avgDeltaMean: average(deltaMean),
    avgDeltaDims: {
      V1: average(deltaV1),
      V2: average(deltaV2),
      V3: average(deltaV3),
    },
  };
}

function buildSearchText(primaryRow, base, compareEntry) {
  return [
    primaryRow.target_id,
    primaryRow.task_id,
    base.sourceLabel,
    base.scenarioLabel,
    base.intentType,
    primaryRow.user_message,
    primaryRow.text_response,
    ...(primaryRow.dialogue_context ?? []).map((turn) => `${turn.role} ${turn.content}`),
    primaryRow.visual_eval.overall_note ?? "",
    ...(primaryRow.visual_eval.issues_detected ?? []),
    compareEntry?.modelLabel ?? "",
    compareEntry?.textResponse ?? "",
    compareEntry?.visual.overallNote ?? "",
    ...(compareEntry?.visual.issues ?? []),
  ]
    .join(" ")
    .toLowerCase();
}

async function main() {
  const scriptDir = dirname(fileURLToPath(import.meta.url));
  const renderDir = resolve(scriptDir, "..");
  const repoDir = resolve(renderDir, "..");

  const primaryResultsDir = resolve(repoDir, PRIMARY_MODEL.resultsDir);
  const primaryRunDir = resolve(primaryResultsDir, PRIMARY_MODEL.visualDirName);
  const compareResultsDir = resolve(repoDir, COMPARE_MODEL.resultsDir);
  const compareRunDir = resolve(compareResultsDir, COMPARE_MODEL.visualDirName);

  const outputDir = resolve(renderDir, `public/showcase/${OUTPUT_SLUG}`);
  const imageDir = join(outputDir, "images");
  const primaryImageDir = join(imageDir, "primary");
  const compareImageDir = join(imageDir, "compare");

  await rm(outputDir, { recursive: true, force: true });
  await mkdir(primaryImageDir, { recursive: true });
  await mkdir(compareImageDir, { recursive: true });

  const [primarySummaryObj, primaryMetadataObj, primaryResults, primaryTaskResults, compareResults, compareTaskResults] =
    await Promise.all([
      readJson(join(primaryRunDir, "summary.json")),
      readJson(join(primaryRunDir, "metadata.json")),
      readJson(join(primaryRunDir, "results.json")),
      readJson(join(primaryResultsDir, "task_results.json")),
      readJson(join(compareRunDir, "results.json")),
      readJson(join(compareResultsDir, "task_results.json")),
    ]);

  const primaryTaskIndex = buildTaskIndex(primaryTaskResults);
  const compareTaskIndex = buildTaskIndex(compareTaskResults);
  const compareResultsByTarget = new Map(compareResults.map((row) => [row.target_id, row]));
  const entries = [];

  for (const primaryRow of primaryResults) {
    const base = primaryTaskIndex.get(primaryRow.target_id);
    if (!base) {
      throw new Error(`Missing primary task result for target ${primaryRow.target_id}`);
    }

    const screenshot = await copyScreenshot(primaryRow, imageDir, "primary");
    const compareRow = compareResultsByTarget.get(primaryRow.target_id);

    let compareEntry = null;
    let delta = null;

    if (compareRow) {
      const compareBase = compareTaskIndex.get(compareRow.target_id);
      if (!compareBase) {
        throw new Error(`Missing compare task result for target ${compareRow.target_id}`);
      }

      const compareScreenshot = await copyScreenshot(compareRow, imageDir, "compare");
      const compareVisual = normalizeVisual(compareRow.visual_eval);
      compareEntry = {
        modelLabel: COMPARE_MODEL.modelLabel,
        screenshot: compareScreenshot,
        textResponse: compareRow.text_response || compareBase.textResponse,
        visual: compareVisual,
        baseline: {
          l2Mean: compareRow.baseline_l2_mean,
          l3Mean: compareRow.baseline_l3_mean,
        },
        a2uiPretty: compareBase.a2uiPretty,
      };

      delta = {
        mean: normalizeVisual(primaryRow.visual_eval).mean - compareVisual.mean,
        v1: normalizeVisual(primaryRow.visual_eval).v1 - compareVisual.v1,
        v2: normalizeVisual(primaryRow.visual_eval).v2 - compareVisual.v2,
        v3: normalizeVisual(primaryRow.visual_eval).v3 - compareVisual.v3,
      };
    }

    entries.push({
      ...base,
      id: primaryRow.target_id,
      modelLabel: PRIMARY_MODEL.modelLabel,
      compareLabel: COMPARE_MODEL.modelLabel,
      screenshot,
      userMessage: primaryRow.user_message || base.userMessage,
      dialogueContext: primaryRow.dialogue_context ?? base.dialogueContext,
      textResponse: primaryRow.text_response || base.textResponse,
      visual: normalizeVisual(primaryRow.visual_eval),
      baseline: {
        l2Mean: primaryRow.baseline_l2_mean,
        l3Mean: primaryRow.baseline_l3_mean,
      },
      compare: compareEntry,
      delta,
      searchText: buildSearchText(primaryRow, base, compareEntry),
      a2uiPretty: base.a2uiPretty,
    });
  }

  entries.sort((a, b) => {
    const deltaA = a.delta?.mean ?? -Infinity;
    const deltaB = b.delta?.mean ?? -Infinity;
    return deltaB - deltaA || b.visual.mean - a.visual.mean;
  });

  const primaryStats = primarySummaryObj.per_model[PRIMARY_MODEL.slug];
  const compareSummary = buildCompareSummary(entries);
  const data = {
    title: PRIMARY_MODEL.title,
    modelLabel: PRIMARY_MODEL.modelLabel,
    compareModelLabel: COMPARE_MODEL.modelLabel,
    heroTitle: PRIMARY_MODEL.heroTitle,
    generatedAt: new Date().toISOString(),
    summary: {
      eligibleTargetCount: primaryMetadataObj.eligible_counts[PRIMARY_MODEL.slug],
      completedCount: primaryStats.completed_count,
      errorCount: primaryStats.error_count,
      avgVisualMean: primaryStats.avg_visual_mean,
      avgVisualDims: primaryStats.avg_visual_dims,
      issueRate: primaryStats.issue_rate,
      topIssues: primaryStats.top_issues,
      compare: compareSummary,
    },
    scenarioDefs: SCENARIO_DEFS,
    counts: buildCounts(entries),
    featuredIds: buildFeaturedIds(entries),
    entries,
  };

  await writeFile(join(outputDir, "data.json"), JSON.stringify(data), "utf-8");
  console.log(`Showcase data written to ${join(outputDir, "data.json")}`);
  console.log(`Entries: ${entries.length}`);
  console.log(`Overlap with ${COMPARE_MODEL.shortLabel}: ${compareSummary.overlapCount}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
