type RoleTurn = { role: string; content: string };

type VisualScores = {
  mean: number;
  v1: number;
  v2: number;
  v3: number;
  overallNote: string;
  issues: string[];
  reasons: Record<string, string>;
};

type BaselineScores = {
  l2Mean: number;
  l3Mean: number;
};

type CompareEntry = {
  modelLabel: string;
  screenshot: string;
  textResponse: string;
  visual: VisualScores;
  baseline: BaselineScores;
  a2uiPretty: string;
};

type ShowcaseEntry = {
  id: string;
  taskId: string;
  targetId: string;
  source: string;
  sourceLabel: string;
  scenarioId: string;
  scenarioLabel: string;
  difficulty: string;
  intentType: string;
  expectedPattern: string;
  stepIdx: number | null;
  stepCount: number;
  stepLabel: string;
  modelLabel: string;
  compareLabel: string;
  screenshot: string;
  userMessage: string;
  dialogueContext: RoleTurn[];
  textResponse: string;
  visual: VisualScores;
  baseline: BaselineScores;
  compare: CompareEntry | null;
  delta: {
    mean: number;
    v1: number;
    v2: number;
    v3: number;
  } | null;
  a2uiPretty: string;
  searchText: string;
};

type ShowcaseData = {
  title: string;
  modelLabel: string;
  compareModelLabel: string;
  heroTitle: string;
  generatedAt: string;
  summary: {
    eligibleTargetCount: number;
    completedCount: number;
    errorCount: number;
    avgVisualMean: number;
    avgVisualDims: Record<string, number>;
    issueRate: number;
    topIssues: Array<[string, number]>;
    compare: {
      label: string;
      overlapCount: number;
      missingCount: number;
      avgCompareVisualMean: number;
      avgCompareVisualDims: Record<string, number>;
      avgDeltaMean: number;
      avgDeltaDims: Record<string, number>;
    };
  };
  scenarioDefs: Record<string, string>;
  counts: {
    sources: Record<string, number>;
    scenarios: Record<string, number>;
    difficulties: Record<string, number>;
  };
  featuredIds: string[];
  entries: ShowcaseEntry[];
};

type SortMode = "visual" | "delta" | "v1" | "v2" | "v3" | "baseline-l2" | "baseline-l3" | "source";

const app = document.getElementById("app");
if (!app) {
  throw new Error("Missing #app");
}
const appRoot = app as HTMLDivElement;

let data: ShowcaseData | null = null;
const state = {
  query: "",
  scenario: "all",
  difficulty: "all",
  source: "all",
  sort: "visual" as SortMode,
  selectedId: null as string | null,
};

