import json
import re
from pathlib import Path
from urllib.parse import quote

from ..core import git as gitcore
from ..core.diff import FileDiff, locate, parse_unified_diff
from ..core.render import comment_body, summary_body
from ..core.review import marker, parse_marker
from .base import Adapter, AdapterError, CommandError, PlatformUnavailable, cli_present, json_file, run

_REQUEST_CHANGES = """mutation($projectPath: ID!, $iid: String!) {
  mergeRequestRequestChanges(input: {projectPath: $projectPath, iid: $iid}) { errors }
}"""


def _decode_pages(output: str):
    # glab --paginate enchaîne un document JSON par page : on les fusionne en une seule liste.
    decoder, index, merged = json.JSONDecoder(), 0, []
    while index < len(output):
        page, index = decoder.raw_decode(output, index)
        merged.extend(page if isinstance(page, list) else [page])
        while index < len(output) and output[index].isspace():
            index += 1
    return merged


def parse_remote(url: str) -> dict | None:
    match = re.match(r"^(?:https?://(?:[^@/]+@)?|ssh://git@|git@)([^/:]+)(?::\d+)?[/:](.+?)(?:\.git)?/?$", url)
    if not match:
        return None
    return {"host": match.group(1), "path": match.group(2)}


def parse_pr_url(url: str) -> dict | None:
    match = re.match(r"^https?://([^/]+)/(.+?)/-/merge_requests/(\d+)", url)
    if not match:
        return None
    return {"host": match.group(1), "path": match.group(2), "number": int(match.group(3))}


def is_known_host(host: str) -> bool:
    return host == "gitlab.com"


