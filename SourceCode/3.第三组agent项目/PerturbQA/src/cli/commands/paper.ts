import { readdirSync, readFileSync, existsSync } from "fs";
import { join } from "path";
import chalk from "chalk";
import { CONFIG } from "../../config.js";
import { C, printSection, printInfo } from "../ui.js";
import {
  promptSelect,
  promptConfirm,
  promptMultiSelect,
  SetupCancelledError,
} from "../setup/prompts.js";
import {
  SIX_QUESTIONS,
  parseCapabilitySummary,
  interrogateQuestion,
} from "../../agents/interrogation.js";
import type { VectorStore } from "../../rag/vector-store.js";

interface PaperMeta {
  slug: string;
  title: string;
  year: number | string;
  contentPath: string;
}

function loadPapers(): PaperMeta[] {
  const kbDir = CONFIG.knowledgeBasePath;
  if (!existsSync(kbDir)) return [];

  return readdirSync(kbDir, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => {
      const slug = d.name;
      const kwPath = join(kbDir, slug, "keywords.json");
      const srcPath = join(kbDir, slug, "source.json");
      const contentPath = join(kbDir, slug, "content", `${slug}.md`);

      let title = slug;
      let year: number | string = "";
      try {
        const kw = JSON.parse(readFileSync(kwPath, "utf-8"));
        title = kw.title ?? slug;
      } catch { /* ignore */ }
      try {
        const src = JSON.parse(readFileSync(srcPath, "utf-8"));
        year = src.year ?? "";
      } catch { /* ignore */ }

      return { slug, title, year, contentPath };
    })
    .sort((a, b) => a.slug.localeCompare(b.slug));
}

function verdictColor(v: string): string {
  if (v === "Yes")     return chalk.green(v);
  if (v === "Partial") return chalk.yellow(v);
  if (v === "No")      return chalk.red(v);
  return chalk.gray(v);
}

function printCapabilityTable(
  answers: Array<{ question: string; verdict: string; evidence: string }>,
  tier: string,
): void {
  const colW = [42, 16];
  const header = chalk.bold(
    `${"Question".padEnd(colW[0])}${"Answer".padEnd(colW[1])}Evidence`,
  );
  console.log(C.sep());
  console.log(header);
  console.log(C.sep());
  for (const row of answers) {
    const q  = row.question.slice(0, colW[0] - 1).padEnd(colW[0]);
    const v  = verdictColor(row.verdict).padEnd(
      colW[1] +
      (row.verdict === "Yes" ? 10 : row.verdict === "Partial" ? 13 : row.verdict === "No" ? 9 : 14),
    );
    const ev = chalk.gray(
      row.evidence.slice(0, 70) + (row.evidence.length > 70 ? "…" : ""),
    );
    console.log(`${q}${v}${ev}`);
  }
  console.log(C.sep());
  console.log(chalk.bold("Overall tier: ") + chalk.cyan(tier));
  console.log();
}

export async function paperCommand(store: VectorStore): Promise<void> {
  const papers = loadPapers();
  if (papers.length === 0) {
    console.log(C.warn("No knowledge base entries found. Run: npm run index"));
    return;
  }

  try {
    // ── Step 1: select paper ───────────────────────────────────────────────
    printSection("Deep Paper Interrogation");
    printInfo("Select a paper to evaluate against the 6 capability questions.");

    const selectedSlug = await promptSelect<string>(
      "Select a paper:",
      papers.map((p) => ({
        value: p.slug,
        label: `${String(p.year).padStart(4)}  ${p.title.slice(0, 60)}`,
        hint: p.slug,
      })),
    );

    const paper = papers.find((p) => p.slug === selectedSlug)!;
    console.log();
    console.log(chalk.bold(`📄 ${paper.title}`) + chalk.gray(` (${paper.year})`));
    console.log();

    // ── Step 2: select capability questions ───────────────────────────────
    const selectedQIds = await promptMultiSelect<string>(
      "Select capability questions to evaluate (space = toggle):",
      SIX_QUESTIONS.map((q) => ({
        value: q.id,
        label: q.label,
        hint: `Q${SIX_QUESTIONS.indexOf(q) + 1}`,
      })),
      SIX_QUESTIONS.map((q) => q.id),  // all pre-selected
    );

    if (selectedQIds.length === 0) {
      console.log(C.warn("No questions selected."));
      return;
    }

    const chosenQs = SIX_QUESTIONS.filter((q) => selectedQIds.includes(q.id));

    // ── Step 3: check for pre-computed Capability Summary ─────────────────
    let content = "";
    if (existsSync(paper.contentPath)) {
      content = readFileSync(paper.contentPath, "utf-8");
    }

    const parsed = parseCapabilitySummary(content);

    if (parsed) {
      const selected = parsed.answers.filter((a) =>
        chosenQs.some((q) =>
          a.question.toLowerCase().includes(q.label.toLowerCase().slice(0, 20)),
        ),
      );
      const displayAnswers = selected.length > 0
        ? selected
        : parsed.answers.filter((_, i) =>
            chosenQs.some(
              (q) => SIX_QUESTIONS[i]?.id && selectedQIds.includes(SIX_QUESTIONS[i].id),
            ),
          );

      const toShow = displayAnswers.length > 0 ? displayAnswers : parsed.answers;

      printSection("Capability Matrix (pre-computed)");
      printCapabilityTable(toShow, parsed.tier);

      const runDeep = await promptConfirm(
        "Run deep LLM interrogation for selected questions?",
        false,
      );
      if (!runDeep) return;
    }

    // ── Step 4: Deep LLM interrogation ────────────────────────────────────
    printSection("Deep LLM Interrogation");
    const results = [];

    for (const q of chosenQs) {
      process.stdout.write(chalk.gray(`  Interrogating: ${q.label}… `));
      try {
        const answer = await interrogateQuestion(store, paper.slug, paper.title, q);
        results.push(answer);
        console.log(verdictColor(answer.verdict));
      } catch (err) {
        console.log(chalk.red("error"));
        results.push({
          question: q.label,
          verdict: "Not evaluated" as const,
          evidence: String(err),
          confidence: "low" as const,
        });
      }
    }

    console.log();
    printCapabilityTable(
      results.map((r) => ({ question: r.question, verdict: r.verdict, evidence: r.evidence })),
      "LLM-analyzed",
    );
  } catch (error) {
    if (error instanceof SetupCancelledError) {
      console.log(C.dim("  Paper interrogation cancelled.\n"));
    } else {
      throw error;
    }
  }
}