function escapeHtml(input: string): string {
  return input
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function formatNumber(value: number, digits = 2): string {
  return value.toFixed(digits);
}

function formatSigned(value: number, digits = 2): string {
  return `${value >= 0 ? "+" : ""}${value.toFixed(digits)}`;
}

function toRoleClass(role: string): string {
  return role.toLowerCase().replace(/[^a-z0-9_-]+/g, "-");
}

function deltaClass(value: number): string {
  if (value > 0.05) return "delta-pill positive";
  if (value < -0.05) return "delta-pill negative";
  return "delta-pill neutral";
}

function scoreClass(score: number): string {
  if (score >= 4.4) return "score-pill top";
  if (score >= 3.8) return "score-pill strong";
  if (score >= 3.2) return "score-pill solid";
  return "score-pill";
}

function sortEntries(entries: ShowcaseEntry[]): ShowcaseEntry[] {
  const sorted = [...entries];
  sorted.sort((a, b) => {
    switch (state.sort) {
      case "delta":
        return (b.delta?.mean ?? -Infinity) - (a.delta?.mean ?? -Infinity) || b.visual.mean - a.visual.mean;
      case "v1":
        return b.visual.v1 - a.visual.v1;
      case "v2":
        return b.visual.v2 - a.visual.v2;
      case "v3":
        return b.visual.v3 - a.visual.v3;
      case "baseline-l2":
        return b.baseline.l2Mean - a.baseline.l2Mean;
      case "baseline-l3":
        return b.baseline.l3Mean - a.baseline.l3Mean;
      case "source":
        return a.sourceLabel.localeCompare(b.sourceLabel) || b.visual.mean - a.visual.mean;
      case "visual":
      default:
        return b.visual.mean - a.visual.mean;
    }
  });
  return sorted;
}

function filterEntries(entries: ShowcaseEntry[]): ShowcaseEntry[] {
  return entries.filter((entry) => {
    if (state.scenario !== "all" && entry.scenarioId !== state.scenario) return false;
    if (state.difficulty !== "all" && entry.difficulty !== state.difficulty) return false;
    if (state.source !== "all" && entry.source !== state.source) return false;
    if (state.query && !entry.searchText.includes(state.query.toLowerCase())) return false;
    return true;
  });
}

function getFeatured(entries: ShowcaseEntry[]): ShowcaseEntry[] {
  if (!data) {
    return [];
  }
  return data.featuredIds
    .map((id) => entries.find((entry) => entry.id === id))
    .filter((entry): entry is ShowcaseEntry => Boolean(entry))
    .slice(0, 12);
}

function getCurrentEntry(entries: ShowcaseEntry[]): ShowcaseEntry | null {
  return entries.find((entry) => entry.id === state.selectedId) ?? null;
}

function renderSummary(dataset: ShowcaseData): string {
  const { summary } = dataset;
  const issueChips = summary.topIssues
    .slice(0, 6)
    .map(([issue, count]) => `<span class="issue-chip">${escapeHtml(issue)} <strong>${count}</strong></span>`)
    .join("");

  const compare = summary.compare;
  return `
    <section class="hero-panel">
      <div class="hero-copy">
        <p class="eyebrow">Visual evidence, not just metrics</p>
        <h1>${escapeHtml(dataset.heroTitle)}</h1>
        <p class="hero-text">
          This gallery is now anchored on the 50-step RL checkpoint. Each sample keeps the dialogue context first, then shows
          the rendered card from Qwen-235B RL-50step against the matching GPT-5.4 full-prompt render so readers can judge the difference directly.
        </p>
      </div>
      <div class="hero-metrics">
        <div class="metric-card"><span>Qwen renders</span><strong>${summary.completedCount}</strong></div>
        <div class="metric-card"><span>Matched GPT-5.4 renders</span><strong>${compare.overlapCount}</strong></div>
        <div class="metric-card"><span>Qwen visual mean</span><strong>${formatNumber(summary.avgVisualMean)}</strong></div>
        <div class="metric-card"><span>Mean advantage vs GPT-5.4</span><strong>${formatSigned(compare.avgDeltaMean)}</strong></div>
      </div>
      <div class="compare-summary-strip">
        <div class="compare-summary-card">
          <span>Qwen V1 / V2 / V3</span>
          <strong>${formatNumber(summary.avgVisualDims.V1)} / ${formatNumber(summary.avgVisualDims.V2)} / ${formatNumber(summary.avgVisualDims.V3)}</strong>
        </div>
        <div class="compare-summary-card">
          <span>GPT-5.4 V1 / V2 / V3</span>
          <strong>${formatNumber(compare.avgCompareVisualDims.V1)} / ${formatNumber(compare.avgCompareVisualDims.V2)} / ${formatNumber(compare.avgCompareVisualDims.V3)}</strong>
        </div>
        <div class="compare-summary-card">
          <span>Delta by dimension</span>
          <strong>${formatSigned(compare.avgDeltaDims.V1)} / ${formatSigned(compare.avgDeltaDims.V2)} / ${formatSigned(compare.avgDeltaDims.V3)}</strong>
        </div>
      </div>
      <div class="issue-ribbon">
        <span class="ribbon-label">Typical remaining imperfections</span>
        <div class="issue-grid compact">${issueChips}</div>
      </div>
    </section>
  `;
}

function renderFeatured(entries: ShowcaseEntry[]): string {
  return `
    <section class="featured-section">
      <div class="section-title-row">
        <div>
          <p class="section-kicker">Featured moments</p>
          <h2>Examples that sell the model's strength immediately</h2>
        </div>
      </div>
      <div class="featured-grid">
        ${entries
          .map(
            (entry) => `
              <button class="featured-card" data-open-detail="${escapeHtml(entry.id)}">
                <img src="${entry.screenshot}" alt="${escapeHtml(entry.targetId)}" loading="lazy" />
                <div class="featured-overlay">
                  <div class="${scoreClass(entry.visual.mean)}">${formatNumber(entry.visual.mean)}</div>
                  <div class="featured-copy">
                    <p>${escapeHtml(entry.sourceLabel)} · ${escapeHtml(entry.stepLabel)}</p>
                    <h3>${escapeHtml(entry.targetId)}</h3>
                    <span>${escapeHtml(entry.visual.overallNote)}</span>
                    ${entry.delta ? `<em class="${deltaClass(entry.delta.mean)}">${formatSigned(entry.delta.mean)} vs GPT-5.4</em>` : ""}
                  </div>
                </div>
              </button>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}

function renderFilters(dataset: ShowcaseData): string {
  const scenarioOptions = Object.entries(dataset.scenarioDefs)
    .map(
      ([key, label]) =>
        `<option value="${key}" ${state.scenario === key ? "selected" : ""}>${key} · ${escapeHtml(label)}</option>`,
    )
    .join("");
  const difficultyOptions = Object.keys(dataset.counts.difficulties)
    .map((key) => `<option value="${key}" ${state.difficulty === key ? "selected" : ""}>${escapeHtml(key)}</option>`)
    .join("");
  const sourceOptions = Object.keys(dataset.counts.sources)
    .map((key) => `<option value="${key}" ${state.source === key ? "selected" : ""}>${escapeHtml(key)}</option>`)
    .join("");

  return `
    <section class="filter-bar">
      <label>
        <span>Search</span>
        <input id="query-input" type="search" placeholder="Search target id, context, response, or issue" value="${escapeHtml(state.query)}" />
      </label>
      <label>
        <span>Scenario</span>
        <select id="scenario-select">
          <option value="all">All scenarios</option>
          ${scenarioOptions}
        </select>
      </label>
      <label>
        <span>Difficulty</span>
        <select id="difficulty-select">
          <option value="all">All difficulties</option>
          ${difficultyOptions}
        </select>
      </label>
      <label>
        <span>Source</span>
        <select id="source-select">
          <option value="all">All sources</option>
          ${sourceOptions}
        </select>
      </label>
      <label>
        <span>Sort</span>
        <select id="sort-select">
          <option value="visual" ${state.sort === "visual" ? "selected" : ""}>Visual mean</option>
          <option value="delta" ${state.sort === "delta" ? "selected" : ""}>Qwen advantage</option>
          <option value="v1" ${state.sort === "v1" ? "selected" : ""}>V1</option>
          <option value="v2" ${state.sort === "v2" ? "selected" : ""}>V2</option>
          <option value="v3" ${state.sort === "v3" ? "selected" : ""}>V3</option>
          <option value="baseline-l2" ${state.sort === "baseline-l2" ? "selected" : ""}>Baseline L2</option>
          <option value="baseline-l3" ${state.sort === "baseline-l3" ? "selected" : ""}>Baseline L3</option>
          <option value="source" ${state.sort === "source" ? "selected" : ""}>Source group</option>
        </select>
      </label>
    </section>
  `;
}

function renderGallery(entries: ShowcaseEntry[]): string {
  return `
    <section class="gallery-section">
      <div class="section-title-row">
        <div>
          <p class="section-kicker">Gallery</p>
          <h2>${entries.length} examples after filtering</h2>
        </div>
      </div>
      <div class="gallery-grid">
        ${entries
          .map(
            (entry) => `
              <button class="gallery-card" data-open-detail="${escapeHtml(entry.id)}">
                <div class="card-media">
                  <img src="${entry.screenshot}" alt="${escapeHtml(entry.targetId)}" loading="lazy" />
                </div>
                <div class="card-body">
                  <div class="card-topline">
                    <span class="mini-badge">${escapeHtml(entry.sourceLabel)}</span>
                    <span class="mini-badge">${escapeHtml(entry.scenarioId)}</span>
                    <span class="mini-badge">${escapeHtml(entry.stepLabel)}</span>
                  </div>
                  <div class="card-head">
                    <h3>${escapeHtml(entry.targetId)}</h3>
                    <span class="${scoreClass(entry.visual.mean)}">${formatNumber(entry.visual.mean)}</span>
                  </div>
                  <p class="card-note">${escapeHtml(entry.visual.overallNote)}</p>
                  <p class="card-compare ${entry.delta ? deltaClass(entry.delta.mean) : "delta-pill neutral"}">
                    ${entry.delta ? `${formatSigned(entry.delta.mean)} vs GPT-5.4 full` : "No matched GPT-5.4 render"}
                  </p>
                  <dl class="card-metrics">
                    <div><dt>V1</dt><dd>${formatNumber(entry.visual.v1)}</dd></div>
                    <div><dt>V2</dt><dd>${formatNumber(entry.visual.v2)}</dd></div>
                    <div><dt>V3</dt><dd>${formatNumber(entry.visual.v3)}</dd></div>
                  </dl>
                </div>
              </button>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}

function renderTranscript(entry: ShowcaseEntry): string {
  const transcript = [
    ...entry.dialogueContext,
    { role: "user", content: entry.userMessage },
    { role: "assistant", content: entry.textResponse },
  ];

  const turns = transcript
    .map(
      (turn, index) => `
        <article class="turn ${toRoleClass(turn.role)}">
          <div class="turn-meta">
            <div class="turn-role">${escapeHtml(turn.role)}</div>
            <span class="turn-index">${String(index + 1).padStart(2, "0")}</span>
          </div>
          <p>${escapeHtml(turn.content)}</p>
        </article>
      `,
    )
    .join("");

  return `
    <section class="detail-section detail-transcript">
      <div class="section-heading">Conversation context</div>
      <p class="detail-caption">The full dialogue is shown in chronological order so the interface can be read against the situation that produced it.</p>
      <div class="turn-stack">${turns || '<p class="empty-copy">No dialogue attached for this sample.</p>'}</div>
    </section>
  `;
}

function renderIssues(issues: string[]): string {
  return issues.length
    ? issues.map((issue) => `<span class="issue-chip">${escapeHtml(issue)}</span>`).join("")
    : '<span class="issue-chip positive">No detected issues</span>';
}

function renderModelPanel(args: {
  title: string;
  modelLabel: string;
  screenshot: string;
  targetId: string;
  visual: VisualScores;
  baseline: BaselineScores;
  tone: "primary" | "compare";
}): string {
  const { title, modelLabel, screenshot, targetId, visual, baseline, tone } = args;

  return `
    <section class="detail-model detail-section ${tone}">
      <div class="model-panel-header">
        <div>
          <p class="section-heading">${escapeHtml(title)}</p>
          <h3>${escapeHtml(modelLabel)}</h3>
        </div>
        <div class="${scoreClass(visual.mean)}">${formatNumber(visual.mean)}</div>
      </div>
      <div class="model-visual-card">
        <img src="${screenshot}" alt="${escapeHtml(targetId)} ${escapeHtml(modelLabel)} screenshot" />
        <div class="metric-strip">
          <div><span>V1</span><strong>${formatNumber(visual.v1)}</strong></div>
          <div><span>V2</span><strong>${formatNumber(visual.v2)}</strong></div>
          <div><span>V3</span><strong>${formatNumber(visual.v3)}</strong></div>
          <div><span>L2 baseline</span><strong>${formatNumber(baseline.l2Mean)}</strong></div>
          <div><span>L3 baseline</span><strong>${formatNumber(baseline.l3Mean)}</strong></div>
        </div>
      </div>
      <section class="detail-section highlight">
        <div class="section-heading">Judge note</div>
        <p>${escapeHtml(visual.overallNote || "No overall note recorded.")}</p>
      </section>
      <section class="detail-section">
        <div class="section-heading">Judge reasoning</div>
        <div class="reason-block">
          <h3>V1</h3>
          <p>${escapeHtml(visual.reasons.V1 || "")}</p>
        </div>
        <div class="reason-block">
          <h3>V2</h3>
          <p>${escapeHtml(visual.reasons.V2 || "")}</p>
        </div>
        <div class="reason-block">
          <h3>V3</h3>
          <p>${escapeHtml(visual.reasons.V3 || "")}</p>
        </div>
      </section>
      <section class="detail-section">
        <div class="section-heading">Issues</div>
        <div class="issue-grid">${renderIssues(visual.issues)}</div>
      </section>
    </section>
  `;
}

function renderComparison(entry: ShowcaseEntry): string {
  if (!entry.compare || !entry.delta) {
    return `
      <div class="detail-grid single-model">
        ${renderModelPanel({
          title: "Rendered card",
          modelLabel: entry.modelLabel,
          screenshot: entry.screenshot,
          targetId: entry.targetId,
          visual: entry.visual,
          baseline: entry.baseline,
          tone: "primary",
        })}
      </div>
    `;
  }

  return `
    <section class="detail-section compare-overview">
      <div class="section-heading">Head-to-head comparison</div>
      <p class="detail-caption">Same target, same dialogue context, but different prompting regimes.</p>
      <div class="delta-row">
        <span class="${deltaClass(entry.delta.mean)}">Overall ${formatSigned(entry.delta.mean)}</span>
        <span class="${deltaClass(entry.delta.v1)}">V1 ${formatSigned(entry.delta.v1)}</span>
        <span class="${deltaClass(entry.delta.v2)}">V2 ${formatSigned(entry.delta.v2)}</span>
        <span class="${deltaClass(entry.delta.v3)}">V3 ${formatSigned(entry.delta.v3)}</span>
      </div>
    </section>
    <div class="detail-grid compare-grid">
      ${renderModelPanel({
        title: "Primary render",
        modelLabel: entry.modelLabel,
        screenshot: entry.screenshot,
        targetId: entry.targetId,
        visual: entry.visual,
        baseline: entry.baseline,
        tone: "primary",
      })}
      ${renderModelPanel({
        title: "Reference render",
        modelLabel: entry.compare.modelLabel,
        screenshot: entry.compare.screenshot,
        targetId: entry.targetId,
        visual: entry.compare.visual,
        baseline: entry.compare.baseline,
        tone: "compare",
      })}
    </div>
  `;
}

function renderJsonBlocks(entry: ShowcaseEntry): string {
  const compareBlock = entry.compare
    ? `
      <section class="detail-section a2ui-block">
        <div class="section-heading row">
          <span>${escapeHtml(entry.compare.modelLabel)} A2UI</span>
          <button class="copy-button" data-copy-a2ui="${escapeHtml(entry.id)}" data-copy-variant="compare">Copy JSON</button>
        </div>
        <pre>${escapeHtml(entry.compare.a2uiPretty)}</pre>
      </section>
    `
    : "";

  return `
    <div class="detail-lower-grid ${entry.compare ? "has-compare" : ""}">
      <section class="detail-section a2ui-block">
        <div class="section-heading row">
          <span>${escapeHtml(entry.modelLabel)} A2UI</span>
          <button class="copy-button" data-copy-a2ui="${escapeHtml(entry.id)}" data-copy-variant="primary">Copy JSON</button>
        </div>
        <pre>${escapeHtml(entry.a2uiPretty)}</pre>
      </section>
      ${compareBlock}
    </div>
  `;
}

function renderDetail(entry: ShowcaseEntry | null): string {
  if (!entry) {
    return "";
  }

  return `
    <div class="detail-backdrop" data-close-detail="true"></div>
    <aside class="detail-panel" role="dialog" aria-modal="true">
      <button class="detail-close" data-close-detail="true">Close</button>
      <div class="detail-header">
        <div>
          <p class="detail-kicker">${escapeHtml(entry.sourceLabel)} · ${escapeHtml(entry.scenarioId)} · ${escapeHtml(entry.stepLabel)}</p>
          <h2>${escapeHtml(entry.targetId)}</h2>
          <p class="detail-subtitle">${escapeHtml(entry.scenarioLabel)}</p>
        </div>
        <div class="detail-header-metrics">
          <div class="${scoreClass(entry.visual.mean)} large">Qwen ${formatNumber(entry.visual.mean)}</div>
          ${entry.delta ? `<div class="${deltaClass(entry.delta.mean)} large">${formatSigned(entry.delta.mean)} vs GPT-5.4</div>` : ""}
        </div>
      </div>
      ${renderTranscript(entry)}
      ${renderComparison(entry)}
      ${renderJsonBlocks(entry)}
    </aside>
  `;
}

function render(): void {
  if (!data) {
    appRoot.innerHTML = `<div class="loading-state">Loading showcase...</div>`;
    return;
  }

  const filtered = sortEntries(filterEntries(data.entries));
  const featured = getFeatured(data.entries);
  const selected = getCurrentEntry(data.entries);

  appRoot.innerHTML = `
    <div class="background-orb orb-a"></div>
    <div class="background-orb orb-b"></div>
    <main class="app-shell">
      <header class="masthead">
        <div>
          <p class="top-kicker">${escapeHtml(data.title)}</p>
          <p class="top-subtitle">${escapeHtml(data.modelLabel)} vs ${escapeHtml(data.compareModelLabel)}</p>
        </div>
        <div class="masthead-meta">Generated ${new Date(data.generatedAt).toLocaleString()}</div>
      </header>
      ${renderSummary(data)}
      ${renderFeatured(featured)}
      ${renderFilters(data)}
      ${renderGallery(filtered)}
    </main>
    ${renderDetail(selected)}
  `;
}

appRoot.addEventListener("input", (event) => {
  const target = event.target as HTMLElement;
  if (target instanceof HTMLInputElement && target.id === "query-input") {
    state.query = target.value;
    render();
  }
});

appRoot.addEventListener("change", (event) => {
  const target = event.target as HTMLSelectElement;
  if (!(target instanceof HTMLSelectElement)) {
    return;
  }

  if (target.id === "scenario-select") state.scenario = target.value;
  if (target.id === "difficulty-select") state.difficulty = target.value;
  if (target.id === "source-select") state.source = target.value;
  if (target.id === "sort-select") state.sort = target.value as SortMode;
  render();
});

appRoot.addEventListener("click", async (event) => {
  const target = event.target as HTMLElement;
  const openTrigger = target.closest<HTMLElement>("[data-open-detail]");
  if (openTrigger) {
    state.selectedId = openTrigger.dataset.openDetail ?? null;
    render();
    return;
  }

  if (target.closest("[data-close-detail]")) {
    state.selectedId = null;
    render();
    return;
  }

  const copyTrigger = target.closest<HTMLElement>("[data-copy-a2ui]");
  if (copyTrigger && data) {
    const entry = data.entries.find((item) => item.id === copyTrigger.dataset.copyA2ui);
    if (entry) {
      const payload = copyTrigger.dataset.copyVariant === "compare" ? entry.compare?.a2uiPretty : entry.a2uiPretty;
      if (!payload) {
        return;
      }
      await navigator.clipboard.writeText(payload);
      copyTrigger.textContent = "Copied";
      window.setTimeout(() => {
        copyTrigger.textContent = "Copy JSON";
      }, 1200);
    }
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && state.selectedId) {
    state.selectedId = null;
    render();
  }
});

async function main(): Promise<void> {
  const dataUrl = `${import.meta.env.BASE_URL}showcase/qwen-235b-rl/data.json`;
  data = await fetch(dataUrl).then((response) => response.json());
  render();
}

void main();
