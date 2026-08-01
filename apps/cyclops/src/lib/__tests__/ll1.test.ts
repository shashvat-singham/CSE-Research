/**
 * Tests for the LL(1) engine.
 *
 * The primary fixture is the grammar the original artifact shipped in
 * `input_specs.py`, together with the FIRST/FOLLOW/parse-table answers it
 * hardcoded — so these assert the rewrite reproduces the reference behaviour
 * rather than merely being self-consistent.
 */

import { describe, expect, it } from "vitest";

import { EPSILON, END_MARKER, parseGrammar, formatProduction } from "../grammar";
import { analyze, parseInput } from "../ll1";
import { grade } from "../feedback";

/**
 * From the artifact's `input_specs.py`:
 *   S -> A b B
 *   A -> a A b | eps
 *   B -> b B | eps
 */
const REFERENCE = `
S -> A b B
A -> a A b
A -> eps
B -> b B
B -> eps
`;

function analyzeSource(source: string) {
  const parsed = parseGrammar(source);
  if (!parsed.ok) throw new Error(`grammar failed to parse: ${JSON.stringify(parsed.errors)}`);
  return analyze(parsed.grammar);
}

function setOf(analysis: ReturnType<typeof analyze>, kind: "first" | "follow", nt: string) {
  return new Set(analysis[kind][nt].map((e) => e.symbol));
}

describe("parseGrammar", () => {
  it("numbers productions from one, in source order", () => {
    const parsed = parseGrammar(REFERENCE);
    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;
    expect(parsed.grammar.productions.map((p) => p.index)).toEqual([1, 2, 3, 4, 5]);
    expect(formatProduction(parsed.grammar.productions[2])).toBe("A → ε");
  });

  it("classifies symbols by use, not by capitalisation", () => {
    const parsed = parseGrammar("expr -> expr PLUS term\nexpr -> term\nterm -> ID");
    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;
    expect(parsed.grammar.nonTerminals).toEqual(["expr", "term"]);
    expect(parsed.grammar.terminals).toEqual(["PLUS", "ID"]);
  });

  it("expands alternatives written with a pipe", () => {
    const piped = parseGrammar("S -> A b B\nA -> a A b | eps\nB -> b B | eps");
    const explicit = parseGrammar(REFERENCE);
    expect(piped.ok && explicit.ok).toBe(true);
    if (!piped.ok || !explicit.ok) return;
    expect(piped.grammar.productions).toEqual(explicit.grammar.productions);
  });

  it("accepts the artifact's padded epsilon productions", () => {
    // input_specs.py writes ['A','eps','eps','eps'] to keep rules rectangular.
    const parsed = parseGrammar("S -> a\nA -> eps eps eps");
    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;
    expect(parsed.grammar.productions[1].body).toEqual([]);
  });

  it("supports symbols containing underscores", () => {
    // The original joined right-hand sides with "_" and split on it, which
    // made these unrepresentable.
    const parsed = parseGrammar("stmt -> if_kw cond then_kw stmt");
    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;
    expect(parsed.grammar.productions[0].body).toEqual(["if_kw", "cond", "then_kw", "stmt"]);
  });

  it.each([
    ["S A b", "Missing an arrow"],
    ["S -> a -> b", "More than one arrow"],
    ["-> a", "Missing the non-terminal"],
    ["S T -> a", "not a single symbol"],
    ["S -> a eps b", "cannot sit beside"],
  ])("reports %s as an error", (source, expected) => {
    const parsed = parseGrammar(source);
    expect(parsed.ok).toBe(false);
    if (parsed.ok) return;
    expect(parsed.errors[0].message).toContain(expected);
  });

  it("reports the line number of an error", () => {
    const parsed = parseGrammar("S -> a\n\nbroken line\n");
    expect(parsed.ok).toBe(false);
    if (parsed.ok) return;
    expect(parsed.errors[0].line).toBe(3);
  });

  it("ignores comments and blank lines", () => {
    const parsed = parseGrammar("# a comment\n\nS -> a  # trailing\n");
    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;
    expect(parsed.grammar.productions).toHaveLength(1);
  });
});

