import re
import time
from pathlib import Path

from .diff import FileDiff
from .git import GitError, git
from .render import age_label

_MERGE_PREFIXES = [
    re.compile(r"^Merged PR \d+:\s*", re.IGNORECASE),
    re.compile(r"^Merge pull request #\d+ from \S+\s*", re.IGNORECASE),
    re.compile(r"^Merge branch '[^']*'\s*", re.IGNORECASE),
]
_FIX_SUBJECT = re.compile(r"^(fix|hotfix|bugfix)(\([^)]*\))?!?:", re.IGNORECASE)
_FIX_BRANCH = re.compile(r"(?:from \S+/|Merge branch ')(hotfix|fix|bugfix)/", re.IGNORECASE)
_PR_REFS = [
    (re.compile(r"\(#(\d+)\)"), "PR #{}"),
    (re.compile(r"Merge pull request #(\d+)", re.IGNORECASE), "PR #{}"),
    (re.compile(r"Merged PR (\d+)", re.IGNORECASE), "PR {}"),
    (re.compile(r"!(\d+)\b"), "MR !{}"),
]
_ISSUE_REF = re.compile(r"(?<![\w(])#(\d+)\b")


def is_fix(subject: str) -> bool:
    if _FIX_BRANCH.search(subject):
        return True
    stripped = subject
    for prefix in _MERGE_PREFIXES:
        stripped = prefix.sub("", stripped)
    return bool(_FIX_SUBJECT.match(stripped)) or stripped.lower().startswith("hotfix")


def references(subject: str) -> str | None:
    for pattern, label in _PR_REFS:
        match = pattern.search(subject)
        if match:
            return label.format(match.group(1))
    match = _ISSUE_REF.search(subject)
    return f"#{match.group(1)}" if match else None


def _deleted_runs(diff: FileDiff) -> list[tuple[list[int], int | None]]:
    runs = []
    for hunk in diff.hunks:
        index = 0
        while index < len(hunk):
            if hunk[index].kind != "deleted":
                index += 1
                continue
            run = []
            while index < len(hunk) and hunk[index].kind == "deleted":
                run.append(hunk[index].old_line)
                index += 1
            anchor = None
            for entry in hunk[index:]:
                if entry.kind == "added":
                    anchor = entry.new_line
                    break
                if entry.kind == "context":
                    break
            runs.append((run, anchor))
    return runs


def _blame(path: str, start: int, end: int, revision: str, cwd: Path) -> dict[str, dict]:
    output = git("blame", "--porcelain", "-L", f"{start},{end}", revision, "--", path, cwd=cwd)
    commits: dict[str, dict] = {}
    current = None
    for line in output.splitlines():
        head = line.split(" ")
        if len(head) >= 3 and re.fullmatch(r"[0-9a-f]{40}", head[0]):
            current = commits.setdefault(head[0], {"sha": head[0]})
        elif current is not None and line.startswith("committer-time "):
            current["time"] = int(line.split(" ", 1)[1])
        elif current is not None and line.startswith("summary "):
            current["subject"] = line.split(" ", 1)[1]
    return commits


def scan(files: dict[str, FileDiff], revision: str, cwd: Path, window_days: int, now: float | None = None) -> list[dict]:
    if window_days <= 0:
        return []
    now = now if now is not None else time.time()
    threshold = now - window_days * 86400
    risks = []
    for diff in files.values():
        if not diff.old_path:
            continue
        for run, anchor in _deleted_runs(diff):
            try:
                commits = _blame(diff.old_path, min(run), max(run), revision, cwd)
            except GitError:
                continue
            fixes = [c for c in commits.values()
                     if c.get("time", 0) >= threshold and is_fix(c.get("subject", ""))]
            for commit in sorted(fixes, key=lambda c: -c["time"]):
                risks.append({
                    "path": diff.path,
                    "line": anchor if anchor is not None else min(run),
                    "side": "RIGHT" if anchor is not None else "LEFT",
                    "base_lines": [min(run), max(run)],
                    "commit": commit["sha"],
                    "subject": commit["subject"],
                    "ref": references(commit["subject"]),
                    "age_days": max(0, int((now - commit["time"]) // 86400)),
                })
    return risks


def to_comments(risks: list[dict]) -> list[dict]:
    comments = []
    for risk in risks:
        short = risk["commit"][:7]
        origin = f"{short} ({risk['ref']})" if risk["ref"] else short
        start, end = risk["base_lines"]
        lines = f"ligne {start}" if start == end else f"lignes {start}–{end}"
        comments.append({
            "path": risk["path"],
            "line_start": risk["line"],
            "line_end": risk["line"],
            "side": risk["side"],
            "severity": "question",
            "category": "regression",
            "body": {
                "problem": f"Cette zone ({lines} avant la PR) a été modifiée {age_label(risk['age_days'])} "
                           f"par {origin}. Ce changement annule-t-il ce correctif ?",
                "justification": f"Commit {short} — « {risk['subject']} », correctif récent sur les lignes remplacées ici.",
                "proposal": "Vérifier que le comportement corrigé par ce commit est conservé (idéalement par un test), "
                            "ou expliquer dans la PR pourquoi il est volontairement modifié.",
            },
            "rule_ref": None,
            "evidence": [f"commit {risk['commit']}"],
        })
    return comments
