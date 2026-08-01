/**
 * LL(1) analysis: FIRST, FOLLOW, the parse table, and a trace-producing parser.
 *
 * The original Python implementation computed FIRST and FOLLOW by direct
 * recursion with `sys.setrecursionlimit(80)`, which silently blew up on
 * grammars with cycles among nullable non-terminals. Both sets here are
 * computed as least fixed points — iterate until nothing changes — which
 * terminates on every grammar, cyclic or not.
 *
 * Every set is also recorded with the *rule* that justified each member, so
 * the UI can tell a student not just that their answer is wrong but which rule
 * they misapplied.
 */

import {
  END_MARKER,
  EPSILON,
  type Grammar,
  type Production,
  findLeftRecursion,
  formatProduction,
} from "./grammar";

/** Which textbook rule put a symbol into a set. */
export type FirstRule = "First_1" | "First_2" | "First_3";
export type FollowRule = "Follow_1" | "Follow_2" | "Follow_3";
export type TableRule = "PT_1" | "PT_2";

export const RULE_DESCRIPTIONS: Record<FirstRule | FollowRule | TableRule, string> = {
  First_1: "FIRST rule 1 — a terminal is its own FIRST set.",
  First_2: "FIRST rule 2 — for A → X…, add FIRST(X) minus ε.",
  First_3: "FIRST rule 3 — if every symbol on the right is nullable, add ε.",
  Follow_1: "FOLLOW rule 1 — the start symbol is followed by $.",
  Follow_2: "FOLLOW rule 2 — for A → α B β, add FIRST(β) minus ε to FOLLOW(B).",
  Follow_3: "FOLLOW rule 3 — for A → α B, or A → α B β with β nullable, add FOLLOW(A) to FOLLOW(B).",
  PT_1: "Table rule 1 — put A → α under every terminal in FIRST(α).",
  PT_2: "Table rule 2 — if α is nullable, put A → α under every terminal in FOLLOW(A).",
};

export interface SetEntry {
  readonly symbol: string;
  readonly rules: readonly (FirstRule | FollowRule)[];
}

export type SymbolSets = Record<string, readonly SetEntry[]>;

export interface TableEntry {
  readonly production: Production;
  readonly rule: TableRule;
}

export interface TableCell {
  readonly nonTerminal: string;
  readonly terminal: string;
  /** More than one entry means the grammar is not LL(1) at this cell. */
  readonly entries: readonly TableEntry[];
}

export interface Conflict {
  readonly nonTerminal: string;
  readonly terminal: string;
  readonly productions: readonly Production[];
  readonly explanation: string;
}

export interface Ll1Analysis {
  readonly grammar: Grammar;
  readonly nullable: readonly string[];
  readonly first: SymbolSets;
  readonly follow: SymbolSets;
  /** Indexed as `table[nonTerminal][terminal]`. */
  readonly table: Record<string, Record<string, TableCell>>;
  readonly columns: readonly string[];
  readonly conflicts: readonly Conflict[];
  readonly isLl1: boolean;
  readonly diagnostics: readonly string[];
}

class RuleSet {
  private readonly entries = new Map<string, Set<string>>();

  /**
   * Record that `rule` justifies `symbol`'s membership.
   *
   * @returns True only when the symbol is newly a member. The fixed-point
   *   loops below iterate on membership alone; noting an additional rule for
   *   a symbol already present does not require another pass, and the final
   *   pass re-visits every production, so provenance ends up complete either
   *   way.
   */
  add(symbol: string, rule: string): boolean {
    const existing = this.entries.get(symbol);
    if (existing) {
      existing.add(rule);
      return false;
    }
    this.entries.set(symbol, new Set([rule]));
    return true;
  }

  has(symbol: string): boolean {
    return this.entries.has(symbol);
  }

  get size(): number {
    return this.entries.size;
  }

  symbols(): string[] {
    return [...this.entries.keys()];
  }