describe("FIRST and FOLLOW on the reference grammar", () => {
  const analysis = analyzeSource(REFERENCE);

  it("marks the nullable non-terminals", () => {
    expect(new Set(analysis.nullable)).toEqual(new Set(["A", "B"]));
  });

  it("computes FIRST", () => {
    expect(setOf(analysis, "first", "S")).toEqual(new Set(["a", "b"]));
    expect(setOf(analysis, "first", "A")).toEqual(new Set(["a", EPSILON]));
    expect(setOf(analysis, "first", "B")).toEqual(new Set(["b", EPSILON]));
  });

  it("computes FOLLOW", () => {
    expect(setOf(analysis, "follow", "S")).toEqual(new Set([END_MARKER]));
    expect(setOf(analysis, "follow", "A")).toEqual(new Set(["b"]));
    expect(setOf(analysis, "follow", "B")).toEqual(new Set([END_MARKER]));
  });

  it("records which rule justified each member", () => {
    const startFollow = analysis.follow.S.find((e) => e.symbol === END_MARKER);
    expect(startFollow?.rules).toContain("Follow_1");

    const firstOfS = analysis.first.S.find((e) => e.symbol === "a");
    expect(firstOfS?.rules).toContain("First_2");
  });
});

describe("parse table on the reference grammar", () => {
  const analysis = analyzeSource(REFERENCE);
  const at = (nt: string, t: string) =>
    analysis.table[nt][t].entries.map((e) => e.production.index);

  it("matches the table hardcoded in input_specs.py", () => {
    // parse_table = [{'S': a:1, b:1, $:0}, {'A': a:2, b:3, $:0}, {'B': a:0, b:4, $:5}]
    expect(at("S", "a")).toEqual([1]);
    expect(at("S", "b")).toEqual([1]);
    expect(at("S", END_MARKER)).toEqual([]);

    expect(at("A", "a")).toEqual([2]);
    expect(at("A", "b")).toEqual([3]);
    expect(at("A", END_MARKER)).toEqual([]);

    expect(at("B", "a")).toEqual([]);
    expect(at("B", "b")).toEqual([4]);
    expect(at("B", END_MARKER)).toEqual([5]);
  });

  it("is LL(1) with no conflicts", () => {
    expect(analysis.isLl1).toBe(true);
    expect(analysis.conflicts).toHaveLength(0);
  });

  it("labels entries with the rule that placed them", () => {
    expect(analysis.table.A.a.entries[0].rule).toBe("PT_1");
    // A -> eps lands under b via FOLLOW(A), not FIRST.
    expect(analysis.table.A.b.entries[0].rule).toBe("PT_2");
  });
});

describe("non-LL(1) grammars", () => {
  it("detects a FIRST/FIRST conflict", () => {
    const analysis = analyzeSource("S -> a b\nS -> a c");
    expect(analysis.isLl1).toBe(false);
    expect(analysis.conflicts[0].terminal).toBe("a");
    expect(analysis.conflicts[0].productions.map((p) => p.index)).toEqual([1, 2]);
    expect(analysis.conflicts[0].explanation).toContain("cannot choose");
  });

  it("detects a FIRST/FOLLOW conflict", () => {
    const analysis = analyzeSource("S -> A a\nA -> a\nA -> eps");
    expect(analysis.isLl1).toBe(false);
    const conflict = analysis.conflicts.find((c) => c.nonTerminal === "A");
    expect(conflict?.explanation).toContain("vanish");
  });

  it("names left recursion instead of only reporting the conflict", () => {
    const analysis = analyzeSource("E -> E plus T\nE -> T\nT -> id");
    expect(analysis.isLl1).toBe(false);
    expect(analysis.diagnostics.some((d) => d.includes("Left recursion on E"))).toBe(true);
  });

  it("detects indirect left recursion", () => {
    const analysis = analyzeSource("A -> B c\nB -> A d\nB -> e");
    expect(analysis.diagnostics.some((d) => d.includes("Left recursion"))).toBe(true);
  });

  it("terminates on cycles among nullable non-terminals", () => {
    // sys.setrecursionlimit(80) in the original made this blow the stack.
    const analysis = analyzeSource("S -> A\nA -> B\nB -> A\nA -> eps\nB -> eps");
    expect(analysis.nullable).toContain("A");
    expect(analysis.nullable).toContain("B");
  });
});

