import re
from dataclasses import dataclass, field

_HUNK_HEADER = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


@dataclass
class DiffLine:
    kind: str
    old_line: int | None
    new_line: int | None
    hunk: int


@dataclass
class FileDiff:
    old_path: str | None
    new_path: str | None
    right: dict[int, DiffLine] = field(default_factory=dict)
    left: dict[int, DiffLine] = field(default_factory=dict)
    hunks: list[list[DiffLine]] = field(default_factory=list)

    @property
    def path(self) -> str:
        return self.new_path or self.old_path or ""


def _strip_prefix(raw: str) -> str | None:
    raw = raw.split("\t", 1)[0].strip()
    if raw.startswith('"') and raw.endswith('"'):
        raw = raw[1:-1]
    if raw == "/dev/null":
        return None
    if raw.startswith(("a/", "b/")):
        return raw[2:]
    return raw


def parse_unified_diff(text: str) -> dict[str, FileDiff]:
    files: dict[str, FileDiff] = {}
    current: FileDiff | None = None
    old_no = new_no = old_left = new_left = 0

    def register(diff: FileDiff | None) -> None:
        if diff is not None and diff.path:
            files[diff.path] = diff

    for line in text.splitlines():
        if line.startswith("diff --git "):
            register(current)
            current = FileDiff(old_path=None, new_path=None)
            old_left = new_left = 0
            continue
        if current is None:
            continue
        if old_left == 0 and new_left == 0:
            match = _HUNK_HEADER.match(line)
            if match:
                old_no, new_no = int(match.group(1)), int(match.group(3))
                old_left = int(match.group(2)) if match.group(2) is not None else 1
                new_left = int(match.group(4)) if match.group(4) is not None else 1
                current.hunks.append([])
            elif not current.hunks:
                if line.startswith("--- "):
                    current.old_path = _strip_prefix(line[4:])
                elif line.startswith("+++ "):
                    current.new_path = _strip_prefix(line[4:])
                elif line.startswith("rename from "):
                    current.old_path = line[len("rename from "):]
                elif line.startswith("rename to "):
                    current.new_path = line[len("rename to "):]
            continue
        hunk_index = len(current.hunks) - 1
        if line.startswith("\\"):
            continue
        if line.startswith("+"):
            entry = DiffLine("added", None, new_no, hunk_index)
            current.right[new_no] = entry
            new_no += 1
            new_left -= 1
        elif line.startswith("-"):
            entry = DiffLine("deleted", old_no, None, hunk_index)
            current.left[old_no] = entry
            old_no += 1
            old_left -= 1
        else:
            # Certains outils retirent l'espace initial des lignes de contexte vides.
            entry = DiffLine("context", old_no, new_no, hunk_index)
            current.right[new_no] = entry
            current.left[old_no] = entry
            old_no += 1
            new_no += 1
            old_left -= 1
            new_left -= 1
        current.hunks[-1].append(entry)
    register(current)
    return files


def locate(files: dict[str, FileDiff], path: str, line_start: int, line_end: int, side: str) -> list[DiffLine] | None:
    diff = files.get(path)
    if diff is None or line_start > line_end:
        return None
    index = diff.right if side == "RIGHT" else diff.left
    covered = [index.get(n) for n in range(line_start, line_end + 1)]
    if any(entry is None for entry in covered):
        return None
    if len({entry.hunk for entry in covered}) != 1:
        return None
    return covered


def changed_paths(files: dict[str, FileDiff]) -> list[str]:
    return sorted(files)
