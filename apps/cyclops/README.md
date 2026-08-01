# Cyclops

An LL(1) parser workbench. Enter a grammar, get FIRST sets, FOLLOW sets and the
parse table — then fill the table in yourself and have it checked cell by cell,
with the governing rule named for every mistake.

**Live → [cyclops-delta.vercel.app](https://cyclops-delta.vercel.app/)**

## Running it

```bash
npm ci
npm run dev        # http://localhost:3000
```

```bash
npm test           # engine tests
npm run lint
npm run typecheck
npm run build
```

### Docker

```bash
docker build -t cyclops .
docker run --rm -p 3000:3000 cyclops
```

Three stages: dependencies from the lockfile alone (so a source-only change
reuses the layer), the build, then a runtime image holding just Next's
standalone output. It runs as the unprivileged `node` user, and the
healthcheck POSTs a grammar to `/api/analyze` — a passing check means the LL(1)
engine is actually answering, not merely that a port is open.

`output: "standalone"` is switched on by `BUILD_STANDALONE=1`, which the
Dockerfile sets. Vercel does its own tracing, so the flag stays off there.

## Layout

```
src/
  lib/
    grammar.ts     grammar text -> Grammar; productive/reachable/left-recursion checks
    ll1.ts         FIRST, FOLLOW, parse table, conflicts, the table-driven parser
    feedback.ts    grading a student's answers against the analysis
    examples.ts    the grammars offered in the workbench picker
  app/
    api/analyze    POST a grammar, get the analysis and an optional parse trace
    api/grade      POST answers, get per-cell feedback
    workbench      the interactive page
  components/
    Workbench.tsx      state, fetching, and layout for the workbench
    ParseTableGrid.tsx the editable table
```

Both API routes run on the **edge runtime**: the analysis is pure computation
over a small input, so there is no cold start and nothing to leak.

## What changed from the original

The previous version was a create-react-app frontend, an Express server that
shelled out to Python, and a parallel set of PHP scripts that were the part
actually deployed at `cyclops.cse.iitk.ac.in`. Rewriting it fixed the
following, each of which was a real defect rather than a style preference.

**The server ignored its own arguments.** `server/nodeHandle.py` opened with

```python
grammar = 2 #sys.argv[1]
task = 1 #sys.argv[2]
```

so every request returned the same hardcoded grammar regardless of what the
user selected. The endpoint that called it passed `grammarSelected` and
`taskSelected` into a `spawn()` that discarded them.

**The parse-table generator could not run anywhere.** `generate_parsetable.py`
loaded grammars with `imp.load_source(inputFile, '/cyclopsWeb/inputs/' + ...)`
— an absolute path on a machine that no longer exists, via a module removed
from Python in 3.12.

**Right-hand sides were strings joined by `_`.** The old engine represented
`A -> a A b` as `"a_A_b"` and recovered the symbols by splitting on `_`, so no
grammar symbol could contain an underscore, and `FIRST` of a suffix was
computed by slicing the *string* rather than walking the symbols.

**FIRST and FOLLOW recursed without a base case.** They were mutually recursive
functions under `sys.setrecursionlimit(80)`; any grammar with a cycle among
nullable non-terminals overflowed the stack. Both are now least fixed points —
iterate until nothing changes — which terminates on every grammar.

**Feedback was eight digits.** The old response was a string like
`"0,0,0,0,0,0,0,0"`, one flag per rule, with no indication of which cell was
wrong. Feedback now names the cell, shows submitted against expected, and
quotes the rule that governs it.

**Submissions were written to the local filesystem.** `fs.writeFile('./submissions/…')`
does not work on any serverless host, and the read path did
`readdirSync("./submissions/").filter(fn => fn.startsWith(passcode))` with an
unvalidated passcode — a path-traversal risk. The current app has no
submission storage; see below.

**Everything ran with permissive CORS and no security headers.** The Express
app set `Access-Control-Allow-Origin: *` on POST endpoints. The app now ships a
strict CSP, `X-Frame-Options: DENY`, and the rest via `next.config.mjs`.

### Why TypeScript rather than Python

The LL(1) engine is a few hundred lines of pure algorithm with no library
dependency. Keeping it in the same language as the UI means one runtime on
Vercel, no Python cold start on the request path, and the same `Grammar` and
`Ll1Analysis` types on both sides of the API — the client renders exactly the
structure the server validated. The Java-to-Python port requested for this
repository applies to `NNRepair/CombinationCode`, which is genuinely numerical
work; see [`apps/nnrepair`](../nnrepair).

### Authentication and submissions

The original used Firebase auth with the config committed to
`src/config/fire.js`, plus passcode-gated coursework submission. Neither is
present here: the workbench needs no account, and grading happens per-request.

If coursework submission is wanted back, it needs a real datastore rather than
the filesystem — Vercel Postgres or Firestore — and the passcode must be
validated before it reaches a path.

Firebase web config values are public by design: they identify the project,
they do not authorise anything, and access is controlled by Firestore security
rules rather than by hiding them. So `NEXT_PUBLIC_FIREBASE_API_KEY`,
`…_AUTH_DOMAIN`, `…_PROJECT_ID`, `…_STORAGE_BUCKET`,
`…_MESSAGING_SENDER_ID` and `…_APP_ID` are the right shape if it comes back.
A service-account credential is not — that one stays server-side, with no
`NEXT_PUBLIC_` prefix. The app reads none of these today.

## Tests

`src/lib/__tests__/ll1.test.ts` checks the engine against the reference
grammar the artifact shipped in `input_specs.py`, including the FIRST/FOLLOW
sets and the parse table it hardcoded, and the accept/reject strings it listed.
