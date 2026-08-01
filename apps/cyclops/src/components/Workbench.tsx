"use client";

import { useCallback, useMemo, useState } from "react";

import { ParseTableGrid, type CellValues } from "@/components/ParseTableGrid";
import { DEFAULT_EXAMPLE, EXAMPLES } from "@/lib/examples";
import type { Feedback } from "@/lib/feedback";
import { EPSILON, type GrammarError, formatProduction } from "@/lib/grammar";
import { RULE_DESCRIPTIONS, type Ll1Analysis, type ParseResult } from "@/lib/ll1";

type Mode = "explore" | "practise";

interface AnalyzeResponse {
  ok: boolean;
  analysis?: Ll1Analysis;
  parse?: ParseResult;
  errors?: GrammarError[];
  error?: string;
}

export function Workbench() {
  const [grammarSource, setGrammarSource] = useState(DEFAULT_EXAMPLE.grammar);
  const [inputString, setInputString] = useState(DEFAULT_EXAMPLE.sampleInput);
  const [mode, setMode] = useState<Mode>("explore");

  const [analysis, setAnalysis] = useState<Ll1Analysis | null>(null);
  const [parseResult, setParseResult] = useState<ParseResult | null>(null);
  const [grammarErrors, setGrammarErrors] = useState<GrammarError[]>([]);
  const [requestError, setRequestError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [answers, setAnswers] = useState<CellValues>({});
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [revealed, setRevealed] = useState(false);

  const resetAnswers = useCallback(() => {
    setAnswers({});
    setFeedback(null);
    setRevealed(false);
  }, []);

  const runAnalysis = useCallback(async () => {
    setBusy(true);
    setRequestError(null);
    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ grammar: grammarSource, input: inputString }),
      });
      const payload = (await response.json()) as AnalyzeResponse;

      if (!response.ok) {
        setRequestError(payload.error ?? "The analysis failed.");
        return;
      }
      if (!payload.ok) {
        setGrammarErrors(payload.errors ?? []);
        setAnalysis(null);
        setParseResult(null);
        return;
      }

      setGrammarErrors([]);
      setAnalysis(payload.analysis ?? null);
      setParseResult(payload.parse ?? null);
      resetAnswers();
    } catch {
      setRequestError("Could not reach the server. Check your connection and try again.");
    } finally {
      setBusy(false);
    }
  }, [grammarSource, inputString, resetAnswers]);

  const submitAnswers = useCallback(async () => {
    if (!analysis) return;
    setBusy(true);
    setRequestError(null);
    try {
      const table: Record<string, Record<string, number>> = {};
      for (const nonTerminal of analysis.grammar.nonTerminals) {
        table[nonTerminal] = {};
        for (const terminal of analysis.columns) {
          const raw = answers[nonTerminal]?.[terminal] ?? "";
          table[nonTerminal][terminal] = raw === "" ? 0 : Number(raw);
        }
      }

      const response = await fetch("/api/grade", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ grammar: grammarSource, table }),
      });
      const payload = (await response.json()) as { feedback?: Feedback; error?: string };

      if (!response.ok) {
        setRequestError(payload.error ?? "Grading failed.");
        return;
      }
      setFeedback(payload.feedback ?? null);
    } catch {
      setRequestError("Could not reach the server. Check your connection and try again.");
    } finally {
      setBusy(false);
    }
  }, [analysis, answers, grammarSource]);

  const verdicts = useMemo(() => {
    if (!feedback?.table || !analysis) return undefined;
    const wrong = new Set(feedback.table.discrepancies.map((d) => d.location));
    const result: Record<string, Record<string, boolean>> = {};
    for (const nonTerminal of analysis.grammar.nonTerminals) {
      result[nonTerminal] = {};
      for (const terminal of analysis.columns) {
        result[nonTerminal][terminal] = !wrong.has(`[${nonTerminal}, ${terminal}]`);
      }
    }
    return result;
  }, [feedback, analysis]);

  const setCell = useCallback((nonTerminal: string, terminal: string, value: string) => {
    setAnswers((current) => ({
      ...current,
      [nonTerminal]: { ...current[nonTerminal], [terminal]: value },
    }));
  }, []);

  const loadExample = useCallback((id: string) => {
    const example = EXAMPLES.find((e) => e.id === id);
    if (!example) return;
    setGrammarSource(example.grammar);
    setInputString(example.sampleInput);
    setAnalysis(null);
    setParseResult(null);
    setGrammarErrors([]);
    resetAnswers();
  }, [resetAnswers]);

  return (
    <div className="space-y-6">
      {/* -- grammar input -------------------------------------------------- */}
      <section className="card p-5" aria-labelledby="grammar-heading">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <h2 id="grammar-heading" className="text-lg font-semibold">
            Grammar
          </h2>
          <label className="flex items-center gap-2 text-sm text-ink-secondary">
            Load an example
            <select
              className="field w-auto py-1.5"
              defaultValue={DEFAULT_EXAMPLE.id}
              onChange={(event) => loadExample(event.target.value)}
            >
              {EXAMPLES.map((example) => (
                <option key={example.id} value={example.id}>
                  {example.name}
                </option>
              ))}
            </select>
          </label>
        </div>

        <label htmlFor="grammar-source" className="sr-only">
          Grammar source
        </label>
        <textarea
          id="grammar-source"
          value={grammarSource}
          onChange={(event) => setGrammarSource(event.target.value)}
          rows={8}
          spellCheck={false}
          className="field font-mono leading-relaxed"
          aria-describedby="grammar-help"
        />
        <p id="grammar-help" className="mt-2 text-xs text-ink-muted">
          One production per line. Use <code>-&gt;</code> for the arrow,{" "}
          <code>|</code> to separate alternatives, and <code>eps</code> for the
          empty string. The first line&apos;s left-hand side is the start symbol.
        </p>

        {grammarErrors.length > 0 && (
          <div
            role="alert"
            className="mt-4 rounded-md border border-bad bg-bad/10 p-3 text-sm"
          >
            <p className="font-medium text-bad">This grammar does not parse:</p>
            <ul className="mt-2 space-y-1">
              {grammarErrors.map((error, index) => (
                <li key={index} className="text-ink-secondary">
                  <span className="font-mono text-xs">line {error.line}</span> — {error.message}
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="mt-4 flex flex-wrap items-end gap-3">
          <div className="min-w-[14rem] flex-1">
            <label htmlFor="input-string" className="mb-1 block text-sm text-ink-secondary">
              Input to parse (space-separated tokens)
            </label>
            <input
              id="input-string"
              type="text"
              value={inputString}
              onChange={(event) => setInputString(event.target.value)}
              spellCheck={false}
              className="field font-mono"
              placeholder="a b b"
            />
          </div>
          <button type="button" className="btn-primary" onClick={runAnalysis} disabled={busy}>
            {busy ? "Working…" : "Analyse"}
          </button>
        </div>

        {requestError && (
          <p role="alert" className="mt-3 text-sm text-bad">
            {requestError}
          </p>
        )}
      </section>

      {analysis && (
        <>
          {/* -- verdict ---------------------------------------------------- */}
          <section
            className={`card p-5 ${analysis.isLl1 ? "border-good" : "border-warn"}`}
            aria-live="polite"
          >
            <h2 className="text-lg font-semibold">
              {analysis.isLl1 ? "This grammar is LL(1)" : "This grammar is not LL(1)"}
            </h2>
            {analysis.diagnostics.length > 0 ? (
              <ul className="mt-3 space-y-2 text-sm text-ink-secondary">
                {analysis.diagnostics.map((diagnostic, index) => (
                  <li key={index} className="flex gap-2">
                    <span aria-hidden className="text-warn">
                      ▲
                    </span>
                    <span>{diagnostic}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-2 text-sm text-ink-secondary">
                Every cell of the parse table holds at most one production, so a
                single token of lookahead is enough to choose.
              </p>
            )}
          </section>

          {/* -- productions ------------------------------------------------ */}
          <section className="card p-5" aria-labelledby="productions-heading">
            <h2 id="productions-heading" className="mb-3 text-lg font-semibold">
              Productions
            </h2>
            <ol className="space-y-1 font-mono text-sm">
              {analysis.grammar.productions.map((production) => (
                <li key={production.index} className="flex gap-3">
                  <span className="w-6 shrink-0 text-right text-ink-muted">
                    {production.index}
                  </span>
                  <span>{formatProduction(production)}</span>
                </li>
              ))}
            </ol>
            <dl className="mt-4 grid gap-2 text-sm sm:grid-cols-3">
              <div>
                <dt className="text-ink-muted">Non-terminals</dt>
                <dd className="font-mono">{analysis.grammar.nonTerminals.join(", ")}</dd>
              </div>
              <div>
                <dt className="text-ink-muted">Terminals</dt>
                <dd className="font-mono">{analysis.grammar.terminals.join(", ") || "—"}</dd>
              </div>
              <div>
                <dt className="text-ink-muted">Nullable</dt>
                <dd className="font-mono">{analysis.nullable.join(", ") || "none"}</dd>
              </div>
            </dl>
          </section>

          {/* -- FIRST / FOLLOW --------------------------------------------- */}
          <section className="card p-5" aria-labelledby="sets-heading">
            <h2 id="sets-heading" className="mb-3 text-lg font-semibold">
              FIRST and FOLLOW
            </h2>
            <div className="table-scroll">
              <table className="w-full min-w-[28rem] border-collapse text-sm">
                <thead>
                  <tr className="border-b border-line text-left text-ink-secondary">
                    <th scope="col" className="px-3 py-2 font-medium">
                      Non-terminal
                    </th>
                    <th scope="col" className="px-3 py-2 font-medium">
                      FIRST
                    </th>
                    <th scope="col" className="px-3 py-2 font-medium">
                      FOLLOW
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {analysis.grammar.nonTerminals.map((nonTerminal) => (
                    <tr key={nonTerminal} className="border-b border-line">
                      <th scope="row" className="px-3 py-2 text-left font-mono font-medium">
                        {nonTerminal}
                      </th>
                      <td className="px-3 py-2 font-mono">
                        {"{ "}
                        {analysis.first[nonTerminal].map((e) => e.symbol).join(", ")}
                        {" }"}
                      </td>
                      <td className="px-3 py-2 font-mono">
                        {"{ "}
                        {analysis.follow[nonTerminal].map((e) => e.symbol).join(", ")}
                        {" }"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-xs text-ink-muted">
              <code>{EPSILON}</code> in a FIRST set means the non-terminal can
              derive the empty string.
            </p>
          </section>

          {/* -- parse table ------------------------------------------------ */}
          <section className="card p-5" aria-labelledby="table-heading">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <h2 id="table-heading" className="text-lg font-semibold">
                Parse table
              </h2>
              <div
                className="inline-flex rounded-md border border-line p-0.5"
                role="group"
                aria-label="Table mode"
              >
                {(["explore", "practise"] as const).map((option) => (
                  <button
                    key={option}
                    type="button"
                    aria-pressed={mode === option}
                    onClick={() => {
                      setMode(option);
                      resetAnswers();
                    }}
                    className={`rounded px-3 py-1.5 text-sm font-medium transition-colors ${
                      mode === option
                        ? "bg-accent text-white"
                        : "text-ink-secondary hover:text-ink"
                    }`}
                  >
                    {option === "explore" ? "Show answer" : "Fill it in"}
                  </button>
                ))}
              </div>
            </div>

            <ParseTableGrid
              analysis={analysis}
              values={answers}
              onChange={setCell}
              verdicts={verdicts}
              reveal={mode === "explore" || revealed}
              disabled={busy}
            />

            <p className="mt-3 text-xs text-ink-muted">
              Each cell holds the number of the production to apply. A dash means
              the parser reports an error on that lookahead.
            </p>

            {mode === "practise" && (
              <div className="mt-4 flex flex-wrap gap-3">
                <button
                  type="button"
                  className="btn-primary"
                  onClick={submitAnswers}
                  disabled={busy || revealed}
                >
                  Check my answers
                </button>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setRevealed(true)}
                  disabled={revealed}
                >
                  Reveal the answer
                </button>
                <button type="button" className="btn-secondary" onClick={resetAnswers}>
                  Clear
                </button>
              </div>
            )}

            {feedback && (
              <div
                role="status"
                aria-live="polite"
                className={`mt-4 rounded-md border p-4 text-sm ${
                  feedback.allCorrect ? "border-good bg-good/10" : "border-warn bg-warn/10"
                }`}
              >
                <p className="font-medium">{feedback.summary}</p>

                {feedback.table && feedback.table.discrepancies.length > 0 && (
                  <ul className="mt-3 space-y-2">
                    {feedback.table.discrepancies.map((discrepancy, index) => (
                      <li key={index} className="border-l-2 border-line-strong pl-3">
                        <span className="font-mono text-xs text-ink-secondary">
                          {discrepancy.location}
                        </span>
                        <span className="ml-2">
                          you put <strong>{discrepancy.submitted}</strong>, expected{" "}
                          <strong>{discrepancy.expected}</strong>
                        </span>
                        <p className="mt-0.5 text-ink-secondary">{discrepancy.hint}</p>
                      </li>
                    ))}
                  </ul>
                )}

                {feedback.rulesToRevisit.length > 0 && (
                  <div className="mt-4">
                    <p className="font-medium">Rules to revisit</p>
                    <ul className="mt-1 space-y-1 text-ink-secondary">
                      {feedback.rulesToRevisit.map((rule) => (
                        <li key={rule}>{RULE_DESCRIPTIONS[rule]}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </section>

          {/* -- trace ------------------------------------------------------ */}
          {parseResult && (
            <section className="card p-5" aria-labelledby="trace-heading">
              <h2 id="trace-heading" className="mb-1 text-lg font-semibold">
                Parsing <span className="font-mono text-base">{inputString}</span>
              </h2>
              <p
                className={`mb-4 text-sm font-medium ${
                  parseResult.accepted ? "text-good" : "text-bad"
                }`}
              >
                {parseResult.accepted ? "Accepted" : `Rejected — ${parseResult.error}`}
              </p>

              <div className="table-scroll">
                <table className="w-full min-w-[36rem] border-collapse text-sm">
                  <thead>
                    <tr className="border-b border-line text-left text-ink-secondary">
                      <th scope="col" className="px-3 py-2 font-medium">
                        #
                      </th>
                      <th scope="col" className="px-3 py-2 font-medium">
                        Stack
                      </th>
                      <th scope="col" className="px-3 py-2 font-medium">
                        Remaining input
                      </th>
                      <th scope="col" className="px-3 py-2 font-medium">
                        Action
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {parseResult.trace.map((step) => (
                      <tr key={step.step} className="border-b border-line align-top">
                        <td className="px-3 py-1.5 text-ink-muted">{step.step}</td>
                        <td className="px-3 py-1.5 font-mono text-xs">
                          {step.stack.join(" ")}
                        </td>
                        <td className="px-3 py-1.5 font-mono text-xs">
                          {step.remainingInput.join(" ")}
                        </td>
                        <td className="px-3 py-1.5">{step.action}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="mt-3 text-xs text-ink-muted">
                The stack is written left to right with the top at the right, so
                the rightmost symbol is the one the parser is working on.
              </p>
            </section>
          )}
        </>
      )}
    </div>
  );
}
