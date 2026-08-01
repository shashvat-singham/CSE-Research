# CSE-Research

Two research artifacts from the compilers and program-analysis group at IIT
Kanpur, each with a deployed application built on top of it.

| | What it is | App | Host |
|---|---|---|---|
| **[Cyclops](apps/cyclops)** | LL(1) parser teaching tool | Next.js | Vercel |
| **[NNRepair](apps/nnrepair)** | Constraint-based repair of NN classifiers | Streamlit | Streamlit Community Cloud |

## Layout

```
apps/
  cyclops/        Next.js app — the LL(1) engine and workbench
  nnrepair/       Streamlit app — results explorer + the Python port
Cyclops/          original artifact (CRA + Express + PHP + Python)
NNRepair/         original artifact (Java, constraints, Z3 solutions, results)
```

The originals are left in place. The apps under `apps/` are what deploys.

## Why two different hosts

They are different kinds of thing, and forcing both onto one host would make
one of them worse.

Cyclops is an interactive app: routing, an editable parse-table grid, per-cell
validation. That is a web front end, and Streamlit cannot express the grid.

NNRepair is data exploration over 345 result CSVs plus numerical code someone
might want to actually run. That is Streamlit's core competence, and it
tolerates compute and data sizes that Vercel's serverless limits do not.

## Getting started

```bash
# Cyclops
cd apps/cyclops && npm ci && npm run dev

# NNRepair
cd apps/nnrepair && pip install -r requirements.txt && streamlit run streamlit_app.py
```

## Repository size

`.git` is ~457 MB and the working tree ~1 GB, almost entirely
`NNRepair/NN-Code`: ten MNIST/CIFAR dataset files of 94 MB each, plus extracted
weight dumps. `Cyclops/node_modules` was also committed — 42,237 files.

`Cyclops/node_modules` has been untracked — it is reinstallable and never
belonged in version control. **`NNRepair/NN-Code` is still tracked**: it is
research data, and dropping it would deny it to anyone cloning the repository.
`.gitignore` now covers both, so neither grows further.

Shrinking `.git` itself means rewriting history with `git filter-repo`, which
changes every commit hash and needs a force-push. Worth doing, but that is a
call for whoever owns the remote — not a side effect of this work.

Neither deployment includes the large data. See
[`apps/nnrepair/README.md`](apps/nnrepair/README.md) for which pages need a
local checkout.

## Notes on the ports

Both apps rewrote code rather than wrapping it, and both READMEs record what
changed and why:

- [Cyclops](apps/cyclops/README.md#what-changed-from-the-original) — the old
  server ignored its own arguments and returned one hardcoded grammar for every
  request; the parse-table generator loaded grammars from an absolute path on a
  machine that no longer exists; FIRST/FOLLOW recursed with no base case under
  a recursion limit of 80.
- [NNRepair](apps/nnrepair/README.md#the-python-port) — the Java is ported to
  NumPy and verified against literal transcriptions of its own loops to 1.6e-14.
  It also documents a **~1.5 point discrepancy** between re-running the pipeline
  and the shipped result CSVs, which traces to the committed weights/datasets
  rather than to the port.
