# etiny

Scan your goals, plans, and pitch decks against the distilled advice of
classic self-improvement works — deterministically, entirely on your
machine. No accounts, no API.

## Usage

```bash
etiny scan notes.md
```

## Install

```bash
pipx install etiny
```

(Or `pip install etiny` — [on PyPI](https://pypi.org/project/etiny/).
Installing downloads nothing — bundles arrive on demand. For the optional
neural matching: `pipx install "etiny[semantic]"`.)

## Quickstart

```bash
etiny pull goals        # fetch the personal-goals bundle (~36 MB, sha-verified)
etiny scan notes.md     # scan a document (regex + optional neural pass)
etiny scan - --json     # stdin, machine-readable output
etiny elevators         # list the source works with their counts
etiny elevations --search "habit"   # query the rule corpus
etiny list --remote     # what models exist; what you have
etiny update            # check for newer bundles
etiny doctor            # environment + store diagnostics
```

`scan` is the `run` of this CLI: `pull` fetches a model, `scan` uses it.
If the model isn't local yet, `scan` offers to pull it first — never
silently.

## Why it's different

An etiny bundle is **runnable and readable**:

- **Runnable** — `etiny scan` matches your document against the bundle's
  rules and detectors with the same maths as the
  [webapp](https://shanedevane.com/etiny/).
- **Readable** — every bundle ships plain JSONL data plus `AGENTS.md` and
  an installable Claude skill, so AI agents can reason over the corpus
  directly.

Both passes are deterministic: the same text always produces the same
matches, and nothing is generated.

## How it works

```
PyPI / git          etiny CLI (tiny, code only)         ~/.etiny
──────────          ───────────────────────────         ─────────────────────────
pipx install  ──▶   pull ── reads ──▶ registry.json ─┐  models/goals/2026-10-29/
                    (S3, versioned, sha256-pinned)  ───▶  data/  models/  tools/
                    scan ─ runs the bundle's own       latest -> 2026-10-29
                    deterministic tools against it
```

- The **registry** is one `registry.json` on S3: every model, version, byte
  size, sha256, and URL. Each asset carries a mirror URL for resilience.
- **Bundles are immutable per version**; `latest` is a moving pointer.
- No telemetry, no account.
- Neural matching (`--semantic auto`) activates automatically when
  `onnxruntime` is installed; without it the regex pass stands alone and
  says so.

## What's in a bundle

The current goals bundle (`etiny info goals`):

| | |
|---|---|
| Source works | 21 public-domain classics (Meditations, As a Man Thinketh, Self-Help, …) |
| Detectors / rules | 31 detectors, 6,292 patterns, 15,833 rules |
| Advice | 391 entries (gap actions + self-check questions) |
| Neural embedder | 33M-param q8 ONNX, runs offline |

Also inside: dependency-free Python tools, `AGENTS.md`, a ready-to-install
Claude Code skill, `VERSION.json` with sha256 of every file (`etiny verify`
re-checks them).

## Copyright

Bundles contain derived data only — no source texts, no verbatim passages.
Works that remain in copyright are deliberately excluded. Every bundle
ships a `DISCLAIMER.md` with attribution and usage terms; read it before
redistributing.

## Status

Pre-beta, `0.1.0` on PyPI. Spec-first development: the command reference in
[docs/cli-commands.md](docs/cli-commands.md) is the source of truth the
implementation follows.
