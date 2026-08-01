/**
 * Grading a student's answers against the computed analysis.
 *
 * The original PHP/Python version returned an eight-digit string like
 * `"0,0,0,0,0,0,0,0"` — one flag per rule, with no indication of *where* the
 * student went wrong. This module reports the specific cell or set member at
 * fault and names the rule that governs it, because "you misapplied FOLLOW
 * rule 3 on B" is a lesson and "wrong" is not.
 */

import { END_MARKER, EPSILON, type Production, formatProduction } from "./grammar";
import {
  type FirstRule,
  type FollowRule,
  type Ll1Analysis,
  RULE_DESCRIPTIONS,
  type TableRule,
} from "./ll1";

export type RuleId = FirstRule | FollowRule | TableRule;

export interface Discrepancy {
  /** Where the mistake is, e.g. `FIRST(A)` or `[A, b]`. */
  readonly location: string;
  /** What the student put. */
  readonly submitted: string;
  /** What the analysis says. */
  readonly expected: string;
  /** Rules that would have produced the right answer. */
  readonly rules: readonly RuleId[];
  readonly hint: string;
}

export interface SectionFeedback {
  readonly correct: boolean;
  readonly total: number;
  readonly matched: number;
  readonly discrepancies: readonly Discrepancy[];
}

export interface Feedback {
  readonly first?: SectionFeedback;
  readonly follow?: SectionFeedback;
  readonly table?: SectionFeedback;
  readonly allCorrect: boolean;
  /** Rules the student appears not to have applied correctly. */
  readonly rulesToRevisit: readonly RuleId[];
  readonly summary: string;
}

/** A student's sets, as `{ A: ["a", "ε"] }`. */
export type SubmittedSets = Record<string, readonly string[]>;

/**
 * A student's parse table, as `{ A: { b: 3 } }`, where the value is a
 * production number and `0` or absent means "blank".
 */
export type SubmittedTable = Record<string, Record<string, number | string | null>>;

function normalizeSet(values: readonly string[] | undefined): Set<string> {
  const result = new Set<string>();
  for (const raw of values ?? []) {
    const value = String(raw).trim();
    if (value === "") continue;
    result.add(value === "eps" || value === "@" ? EPSILON : value);
  }
  return result;
}

function describeSet(values: Iterable<string>): string {
  const sorted = [...values].sort();
  return sorted.length > 0 ? `{ ${sorted.join(", ")} }` : "{ }";
}

function compareSets(
  kind: "FIRST" | "FOLLOW",
  nonTerminals: readonly string[],
  expectedSets: Record<string, readonly { symbol: string; rules: readonly string[] }[]>,
  submitted: SubmittedSets,
): SectionFeedback {
  const discrepancies: Discrepancy[] = [];
  let matched = 0;

  for (const nonTerminal of nonTerminals) {
    const expected = new Set((expectedSets[nonTerminal] ?? []).map((e) => e.symbol));
    const given = normalizeSet(submitted[nonTerminal]);

    const missing = [...expected].filter((s) => !given.has(s));
    const extra = [...given].filter((s) => !expected.has(s));

    if (missing.length === 0 && extra.length === 0) {
      matched += 1;
      continue;
    }

    // Name the rules that justify exactly the members they got wrong.
    const rules = new Set<RuleId>();
    for (const entry of expectedSets[nonTerminal] ?? []) {
      if (missing.includes(entry.symbol)) {
        for (const rule of entry.rules) rules.add(rule as RuleId);
      }
    }
    if (extra.length > 0 && rules.size === 0) {
      rules.add(kind === "FIRST" ? "First_2" : "Follow_2");
    }

    const parts: string[] = [];
    if (missing.length > 0) parts.push(`missing ${missing.map((s) => `"${s}"`).join(", ")}`);
    if (extra.length > 0) parts.push(`should not include ${extra.map((s) => `"${s}"`).join(", ")}`);

    discrepancies.push({
      location: `${kind}(${nonTerminal})`,
      submitted: describeSet(given),
      expected: describeSet(expected),
      rules: [...rules].sort(),
      hint: `${kind}(${nonTerminal}) is ${parts.join(" and ")}.`,
    });
  }

  return {
    correct: discrepancies.length === 0,
    total: nonTerminals.length,
    matched,
    discrepancies,
  };
}

function cellText(entries: readonly { production: Production }[]): string {
  if (entries.length === 0) return "blank";
  return entries.map((e) => `(${e.production.index}) ${formatProduction(e.production)}`).join(" / ");
}