  toEntries(order: readonly string[]): SetEntry[] {
    const rank = new Map(order.map((s, i) => [s, i]));
    return [...this.entries.entries()]
      .map(([symbol, rules]) => ({ symbol, rules: [...rules].sort() as SetEntry["rules"] }))
      .sort((a, b) => {
        const ra = rank.get(a.symbol) ?? Number.MAX_SAFE_INTEGER;
        const rb = rank.get(b.symbol) ?? Number.MAX_SAFE_INTEGER;
        return ra !== rb ? ra - rb : a.symbol.localeCompare(b.symbol);
      });
  }
}

/** Non-terminals that can derive the empty string. */
function computeNullable(grammar: Grammar): Set<string> {
  const nullable = new Set<string>();
  let changed = true;
  while (changed) {
    changed = false;
    for (const production of grammar.productions) {
      if (nullable.has(production.head)) continue;
      if (production.body.every((s) => nullable.has(s))) {
        nullable.add(production.head);
        changed = true;
      }
    }
  }
  return nullable;
}

function computeFirst(grammar: Grammar, nullable: ReadonlySet<string>) {
  const first = new Map<string, RuleSet>();
  for (const nonTerminal of grammar.nonTerminals) first.set(nonTerminal, new RuleSet());

  const isNonTerminal = (s: string) => grammar.nonTerminals.includes(s);

  let changed = true;
  while (changed) {
    changed = false;

    for (const production of grammar.productions) {
      const target = first.get(production.head)!;

      if (production.body.length === 0) {
        if (target.add(EPSILON, "First_3")) changed = true;
        continue;
      }

      let allNullable = true;
      for (const symbol of production.body) {
        if (!isNonTerminal(symbol)) {
          // Rule 1: a terminal is its own FIRST set, and stops the scan.
          if (target.add(symbol, "First_1")) changed = true;
          allNullable = false;
          break;
        }
        // Rule 2: pull in FIRST of the non-terminal, minus epsilon.
        for (const inner of first.get(symbol)!.symbols()) {
          if (inner === EPSILON) continue;
          if (target.add(inner, "First_2")) changed = true;
        }
        if (!nullable.has(symbol)) {
          allNullable = false;
          break;
        }
      }

      // Rule 3: every symbol could vanish, so the whole right side can.
      if (allNullable && target.add(EPSILON, "First_3")) changed = true;
    }
  }

  return first;
}

/**
 * FIRST of an arbitrary symbol string, used for right-hand sides and suffixes.
 *
 * @returns The terminals that can begin the string, including ε if the whole
 *   string is nullable.
 */
export function firstOfSequence(
  symbols: readonly string[],
  grammar: Grammar,
  first: SymbolSets,
  nullable: ReadonlySet<string>,
): Set<string> {
  const result = new Set<string>();
  const isNonTerminal = (s: string) => grammar.nonTerminals.includes(s);

  for (const symbol of symbols) {
    if (!isNonTerminal(symbol)) {
      result.add(symbol);
      return result;
    }
    for (const entry of first[symbol] ?? []) {
      if (entry.symbol !== EPSILON) result.add(entry.symbol);
    }
    if (!nullable.has(symbol)) return result;
  }

  result.add(EPSILON);
  return result;
}

