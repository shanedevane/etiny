# etiny: Explorable tiny models for your second brain

Pull whole libraries of distilled book advice and scan your own documents
against them, locally. Like ollama, but the models are libraries.

- **Pull models, not just install one.** `etiny pull goals` fetches a
  versioned, sha-verified bundle from the registry. More models (pitch
  decks, career advice, and more) land in the same store as they ship.
- **Scan any document.** Point it at a file, or run it bare in a folder and
  every `.md` gets checked.
- **Nothing generated, nothing uploaded.** Regex detectors plus a small
  embedding model decide what your document trips. Every finding quotes
  your own words back as evidence.
- **No accounts, no API, no telemetry.**

<!-- Screenshots: drop PNGs into docs/screens/ and uncomment
<p align="center">
  <a href="docs/screens/pull.png"><img src="docs/screens/pull.png" width="32%"></a>
  <a href="docs/screens/scan.png"><img src="docs/screens/scan.png" width="32%"></a>
  <a href="docs/screens/list.png"><img src="docs/screens/list.png" width="32%"></a>
</p>
-->

## Usage

```bash
etiny scan notes.md          # scan one document [model: personal goals, default]
etiny scan                   # scan every .md in the current folder
etiny list --remote          # every model you can pull
etiny pull goals             # fetch the personal-goals bundle (~36 MB, sha-verified)
etiny pull pitch-decks       # a second model, same store
```

Running bare `etiny` pulls the default model (personal goals) and shows
the shortest path to a first scan.

## Install

```bash
pipx install etiny
```

Or `pip install etiny`, [on PyPI](https://pypi.org/project/etiny/).
Installing downloads nothing; bundles arrive on demand. For the optional
neural matching: `pipx install "etiny[semantic]"`.

## Quickstart

```bash
etiny scan notes.md     # scan a document (regex plus the optional neural pass)
etiny scan - --json     # stdin, machine-readable output
etiny elevators         # list the source works with their counts
etiny elevations --search "habit"   # query the rule corpus
etiny update            # check for newer bundles
etiny doctor            # environment and store diagnostics
```

`scan` is the `run` of this CLI: `pull` fetches a model, `scan` uses it.
If the model is not local yet, `scan` offers to pull it first. Never
silently.

## Why it's different

An etiny bundle is runnable and readable:

- **Runnable.** `etiny scan` matches your document against the bundle's
  rules and detectors with the same maths as the
  [webapp](https://shanedevane.com/etiny/).
- **Readable.** Every bundle ships plain JSONL data plus `AGENTS.md` and an
  installable Claude skill, so AI agents can reason over the corpus
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

- The registry is one `registry.json` on S3: every model, version, byte
  size, sha256, and URL. Each asset carries a mirror URL for resilience.
- Bundles are immutable per version; `latest` is a moving pointer.
- No telemetry, no account.
- Neural matching (`--semantic auto`) activates automatically when
  `onnxruntime` is installed. Without it the regex pass stands alone and
  says so.

## What's in a bundle

The current goals bundle (`etiny info goals`):

| | |
|---|---|
| Source works | 21 public-domain books (Meditations, As a Man Thinketh, Self-Help, and more) |
| Detectors and rules | 31 detectors, 6,292 patterns, 15,833 rules |
| Advice | 391 entries (gap actions plus self-check questions) |
| Neural embedder | 33M-param q8 ONNX, runs offline |

Also inside: dependency-free Python tools, `AGENTS.md`, a ready-to-install
Claude Code skill, and `VERSION.json` with the sha256 of every file
(`etiny verify` re-checks them).

## Copyright

Bundles contain derived data only. No source texts, no verbatim passages.
Works that remain in copyright are deliberately excluded. Every bundle
ships a `DISCLAIMER.md` with attribution and usage terms; read it before
redistributing.

## Status

Pre-beta, `0.1.0` on PyPI. Spec-first development: the command reference in
[docs/cli-commands.md](docs/cli-commands.md) is the source of truth the
implementation follows.
