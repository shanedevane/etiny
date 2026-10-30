# etiny

**Elevation models for personal goals and pitch decks.** Scan any document
against distilled rulebooks — deterministically, entirely on your machine.
No accounts, no API.

An etiny bundle is **runnable and readable**:

- **Runnable** — `etiny scan notes.md` matches your document against the
  bundle's detectors and elevation corpus with the same maths as the
  [webapp](https://shanedevane.com/etiny/).
- **Readable** — every bundle ships plain JSONL (rules, detectors, advice)
  plus `AGENTS.md` and an installable Claude skill, so frontier models can
  reason over the corpus directly. Unlike an ollama model, which can only
  be run, an etiny bundle is data an agent can think with.

Both passes are deterministic: the same text always produces the same
matches, and nothing is generated.

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
etiny scan notes.md     # scan a document (regex + optional semantic pass)
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

## The command set

Full reference: [docs/cli-commands.md](docs/cli-commands.md).

| Group | Commands |
|---|---|
| Lifecycle | `init` · `doctor` |
| Manage bundles | `pull` · `list [--remote]` · `update [--upgrade]` · `info` · `rm` · `prune` · `verify` |
| Use bundles | `scan` · `elevators` · `elevations` |

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
- The CLI keeps **no telemetry** and needs **no account**.
- Semantic matching (`--semantic auto`) upgrades itself automatically when
  `onnxruntime` is installed (`pipx install "etiny[semantic]"`); without it
  the regex pass stands alone and says so.

## What's in a bundle

The current goals bundle (`etiny info goals`):

| | |
|---|---|
| Elevators (source works) | 21 — public-domain classics (Meditations, As a Man Thinketh, Self-Help, …) |
| Regex detectors / patterns | 31 / 6,292 |
| Elevations (rules) | 15,833 |
| Advice entries | 391 (gap actions + self-check questions) |
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
