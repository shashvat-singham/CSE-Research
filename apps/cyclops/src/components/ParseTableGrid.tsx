"use client";

import { useId } from "react";

import type { Ll1Analysis } from "@/lib/ll1";

export type CellValues = Record<string, Record<string, string>>;

interface Props {
  analysis: Ll1Analysis;
  /** Student answers when editable; ignored in reveal mode. */
  values: CellValues;
  onChange: (nonTerminal: string, terminal: string, value: string) => void;
  /** Per-cell correctness, set once an answer has been graded. */
  verdicts?: Record<string, Record<string, boolean>>;
  /** Show the computed answer instead of inputs. */
  reveal: boolean;
  disabled?: boolean;
}

/**
 * The editable LL(1) parse table.
 *
 * Students type a production *number* per cell, which is how the table is
 * written by hand and keeps the grid to one keystroke per entry. A blank cell
 * means "the parser errors here", which is a real answer and graded as one.
 */
export function ParseTableGrid({
  analysis,
  values,
  onChange,
  verdicts,
  reveal,
  disabled = false,
}: Props) {
  const gridId = useId();
  const { grammar, columns, table } = analysis;

  const cellClass = (nonTerminal: string, terminal: string) => {
    const verdict = verdicts?.[nonTerminal]?.[terminal];
    if (verdict === undefined) return "border-line";
    return verdict ? "border-good bg-good/10" : "border-bad bg-bad/10";
  };

  return (
    <div className="table-scroll">
      <table className="w-full min-w-[32rem] border-collapse text-sm">
        <caption className="sr-only">
          LL(1) parse table. Rows are non-terminals, columns are lookahead
          terminals, and each cell holds the number of the production to apply.
        </caption>
        <thead>
          <tr>
            <th
              scope="col"
              className="sticky left-0 z-10 border-b border-line bg-surface px-3 py-2
                         text-left font-medium text-ink-secondary"
            >
              <span className="sr-only">Non-terminal</span>
              <span aria-hidden>&nbsp;</span>
            </th>
            {columns.map((terminal) => (
              <th
                key={terminal}
                scope="col"
                className="border-b border-line px-3 py-2 text-center font-mono
                           text-xs font-medium text-ink-secondary"
              >
                {terminal}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {grammar.nonTerminals.map((nonTerminal) => (
            <tr key={nonTerminal}>
              <th
                scope="row"
                className="sticky left-0 z-10 border-b border-line bg-surface px-3 py-2
                           text-left font-mono text-sm font-medium text-ink"
              >
                {nonTerminal}
              </th>
              {columns.map((terminal) => {
                const expected = table[nonTerminal][terminal].entries;
                const inputId = `${gridId}-${nonTerminal}-${terminal}`;

                if (reveal) {
                  return (
                    <td
                      key={terminal}
                      className="border-b border-line px-2 py-1.5 text-center"
                    >
                      {expected.length === 0 ? (
                        <span className="text-ink-muted" aria-label="blank">
                          —
                        </span>
                      ) : (
                        <span
                          className={
                            expected.length > 1
                              ? "font-mono text-bad"
                              : "font-mono text-ink"
                          }
                          title={expected
                            .map((e) => `${e.production.head} → ${e.production.body.join(" ") || "ε"}`)
                            .join("  |  ")}
                        >
                          {expected.map((e) => e.production.index).join(" / ")}
                        </span>
                      )}
                    </td>
                  );
                }

                return (
                  <td key={terminal} className="border-b border-line px-1 py-1">
                    <label className="sr-only" htmlFor={inputId}>
                      Production number for {nonTerminal} with lookahead {terminal}
                    </label>
                    <input
                      id={inputId}
                      type="text"
                      inputMode="numeric"
                      autoComplete="off"
                      disabled={disabled}
                      value={values[nonTerminal]?.[terminal] ?? ""}
                      onChange={(event) =>
                        onChange(nonTerminal, terminal, event.target.value.trim())
                      }
                      placeholder="—"
                      className={`w-14 rounded border bg-surface px-2 py-1.5 text-center
                                  font-mono text-sm text-ink placeholder:text-ink-muted
                                  focus:border-accent focus:outline-none
                                  disabled:opacity-50 ${cellClass(nonTerminal, terminal)}`}
                    />
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
