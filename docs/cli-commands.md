# etiny CLI — command specification

**30 Oct 2026.** Spec-first: this file defines the commands; implementation follows it. Inspiration: `docker` (pull/run/manage local artifacts) and `huggingface-cli` (download + cache model repos) — but neither is copied wholesale. The CLI is a **thin Python tool** (pip/pipx-installable); bundles are **data+weights artifacts** pulled on demand from a registry. Installing the CLI downloads nothing.

---

## 1 · Concepts

| Concept | Meaning | Analogy |
|---|---|---|
| **model** | One vertical's bundle (elevators, elevations, detectors, advice, ONNX weights) — e.g. `goals`, `pitch-decks`, later `career-advice`, `fund-docs`… | docker *image* |
| **version** | Dated, immutable bundle build (`2026-10-29`); `latest` is a moving pointer | image *tag* |
| **store** | Local cache dir with all downloaded models/versions | docker *image store* |
| **registry** | One `registry.json` index + bundle zips, self-hosted (GitHub Releases assets and/or the existing enanoPacks S3 bucket) | docker *registry* |

**Store layout** (docker/hf-style, content-addressed by version):

```
~/.etiny/                        # ETINY_HOME overrides
  registry.json                  # cached index (refreshed on list/pull/update)
  models/
    goals/
      2026-10-29/                # extracted bundle: data/ models/ tools/ VERSION.json
      2026-11-02/
      latest -> 2026-11-02       # symlink (or pointer file on Windows)
    pitch-decks/
      latest -> ...
  cache/                         # scan artifacts (optional, prunable)
```

**Registry question (HF API vs self-host):** use a **self-hosted `registry.json`** — one JSON listing every model, version, byte size, sha256, and URL. Preferred home: the **existing enanoPacks S3 bucket** (zips already live there; one PUT updates the index; no rate limits; per-object Cache-Control ~5 min; CORS already allows GET). The GitHub repo keeps a human-readable copy; each asset carries an optional `mirrorUrl` (GitHub Release asset) for resilience. The HuggingFace Hub remains an *optional later* mirror for the raw ONNX weights only, not the primary registry.

---

## 1b · `run` vs `scan` — the ollama mapping, and two kinds of consumer

Ollama's mental model maps 1:1, with `scan` playing the role of `run`:

| ollama | etiny | What it actually is |
|---|---|---|
| `ollama pull llama3` | `etiny pull goals` | fetch bundle into the local store |
| `ollama run llama3 "hi"` | `etiny scan notes.md` | **use the pulled model** — compares a document against the bundle's detectors + corpus (the same maths as the webapp), prints findings, meaningful exit codes |
| `ollama list` / `rm` | `etiny list` / `rm` | store management |

The command stays `scan` (it says what it does); `run` is a cheap alias if ollama muscle-memory ever matters.

**The artifact has two consumers, and both are first-class:**

1. **Deterministic run** — `etiny scan`: programmatic, reproducible, exit codes, `--json`. The bundle is *runnable*.
2. **Agentic run** — a frontier model (Claude, etc.) consuming the bundle directly as plain data: reading `elevations.jsonl` / `advice.jsonl`, reasoning over them, shelling out to `scan` for the deterministic pass. This is why `AGENTS.md` and `skills/goals-scan/SKILL.md` ship inside the zip. The bundle is also *readable*.

Unlike an ollama model (which can only be run), an etiny bundle is **runnable and readable** — that line belongs verbatim in the repo README.

---

## 2 · Command reference

### Lifecycle

| Command | Behaviour |
|---|---|
| `etiny init` | Create store, fetch registry index. (Also runs implicitly on first use.) |
| `etiny doctor` | Diagnostics: python version, onnxruntime present (semantic on/off/auto), disk free, store path, registry reachable, `latest` consistency. Green/red lines. |

### Downloading & managing models (the docker-like core)

| Command | Behaviour |
|---|---|
| `etiny pull <model>[@version]` | Download + verify (sha256 vs registry) + extract into the store. No version ⇒ resolve `latest`. `etiny pull goals`, `etiny pull goals@2026-10-29`. |
| `etiny pull --all` | Pull every model at `latest`. |
| `etiny list` | Local models: name, resolved version, size on disk, path. |
| `etiny list --remote` | Registry models: every version, size, date; marks which are local/stale. |
| `etiny update` | Check registry for newer versions of local models; print what's available. |
| `etiny update [model]` / `etiny upgrade [model]` | Fetch newer version and re-point `latest` (old version kept). |
| `etiny info <model>[@version]` | Full manifest: version, counts (elevators/detectors/patterns/elevations/advice), sha256, disk path, provenance from `VERSION.json`. |
| `etiny rm <model>[@version]` | Remove one version (`rm goals@2026-10-29`); refuses to remove the version `latest` points at unless `--force`. |
| `etiny prune` | Remove all non-`latest` local versions. `--all` also removes everything (empty store). |
| `etiny verify [model]` | Re-run the bundle's own checksum manifest against the store copy. |

### Using models

| Command | Behaviour |
|---|---|
| `etiny scan <file|->` | **The `run` command.** Scan a document. `--model goals` (default: the single local model, or prompt/auto-pull with `--yes` if none). Flags as today: `--elevator`, `--status`, `--semantic on/off/auto` (auto = on when onnxruntime importable), `--limit`, `--all`, `--json`. Exit codes meaningful. **Auto-pull**: if the requested model isn't local, offer to `pull` it first (never silent — size is shown first). |
| `etiny elevators [--model]` | List elevators (books) with per-elevator counts. |
| `etiny elevations [--elevator <id>] [--search <text>] [--limit N]` | Query the elevation corpus. |

### Global

| Flag | Behaviour |
|---|---|
| `etiny --version` | CLI version (semver from the package), plus registry index date. |
| `--model` anywhere | Model selector; accepts `name` (latest) or `name@version`. |
| `--json` anywhere | Machine-readable output (CI-friendly). |
| `ETINY_HOME` | Store location override. |
| `--no-color` / not-a-tty | Plain output. |

---

## 3 · Non-goals (explicitly not docker)

- No daemon, no containers, no build step.
- No registry *push* from the CLI — publishing stays server-side (the existing `sync_all` / upload scripts).
- No accounts or auth: everything public-read.
- No telemetry of any kind ("no accounts, no API" stays true locally too).

## 4 · Command set summary (cheat-sheet)

```
etiny pull goals              # fetch latest goals bundle
etiny pull goals@2026-10-29   # fetch a pinned version
etiny list [--remote]         # what do I have / what exists
etiny update [goals]          # check / fetch newer
etiny info goals              # manifest + counts + path
etiny scan notes.md           # use it (auto-pulls if missing, asks first)
etiny scan - --json           # stdin, machine output
etiny elevators / elevations  # explore the corpus
etiny verify / doctor         # integrity / environment
etiny rm goals@old · prune    # disk management
```

## 5 · Open decisions (founder call)

1. **Registry home**: GitHub Releases assets vs existing S3 bucket vs both (registry.json can list either; start with what exists — S3 — add GitHub as mirror).
2. **Model naming**: `goals` vs `personal-goals` vs `etiny-goals` (zip file names are `enano-…` today; the registry index can map clean names → existing artifacts without rebuilding them).
3. **Semantic matching in the CLI**: ship `--semantic auto` against the bundled q8 ONNX via pip `onnxruntime` (optional extra: `pip install etiny[semantic]`), keeping the stdlib-only core.
4. **20-model future**: the registry index scales (one entry per model); `pull` stays per-model so users never download more than they use.