function compareTable(analysis: Ll1Analysis, submitted: SubmittedTable): SectionFeedback {
  const discrepancies: Discrepancy[] = [];
  let matched = 0;
  let total = 0;

  for (const nonTerminal of analysis.grammar.nonTerminals) {
    for (const terminal of analysis.columns) {
      total += 1;

      const cell = analysis.table[nonTerminal][terminal];
      const expectedIndices = cell.entries.map((e) => e.production.index).sort((a, b) => a - b);

      const raw = submitted[nonTerminal]?.[terminal];
      const parsed = raw === null || raw === undefined || raw === "" ? 0 : Number(raw);
      const givenIndex = Number.isFinite(parsed) ? parsed : NaN;

      if (Number.isNaN(givenIndex)) {
        discrepancies.push({
          location: `[${nonTerminal}, ${terminal}]`,
          submitted: String(raw),
          expected: cellText(cell.entries),
          rules: [],
          hint: `"${raw}" is not a production number. Use the number to the left of each production, or leave the cell blank.`,
        });
        continue;
      }

      const givenIndices = givenIndex === 0 ? [] : [givenIndex];
      const same =
        givenIndices.length === expectedIndices.length &&
        givenIndices.every((v, i) => v === expectedIndices[i]);

      if (same) {
        matched += 1;
        continue;
      }

      // A conflicted cell cannot be answered with a single number; say so
      // rather than marking the student wrong for the grammar's defect.
      if (expectedIndices.length > 1) {
        discrepancies.push({
          location: `[${nonTerminal}, ${terminal}]`,
          submitted: givenIndex === 0 ? "blank" : String(givenIndex),
          expected: cellText(cell.entries),
          rules: [...new Set(cell.entries.map((e) => e.rule))].sort(),
          hint: `This cell has a conflict — ${cell.entries.length} productions compete for it, so this grammar is not LL(1).`,
        });
        continue;
      }

      const rules = [...new Set(cell.entries.map((e) => e.rule))].sort() as RuleId[];
      const hint =
        expectedIndices.length === 0
          ? `This cell should be blank. Nothing in FIRST or FOLLOW puts a production of ${nonTerminal} under "${terminal}".`
          : cell.entries[0].rule === "PT_1"
            ? `"${terminal}" is in FIRST of production ${expectedIndices[0]}, so that production belongs here.`
            : `Production ${expectedIndices[0]} can derive ε and "${terminal}" is in FOLLOW(${nonTerminal}), so it belongs here.`;

      discrepancies.push({
        location: `[${nonTerminal}, ${terminal}]`,
        submitted: givenIndex === 0 ? "blank" : String(givenIndex),
        expected: cellText(cell.entries),
        rules,
        hint,
      });
    }
  }

  return {
    correct: discrepancies.length === 0,
    total,
    matched,
    discrepancies,
  };
}

export interface GradeRequest {
  readonly first?: SubmittedSets;
  readonly follow?: SubmittedSets;
  readonly table?: SubmittedTable;
}

/**
 * Grade whichever sections the student submitted.
 *
 * @param analysis The reference analysis for the grammar.
 * @param submission The student's answers; omitted sections are not graded.
 * @returns Per-section results, the rules to revisit, and a plain summary.
 */
export function grade(analysis: Ll1Analysis, submission: GradeRequest): Feedback {
  const sections: { name: string; result: SectionFeedback }[] = [];

  const first = submission.first
    ? compareSets("FIRST", analysis.grammar.nonTerminals, analysis.first, submission.first)
    : undefined;
  const follow = submission.follow
    ? compareSets("FOLLOW", analysis.grammar.nonTerminals, analysis.follow, submission.follow)
    : undefined;
  const table = submission.table ? compareTable(analysis, submission.table) : undefined;

  if (first) sections.push({ name: "FIRST sets", result: first });
  if (follow) sections.push({ name: "FOLLOW sets", result: follow });
  if (table) sections.push({ name: "parse table", result: table });

  const rulesToRevisit = new Set<RuleId>();
  for (const { result } of sections) {
    for (const discrepancy of result.discrepancies) {
      for (const rule of discrepancy.rules) rulesToRevisit.add(rule);
    }
  }

  const allCorrect = sections.length > 0 && sections.every((s) => s.result.correct);

  let summary: string;
  if (sections.length === 0) {
    summary = "Nothing was submitted.";
  } else if (allCorrect) {
    summary = `Everything checks out — ${sections.map((s) => s.name).join(", ")} all correct.`;
  } else {
    const wrong = sections.filter((s) => !s.result.correct);
    summary = wrong
      .map(({ name, result }) => `${result.matched} of ${result.total} correct in the ${name}`)
      .join("; ") + ".";
  }

  return { first, follow, table, allCorrect, rulesToRevisit: [...rulesToRevisit].sort(), summary };
}

/** Human-readable descriptions for the rules a student should revisit. */
export function describeRules(rules: readonly RuleId[]): string[] {
  return rules.map((rule) => RULE_DESCRIPTIONS[rule]);
}

export { END_MARKER, EPSILON };
