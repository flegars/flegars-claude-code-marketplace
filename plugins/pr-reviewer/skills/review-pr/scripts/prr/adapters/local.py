from ..core import git as gitcore
from .base import Adapter, AdapterError


class LocalAdapter(Adapter):
    name = "local"

    def check(self) -> None:
        return None

    def _default_base(self) -> str:
        head = gitcore.git("symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD",
                           cwd=self.repo_root, check=False).strip()
        if head:
            return head
        for candidate in ("origin/main", "origin/master", "main", "master", "develop"):
            if gitcore.git("rev-parse", "--verify", "--quiet", f"{candidate}^{{commit}}",
                           cwd=self.repo_root, check=False).strip():
                return candidate
        raise AdapterError("Branche cible introuvable : précise-la avec --base <branche>.")

    def fetch_pull_request(self, ref: str | None, base: str | None) -> dict:
        base_ref = base or self._default_base()
        try:
            base_sha = gitcore.git("rev-parse", "--verify", f"{base_ref}^{{commit}}", cwd=self.repo_root).strip()
            head_sha = gitcore.git("rev-parse", "--verify", "HEAD^{commit}", cwd=self.repo_root).strip()
        except gitcore.GitError as error:
            raise AdapterError(f"Référence invalide : {error}") from error
        merge_base, diff = self.local_diff(base_sha, head_sha)
        branch = gitcore.current_branch(self.repo_root) or head_sha[:12]
        return {
            "platform": self.name,
            "host": None,
            "repo": self.repo_root.name,
            "number": None,
            "url": None,
            "title": branch,
            "description": "",
            "source_branch": branch,
            "target_branch": base_ref,
            "base_sha": merge_base,
            "head_sha": head_sha,
            "diff": diff,
            "linked_items": [],
            "native": {},
        }

    def list_existing_comments(self, context: dict) -> dict:
        return {"summary": None, "comments": []}

    def build_payloads(self, review: dict, context: dict, existing: dict, request_changes: bool) -> list[dict]:
        return []

    def send(self, payload: dict, context: dict) -> dict:
        return {}