function computeFollow(
  grammar: Grammar,
  first: SymbolSets,
  nullable: ReadonlySet<string>,
) {
  const follow = new Map<string, RuleSet>();
  for (const nonTerminal of grammar.nonTerminals) follow.set(nonTerminal, new RuleSet());

  // Rule 1: the start symbol is followed by end-of-input.
  follow.get(grammar.startSymbol)!.add(END_MARKER, "Follow_1");

  const isNonTerminal = (s: string) => grammar.nonTerminals.includes(s);

  let changed = true;
  while (changed) {
    changed = false;

    for (const production of grammar.productions) {
      for (let position = 0; position < production.body.length; position += 1) {
        const symbol = production.body[position];
        if (!isNonTerminal(symbol)) continue;

        const target = follow.get(symbol)!;
        const rest = production.body.slice(position + 1);
        const firstOfRest = firstOfSequence(rest, grammar, first, nullable);

        // Rule 2: whatever can start the remainder can follow this symbol.
        for (const candidate of firstOfRest) {
          if (candidate === EPSILON) continue;
          if (target.add(candidate, "Follow_2")) changed = true;
        }

        // Rule 3: if the remainder can vanish, the head's followers apply.
        if (firstOfRest.has(EPSILON) || rest.length === 0) {
          for (const candidate of follow.get(production.head)!.symbols()) {
            if (target.add(candidate, "Follow_3")) changed = true;
          }
        }
      }
    }
  }

  return follow;
}

function toSymbolSets(sets: Map<string, RuleSet>, order: readonly string[]): SymbolSets {
  const result: SymbolSets = {};
  for (const [key, value] of sets) {
    (result as Record<string, readonly SetEntry[]>)[key] = value.toEntries(order);
  }
  return result;
}

/**
 * Run the full LL(1) analysis on a grammar.
 *
 * @param grammar The grammar to analyse.
 * @returns FIRST and FOLLOW sets with rule provenance, the parse table, and
 *   any conflicts that make the grammar non-LL(1).
 */
export function analyze(grammar: Grammar): Ll1Analysis {
  const nullableSet = computeNullable(grammar);
  const firstMap = computeFirst(grammar, nullableSet);
  const first = toSymbolSets(firstMap, [...grammar.terminals, EPSILON]);
  const followMap = computeFollow(grammar, first, nullableSet);
  const follow = toSymbolSets(followMap, [...grammar.terminals, END_MARKER]);

  const columns = [...grammar.terminals, END_MARKER];

  const table: Record<string, Record<string, TableCell>> = {};
  for (const nonTerminal of grammar.nonTerminals) {
    table[nonTerminal] = {};
    for (const terminal of columns) {
      table[nonTerminal][terminal] = { nonTerminal, terminal, entries: [] };
    }
  }

  const push = (nonTerminal: string, terminal: string, entry: TableEntry) => {
    const cell = table[nonTerminal]?.[terminal];
    if (!cell) return;
    // A production can qualify under both rules; record it once.
    if (cell.entries.some((e) => e.production.index === entry.production.index)) return;
    (cell.entries as TableEntry[]).push(entry);
  };

  for (const production of grammar.productions) {
    const firstOfBody = firstOfSequence(production.body, grammar, first, nullableSet);

    // Rule 1: under every terminal that can begin the right-hand side.
    for (const terminal of firstOfBody) {
      if (terminal === EPSILON) continue;
      push(production.head, terminal, { production, rule: "PT_1" });
    }

    // Rule 2: if the right-hand side can vanish, under every follower.
    if (firstOfBody.has(EPSILON)) {
      for (const entry of follow[production.head] ?? []) {
        push(production.head, entry.symbol, { production, rule: "PT_2" });
      }
    }
  }

  const conflicts: Conflict[] = [];
  for (const nonTerminal of grammar.nonTerminals) {
    for (const terminal of columns) {
      const cell = table[nonTerminal][terminal];
      if (cell.entries.length <= 1) continue;

      const productions = cell.entries.map((e) => e.production);
      const bothFromFirst = cell.entries.every((e) => e.rule === "PT_1");
      const explanation = bothFromFirst
        ? `Two alternatives of ${nonTerminal} can both begin with "${terminal}", so the parser cannot choose by looking at one token.`
        : `${nonTerminal} can both start with "${terminal}" and vanish while "${terminal}" follows it, so the parser cannot tell whether to expand or skip.`;

      conflicts.push({ nonTerminal, terminal, productions, explanation });
    }
  }

  const diagnostics: string[] = [];
  const leftRecursive = findLeftRecursion(grammar, nullableSet);
  if (leftRecursive.length > 0) {
    diagnostics.push(
      `Left recursion on ${leftRecursive.join(", ")}. No left-recursive grammar is LL(1); rewrite it before building a table.`,
    );
  }
  for (const conflict of conflicts) {
    diagnostics.push(
      `Conflict at [${conflict.nonTerminal}, ${conflict.terminal}]: ${conflict.productions
        .map((p) => `(${p.index}) ${formatProduction(p)}`)
        .join(" and ")}. ${conflict.explanation}`,
    );
  }

  return {
    grammar,
    nullable: grammar.nonTerminals.filter((nt) => nullableSet.has(nt)),
    first,
    follow,
    table,
    columns,
    conflicts,
    isLl1: conflicts.length === 0,
    diagnostics,
  };
}

