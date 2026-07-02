// Terminal UI — Feynman color palette + clack-compatible panel helpers

const RESET = "\x1b[0m";
const BOLD  = "\x1b[1m";
const DIM   = "\x1b[2m";

function rgb(r: number, g: number, b: number): string {
  return `\x1b[38;2;${r};${g};${b}m`;
}

// Feynman palette (matches feynman/src/ui/terminal.ts exactly)
const INK      = rgb(211, 198, 170);
const STONE    = rgb(157, 169, 160);
export const ASH      = rgb(133, 146, 137);
const DARK_ASH = rgb(92,  106, 114);
export const SAGE     = rgb(167, 192, 128);
const TEAL     = rgb(127, 187, 179);
const ROSE     = rgb(230, 126, 128);

function paint(text: string, ...codes: string[]): string {
  return `${codes.join("")}${text}${RESET}`;
}

// ── PerturbQA ASCII logo (feynman solid-block style) ─────────────────────
const LOGO_LINES = [
  "   ██████╗ ███████╗██████╗ ████████╗██╗   ██╗██████╗ ██████╗  ██████╗  █████╗",
  "   ██╔══██╗██╔════╝██╔══██╗╚══██╔══╝██║   ██║██╔══██╗██╔══██╗██╔═══██╗██╔══██╗",
  "   ██████╔╝█████╗  ██████╔╝   ██║   ██║   ██║██████╔╝██████╔╝██║   ██║███████║",
  "   ██╔═══╝ ██╔══╝  ██╔══██╗   ██║   ██║   ██║██╔══██╗██╔══██╗██║▄▄ ██║██╔══██║",
  "   ██║     ███████╗██║  ██║   ██║   ╚██████╔╝██║  ██║██████╔╝╚██████╔╝██║  ██║",
  "   ╚═╝     ╚══════╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═════╝  ╚══▀▀═╝╚═╝  ╚═╝",
];

export function printAsciiHeader(subtitleLines: string[] = []): void {
  console.log();
  for (const line of LOGO_LINES) {
    console.log(paint(line, TEAL, BOLD));
  }
  for (const line of subtitleLines) {
    console.log(paint(`  ${line}`, ASH));
  }
  console.log();
}

export function printBanner(): void {
  printAsciiHeader([
    "Gene Perturbation Knowledge Q&A",
    "Agentic RAG · Multi-Agent · Domain MCP · 51 papers",
  ]);
}

export function printHelp(): void {
  const inner = 54;
  const border = "─".repeat(inner + 2);

  const line = (text: string, color = INK, bold = false): void => {
    const content = text.length > inner ? text.slice(0, inner - 1) : text;
    const codes = bold ? `${color}${BOLD}` : color;
    console.log(`${DARK_ASH}${BOLD}│${RESET} ${codes}${content.padEnd(inner)}${RESET} ${DARK_ASH}${BOLD}│${RESET}`);
  };

  console.log();
  console.log(paint(`┌${border}┐`, DARK_ASH, BOLD));
  line("Commands", TEAL, true);
  console.log(paint(`├${border}┤`, DARK_ASH, BOLD));
  line(`\\model              Switch LLM backend`);
  line(`\\paper              Deep-interrogate a paper (6 capability questions)`);
  line(`\\bench              Run all benchmark questions`);
  line(`\\bench gp-001 ...   Run specific questions by ID`);
  line(`\\help               Show this help`);
  line(`\\exit               Exit PerturbQA`);
  line(`(free text)         Q&A: Planner → Retriever → Generator → Validator`);
  console.log(paint(`└${border}┘`, DARK_ASH, BOLD));
  console.log();
}

export function printPanel(title: string, subtitleLines: string[] = []): void {
  const inner = 53;
  const border = "─".repeat(inner + 2);
  const renderLine = (text: string, color: string, bold = false): string => {
    const content = text.length > inner ? `${text.slice(0, inner - 3)}...` : text;
    const codes = bold ? `${color}${BOLD}` : color;
    return `${DARK_ASH}${BOLD}│${RESET} ${codes}${content.padEnd(inner)}${RESET} ${DARK_ASH}${BOLD}│${RESET}`;
  };

  console.log();
  console.log(paint(`┌${border}┐`, DARK_ASH, BOLD));
  console.log(renderLine(title, TEAL, true));
  if (subtitleLines.length > 0) {
    console.log(paint(`├${border}┤`, DARK_ASH, BOLD));
    for (const sub of subtitleLines) {
      console.log(renderLine(sub, INK));
    }
  }
  console.log(paint(`└${border}┘`, DARK_ASH, BOLD));
  console.log();
}

export function printSection(title: string): void {
  console.log();
  console.log(paint(`◆ ${title}`, TEAL, BOLD));
}

export function printInfo(text: string): void {
  console.log(paint(`  ${text}`, ASH));
}

export function printSuccess(text: string): void {
  console.log(paint(`✓ ${text}`, SAGE, BOLD));
}

export function printWarning(text: string): void {
  console.log(paint(`⚠ ${text}`, STONE, BOLD));
}

export function printError(text: string): void {
  console.log(paint(`✗ ${text}`, ROSE, BOLD));
}

// ── REPL prompt helpers ────────────────────────────────────────────────────
import chalk from "chalk";

export const C = {
  prompt:  chalk.bold.cyan("perturbqa"),
  dim:     (s: string) => paint(s, DIM + ASH),
  bold:    (s: string) => paint(s, BOLD),
  accent:  (s: string) => paint(s, TEAL),
  success: (s: string) => paint(s, SAGE, BOLD),
  warn:    (s: string) => paint(s, INK, BOLD),
  error:   (s: string) => paint(s, ROSE, BOLD),
  sep:     () => paint("─".repeat(56), DARK_ASH),
};

// ── Inline spinner ─────────────────────────────────────────────────────────
export function createSpinner(text: string): { stop: (msg?: string) => void } {
  const frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];
  let i = 0;
  const iv = setInterval(() => {
    process.stdout.write(`\r${paint(frames[i++ % frames.length], TEAL)}${paint(` ${text}`, ASH)}`);
  }, 80);
  return {
    stop(msg?: string) {
      clearInterval(iv);
      process.stdout.write("\r" + " ".repeat(text.length + 4) + "\r");
      if (msg) console.log(msg);
    },
  };
}
