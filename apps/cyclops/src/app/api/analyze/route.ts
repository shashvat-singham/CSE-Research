/**
 * Analyse a grammar: FIRST, FOLLOW, parse table, conflicts.
 *
 * The analysis is pure computation over a small input, so it runs on the edge
 * runtime — no cold start, no filesystem, nothing to leak. The original
 * endpoint shelled out to `python ./nodeHandle.py` with `spawn`, streamed
 * stdout, and hardcoded `grammar = 2; task = 1`, ignoring the arguments it was
 * passed. Everything here is derived from the request.
 */

import { NextResponse } from "next/server";

import { parseGrammar } from "@/lib/grammar";
import { analyze, parseInput } from "@/lib/ll1";

export const runtime = "edge";

/** Guard against a pathological grammar pinning an edge worker. */
const MAX_SOURCE_LENGTH = 20_000;
const MAX_INPUT_LENGTH = 2_000;

interface AnalyzeBody {
  grammar?: unknown;
  input?: unknown;
}

export async function POST(request: Request) {
  let body: AnalyzeBody;
  try {
    body = (await request.json()) as AnalyzeBody;
  } catch {
    return NextResponse.json({ error: "Request body must be JSON." }, { status: 400 });
  }

  const source = typeof body.grammar === "string" ? body.grammar : "";
  if (source.trim() === "") {
    return NextResponse.json({ error: "No grammar supplied." }, { status: 400 });
  }
  if (source.length > MAX_SOURCE_LENGTH) {
    return NextResponse.json(
      { error: `Grammar is too large (limit ${MAX_SOURCE_LENGTH} characters).` },
      { status: 413 },
    );
  }

  const parsed = parseGrammar(source);
  if (!parsed.ok) {
    return NextResponse.json({ ok: false, errors: parsed.errors }, { status: 200 });
  }

  const analysis = analyze(parsed.grammar);

  const input = typeof body.input === "string" ? body.input : "";
  const parseResult =
    input.trim() === ""
      ? undefined
      : input.length > MAX_INPUT_LENGTH
        ? undefined
        : parseInput(input, analysis);

  return NextResponse.json(
    { ok: true, analysis, parse: parseResult },
    { headers: { "Cache-Control": "no-store" } },
  );
}
