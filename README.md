# CSE-Research

Two research artifacts from the compilers and program-analysis group at IIT
Kanpur, each with a deployed application built on top of it.

| | What it is | Live | Stack |
|---|---|---|---|
| **[Cyclops](apps/cyclops)** | LL(1) grammar analysis and parse-table workbench | **https://cyclops-delta.vercel.app** | Next.js on Vercel |
| **[NNRepair](apps/nnrepair)** | Constraint-based repair of NN classifiers | _pending_ | Streamlit Community Cloud |

NNRepair deploys from **[shashvat-singham/nnrepair-app](https://github.com/shashvat-singham/nnrepair-app)**,
a split-out copy of `apps/nnrepair`, so the build does not clone the 954 MB of
research data this repository carries.

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

### Docker

Both apps together:

```bash
docker compose up --build
```

| | URL |
|---|---|
| Cyclops | http://localhost:3000 |
| NNRepair | http://localhost:8501 |

Or one at a time:

```bash
docker build -t cyclops ./apps/cyclops   && docker run --rm -p 3000:3000 cyclops
docker build -t nnrepair ./apps/nnrepair && docker run --rm -p 8501:8501 nnrepair
```

Both images are multi-stage, run as a non-root user, and carry a healthcheck
that exercises the app rather than just the port. Cyclops builds Next's
standalone output, so the runtime image holds only the modules actually
imported; NNRepair installs into a virtualenv in the builder stage and copies
it forward, leaving no compilers or pip cache behind.

Compose bind-mounts `NNRepair/Z3Solutions` and `NNRepair/NN-Code` read-only,
which lights up the two NNRepair pages that need them. They are far too large
to bake into an image, so `docker run` without the mounts gets an app that
explains their absence instead.

### Without Docker

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
