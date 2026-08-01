/**
 * Grammar representation and parsing.
 *
 * The original Python engine represented a production's right-hand side by
 * joining symbols with `_` and splitting on it later. That made any symbol
 * containing an underscore unrepresentable, and made `FIRST` of a
 * multi-symbol string depend on string slicing rather than on the symbols
 * themselves. Here a right-hand side is an array of symbols, so the algorithms
 * below operate on the grammar rather than on its printed form.
 */

/** The empty string. Written `eps` in grammar source, rendered as ε. */
export const EPSILON = "ε";

/** End-of-input marker, used in FOLLOW sets and the parse table. */
export const END_MARKER = "$";

/** Spellings accepted for epsilon in grammar source text. */
const EPSILON_ALIASES = new Set(["eps", "epsilon", "ε", "@", "''", '""']);

/** Arrow forms accepted between a production's sides. */
const ARROW = /\s*(?:->|→|::=|:)\s*/;

export interface Production {
  /** Non-terminal on the left. */
  readonly head: string;
  /** Symbols on the right; empty array means an epsilon production. */
  readonly body: readonly string[];
  /** 1-based index, matching the numbering shown in the parse table. */
  readonly index: number;
}

export interface Grammar {
  readonly productions: readonly Production[];
  readonly nonTerminals: readonly string[];
  readonly terminals: readonly string[];
  readonly startSymbol: string;
}

export interface GrammarError {
  readonly line: number;
  readonly message: string;
}

export type GrammarParseResult =
  | { readonly ok: true; readonly grammar: Grammar }
  | { readonly ok: false; readonly errors: readonly GrammarError[] };

/** True when a token spells the empty string. */
export function isEpsilon(symbol: string): boolean {
  return EPSILON_ALIASES.has(symbol) || symbol === EPSILON;
}

/**
 * Render a production the way it is displayed in the UI.
 *
 * @example formatProduction({head: "A", body: [], index: 3}) // "A → ε"
 */
export function formatProduction(production: Production): string {
  const body = production.body.length > 0 ? production.body.join(" ") : EPSILON;
  return `${production.head} → ${body}`;
}

/**
 * Parse grammar source into a {@link Grammar}.
 *
 * Accepts one production per line, `->`, `→`, `::=` or `:` as the arrow, and
 * `|` to separate alternatives. Blank lines and `#` comments are ignored. The
 * head of the first production becomes the start symbol.
 *
 * Every symbol appearing as some production's head is a non-terminal;
 * everything else on a right-hand side is a terminal. This means a symbol is
 * classified by how the grammar uses it, not by its capitalisation — so
 * lowercase non-terminals and uppercase terminals both work.
 *
 * @param source Grammar text.
 * @returns The grammar, or the collected syntax errors with line numbers.
 *
 * @example
 * parseGrammar("S -> A b B\nA -> a A b | eps\nB -> b B | eps")
 */
