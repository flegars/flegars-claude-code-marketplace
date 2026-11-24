import html
import re
from pathlib import Path

from ..core import git as gitcore
from ..core.render import comment_body, summary_body
from ..core.review import marker, parse_marker
from .base import Adapter, AdapterError, CommandError, PlatformUnavailable, cli_present, json_file, run, run_json

API_VERSION = "7.1"
PROPERTY_PREFIX = "pr-reviewer."
AUTH_COMMAND = "az login && az extension add --name azure-devops"


def parse_remote(url: str) -> dict | None:
    patterns = [
        r"^https://(?:[^@/]+@)?dev\.azure\.com/(?P<org>[^/]+)/(?P<project>[^/]+)/_git/(?P<repo>[^/?#]+)",
        r"^(?:ssh://)?git@ssh\.dev\.azure\.com:(?:22/)?v3/(?P<org>[^/]+)/(?P<project>[^/]+)/(?P<repo>[^/?#]+)",
        r"^https://(?:[^@/]+@)?(?P<org>[^./]+)\.visualstudio\.com/(?:DefaultCollection/)?(?P<project>[^/]+)/_git/(?P<repo>[^/?#]+)",
        r"^(?:ssh://)?(?P<org>[^@/]+)@vs-ssh\.visualstudio\.com:(?:22/)?v3/[^/]+/(?P<project>[^/]+)/(?P<repo>[^/?#]+)",
    ]
    for pattern in patterns:
        match = re.match(pattern, url)
        if match:
            parts = {k: html.unescape(v).replace("%20", " ") for k, v in match.groupdict().items()}
            parts["repo"] = re.sub(r"\.git$", "", parts["repo"])
            parts["host"] = "dev.azure.com"
            return parts
    return None


def parse_pr_url(url: str) -> dict | None:
    match = re.search(r"/pullrequest/(\d+)", url, re.IGNORECASE)
    parsed = parse_remote(url)
    if not match or not parsed:
        return None
    return {**parsed, "number": int(match.group(1))}


def is_known_host(host: str) -> bool:
    return host in ("dev.azure.com", "ssh.dev.azure.com") or host.endswith(".visualstudio.com")


def strip_html(value: str | None) -> str:
    if not value:
        return ""
    text = re.sub(r"<\s*(br|/p|/div|/li)\s*/?>", "\n", value, flags=re.IGNORECASE)
    text = re.sub(r"<li[^>]*>", "- ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\n{3,}", "\n\n", html.unescape(text)).strip()


def _property(value):
    return {"$type": "System.String", "$value": value}


def _read_property(properties: dict | None, key: str):
    raw = (properties or {}).get(PROPERTY_PREFIX + key)
    return raw.get("$value") if isinstance(raw, dict) else raw


