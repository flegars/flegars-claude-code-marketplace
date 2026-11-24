# Format interne neutre d'une review

Ce format est le **seul contrat** entre le cœur (agent `pr-reviewer`) et le reste du plugin. Il ne contient
aucune notion propre à une plateforme d'hébergement : la traduction vers un modèle natif est l'affaire des
adaptateurs.

## Ce que produit l'agent : `agent-review.json`

```json
{
  "comments": [
    {
      "path": "src/Billing/InvoiceService.php",
      "line_start": 40,
      "line_end": 42,
      "side": "RIGHT",
      "severity": "important",
      "category": "reuse",
      "body": {
        "problem": "Le calcul d'arrondi est réimplémenté à la main.",
        "justification": "`src/Shared/Money/Rounding.php:12` fournit déjà `Rounding::bankers()`, utilisé par 6 services.",
        "proposal": "Remplacer les lignes 40-42 par `Rounding::bankers($amount, 2)`."
      },
      "rule_ref": null,
      "evidence": ["src/Shared/Money/Rounding.php:12"]
    }
  ],
  "summary": {
    "us": {
      "found": true,
      "id": "#123",
      "title": "Exporter les factures en CSV",
      "source": "closing_issue",
      "uncovered_criteria": ["Le fichier est encodé en UTF-8 avec BOM"],
      "out_of_scope": ["src/User/ProfileController.php:15 — refonte du profil, absente de l'US"]
    },
    "claude_md_loaded": ["CLAUDE.md", "src/Billing/CLAUDE.md"],
    "notes": []
  }
}
```

### Champs d'un commentaire

| Champ | Valeurs | Règle |
|---|---|---|
| `path` | chemin relatif à la racine du repo | Tel qu'il apparaît dans le diff (côté nouvelle version, sauf fichier supprimé). |
| `line_start`, `line_end` | entiers ≥ 1 | Numéros de ligne **de la version visée par `side`**. `line_start = line_end` pour une seule ligne. Une plage doit rester dans **un seul hunk**. |
| `side` | `RIGHT` \| `LEFT` | `RIGHT` = nouvelle version (cas normal). `LEFT` = ligne supprimée, numérotée dans l'ancienne version. |
| `severity` | `bloquant` \| `important` \| `suggestion` \| `question` | Voir l'échelle ci-dessous. |
| `category` | `rule` \| `duplication` \| `reuse` \| `interface` \| `us_coverage` \| `us_scope` \| `generic` | `regression` est réservé au script de détection : ne pas l'utiliser. |
| `body.problem` | texte | Le problème, en une ou deux phrases. |
| `body.justification` | texte | Règle CLAUDE.md, fichier existant ou commit cité. Jamais « bonne pratique » sans source. |
| `body.proposal` | texte | Proposition concrète, idéalement un snippet prêt à coller. |
| `rule_ref` | `null` ou `{ "file": "…/CLAUDE.md", "rule": "citation exacte" }` | **Obligatoire** dès que le commentaire découle d'une règle d'un CLAUDE.md (et alors `category: rule`). |
| `evidence` | liste de chaînes | Chemins `fichier:ligne` ou SHA de commit qui étayent le commentaire. |

### Échelle de sévérité

| Sévérité | Quand l'utiliser |
|---|---|
| `bloquant` | Bug avéré, faille de sécurité, perte de données, violation explicite d'une règle CLAUDE.md marquée obligatoire. |
| `important` | Problème réel qui devrait être corrigé avant merge : duplication avérée, réutilisation manquée, critère d'US non couvert. |
| `suggestion` | Amélioration utile mais facultative. |
| `question` | Doute que seul l'auteur peut lever. Toujours formulée comme une question. |

Le verdict est calculé, jamais choisi : `blocking` s'il existe au moins un commentaire `bloquant`, sinon
`non_blocking`.

## Ce que produit le plugin : `review.json`

Le script `prr.py publish` complète la review de l'agent et produit le format final :

- ajoute les commentaires `question` de détection de régression ;
- calcule une empreinte (`fingerprint`) par commentaire : chemin + lignes + côté + catégorie ;
- envoie dans la synthèse (`summary.not_postable_inline`) tout commentaire hors des hunks du diff
  (`reason: out_of_diff`) ou au-delà du plafond (`reason: over_cap`), en gardant les plus sévères en inline ;
- écarte les commentaires dont l'empreinte a déjà été postée (`summary.already_posted`) ;
- calcule `summary.counts` et `verdict`.

```json
{
  "schema": "pr-reviewer/review@2",
  "verdict": "blocking | non_blocking",
  "comments": [{ "...": "champs ci-dessus", "fingerprint": "3f2a9c1d0b7e" }],
  "summary": {
    "us": { "...": "..." },
    "claude_md_loaded": ["..."],
    "notes": ["..."],
    "counts": { "bloquant": 0, "important": 1, "suggestion": 0, "question": 1 },
    "already_posted": 0,
    "regression_risks": [{ "path": "…", "line": 10, "side": "RIGHT", "commit": "…", "subject": "…", "ref": "PR #456", "age_days": 2 }],
    "not_postable_inline": [{ "reason": "out_of_diff | over_cap", "comment": { "...": "..." } }]
  }
}
```

## Rendu d'un commentaire inline

```
**🟠 Important**

**Problème** — …

**Justification** — …

> Règle `CLAUDE.md` : citation exacte (si rule_ref)

Références : `src/Shared/Money/Rounding.php:12`

**Proposition** — …
```

## Commentaire de synthèse

Un seul par PR, mis à jour à chaque exécution. Il contient : l'US détectée (ou son absence) avec les critères
non couverts et les modifications hors périmètre, les CLAUDE.md chargés (ou leur absence), le nombre de
problèmes par sévérité et le verdict, les risques de régression, les remarques non postables en inline (avec
`fichier:ligne`) et les notes.
