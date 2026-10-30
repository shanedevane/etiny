# etiny

Elevation models for personal goals and pitch decks. Scan any document
against distilled rulebooks — deterministically, entirely on your machine.
No accounts, no API.

An etiny bundle is **runnable and readable**:

- **Runnable** — `etiny scan notes.md` matches a document against the
  bundle's detectors and elevation corpus with the same maths as the
  [webapp](https://shanedevane.com/etiny/).
- **Readable** — every bundle ships plain JSONL (rules, detectors, advice)
  plus `AGENTS.md` and an installable Claude skill, so frontier models can
  reason over the corpus directly.

## Status

Pre-beta. The CLI command set is specified in
[docs/cli-commands.md](docs/cli-commands.md) — pull-based bundle management
(`etiny pull goals`), versioned model store, deterministic scanning.
Bundles download from the etiny registry on demand; installing the CLI
downloads nothing.

## Copyright

Bundles contain derived data only — no source texts, no verbatim passages.
Works that remain in copyright are deliberately excluded. See the
DISCLAIMER inside any bundle.