// -- parsing -----------------------------------------------------------------

export interface TraceStep {
  readonly step: number;
  /** Top of stack is the last element, matching how it is drawn. */
  readonly stack: readonly string[];
  readonly remainingInput: readonly string[];
  readonly action: string;
  readonly production?: Production;
}

export interface ParseResult {
  readonly accepted: boolean;
  readonly trace: readonly TraceStep[];
  readonly error?: string;
}

/**
 * Parse a token string with the LL(1) table, recording every step.
 *
 * @param input Whitespace-separated tokens, without the end marker.
 * @param analysis A completed {@link analyze} result.
 * @param maxSteps Guard against runaway expansion on a non-LL(1) grammar.
 * @returns Whether the input is accepted, plus the full derivation trace.
 */
export function parseInput(
  input: string,
  analysis: Ll1Analysis,
  maxSteps = 500,
): ParseResult {
  const tokens = input.trim().split(/\s+/).filter((t) => t !== "");
  tokens.push(END_MARKER);

  const stack: string[] = [END_MARKER, analysis.grammar.startSymbol];
  const trace: TraceStep[] = [];
  let cursor = 0;
  let step = 0;

  const record = (action: string, production?: Production) => {
    trace.push({
      step: step + 1,
      stack: [...stack],
      remainingInput: tokens.slice(cursor),
      action,
      production,
    });
    step += 1;
  };

  while (step < maxSteps) {
    const top = stack[stack.length - 1];
    const lookahead = tokens[cursor];

    if (top === END_MARKER && lookahead === END_MARKER) {
      record("Accept");
      return { accepted: true, trace };
    }

    const isNonTerminal = analysis.grammar.nonTerminals.includes(top);

    if (!isNonTerminal) {
      if (top === lookahead) {
        record(`Match "${top}"`);
        stack.pop();
        cursor += 1;
        continue;
      }
      const error = `Expected "${top}" but found "${lookahead}".`;
      record(`Error — ${error}`);
      return { accepted: false, trace, error };
    }

    const cell = analysis.table[top]?.[lookahead];
    if (!cell || cell.entries.length === 0) {
      const expected = analysis.columns
        .filter((t) => (analysis.table[top]?.[t]?.entries.length ?? 0) > 0)
        .map((t) => `"${t}"`)
        .join(", ");
      const error = `No table entry for [${top}, ${lookahead}].${
        expected ? ` ${top} can only begin with ${expected}.` : ""
      }`;
      record(`Error — ${error}`);
      return { accepted: false, trace, error };
    }

    // On a conflicted cell, take the first entry so the trace still shows the
    // student what the parser would attempt; the conflict is reported separately.
    const production = cell.entries[0].production;
    record(`Expand using (${production.index}) ${formatProduction(production)}`, production);
    stack.pop();
    for (let i = production.body.length - 1; i >= 0; i -= 1) {
      stack.push(production.body[i]);
    }
  }

  const error = `Stopped after ${maxSteps} steps — the grammar appears to loop on this input.`;
  return { accepted: false, trace, error };
}
