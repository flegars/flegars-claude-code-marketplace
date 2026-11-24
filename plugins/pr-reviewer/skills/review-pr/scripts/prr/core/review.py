import hashlib
import re

from .diff import FileDiff, locate

SCHEMA = "pr-reviewer/review@2"
SEVERITIES = ("bloquant", "important", "suggestion", "question")
CATEGORIES = ("rule", "duplication", "reuse", "interface", "regression", "us_coverage", "us_scope", "generic")
SIDES = ("RIGHT", "LEFT")


class ReviewError(Exception):
    pass


def fingerprint(comment: dict) -> str:
    # Le texte produit par le modèle varie d'une exécution à l'autre : l'empreinte ne repose que sur
    # l'ancrage et la catégorie, pour qu'une relance ne reposte pas le même problème reformulé.
    key = "|".join([comment["path"], str(comment["line_start"]), str(comment["line_end"]),
                    comment["side"], comment["category"]])
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def _validate_comment(index: int, comment: dict) -> list[str]:
    errors = []
    where = f"comments[{index}]"
    if not isinstance(comment, dict):
        return [f"{where} n'est pas un objet"]
    if not isinstance(comment.get("path"), str) or not comment["path"]:
        errors.append(f"{where}.path manquant")
    for key in ("line_start", "line_end"):
        if not isinstance(comment.get(key), int) or comment[key] < 1:
            errors.append(f"{where}.{key} doit être un entier ≥ 1")
    if comment.get("side", "RIGHT") not in SIDES:
        errors.append(f"{where}.side doit valoir RIGHT ou LEFT")
    if comment.get("severity") not in SEVERITIES:
        errors.append(f"{where}.severity doit valoir {' | '.join(SEVERITIES)}")
    if comment.get("category", "generic") not in CATEGORIES:
        errors.append(f"{where}.category doit valoir {' | '.join(CATEGORIES)}")
    body = comment.get("body")
    if not isinstance(body, dict) or not all(isinstance(body.get(k), str) and body[k].strip()
                                             for k in ("problem", "justification", "proposal")):
        errors.append(f"{where}.body doit contenir problem, justification et proposal")
    rule_ref = comment.get("rule_ref")
    if rule_ref is not None and not (isinstance(rule_ref, dict) and rule_ref.get("file") and rule_ref.get("rule")):
        errors.append(f"{where}.rule_ref doit être null ou {{file, rule}}")
    if comment.get("category") == "rule" and rule_ref is None:
        errors.append(f"{where} est de catégorie rule mais ne cite aucune règle (rule_ref)")
    return errors


def _normalize(comment: dict) -> dict:
    normalized = {
        "path": comment["path"].lstrip("/"),
        "line_start": comment["line_start"],
        "line_end": comment["line_end"],
        "side": comment.get("side", "RIGHT"),
        "severity": comment["severity"],
        "category": comment.get("category", "generic"),
        "body": {k: comment["body"][k].strip() for k in ("problem", "justification", "proposal")},
        "rule_ref": comment.get("rule_ref"),
        "evidence": list(comment.get("evidence") or []),
    }
    normalized["fingerprint"] = fingerprint(normalized)
    return normalized


def _summary_defaults(raw_summary: dict) -> dict:
    us = raw_summary.get("us") or {}
    return {
        "us": {
            "found": bool(us.get("found")),
            "id": us.get("id"),
            "title": us.get("title"),
            "source": us.get("source"),
            "uncovered_criteria": list(us.get("uncovered_criteria") or []),
            "out_of_scope": list(us.get("out_of_scope") or []),
        },
        "claude_md_loaded": list(raw_summary.get("claude_md_loaded") or []),
        "notes": list(raw_summary.get("notes") or []),
    }


def build_review(raw: dict, files: dict[str, FileDiff], extra_comments: list[dict], regression_risks: list[dict],
                 existing_fingerprints: set[str], max_inline: int) -> dict:
    if not isinstance(raw, dict):
        raise ReviewError("La review de l'agent doit être un objet JSON.")
    raw_comments = raw.get("comments") or []
    errors = [e for i, c in enumerate(raw_comments) for e in _validate_comment(i, c)]
    errors += [e.replace("comments[", "extra[") for i, c in enumerate(extra_comments) for e in _validate_comment(i, c)]
    if errors:
        raise ReviewError("Review invalide :\n- " + "\n- ".join(errors))

    seen: set[str] = set()
    candidates, not_postable, already_posted = [], [], []
    for comment in [_normalize(c) for c in [*raw_comments, *extra_comments]]:
        if comment["fingerprint"] in seen:
            continue
        seen.add(comment["fingerprint"])
        if locate(files, comment["path"], comment["line_start"], comment["line_end"], comment["side"]) is None:
            not_postable.append({"reason": "out_of_diff", "comment": comment})
        elif comment["fingerprint"] in existing_fingerprints:
            already_posted.append(comment)
        else:
            candidates.append(comment)

    order = {severity: rank for rank, severity in enumerate(SEVERITIES)}
    candidates.sort(key=lambda c: (order[c["severity"]], c["path"], c["line_start"]))
    inline = candidates[:max_inline]
    not_postable += [{"reason": "over_cap", "comment": c} for c in candidates[max_inline:]]

    every = [*inline, *(item["comment"] for item in not_postable), *already_posted]
    counts = {severity: 0 for severity in SEVERITIES}
    for comment in every:
        counts[comment["severity"]] += 1

    summary = _summary_defaults(raw.get("summary") or {})
    summary.update({
        "counts": counts,
        "already_posted": len(already_posted),
        "regression_risks": regression_risks,
        "not_postable_inline": not_postable,
    })
    return {
        "schema": SCHEMA,
        "verdict": "blocking" if counts["bloquant"] > 0 else "non_blocking",
        "comments": inline,
        "summary": summary,
    }


_MARKER = re.compile(r"<!--\s*pr-reviewer:v2\s+([^>]*?)\s*-->")


def marker(kind: str, fp: str | None = None) -> str:
    return f"<!-- pr-reviewer:v2 kind={kind}" + (f" fp={fp}" if fp else "") + " -->"


def parse_marker(body: str | None) -> dict | None:
    match = _MARKER.search(body or "")
    if not match:
        return None
    return dict(part.split("=", 1) for part in match.group(1).split() if "=" in part)
