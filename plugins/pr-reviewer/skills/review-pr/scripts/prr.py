#!/usr/bin/env python3
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from prr.adapters import ADAPTERS, EXPERIMENTAL, AdapterError, PlatformUnavailable  # noqa: E402
from prr.core import git as gitcore  # noqa: E402
from prr.core import regression, repo_context  # noqa: E402
from prr.core.config import ConfigError, load_config  # noqa: E402
from prr.core.diff import parse_unified_diff  # noqa: E402
from prr.core.render import local_report  # noqa: E402
from prr.core.review import ReviewError, build_review  # noqa: E402
from prr.detect import detect  # noqa: E402

AGENT_REVIEW = "agent-review.json"


def _emit(payload: dict) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def _fail(message: str, **extra) -> int:
    _emit({"ok": False, "error": message, **extra})
    return 1


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-")[:60] or "review"


def _work_dir(root: Path, context: dict) -> Path:
    git_dir = Path(gitcore.git("rev-parse", "--absolute-git-dir", cwd=root).strip())
    key = f"{context['platform']}-{context['number']}" if context.get("number") else f"local-{_slug(context['source_branch'])}"
    path = git_dir / "pr-reviewer" / key
    path.mkdir(parents=True, exist_ok=True)
    return path


def collect(args) -> int:
    try:
        root = gitcore.repo_root(Path.cwd())
        config = load_config(root)
    except (gitcore.GitError, ConfigError) as error:
        return _fail(str(error))
    messages = []
    detection = detect(args.platform, config, args.ref, gitcore.remote_url("origin", root))
    platform = detection["platform"]
    if platform not in ADAPTERS:
        return _fail(f"Plateforme inconnue : {platform} (attendu : {' | '.join(ADAPTERS)}).")
    messages.append(f"Plateforme : {platform} — {detection['reason']}")
    if platform in EXPERIMENTAL:
        messages.append(f"L'adaptateur {platform} est expérimental (non validé sur une PR réelle).")

    base = args.base or config.get("base")
    adapter = ADAPTERS[platform](root, detection.get("host"))
    fallback = None
    try:
        adapter.check()
        context = adapter.fetch_pull_request(args.ref, base)
    except PlatformUnavailable as error:
        fallback = {"reason": str(error), "auth_command": error.auth_command}
    except AdapterError as error:
        fallback = {"reason": str(error), "auth_command": None}
    if fallback:
        hint = f" Pour t'authentifier : `{fallback['auth_command']}`." if fallback["auth_command"] else ""
        messages.append(f"Bascule en mode local : {fallback['reason']}{hint}")
        adapter = ADAPTERS["local"](root)
        try:
            context = adapter.fetch_pull_request(None, base)
        except AdapterError as error:
            return _fail(str(error), messages=messages)

    files = parse_unified_diff(context["diff"])
    if not files:
        return _fail("Le diff est vide : rien à relire.", messages=messages)
    tree = gitcore.list_files(context["head_sha"], root)
    context["changed_files"] = sorted(files)
    context["claude_md"] = repo_context.claude_md_files(tree, context["changed_files"])
    context["linters"] = repo_context.linters(tree)
    risks = regression.scan(files, context["base_sha"], root, config["regression_window_days"])
    context["regression_risks"] = risks
    context["config"] = config

    work_dir = _work_dir(root, context)
    (work_dir / "context.json").write_text(json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8")
    (work_dir / AGENT_REVIEW).unlink(missing_ok=True)
    _emit({
        "ok": True,
        "platform": context["platform"],
        "fallback": fallback,
        "messages": messages,
        "work_dir": str(work_dir),
        "context_file": str(work_dir / "context.json"),
        "agent_review_file": str(work_dir / AGENT_REVIEW),
        "pr": {k: context.get(k) for k in ("url", "number", "title", "source_branch", "target_branch", "head_sha")},
        "changed_files": len(files),
        "claude_md": context["claude_md"],
        "linters": context["linters"],
        "linked_items": [item["id"] for item in context["linked_items"]],
        "regression_risks": len(risks),
    })
    return 0


def _write_reports(root: Path, context: dict, review: dict, payloads: list | None) -> dict:
    reports = root / "reviews"
    reports.mkdir(exist_ok=True)
    name = f"pr-{context['number']}" if context.get("number") else _slug(context["source_branch"])
    stem = reports / f"{name}-{datetime.now().strftime('%Y-%m-%dT%Hh%M%S')}"
    markdown = local_report(review, context)
    paths = {"markdown": str(stem.with_suffix(".md")), "json": str(stem.with_suffix(".json"))}
    Path(paths["markdown"]).write_text(markdown, encoding="utf-8")
    Path(paths["json"]).write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    if payloads is not None:
        paths["payload"] = str(stem) + "-payload.json"
        Path(paths["payload"]).write_text(json.dumps(payloads, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"files": paths, "markdown": markdown}


def publish(args) -> int:
    work_dir = Path(args.work_dir)
    try:
        context = json.loads((work_dir / "context.json").read_text(encoding="utf-8"))
        raw = json.loads((work_dir / AGENT_REVIEW).read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        return _fail(f"Fichier manquant : {error.filename}")
    except json.JSONDecodeError as error:
        return _fail(f"{AGENT_REVIEW} n'est pas un JSON valide : {error}")
    root = gitcore.repo_root(Path.cwd())
    adapter = ADAPTERS[context["platform"]](root, context.get("host"))
    messages = []
    try:
        existing = adapter.list_existing_comments(context)
    except AdapterError as error:
        return _fail(f"Lecture des commentaires existants impossible : {error}")
    max_inline = args.max if args.max is not None else context["config"]["max_inline_comments"]
    try:
        review = build_review(raw, parse_unified_diff(context["diff"]),
                              regression.to_comments(context["regression_risks"]), context["regression_risks"],
                              {c["fingerprint"] for c in existing["comments"]}, max_inline)
    except ReviewError as error:
        return _fail(str(error))
    (work_dir / "review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")

    if context["platform"] == "local" or args.dry_run:
        payloads = None
        if args.dry_run and context["platform"] != "local":
            payloads = adapter.build_payloads(review, context, existing, args.request_changes)
        report = _write_reports(root, context, review, payloads)
        _emit({"ok": True, "mode": "dry-run" if args.dry_run else "local", "verdict": review["verdict"],
               "inline": len(review["comments"]), "counts": review["summary"]["counts"],
               "files": report["files"], "payloads": payloads, "messages": messages})
        return 0

    try:
        result = adapter.post_review(review, context, existing, args.request_changes, dry_run=False)
    except AdapterError as error:
        report = _write_reports(root, context, review, None)
        return _fail(f"Publication impossible : {error}. Rapport local écrit à la place.", files=report["files"])
    warnings = [r["warning"] for r in result["results"] if r.get("warning")]
    _emit({"ok": True, "mode": "posted", "platform": context["platform"], "url": context.get("url"),
           "verdict": review["verdict"], "inline": len(review["comments"]),
           "already_posted": review["summary"]["already_posted"], "counts": review["summary"]["counts"],
           "results": result["results"], "messages": messages + warnings})
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="prr", description="pr-reviewer : collecte et publication")
    sub = parser.add_subparsers(dest="command", required=True)
    collect_parser = sub.add_parser("collect")
    collect_parser.add_argument("--platform", choices=sorted(ADAPTERS))
    collect_parser.add_argument("--ref", help="URL, numéro de PR/MR ou branche")
    collect_parser.add_argument("--base", help="branche cible (mode local)")
    publish_parser = sub.add_parser("publish")
    publish_parser.add_argument("--work-dir", required=True)
    publish_parser.add_argument("--request-changes", action="store_true")
    publish_parser.add_argument("--dry-run", action="store_true")
    publish_parser.add_argument("--max", type=int)
    args = parser.parse_args(argv)
    return collect(args) if args.command == "collect" else publish(args)


if __name__ == "__main__":
    sys.exit(main())
