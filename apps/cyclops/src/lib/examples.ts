/** Worked grammars offered in the workbench. */

export interface Example {
  readonly id: string;
  readonly name: string;
  readonly blurb: string;
  readonly grammar: string;
  readonly sampleInput: string;
  /** Set when the grammar is deliberately not LL(1). */
  readonly notLl1?: string;
}

export const EXAMPLES: readonly Example[] = [
  {
    id: "reference",
    name: "Balanced a's and b's",
    blurb:
      "The grammar the original Cyclops shipped with. Two nullable non-terminals, " +
      "so both parse-table rules come into play.",
    grammar: "S -> A b B\nA -> a A b | eps\nB -> b B | eps",
    sampleInput: "a b b",
  },
  {
    id: "expression",
    name: "Arithmetic expressions",
    blurb:
      "The textbook expression grammar after removing left recursion. E' and T' " +
      "are the nullable tails that make it work.",
    grammar:
      "E  -> T E'\n" +
      "E' -> + T E' | eps\n" +
      "T  -> F T'\n" +
      "T' -> * F T' | eps\n" +
      "F  -> ( E ) | id",
    sampleInput: "id + id * id",
  },
  {
    id: "left-recursive",
    name: "Left recursion (not LL(1))",
    blurb:
      "The same language written left-recursively. No left-recursive grammar is " +
      "LL(1); compare its conflicts against the version above.",
    grammar: "E -> E + T | T\nT -> T * F | F\nF -> ( E ) | id",
    sampleInput: "id + id",
    notLl1: "E and T are left-recursive.",
  },
  {
    id: "dangling-else",
    name: "Dangling else (not LL(1))",
    blurb:
      "The classic ambiguity: after an if-statement the parser cannot tell whether " +
      "an else binds here or to an enclosing if.",
    grammar:
      "S -> if e then S S' | a\n" +
      "S' -> else S | eps",
    sampleInput: "if e then a else a",
    notLl1: "S' has a FIRST/FOLLOW conflict on 'else'.",
  },
  {
    id: "statements",
    name: "Statement list",
    blurb: "A right-recursive list, the shape most LL(1) grammars use for sequences.",
    grammar:
      "P -> S L\n" +
      "L -> ; S L | eps\n" +
      "S -> id = E\n" +
      "E -> id | num",
    sampleInput: "id = num ; id = id",
  },
];

export const DEFAULT_EXAMPLE = EXAMPLES[0];
