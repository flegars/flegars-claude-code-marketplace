from pathlib import PurePosixPath

LINTER_CONFIGS = {
    ".php-cs-fixer.php": "php-cs-fixer",
    ".php-cs-fixer.dist.php": "php-cs-fixer",
    "phpcs.xml": "phpcs",
    "phpcs.xml.dist": "phpcs",
    "phpstan.neon": "phpstan",
    "phpstan.neon.dist": "phpstan",
    "phpstan.dist.neon": "phpstan",
    "psalm.xml": "psalm",
    "rector.php": "rector",
    "ecs.php": "easy-coding-standard",
    ".eslintrc": "eslint",
    ".eslintrc.js": "eslint",
    ".eslintrc.cjs": "eslint",
    ".eslintrc.json": "eslint",
    ".eslintrc.yml": "eslint",
    "eslint.config.js": "eslint",
    "eslint.config.mjs": "eslint",
    "eslint.config.cjs": "eslint",
    "eslint.config.ts": "eslint",
    ".prettierrc": "prettier",
    ".prettierrc.json": "prettier",
    ".prettierrc.js": "prettier",
    "prettier.config.js": "prettier",
    "biome.json": "biome",
    ".stylelintrc": "stylelint",
    ".stylelintrc.json": "stylelint",
    "ruff.toml": "ruff",
    ".ruff.toml": "ruff",
    ".flake8": "flake8",
    ".golangci.yml": "golangci-lint",
    ".golangci.yaml": "golangci-lint",
    ".editorconfig": "editorconfig",
    ".rubocop.yml": "rubocop",
}


def claude_md_files(tree: list[str], changed: list[str]) -> list[str]:
    candidates = {p for p in tree if PurePosixPath(p).name == "CLAUDE.md"}
    wanted = {"CLAUDE.md"}
    for path in changed:
        for parent in PurePosixPath(path).parents:
            wanted.add(str(parent / "CLAUDE.md") if str(parent) != "." else "CLAUDE.md")
    ordered = sorted(candidates & wanted, key=lambda p: (p.count("/"), p))
    return ordered


def linters(tree: list[str]) -> list[dict]:
    found = []
    for path in tree:
        name = PurePosixPath(path).name
        if name in LINTER_CONFIGS and path.count("/") <= 1:
            found.append({"tool": LINTER_CONFIGS[name], "config": path})
    return sorted(found, key=lambda item: item["config"])
