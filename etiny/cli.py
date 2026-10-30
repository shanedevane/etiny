"""The etiny CLI: pull-based bundle management plus a front door to the
bundle's own deterministic scan tools."""

from __future__ import annotations

import argparse
import json as jsonlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

from . import __version__
from . import registry as reg
from . import store


def _parse_selector(selector: str) -> tuple[str, str | None]:
    model, _, version = selector.partition("@")
    return model.strip(), (version.strip() or None) if version else None


def _require_bundle(selector: str, auto_pull: bool) -> Path:
    model, version = _parse_selector(selector)
    path = store.resolve_version(model, version)
    if path:
        return path
    entry = reg.resolve_entry(reg.fetch_registry(refresh=True), model, version)
    size_mb = round(entry["bytes"] / 1e6, 1)
    if not auto_pull:
        print(f"{model} is not installed locally. Run: etiny pull {model}  ({size_mb} MB)")
        raise SystemExit(2)
    prompt = f"{model}@{entry['version']} is not installed — download it now ({size_mb} MB)? [y/N] "
    if sys.stdin.isatty() and input(prompt).strip().lower() not in ("y", "yes"):
        raise SystemExit(2)
    print(f"pulling {model}@{entry['version']} …")
    _pull(model, entry)
    path = store.resolve_version(model, version)
    if not path:
        raise SystemExit(f"pull finished but {selector} still not resolvable")
    return path


def _run_tool(bundle: Path, tool: str, forward: list[str]) -> int:
    tool_path = bundle / "tools" / f"{tool}.py"
    if not tool_path.is_file():
        runnable = (bundle / "tools" / "scan.py").is_file()
        hint = "" if runnable else " (this bundle ships no scanner — weights/corpus only)"
        raise SystemExit(f"tool '{tool}' not found in {bundle.name}{hint}")
    return subprocess.call([sys.executable, str(tool_path), *forward], cwd=str(bundle))


def _pull(model: str, entry: dict) -> None:
    archive = reg.download_archive(
        entry.get("url") or entry["mirrorUrl"],
        entry.get("bytes", 0),
        entry["sha256"],
        store.store_root() / "archives",
    )
    target = store.install_bundle(model, entry["version"], archive)
    print(f"installed {model}@{entry['version']} -> {target}")


# ------------------------------------------------------------- subcommands


def cmd_pull(args: argparse.Namespace) -> int:
    registry = reg.fetch_registry(refresh=True)
    selectors = args.selectors or []
    if args.all:
        selectors = sorted(reg.registry_models(registry))
    if not selectors:
        raise SystemExit("nothing to pull: give a model or --all")
    for selector in selectors:
        model, version = _parse_selector(selector)
        entry = reg.resolve_entry(registry, model, version)
        if store.model_dir(model, entry["version"]).is_dir() and not args.force:
            print(f"{model}@{entry['version']} already installed (use --force to re-fetch)")
            continue
        _pull(model, entry)
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    rows = []
    if args.remote:
        registry = reg.fetch_registry(refresh=True)
        local = {(m.model, m.version) for m in store.local_models()}
        for name in sorted(reg.registry_models(registry)):
            entry = reg.registry_models(registry)[name]
            for version in sorted(entry.get("versions", {}), reverse=True):
                meta = entry["versions"][version]
                state = "installed" if (name, version) in local else "available"
                if version == entry.get("latest"):
                    state += " · latest"
                rows.append((name, version, state, round(meta.get("bytes", 0) / 1e6, 1)))
    else:
        for m in store.local_models():
            state = "latest" if store.read_latest(m.model) == m.version else "old"
            rows.append((m.model, m.version, state, round(m.bytes / 1e6, 1)))
    if not rows:
        print("nothing installed — try: etiny pull goals  (or etiny list --remote)")
        return 0
    if args.json:
        print(jsonlib.dumps(
            [{"model": r[0], "version": r[1], "state": r[2], "mb": r[3]} for r in rows], indent=2
        ))
    else:
        print(f"{'MODEL':<16} {'VERSION':<12} {'STATE':<18} SIZE")
        for name, version, state, mb in rows:
            print(f"{name:<16} {version:<12} {state:<18} {mb} MB")
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    registry = reg.fetch_registry(refresh=True)
    targets = [args.model] if args.model else sorted({m.model for m in store.local_models()})
    changed = False
    for model in targets:
        entry = reg.registry_models(registry).get(model)
        if not entry:
            print(f"{model}: not in registry")
            continue
        latest = entry.get("latest")
        local_latest = store.read_latest(model)
        if latest == local_latest:
            print(f"{model}: up to date ({latest})")
            continue
        changed = True
        print(f"{model}: {local_latest or 'none'} -> {latest}")
        if args.upgrade:
            _pull(model, reg.resolve_entry(registry, model, latest))
    return 0 if (changed or not targets) else 0


