# etiny: Explorable tiny models for your second brain

28,000+ advice distilled from key books on the topics of personal goals, career advice and startup pitch decks and more to come. Each model comes with source attributes, excerpts, custom advice and cli tools to explore your own .md and .txt files.

**WEB DEMO**
https://www.shanedevane.com/etiny/

<p align="center">
  <a href="docs/screens/screen-1.png"><img src="docs/screens/screen-1.jpg" width="49%"></a>
  <a href="docs/screens/screen-2.png"><img src="docs/screens/screen-2.jpg" width="49%"></a>
</p>

## Install

```bash
pipx install etiny
```

| Model | Sources | Rules | Detectors | Advice | Pull |
|---|---|---|---|---|---|
| **personal-goals** (default) | 21 | 15,833 | 31 | 391 | 35.8 MB |
| **career-advice** | 5 | 5,026 | 142 | 1,877 | 25 MB |
| **pitch-decks** | 5 | 75 | 75 | 1,132 | 22.5 MB |


## Quickstart

```bash
etiny pull personal-goals         # fetch the personal-goals bundle (~36 MB, sha-verified)
etiny scan notes.md               # scan a document (regex plus the optional neural pass)
etiny scan                        # every .md in the current folder (stdin when piped)
etiny walk                        # every .md in every subfolder
etiny elevators                   # list the source works with their counts
etiny elevations "fear of failure"  # search the rule corpus — any word or phrase
etiny list                        # every model you can pull
etiny models                      # what's installed
etiny use pitch-decks             # switch the default model
etiny update                      # check for newer bundles
etiny upgrade                     # fetch newer bundles
etiny doctor                      # environment and store diagnostics
```

**Global Parameters**
Every command takes `--json`; there are no other flags to learn. Bare `etiny`
onboards: it pulls the default model and shows the shortest path to a first scan.
