from .adapters import PARSERS

CONFIG_HINT = ('Crée `.claude/pr-reviewer.json` à la racine du repo, par exemple '
               '`{"platform": "github", "host": "github.mon-entreprise.fr"}` '
               "(platform : github | ado | gitlab | local), ou passe `--platform`.")


def _from_url(url: str, parse_name: str) -> dict | None:
    for platform, module in PARSERS.items():
        parsed = getattr(module, parse_name)(url)
        if parsed and module.is_known_host(parsed["host"]):
            return {"platform": platform, "host": parsed["host"]}
    return None


def _host_of(url: str | None) -> str | None:
    if not url:
        return None
    for module in PARSERS.values():
        parsed = module.parse_pr_url(url) or module.parse_remote(url)
        if parsed:
            return parsed["host"]
    return None


def detect(option: str | None, config: dict, ref: str | None, origin_url: str | None) -> dict:
    if option:
        return {"platform": option, "host": config.get("host") or _host_of(ref) or _host_of(origin_url),
                "reason": f"option --platform {option}"}
    if config.get("platform"):
        return {"platform": config["platform"], "host": config.get("host") or _host_of(origin_url),
                "reason": "fichier .claude/pr-reviewer.json"}
    if ref and ref.startswith("http"):
        found = _from_url(ref, "parse_pr_url")
        if found:
            return {**found, "reason": f"URL de PR ({found['host']})"}
    if origin_url:
        found = _from_url(origin_url, "parse_remote")
        if found:
            return {**found, "reason": f"remote origin ({found['host']})"}
        host = _host_of(origin_url) or origin_url
        return {"platform": "local", "host": None,
                "reason": f"domaine du remote origin non reconnu ({host}) : bascule en mode local. {CONFIG_HINT}"}
    return {"platform": "local", "host": None, "reason": "aucun remote origin : mode local."}