def cmd_info(args: argparse.Namespace) -> int:
    model, version = _parse_selector(args.model)
    path = store.resolve_version(model, version)
    if not path:
        raise SystemExit(f"{args.model} is not installed (try: etiny pull {model})")
    m = next((lm for lm in store.local_models() if lm.path == path), None)
    doc = m.version_doc if m else {}
    info = {
        "model": model,
        "version": doc.get("built_at") or path.name,
        "latest_local": store.read_latest(model),
        "path": str(path),
        "disk_mb": round((m.bytes if m else 0) / 1e6, 1),
        "counts": doc.get("counts", {}),
        "runnable": (path / "tools" / "scan.py").is_file(),
    }
    if args.json:
        print(jsonlib.dumps(info, indent=2))
    else:
        for key, value in info.items():
            print(f"{key:>12}: {value}")
    return 0


def cmd_rm(args: argparse.Namespace) -> int:
    model, version = _parse_selector(args.model)
    if not version:
        versions = [lm.version for lm in store.local_models() if lm.model == model]
        if len(versions) == 1:
            version = versions[0]
        elif versions:
            raise SystemExit(f"multiple versions installed: {versions} — pick {model}@<version>")
    if store.remove_version(model, version, force=args.force):
        print(f"removed {model}@{version}")
        return 0
    raise SystemExit(f"{model}@{version} is not installed")


def cmd_prune(args: argparse.Namespace) -> int:
    removed = 0
    for m in store.local_models():
        if store.read_latest(m.model) == m.version:
            continue
        store.remove_version(m.model, m.version, force=True)
        print(f"removed {m.model}@{m.version}")
        removed += 1
    if args.all:
        shutil.rmtree(store.models_root(), ignore_errors=True)
        print("removed all models (store emptied)")
        removed += 1
    if not removed:
        print("nothing to prune")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    bundle = _require_bundle(args.model, auto_pull=False) if not args.model_off else None
    if bundle:
        return _run_tool(bundle, "verify", list(args.forward))
    failed = False
    for m in store.local_models():
        code = _run_tool(m.path, "verify", [])
        failed = failed or code != 0
    return 1 if failed else 0


def cmd_scan(args: argparse.Namespace) -> int:
    bundle = _require_bundle(args.model, auto_pull=not args.no_pull)
    return _run_tool(bundle, "scan", list(args.forward))


def cmd_elevators(args: argparse.Namespace) -> int:
    bundle = _require_bundle(args.model, auto_pull=False)
    return _run_tool(bundle, "elevators", list(args.forward))


def cmd_elevations(args: argparse.Namespace) -> int:
    bundle = _require_bundle(args.model, auto_pull=False)
    return _run_tool(bundle, "elevations", list(args.forward))


