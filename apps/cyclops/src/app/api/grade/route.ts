/**
 * Grade a student's FIRST/FOLLOW/parse-table answers.
 *
 * Grading happens server-side so the reference answer is never shipped to the
 * browser alongside the exercise.
 */

import { NextResponse } from "next/server";

import { type GradeRequest, grade } from "@/lib/feedback";
import { parseGrammar } from "@/lib/grammar";
import { analyze } from "@/lib/ll1";

export const runtime = "edge";

const MAX_SOURCE_LENGTH = 20_000;

interface GradeBody extends GradeRequest {
  grammar?: unknown;
}

export async function POST(request: Request) {
  let body: GradeBody;
  try {
    body = (await request.json()) as GradeBody;
  } catch {
    return NextResponse.json({ error: "Request body must be JSON." }, { status: 400 });
  }

  const source = typeof body.grammar === "string" ? body.grammar : "";
  if (source.trim() === "") {
    return NextResponse.json({ error: "No grammar supplied." }, { status: 400 });
  }
  if (source.length > MAX_SOURCE_LENGTH) {
    return NextResponse.json({ error: "Grammar is too large." }, { status: 413 });
  }

  const parsed = parseGrammar(source);
  if (!parsed.ok) {
    return NextResponse.json(
      { error: "The grammar does not parse.", errors: parsed.errors },
      { status: 400 },
    );
  }

  const analysis = analyze(parsed.grammar);
  const feedback = grade(analysis, {
    first: body.first,
    follow: body.follow,
    table: body.table,
  });

  return NextResponse.json(
    { ok: true, feedback },
    { headers: { "Cache-Control": "no-store" } },
  );
}