describe("parseInput", () => {
  const analysis = analyzeSource(REFERENCE);

  it.each([["b"], ["a b b"], ["a b b b"], ["b b"]])("accepts %s", (input) => {
    expect(parseInput(input, analysis).accepted).toBe(true);
  });

  it.each([["b a"], ["a"], ["a a b"]])("rejects %s", (input) => {
    expect(parseInput(input, analysis).accepted).toBe(false);
  });

  it("matches the accept/reject examples from input_specs.py", () => {
    // accept_strings = ["b", "a b b"];  reject_strings = ["b a"]
    expect(parseInput("b", analysis).accepted).toBe(true);
    expect(parseInput("a b b", analysis).accepted).toBe(true);
    expect(parseInput("b a", analysis).accepted).toBe(false);
  });

  it("produces a trace that ends in Accept", () => {
    const result = parseInput("a b b", analysis);
    expect(result.trace.length).toBeGreaterThan(3);
    expect(result.trace.at(-1)?.action).toBe("Accept");
    expect(result.trace[0].stack).toEqual([END_MARKER, "S"]);
  });

  it("explains why an input was rejected", () => {
    const result = parseInput("b a", analysis);
    expect(result.accepted).toBe(false);
    expect(result.error).toBeTruthy();
    expect(result.trace.at(-1)?.action).toContain("Error");
  });

  it("stops rather than looping forever", () => {
    const cyclic = analyzeSource("S -> S a\nS -> a");
    const result = parseInput("a a a", cyclic, 50);
    expect(result.accepted).toBe(false);
    expect(result.trace.length).toBeLessThanOrEqual(50);
  });
});

describe("grading", () => {
  const analysis = analyzeSource(REFERENCE);

  const correctTable = {
    S: { a: 1, b: 1, [END_MARKER]: 0 },
    A: { a: 2, b: 3, [END_MARKER]: 0 },
    B: { a: 0, b: 4, [END_MARKER]: 5 },
  };

  it("accepts a fully correct table", () => {
    const feedback = grade(analysis, { table: correctTable });
    expect(feedback.allCorrect).toBe(true);
    expect(feedback.table?.discrepancies).toHaveLength(0);
    expect(feedback.summary).toContain("Everything checks out");
  });

  it("pinpoints a wrong cell and names the governing rule", () => {
    // The commented-out variant in input_specs.py has A/b as 3; blanking it
    // is the classic FOLLOW-rule mistake.
    const feedback = grade(analysis, {
      table: { ...correctTable, A: { a: 2, b: 0, [END_MARKER]: 0 } },
    });
    expect(feedback.allCorrect).toBe(false);
    const wrong = feedback.table?.discrepancies ?? [];
    expect(wrong).toHaveLength(1);
    expect(wrong[0].location).toBe("[A, b]");
    expect(wrong[0].rules).toContain("PT_2");
    expect(feedback.rulesToRevisit).toContain("PT_2");
  });

  it("counts how many cells were right", () => {
    const feedback = grade(analysis, {
      table: { ...correctTable, A: { a: 9, b: 3, [END_MARKER]: 0 } },
    });
    expect(feedback.table?.matched).toBe(8);
    expect(feedback.table?.total).toBe(9);
  });

  it("grades FIRST sets and reports missing members", () => {
    const feedback = grade(analysis, {
      first: { S: ["a"], A: ["a", "eps"], B: ["b", "eps"] },
    });
    expect(feedback.allCorrect).toBe(false);
    const wrong = feedback.first?.discrepancies ?? [];
    expect(wrong[0].location).toBe("FIRST(S)");
    expect(wrong[0].hint).toContain('missing "b"');
  });

  it("reports members that should not be there", () => {
    const feedback = grade(analysis, {
      follow: { S: [END_MARKER], A: ["b", "a"], B: [END_MARKER] },
    });
    const wrong = feedback.follow?.discrepancies ?? [];
    expect(wrong[0].hint).toContain("should not include");
  });

  it("accepts eps as a spelling of ε", () => {
    const feedback = grade(analysis, {
      first: { S: ["a", "b"], A: ["a", "eps"], B: ["b", "eps"] },
    });
    expect(feedback.first?.correct).toBe(true);
  });

  it("does not penalise a student for a grammar's own conflict", () => {
    const conflicted = analyzeSource("S -> a b\nS -> a c");
    const feedback = grade(conflicted, { table: { S: { a: 1, b: 0, c: 0, [END_MARKER]: 0 } } });
    const cell = feedback.table?.discrepancies.find((d) => d.location === "[S, a]");
    expect(cell?.hint).toContain("not LL(1)");
  });

  it("rejects a non-numeric cell with a usable message", () => {
    const feedback = grade(analysis, {
      table: { ...correctTable, S: { a: "abc", b: 1, [END_MARKER]: 0 } },
    });
    const wrong = feedback.table?.discrepancies.find((d) => d.location === "[S, a]");
    expect(wrong?.hint).toContain("not a production number");
  });

  it("grades only the sections that were submitted", () => {
    const feedback = grade(analysis, { first: { S: ["a", "b"], A: ["a", "eps"], B: ["b", "eps"] } });
    expect(feedback.first).toBeDefined();
    expect(feedback.follow).toBeUndefined();
    expect(feedback.table).toBeUndefined();
  });
});
