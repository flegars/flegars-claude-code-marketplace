import json
import re
from pathlib import Path

from ..core import git as gitcore
from ..core.render import comment_body, summary_body
from ..core.review import marker, parse_marker
from .base import Adapter, AdapterError, CommandError, PlatformUnavailable, cli_present, json_file, run, run_json

_CLOSING = re.compile(r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s*:?\s+(?:([\w.-]+/[\w.-]+))?#(\d+)", re.IGNORECASE)


def parse_remote(url: str) -> dict | None:
    match = re.match(r"^(?:https?://(?:[^@/]+@)?|ssh://git@|git@)([^/:]+)[/:]([^/]+)/([^/]+?)(?:\.git)?/?$", url)
    if not match:
        return None
    return {"host": match.group(1), "owner": match.group(2), "repo": match.group(3)}


def parse_pr_url(url: str) -> dict | None:
    match = re.match(r"^https?://([^/]+)/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not match:
        return None
    return {"host": match.group(1), "owner": match.group(2), "repo": match.group(3), "number": int(match.group(4))}


def is_known_host(host: str) -> bool:
    return host == "github.com"


class GitHubAdapter(Adapter):
    name = "github"

    def __init__(self, repo_root: Path, host: str | None = None):
        super().__init__(repo_root, host or "github.com")

    def _api(self, method: str, endpoint: str, payload=None, paginate: bool = False, jq: str | None = None) -> str:
        command = ["gh", "api", "--hostname", self.host, "-X", method, endpoint]
        if paginate:
            command.append("--paginate")
        if jq:
            command += ["--jq", jq]
        if payload is not None:
            command += ["--input", json_file(payload)]
        return run(command, cwd=self.repo_root)

    def check(self) -> None:
        if not cli_present("gh"):
            raise PlatformUnavailable("La CLI GitHub `gh` est introuvable (https://cli.github.com).",
                                      auth_command=f"gh auth login --hostname {self.host}")
        try:
            run(["gh", "auth", "status", "--hostname", self.host])
        except CommandError as error:
            raise PlatformUnavailable(f"`gh` n'est pas authentifié sur {self.host}.",
                                      auth_command=f"gh auth login --hostname {self.host}") from error

    def _origin(self) -> dict:
        url = gitcore.remote_url("origin", self.repo_root)
        parsed = parse_remote(url) if url else None
        if not parsed:
            raise AdapterError("Le remote `origin` n'est pas un dépôt GitHub reconnu.")
        return parsed

    def fetch_pull_request(self, ref: str | None, base: str | None) -> dict:
        origin = self._origin()
        target = parse_pr_url(ref) if ref and ref.startswith("http") else None
        if target and (target["owner"].lower(), target["repo"].lower()) != (origin["owner"].lower(), origin["repo"].lower()):
            raise AdapterError(f"La PR vise {target['owner']}/{target['repo']} mais le clone courant est "
                               f"{origin['owner']}/{origin['repo']} : lance la review depuis un clone du bon dépôt.")
        repo = f"{self.host}/{origin['owner']}/{origin['repo']}"
        selector = str(target["number"]) if target else (ref or gitcore.current_branch(self.repo_root) or "")
        if not selector:
            raise AdapterError("HEAD détaché : précise la PR (numéro ou URL).")
        fields = "number,title,body,url,baseRefName,headRefName,baseRefOid,headRefOid,closingIssuesReferences,state"
        command = ["gh", "pr", "view", selector, "-R", repo, "--json", fields]
        try:
            pr = run_json(command, cwd=self.repo_root)
        except CommandError as error:
            raise AdapterError(f"Aucune PR trouvée ({selector or 'branche courante'}) : {error.stderr.strip()}") from error

        self.ensure_commits([pr["baseRefOid"], pr["headRefOid"]],
                            [f"refs/pull/{pr['number']}/head", f"refs/heads/{pr['baseRefName']}"])
        merge_base, diff = self.local_diff(pr["baseRefOid"], pr["headRefOid"])
        return {
            "platform": self.name,
            "host": self.host,
            "repo": f"{origin['owner']}/{origin['repo']}",
            "number": pr["number"],
            "url": pr["url"],
            "title": pr["title"],
            "description": pr.get("body") or "",
            "source_branch": pr["headRefName"],
            "target_branch": pr["baseRefName"],
            "base_sha": merge_base,
            "head_sha": pr["headRefOid"],
            "diff": diff,
            "linked_items": self._linked_items(pr, origin),
            "native": {"owner": origin["owner"], "repo": origin["repo"]},
        }

    def _linked_items(self, pr: dict, origin: dict) -> list[dict]:
        refs: dict[tuple[str, int], str] = {}
        for issue in pr.get("closingIssuesReferences") or []:
            owner = (issue.get("repository") or {}).get("owner", {}).get("login") or origin["owner"]
            name = (issue.get("repository") or {}).get("name") or origin["repo"]
            refs[(f"{owner}/{name}", issue["number"])] = "closing_issue"
        # GitHub n'interprète les mots-clés de clôture que si la PR cible la branche par défaut.
        for match in _CLOSING.finditer(pr.get("body") or ""):
            refs.setdefault((match.group(1) or f"{origin['owner']}/{origin['repo']}", int(match.group(2))), "description")
        items = []
        for (repo, number), source in sorted(refs.items()):
            try:
                issue = run_json(["gh", "issue", "view", str(number), "-R", f"{self.host}/{repo}",
                                  "--json", "number,title,body,state,url"], cwd=self.repo_root)
            except CommandError:
                continue
            items.append({"id": f"{repo}#{number}", "title": issue["title"], "body": issue.get("body") or "",
                          "acceptance_criteria": None, "state": issue["state"], "url": issue["url"], "source": source})
        return items

    def list_existing_comments(self, context: dict) -> dict:
        owner, repo, number = context["native"]["owner"], context["native"]["repo"], context["number"]
        jq = ".[] | {id, body, path, line, original_line} | @json"
        summary = None
        for line in self._api("GET", f"repos/{owner}/{repo}/issues/{number}/comments", paginate=True, jq=jq).splitlines():
            comment = json.loads(line)
            meta = parse_marker(comment["body"])
            if meta and meta.get("kind") == "summary":
                summary = {"native_id": comment["id"], "body": comment["body"]}
        comments = []
        for line in self._api("GET", f"repos/{owner}/{repo}/pulls/{number}/comments", paginate=True, jq=jq).splitlines():
            comment = json.loads(line)
            meta = parse_marker(comment["body"])
            if meta and meta.get("fp"):
                comments.append({"native_id": comment["id"], "fingerprint": meta["fp"], "path": comment.get("path"),
                                 "line": comment.get("line") or comment.get("original_line")})
        return {"summary": summary, "comments": comments}

    def build_payloads(self, review: dict, context: dict, existing: dict, request_changes: bool) -> list[dict]:
        owner, repo, number = context["native"]["owner"], context["native"]["repo"], context["number"]
        summary = summary_body(review) + "\n\n" + marker("summary")
        if existing.get("summary"):
            summary_payload = {"step": "update_summary", "method": "PATCH",
                               "endpoint": f"repos/{owner}/{repo}/issues/comments/{existing['summary']['native_id']}",
                               "body": {"body": summary}}
        else:
            summary_payload = {"step": "create_summary", "method": "POST",
                               "endpoint": f"repos/{owner}/{repo}/issues/{number}/comments",
                               "body": {"body": summary}}

        event = "REQUEST_CHANGES" if request_changes and review["verdict"] == "blocking" else "COMMENT"
        if not review["comments"] and event == "COMMENT":
            return [summary_payload]
        comments = []
        for comment in review["comments"]:
            native = {"path": comment["path"], "line": comment["line_end"], "side": comment["side"],
                      "body": comment_body(comment) + "\n\n" + marker("comment", comment["fingerprint"])}
            if comment["line_start"] != comment["line_end"]:
                native.update({"start_line": comment["line_start"], "start_side": comment["side"]})
            comments.append(native)
        count = len(comments)
        review_body = (f"pr-reviewer : {count} nouveau(x) commentaire(s) inline. "
                       "La synthèse est dans le commentaire « Review pr-reviewer » de la PR.") + "\n\n" + marker("review")
        payload = {"step": "create_review", "method": "POST", "endpoint": f"repos/{owner}/{repo}/pulls/{number}/reviews",
                   "body": {"commit_id": context["head_sha"], "event": event, "body": review_body, "comments": comments}}
        if event == "REQUEST_CHANGES":
            payload["fallback_event"] = "COMMENT"
        # La review part en premier : si GitHub la refuse, aucune synthèse orpheline n'est publiée.
        return [payload, summary_payload]

    def send(self, payload: dict, context: dict) -> dict:
        try:
            response = json.loads(self._api(payload["method"], payload["endpoint"], payload["body"]) or "{}")
        except CommandError as error:
            if not payload.get("fallback_event"):
                raise AdapterError(f"Échec de l'étape {payload['step']} : {error.stderr.strip()}") from error
            # REQUEST_CHANGES est refusé sur sa propre PR : on retombe sur un commentaire non bloquant.
            body = dict(payload["body"], event=payload["fallback_event"])
            response = json.loads(self._api(payload["method"], payload["endpoint"], body) or "{}")
            return {"step": payload["step"], "id": response.get("id"), "url": response.get("html_url"),
                    "warning": f"REQUEST_CHANGES refusé ({error.stderr.strip()}), review postée en COMMENT."}
        return {"step": payload["step"], "id": response.get("id"), "url": response.get("html_url")}