def cmd_doctor(_args: argparse.Namespace) -> int:
    ok = True

    def line(label: str, detail: str, good: bool) -> None:
        nonlocal ok
        ok = ok and good
        print(f"  [{'ok' if good else 'FAIL'}] {label:<20} {detail}")

    import importlib.util

    line("python", sys.version.split()[0], sys.version_info >= (3, 9))
    root = store.store_root()
    try:
        root.mkdir(parents=True, exist_ok=True)
        probe = root / ".write-test"
        probe.write_text("x")
        probe.unlink()
        line("store", str(root), True)
    except OSError as exc:
        line("store", f"{root}: {exc}", False)
    line("disk free", f"{shutil.disk_usage(root).free / 1e9:.1f} GB", shutil.disk_usage(root).free > 500e6)
    try:
        registry = reg.fetch_registry(refresh=True)
        line("registry", f"{len(reg.registry_models(registry))} model(s) indexed", True)
    except SystemExit as exc:
        line("registry", str(exc), False)
    line("onnxruntime", "installed (semantic on)" if importlib.util.find_spec("onnxruntime") else "absent (regex-only fallback)", True)
    for m in store.local_models():
        doc = m.version_doc
        line(
            f"{m.model}@{m.version}",
            f"verified manifest, runnable={m.runnable}" if doc else "VERSION.json unreadable",
            bool(doc),
        )
    print("doctor:", "healthy" if ok else "problems found")
    return 0 if ok else 1


# ------------------------------------------------------------------- parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="etiny",
        description="Elevation models on your machine: pull versioned bundles, scan documents deterministically.",
    )
    parser.add_argument("--version", action="version", version=f"etiny {__version__}")
    parser.add_argument("--no-color", action="store_true", help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("pull", help="download and install a model bundle")
    p.add_argument("selectors", nargs="*", help="model[@version] (default version: latest)")
    p.add_argument("--all", action="store_true", help="pull every published model")
    p.add_argument("--force", action="store_true", help="re-fetch even if installed")
    p.set_defaults(func=cmd_pull)

    p = sub.add_parser("list", help="list local (or --remote) models")
    p.add_argument("--remote", action="store_true", help="list registry versions, mark local/stale")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("update", help="check for newer versions of local models")
    p.add_argument("model", nargs="?", help="limit to one model")
    p.add_argument("--upgrade", action="store_true", help="also download and re-point latest")
    p.set_defaults(func=cmd_update)

    p = sub.add_parser("info", help="manifest + counts + path for an installed model")
    p.add_argument("model", help="model[@version]")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_info)

    p = sub.add_parser("rm", help="remove an installed version")
    p.add_argument("model", help="model[@version]")
    p.add_argument("--force", action="store_true", help="remove even if latest points at it")
    p.set_defaults(func=cmd_rm)

    p = sub.add_parser("prune", help="remove non-latest local versions")
    p.add_argument("--all", action="store_true", help="remove every model (empty the store)")
    p.set_defaults(func=cmd_prune)

    p = sub.add_parser("verify", help="verify bundle checksums against VERSION.json")
    p.add_argument("model", nargs="?", help="model[@version]; omit to verify everything local")
    p.add_argument("forward", nargs=argparse.REMAINDER, help=argparse.SUPPRESS)
    p.set_defaults(func=cmd_verify, model_off=False)

    p = sub.add_parser("scan", help="scan a document against a bundle (the run command)")
    p.add_argument("--model", default="goals", help="model[@version] (default: goals)")
    p.add_argument("--no-pull", action="store_true", help="never auto-pull a missing model")
    p.add_argument("forward", nargs=argparse.REMAINDER, help="flags passed to the bundle's scan tool (--json, --elevator, --status, --semantic, file or '-')")
    p.set_defaults(func=cmd_scan)

    p = sub.add_parser("elevators", help="list the bundle's elevators (books)")
    p.add_argument("--model", default="goals")
    p.add_argument("forward", nargs=argparse.REMAINDER, help=argparse.SUPPRESS)
    p.set_defaults(func=cmd_elevators)

    p = sub.add_parser("elevations", help="query the elevation corpus")
    p.add_argument("--model", default="goals")
    p.add_argument("forward", nargs=argparse.REMAINDER, help=argparse.SUPPRESS)
    p.set_defaults(func=cmd_elevations)

    p = sub.add_parser("doctor", help="environment + store diagnostics")
    p.set_defaults(func=cmd_doctor)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    forward = getattr(args, "forward", None)
    if forward and forward[:1] == ["--"]:
        args.forward = forward[1:]
    return args.func(args) or 0


if __name__ == "__main__":
    raise SystemExit(main())
