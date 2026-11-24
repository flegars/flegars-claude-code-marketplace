SEVERITY_LABELS = {
    "bloquant": "🔴 Bloquant",
    "important": "🟠 Important",
    "suggestion": "🔵 Suggestion",
    "question": "❓ Question",
}

REASON_LABELS = {
    "out_of_diff": "hors du diff",
    "over_cap": "au-delà du plafond de commentaires inline",
}


def age_label(days: int) -> str:
    if days == 0:
        return "aujourd'hui"
    if days == 1:
        return "hier"
    return f"il y a {days} jours"


def location(comment: dict) -> str:
    lines = str(comment["line_start"]) if comment["line_start"] == comment["line_end"] \
        else f"{comment['line_start']}-{comment['line_end']}"
    suffix = " (version avant la PR)" if comment["side"] == "LEFT" else ""
    return f"{comment['path']}:{lines}{suffix}"


def comment_body(comment: dict) -> str:
    body = comment["body"]
    justification = body["justification"]
    if comment.get("rule_ref"):
        rule = comment["rule_ref"]
        justification += f"\n\n> Règle `{rule['file']}` : {rule['rule']}"
    if comment.get("evidence"):
        justification += "\n\nRéférences : " + ", ".join(f"`{e}`" for e in comment["evidence"])
    return (
        f"**{SEVERITY_LABELS[comment['severity']]}**\n\n"
        f"**Problème** — {body['problem']}\n\n"
        f"**Justification** — {justification}\n\n"
        f"**Proposition** — {body['proposal']}"
    )


def _us_section(us: dict) -> list[str]:
    if not us["found"]:
        return ["- **US** : aucune US ou work item rattaché directement à la PR."]
    label = " — ".join(filter(None, [us.get("id"), us.get("title")]))
    lines = [f"- **US** : {label}"]
    if us["uncovered_criteria"]:
        lines.append("  - Critères non couverts par le diff :")
        lines += [f"    - {item}" for item in us["uncovered_criteria"]]
    else:
        lines.append("  - Tous les critères d'acceptation identifiés sont couverts par le diff.")
    if us["out_of_scope"]:
        lines.append("  - Modifications hors du périmètre de l'US :")
        lines += [f"    - {item}" for item in us["out_of_scope"]]
    return lines


def summary_body(review: dict) -> str:
    summary = review["summary"]
    counts = summary["counts"]
    total = sum(counts.values())
    verdict = "bloquant" if review["verdict"] == "blocking" else "non bloquant"
    lines = ["## 🔎 Review pr-reviewer", "",
             f"**{total} problème(s)** — verdict **{verdict}** · "
             + " · ".join(f"{SEVERITY_LABELS[s]} : {n}" for s, n in counts.items()), ""]
    lines += _us_section(summary["us"])
    claude_md = summary["claude_md_loaded"]
    lines.append("- **CLAUDE.md chargés** : " + (", ".join(f"`{p}`" for p in claude_md) if claude_md
                                                  else "aucun CLAUDE.md dans le repo — vérifications génériques uniquement."))
    if summary.get("already_posted"):
        lines.append(f"- **Déjà signalés lors d'une review précédente** : {summary['already_posted']} (non repostés).")
    risks = summary["regression_risks"]
    lines += ["", "### Risques de régression", ""]
    if risks:
        for risk in risks:
            origin = risk["commit"][:7] + (f" ({risk['ref']})" if risk.get("ref") else "")
            lines.append(f"- `{risk['path']}:{risk['line']}` — modifié {age_label(risk['age_days'])} par {origin} : "
                         f"« {risk['subject']} »")
    else:
        lines.append("_Aucun correctif récent touché par la PR._")
    not_postable = summary["not_postable_inline"]
    lines += ["", "### Remarques non postées en inline", ""]
    if not_postable:
        for item in not_postable:
            comment = item["comment"]
            lines.append(f"- `{location(comment)}` — {SEVERITY_LABELS[comment['severity']]} "
                         f"({REASON_LABELS[item['reason']]}) — {comment['body']['problem']} "
                         f"→ {comment['body']['proposal']}")
    else:
        lines.append("_Aucune._")
    if summary["notes"]:
        lines += ["", "### Notes", ""] + [f"- {note}" for note in summary["notes"]]
    return "\n".join(lines)


def local_report(review: dict, context: dict) -> str:
    title = context.get("title") or context.get("source_branch") or "branche courante"
    header = [f"# Review — {title}", "",
              f"- Plateforme : `{context['platform']}`",
              f"- Branches : `{context.get('source_branch')}` → `{context.get('target_branch')}`",
              f"- Commit relu : `{context.get('head_sha', '')[:12]}`"]
    if context.get("url"):
        header.append(f"- PR : {context['url']}")
    lines = header + ["", summary_body(review), "", "## Commentaires inline", ""]
    if not review["comments"]:
        lines.append("_Aucun._")
    for comment in review["comments"]:
        lines += [f"### `{location(comment)}`", "", comment_body(comment), ""]
    return "\n".join(lines).rstrip() + "\n"
