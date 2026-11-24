import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from ..core import git as gitcore


class AdapterError(Exception):
    pass


class PlatformUnavailable(AdapterError):
    def __init__(self, message: str, auth_command: str | None = None):
        super().__init__(message)
        self.auth_command = auth_command


class CommandError(AdapterError):
    def __init__(self, command: list[str], stderr: str, stdout: str = ""):
        super().__init__(f"{' '.join(command[:4])}… a échoué : {stderr.strip() or stdout.strip()}")
        self.command = command
        self.stderr = stderr
        self.stdout = stdout


def run(command: list[str], cwd: Path | None = None, stdin: str | None = None, env: dict | None = None) -> str:
    result = subprocess.run(command, cwd=cwd, input=stdin, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise CommandError(command, result.stderr, result.stdout)
    return result.stdout


def run_json(command: list[str], **kwargs):
    output = run(command, **kwargs)
    return json.loads(output) if output.strip() else None


def cli_present(binary: str) -> bool:
    return shutil.which(binary) is not None


def json_file(payload) -> str:
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    with handle:
        json.dump(payload, handle, ensure_ascii=False)
    return handle.name


class Adapter:
    name = ""

    def __init__(self, repo_root: Path, host: str | None = None):
        self.repo_root = repo_root
        self.host = host

    def check(self) -> None:
        raise NotImplementedError

    def fetch_pull_request(self, ref: str | None, base: str | None) -> dict:
        raise NotImplementedError

    def list_existing_comments(self, context: dict) -> dict:
        raise NotImplementedError

    def build_payloads(self, review: dict, context: dict, existing: dict, request_changes: bool) -> list[dict]:
        raise NotImplementedError

    def send(self, payload: dict, context: dict) -> dict:
        raise NotImplementedError

    def post_review(self, review: dict, context: dict, existing: dict, request_changes: bool, dry_run: bool) -> dict:
        payloads = self.build_payloads(review, context, existing, request_changes)
        if dry_run:
            return {"dry_run": True, "payloads": payloads, "results": []}
        results = [self.send(payload, context) for payload in payloads]
        return {"dry_run": False, "payloads": payloads, "results": results}

    def ensure_commits(self, shas: list[str], refspecs: list[str], remote: str = "origin") -> None:
        if all(gitcore.has_commit(sha, self.repo_root) for sha in shas):
            return
        # Sans destination, le fetch ne crée aucune ref locale : seuls les objets sont rapatriés.
        try:
            gitcore.git("fetch", "--quiet", "--no-tags", remote, *refspecs, cwd=self.repo_root)
        except gitcore.GitError as error:
            raise AdapterError(f"Impossible de récupérer {', '.join(refspecs)} depuis {remote} : {error}") from error

    def local_diff(self, base_sha: str, head_sha: str) -> tuple[str, str]:
        for sha in (base_sha, head_sha):
            if not gitcore.has_commit(sha, self.repo_root):
                raise AdapterError(f"Le commit {sha[:12]} est introuvable dans le clone local.")
        merge_base = gitcore.merge_base(base_sha, head_sha, self.repo_root)
        return merge_base, gitcore.diff(merge_base, head_sha, self.repo_root)
