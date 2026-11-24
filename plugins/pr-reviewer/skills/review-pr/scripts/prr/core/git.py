import subprocess
from pathlib import Path


class GitError(Exception):
    pass


def git(*args: str, cwd: Path | None = None, check: bool = True) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise GitError(f"git {' '.join(args)} : {result.stderr.strip()}")
    return result.stdout


def repo_root(cwd: Path | None = None) -> Path:
    return Path(git("rev-parse", "--show-toplevel", cwd=cwd).strip())


def has_commit(sha: str, cwd: Path) -> bool:
    return subprocess.run(["git", "cat-file", "-e", f"{sha}^{{commit}}"], cwd=cwd, capture_output=True).returncode == 0


def merge_base(a: str, b: str, cwd: Path) -> str:
    return git("merge-base", a, b, cwd=cwd).strip()


def diff(base: str, head: str, cwd: Path) -> str:
    return git("diff", "--no-color", "--no-ext-diff", "-U3", "-M", f"{base}...{head}", cwd=cwd)


def list_files(sha: str, cwd: Path) -> list[str]:
    return [line for line in git("ls-tree", "-r", "--name-only", sha, cwd=cwd).splitlines() if line]


def remote_url(name: str, cwd: Path) -> str | None:
    url = git("remote", "get-url", name, cwd=cwd, check=False).strip()
    return url or None


def current_branch(cwd: Path) -> str | None:
    branch = git("branch", "--show-current", cwd=cwd, check=False).strip()
    return branch or None