export function parseGrammar(source: string): GrammarParseResult {
  const errors: GrammarError[] = [];
  const draft: { head: string; body: string[] }[] = [];

  const lines = source.split(/\r?\n/);

  lines.forEach((rawLine, offset) => {
    const line = rawLine.replace(/#.*$/, "").trim();
    if (line === "") return;

    const lineNumber = offset + 1;
    const parts = line.split(ARROW);

    if (parts.length < 2) {
      errors.push({
        line: lineNumber,
        message: `Missing an arrow. Write productions as "A -> b C".`,
      });
      return;
    }
    if (parts.length > 2) {
      errors.push({
        line: lineNumber,
        message: "More than one arrow on this line.",
      });
      return;
    }

    const head = parts[0].trim();
    if (head === "") {
      errors.push({ line: lineNumber, message: "Missing the non-terminal before the arrow." });
      return;
    }
    if (/\s/.test(head)) {
      errors.push({
        line: lineNumber,
        message: `"${head}" is not a single symbol. The left of the arrow must be one non-terminal.`,
      });
      return;
    }

    for (const alternative of parts[1].split("|")) {
      const symbols = alternative.trim().split(/\s+/).filter((s) => s !== "");

      if (symbols.length === 0) {
        errors.push({
          line: lineNumber,
          message: `Empty alternative. Write "eps" if ${head} can derive the empty string.`,
        });
        continue;
      }

      // "a eps b" is almost always a mistake; a lone "eps" is the real thing.
      const hasEpsilon = symbols.some(isEpsilon);
      if (hasEpsilon && symbols.length > 1) {
        if (symbols.every(isEpsilon)) {
          // The artifact's own grammars pad epsilon productions to a fixed
          // width, e.g. "A -> eps eps eps". Treat that as a single epsilon.
          draft.push({ head, body: [] });
          continue;
        }
        errors.push({
          line: lineNumber,
          message: `"eps" cannot sit beside other symbols. Split this into separate alternatives.`,
        });
        continue;
      }

      draft.push({ head, body: hasEpsilon ? [] : symbols });
    }
  });

  if (draft.length === 0) {
    if (errors.length === 0) {
      errors.push({ line: 1, message: "The grammar is empty." });
    }
    return { ok: false, errors };
  }
  if (errors.length > 0) {
    return { ok: false, errors };
  }

  const productions: Production[] = draft.map((p, i) => ({
    head: p.head,
    body: p.body,
    index: i + 1,
  }));

  const nonTerminalSet = new Set(productions.map((p) => p.head));

  // Preserve first-appearance order: it drives row and column order in the
  // parse table, and a stable order keeps the UI from reshuffling on edit.
  const nonTerminals: string[] = [];
  const terminals: string[] = [];
  for (const production of productions) {
    if (!nonTerminals.includes(production.head)) nonTerminals.push(production.head);
    for (const symbol of production.body) {
      if (!nonTerminalSet.has(symbol) && !terminals.includes(symbol)) {
        terminals.push(symbol);
      }
    }
  }

  return {
    ok: true,
    grammar: {
      productions,
      nonTerminals,
      terminals,
      startSymbol: productions[0].head,
    },
  };
}

/** Symbols that can never derive a terminal string, so no input reaches them. */
export function findNonProductiveSymbols(grammar: Grammar): string[] {
  const productive = new Set<string>();
  let changed = true;

  while (changed) {
    changed = false;
    for (const production of grammar.productions) {
      if (productive.has(production.head)) continue;
      const bodyProductive = production.body.every(
        (symbol) => !grammar.nonTerminals.includes(symbol) || productive.has(symbol),
      );
      if (bodyProductive) {
        productive.add(production.head);
        changed = true;
      }
    }
  }

  return grammar.nonTerminals.filter((nt) => !productive.has(nt));
}

/** Non-terminals no derivation from the start symbol can reach. */
export function findUnreachableSymbols(grammar: Grammar): string[] {
  const reachable = new Set<string>([grammar.startSymbol]);
  let changed = true;

  while (changed) {
    changed = false;
    for (const production of grammar.productions) {
      if (!reachable.has(production.head)) continue;
      for (const symbol of production.body) {
        if (grammar.nonTerminals.includes(symbol) && !reachable.has(symbol)) {
          reachable.add(symbol);
          changed = true;
        }
      }
    }
  }

  return grammar.nonTerminals.filter((nt) => !reachable.has(nt));
}

/**
 * Non-terminals that are left-recursive, directly or through other symbols.
 *
 * Left recursion is the most common reason a grammar cannot be LL(1), and it
 * produces a table conflict that is hard to interpret without being named.
 */
export function findLeftRecursion(grammar: Grammar, nullable: ReadonlySet<string>): string[] {
  // A -> B ... contributes an edge A -> B whenever every symbol before B is
  // nullable, since then B can appear leftmost.
  const edges = new Map<string, Set<string>>();
  for (const nonTerminal of grammar.nonTerminals) {
    edges.set(nonTerminal, new Set());
  }

  for (const production of grammar.productions) {
    for (const symbol of production.body) {
      if (!grammar.nonTerminals.includes(symbol)) break;
      edges.get(production.head)!.add(symbol);
      if (!nullable.has(symbol)) break;
    }
  }

  const recursive: string[] = [];
  for (const start of grammar.nonTerminals) {
    const seen = new Set<string>();
    const stack = [...(edges.get(start) ?? [])];
    while (stack.length > 0) {
      const current = stack.pop()!;
      if (current === start) {
        recursive.push(start);
        break;
      }
      if (seen.has(current)) continue;
      seen.add(current);
      stack.push(...(edges.get(current) ?? []));
    }
  }
  return recursive;
}