class AzureDevOpsAdapter(Adapter):
    name = "ado"

    def _origin(self) -> dict:
        url = gitcore.remote_url("origin", self.repo_root)
        parsed = parse_remote(url) if url else None
        if not parsed:
            raise AdapterError("Le remote `origin` n'est pas un dépôt Azure DevOps reconnu.")
        parsed["org_url"] = f"https://dev.azure.com/{parsed['org']}"
        return parsed

    def check(self) -> None:
        if not cli_present("az"):
            raise PlatformUnavailable("La CLI Azure `az` est introuvable "
                                      "(https://learn.microsoft.com/cli/azure/install-azure-cli).", AUTH_COMMAND)
        try:
            run(["az", "extension", "show", "--name", "azure-devops", "-o", "none"])
        except CommandError as error:
            raise PlatformUnavailable("L'extension `azure-devops` de `az` n'est pas installée.",
                                      "az extension add --name azure-devops") from error
        try:
            run(["az", "account", "show", "-o", "none"])
        except CommandError as error:
            raise PlatformUnavailable("`az` n'est pas authentifié.", "az login") from error

    def _invoke(self, origin: dict, resource: str, route: dict, method: str = "GET", body=None, query: dict | None = None):
        command = ["az", "devops", "invoke", "--org", origin["org_url"], "--area", "git", "--resource", resource,
                   "--route-parameters", *[f"{k}={v}" for k, v in route.items()],
                   "--http-method", method, "--api-version", API_VERSION, "-o", "json"]
        if query:
            command += ["--query-parameters", *[f"{k}={v}" for k, v in query.items()]]
        if body is not None:
            command += ["--in-file", json_file(body)]
        return run_json(command, cwd=self.repo_root)

    def fetch_pull_request(self, ref: str | None, base: str | None) -> dict:
        origin = self._origin()
        target = parse_pr_url(ref) if ref and ref.startswith("http") else None
        if target and (target["project"].lower(), target["repo"].lower()) != (origin["project"].lower(), origin["repo"].lower()):
            raise AdapterError(f"La PR vise {target['project']}/{target['repo']} mais le clone courant est "
                               f"{origin['project']}/{origin['repo']} : lance la review depuis un clone du bon dépôt.")
        common = ["--org", origin["org_url"], "-o", "json"]
        try:
            if target or (ref and ref.isdigit()):
                number = target["number"] if target else int(ref)
            else:
                branch = ref or gitcore.current_branch(self.repo_root)
                if not branch:
                    raise AdapterError("HEAD détaché : précise la PR (numéro ou URL).")
                found = run_json(["az", "repos", "pr", "list", "--project", origin["project"], "--repository",
                                  origin["repo"], "--source-branch", branch, "--status", "active", *common])
                if not found:
                    raise AdapterError(f"Aucune PR active pour la branche {branch}.")
                number = found[0]["pullRequestId"]
            pr = run_json(["az", "repos", "pr", "show", "--id", str(number), *common])
        except CommandError as error:
            raise AdapterError(f"Lecture de la PR impossible : {error.stderr.strip()}") from error

        source = pr["sourceRefName"].removeprefix("refs/heads/")
        target_branch = pr["targetRefName"].removeprefix("refs/heads/")
        head_sha = pr["lastMergeSourceCommit"]["commitId"]
        base_sha = pr["lastMergeTargetCommit"]["commitId"]
        self.ensure_commits([base_sha, head_sha], [f"refs/heads/{source}", f"refs/heads/{target_branch}"])
        merge_base, diff = self.local_diff(base_sha, head_sha)

        route = {"project": pr["repository"]["project"]["name"], "repositoryId": pr["repository"]["id"],
                 "pullRequestId": number}
        iterations = (self._invoke(origin, "pullRequestIterations", route) or {}).get("value") or []
        iteration = iterations[-1]["id"] if iterations else 1
        changes = self._invoke(origin, "pullRequestIterationChanges", {**route, "iterationId": iteration}) or {}
        tracking = {entry["item"]["path"].lstrip("/"): entry["changeTrackingId"]
                    for entry in changes.get("changeEntries") or [] if entry.get("item", {}).get("path")}

        return {
            "platform": self.name,
            "host": origin["host"],
            "repo": f"{origin['org']}/{origin['project']}/{origin['repo']}",
            "number": number,
            "url": f"{origin['org_url']}/{origin['project']}/_git/{origin['repo']}/pullrequest/{number}",
            "title": pr["title"],
            "description": pr.get("description") or "",
            "source_branch": source,
            "target_branch": target_branch,
            "base_sha": merge_base,
            "head_sha": head_sha,
            "diff": diff,
            "linked_items": self._linked_items(origin, number),
            "native": {"org_url": origin["org_url"], "route": route, "iteration": iteration,
                       "change_tracking": tracking},
        }

    def _linked_items(self, origin: dict, number: int) -> list[dict]:
        try:
            refs = run_json(["az", "repos", "pr", "work-item", "list", "--id", str(number),
                             "--org", origin["org_url"], "-o", "json"]) or []
        except CommandError:
            return []
        items = []
        for ref in refs:
            fields = ref.get("fields") or {}
            if "System.Title" not in fields:
                try:
                    fields = run_json(["az", "boards", "work-item", "show", "--id", str(ref["id"]),
                                       "--org", origin["org_url"], "-o", "json"])["fields"]
                except CommandError:
                    continue
            items.append({
                "id": str(ref["id"]),
                "title": fields.get("System.Title"),
                "body": strip_html(fields.get("System.Description")),
                "acceptance_criteria": strip_html(fields.get("Microsoft.VSTS.Common.AcceptanceCriteria")) or None,
                "state": fields.get("System.State"),
                "url": f"{origin['org_url']}/_workitems/edit/{ref['id']}",
                "source": "work_item",
            })
        return items

    def list_existing_comments(self, context: dict) -> dict:
        origin = {"org_url": context["native"]["org_url"]}
        threads = (self._invoke(origin, "pullRequestThreads", context["native"]["route"]) or {}).get("value") or []
        summary, comments = None, []
        for thread in threads:
            first = (thread.get("comments") or [{}])[0]
            meta = parse_marker(first.get("content")) or {}
            kind = _read_property(thread.get("properties"), "kind") or meta.get("kind")
            fp = _read_property(thread.get("properties"), "fp") or meta.get("fp")
            if kind == "summary":
                summary = {"native_id": thread["id"], "comment_id": first.get("id", 1), "body": first.get("content")}
            elif fp:
                context_ = thread.get("threadContext") or {}
                start = context_.get("rightFileStart") or context_.get("leftFileStart") or {}
                comments.append({"native_id": thread["id"], "fingerprint": fp,
                                 "path": (context_.get("filePath") or "").lstrip("/"), "line": start.get("line")})
        return {"summary": summary, "comments": comments}

    def build_payloads(self, review: dict, context: dict, existing: dict, request_changes: bool) -> list[dict]:
        native = context["native"]
        route = native["route"]
        base_endpoint = (f"{route['project']}/_apis/git/repositories/{route['repositoryId']}"
                         f"/pullRequests/{route['pullRequestId']}")
        blocking = request_changes and review["verdict"] == "blocking"
        payloads = []
        summary = summary_body(review) + "\n\n" + marker("summary")
        if existing.get("summary"):
            thread_id, comment_id = existing["summary"]["native_id"], existing["summary"]["comment_id"]
            payloads.append({"step": "update_summary", "method": "PATCH",
                             "endpoint": f"{base_endpoint}/threads/{thread_id}/comments/{comment_id}",
                             "invoke": {"resource": "pullRequestThreadComments",
                                        "route": {**route, "threadId": thread_id, "commentId": comment_id}},
                             "body": {"content": summary}})
        else:
            payloads.append({"step": "create_summary", "method": "POST", "endpoint": f"{base_endpoint}/threads",
                             "invoke": {"resource": "pullRequestThreads", "route": route},
                             "body": {"comments": [{"parentCommentId": 0, "content": summary, "commentType": "text"}],
                                      "status": "closed",
                                      "properties": {PROPERTY_PREFIX + "kind": _property("summary"),
                                                     PROPERTY_PREFIX + "marker": _property("v2")}}})

        # Un thread « active » bloque la complétion sous la politique de résolution des commentaires :
        # sans --request-changes, les threads sont créés résolus pour rester non bloquants.
        status = "active" if blocking else "closed"
        for comment in review["comments"]:
            side = "right" if comment["side"] == "RIGHT" else "left"
            thread_context = {"filePath": "/" + comment["path"],
                              f"{side}FileStart": {"line": comment["line_start"], "offset": 1},
                              f"{side}FileEnd": {"line": comment["line_end"], "offset": 1}}
            pr_context = {"iterationContext": {"firstComparingIteration": 1,
                                               "secondComparingIteration": native["iteration"]}}
            tracking = native["change_tracking"].get(comment["path"])
            if tracking is not None:
                pr_context["changeTrackingId"] = tracking
            payloads.append({
                "step": "create_thread", "method": "POST", "endpoint": f"{base_endpoint}/threads",
                "invoke": {"resource": "pullRequestThreads", "route": route},
                "body": {
                    "comments": [{"parentCommentId": 0, "commentType": "text",
                                  "content": comment_body(comment) + "\n\n" + marker("comment", comment["fingerprint"])}],
                    "status": status,
                    "threadContext": thread_context,
                    "pullRequestThreadContext": pr_context,
                    "properties": {PROPERTY_PREFIX + "kind": _property("comment"),
                                   PROPERTY_PREFIX + "fp": _property(comment["fingerprint"]),
                                   PROPERTY_PREFIX + "marker": _property("v2")},
                },
            })
        if blocking:
            payloads.append({"step": "vote_wait_for_author",
                             "cli": ["az", "repos", "pr", "set-vote", "--id", str(route["pullRequestId"]),
                                     "--vote", "wait-for-author", "--org", native["org_url"], "-o", "json"]})
        return payloads

    def send(self, payload: dict, context: dict) -> dict:
        try:
            if "cli" in payload:
                run(payload["cli"], cwd=self.repo_root)
                return {"step": payload["step"]}
            response = self._invoke({"org_url": context["native"]["org_url"]}, payload["invoke"]["resource"],
                                    payload["invoke"]["route"], payload["method"], payload["body"]) or {}
        except CommandError as error:
            raise AdapterError(f"Échec de l'étape {payload['step']} : {error.stderr.strip()}") from error
        return {"step": payload["step"], "id": response.get("id")}