class GitLabAdapter(Adapter):
    name = "gitlab"

    def __init__(self, repo_root: Path, host: str | None = None):
        super().__init__(repo_root, host or "gitlab.com")

    def _api(self, method: str, endpoint: str, payload=None, paginate: bool = False):
        command = ["glab", "api", "--hostname", self.host, "-X", method, endpoint]
        if paginate:
            command.append("--paginate")
        if payload is not None:
            command += ["-H", "Content-Type: application/json", "--input", json_file(payload)]
        output = run(command, cwd=self.repo_root).strip()
        if not output:
            return None
        return _decode_pages(output) if paginate else json.loads(output)

    def check(self) -> None:
        if not cli_present("glab"):
            raise PlatformUnavailable("La CLI GitLab `glab` est introuvable (https://gitlab.com/gitlab-org/cli).",
                                      auth_command=f"glab auth login --hostname {self.host}")
        try:
            run(["glab", "auth", "status", "--hostname", self.host])
        except CommandError as error:
            raise PlatformUnavailable(f"`glab` n'est pas authentifié sur {self.host}.",
                                      auth_command=f"glab auth login --hostname {self.host}") from error

    def _origin(self) -> dict:
        url = gitcore.remote_url("origin", self.repo_root)
        parsed = parse_remote(url) if url else None
        if not parsed:
            raise AdapterError("Le remote `origin` n'est pas un dépôt GitLab reconnu.")
        return parsed

    def fetch_pull_request(self, ref: str | None, base: str | None) -> dict:
        origin = self._origin()
        target = parse_pr_url(ref) if ref and ref.startswith("http") else None
        if target and target["path"].lower() != origin["path"].lower():
            raise AdapterError(f"La MR vise {target['path']} mais le clone courant est {origin['path']} : "
                               "lance la review depuis un clone du bon dépôt.")
        project = quote(origin["path"], safe="")
        try:
            if target or (ref and ref.lstrip("!").isdigit()):
                iid = target["number"] if target else int(ref.lstrip("!"))
            else:
                branch = ref or gitcore.current_branch(self.repo_root)
                if not branch:
                    raise AdapterError("HEAD détaché : précise la MR (numéro ou URL).")
                found = self._api("GET", f"projects/{project}/merge_requests?state=opened&source_branch={quote(branch, safe='')}")
                if not found:
                    raise AdapterError(f"Aucune MR ouverte pour la branche {branch}.")
                iid = found[0]["iid"]
            mr = self._api("GET", f"projects/{project}/merge_requests/{iid}")
            versions = self._api("GET", f"projects/{project}/merge_requests/{iid}/versions") or []
        except CommandError as error:
            raise AdapterError(f"Lecture de la MR impossible : {error.stderr.strip()}") from error
        if versions:
            refs = {"base_sha": versions[0]["base_commit_sha"], "start_sha": versions[0]["start_commit_sha"],
                    "head_sha": versions[0]["head_commit_sha"]}
        elif mr.get("diff_refs"):
            refs = dict(mr["diff_refs"])
        else:
            raise AdapterError("Les diff_refs de la MR ne sont pas encore calculés par GitLab : réessaie dans un instant.")

        self.ensure_commits([refs["base_sha"], refs["head_sha"]],
                            [f"refs/merge-requests/{iid}/head", f"refs/heads/{mr['target_branch']}"])
        merge_base, diff = self.local_diff(refs["base_sha"], refs["head_sha"])
        return {
            "platform": self.name,
            "host": self.host,
            "repo": origin["path"],
            "number": iid,
            "url": mr["web_url"],
            "title": mr["title"],
            "description": mr.get("description") or "",
            "source_branch": mr["source_branch"],
            "target_branch": mr["target_branch"],
            "base_sha": merge_base,
            "head_sha": refs["head_sha"],
            "diff": diff,
            "linked_items": self._linked_items(project, iid),
            "native": {"project": project, "project_path": origin["path"], "diff_refs": refs},
        }

    def _linked_items(self, project: str, iid: int) -> list[dict]:
        try:
            issues = self._api("GET", f"projects/{project}/merge_requests/{iid}/closes_issues") or []
        except CommandError:
            return []
        return [{"id": f"#{issue['iid']}", "title": issue["title"], "body": issue.get("description") or "",
                 "acceptance_criteria": None, "state": issue["state"], "url": issue["web_url"], "source": "closing_issue"}
                for issue in issues]

    def list_existing_comments(self, context: dict) -> dict:
        project, iid = context["native"]["project"], context["number"]
        discussions = self._api("GET", f"projects/{project}/merge_requests/{iid}/discussions?per_page=100",
                                paginate=True) or []
        summary, comments = None, []
        for discussion in discussions:
            for note in discussion.get("notes") or []:
                meta = parse_marker(note.get("body"))
                if not meta:
                    continue
                if meta.get("kind") == "summary":
                    summary = {"native_id": note["id"], "body": note["body"]}
                elif meta.get("fp"):
                    position = note.get("position") or {}
                    comments.append({"native_id": note["id"], "fingerprint": meta["fp"],
                                     "path": position.get("new_path") or position.get("old_path"),
                                     "line": position.get("new_line") or position.get("old_line")})
        return {"summary": summary, "comments": comments}

    @staticmethod
    def _position(comment: dict, refs: dict, files: dict[str, FileDiff]) -> dict:
        # Une plage GitLab exige des line_code internes : on ancre sur la dernière ligne de la plage.
        line = locate(files, comment["path"], comment["line_end"], comment["line_end"], comment["side"])[0]
        diff = files[comment["path"]]
        position = {"position_type": "text", **refs,
                    "new_path": diff.new_path or comment["path"], "old_path": diff.old_path or comment["path"]}
        if line.old_line is not None:
            position["old_line"] = line.old_line
        if line.new_line is not None:
            position["new_line"] = line.new_line
        return position

    def build_payloads(self, review: dict, context: dict, existing: dict, request_changes: bool) -> list[dict]:
        project, iid = context["native"]["project"], context["number"]
        files = parse_unified_diff(context["diff"])
        payloads = []
        summary = summary_body(review) + "\n\n" + marker("summary")
        if existing.get("summary"):
            payloads.append({"step": "update_summary", "method": "PUT",
                             "endpoint": f"projects/{project}/merge_requests/{iid}/notes/{existing['summary']['native_id']}",
                             "body": {"body": summary}})
        else:
            payloads.append({"step": "create_summary", "method": "POST",
                             "endpoint": f"projects/{project}/merge_requests/{iid}/notes", "body": {"body": summary}})
        for comment in review["comments"]:
            prefix = (f"_Lignes {comment['line_start']}–{comment['line_end']}_\n\n"
                      if comment["line_start"] != comment["line_end"] else "")
            position = self._position(comment, context["native"]["diff_refs"], files)
            payloads.append({"step": "create_discussion", "method": "POST",
                             "endpoint": f"projects/{project}/merge_requests/{iid}/discussions",
                             "body": {"body": prefix + comment_body(comment) + "\n\n"
                                      + marker("comment", comment["fingerprint"]),
                                      "position": position}})
        if request_changes and review["verdict"] == "blocking":
            payloads.append({"step": "request_changes", "method": "POST", "endpoint": "graphql",
                             "body": {"query": _REQUEST_CHANGES,
                                      "variables": {"projectPath": context["native"]["project_path"], "iid": str(iid)}}})
        return payloads

    def send(self, payload: dict, context: dict) -> dict:
        try:
            response = self._api(payload["method"], payload["endpoint"], payload["body"]) or {}
        except CommandError as error:
            raise AdapterError(f"Échec de l'étape {payload['step']} : {error.stderr.strip()}") from error
        if payload["step"] == "request_changes":
            errors = (((response.get("data") or {}).get("mergeRequestRequestChanges") or {}).get("errors")
                      or response.get("errors"))
            if errors:
                return {"step": payload["step"],
                        "warning": f"Statut « changements demandés » indisponible sur cette instance ({errors}) : "
                                   "review postée en commentaire seul."}
        return {"step": payload["step"], "id": response.get("id")}
