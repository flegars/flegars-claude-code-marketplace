---
name: review-pr
description: "Review de code d'une Pull Request / Merge Request : relève des problèmes concrets en commentaires inline (sévérité, justification, proposition), poste une synthèse unique mise à jour à chaque passage, sans jamais approuver ni noter. Applique les CLAUDE.md du repo relu, confronte le diff aux US rattachées, signale les correctifs récents écrasés. GitHub (et GitHub Enterprise), Azure DevOps et GitLab via leur CLI officielle (gh, az, glab) ; mode local universel (rapport Markdown + JSON) pour toute autre plateforme ou sans authentification ; --dry-run montre le payload natif sans rien poster. Déclencher quand l'utilisateur dit : /review-pr, 'review cette PR', 'review cette MR', 'fais une review', 'relis ma branche', 'review en local', 'dry-run de la review', ou fournit une URL de PR GitHub / Azure DevOps ou de MR GitLab."
user_invocable: true
argument-hint: "[url|numéro|branche] [--platform github|ado|gitlab|local] [--base <branche>] [--dry-run] [--request-changes]"
---

# Review PR

Review de code orientée problèmes : chaque commentaire inline vise des lignes du diff, porte une sévérité
(`bloquant` | `important` | `suggestion` | `question`), une justification vérifiable et une proposition. Une
synthèse unique accompagne les commentaires. Aucune note, aucune approbation.

Architecture : un **cœur** neutre (agent `pr-reviewer` + scripts `prr/core`) et des **adaptateurs** de
plateforme (`prr/adapters`). Le skill ne fait qu'orchestrer.

```
PRR="${CLAUDE_PLUGIN_ROOT}/skills/review-pr/scripts/prr.py"
```

## Arguments

```
/review-pr [url|numéro|branche] [--platform github|ado|gitlab|local] [--base <branche>] [--dry-run] [--request-changes]
```

| Argument | Effet |
|---|---|
| `url` / `numéro` / `branche` | PR ou MR à relire. Omis : PR ouverte de la branche courante. |
| `--platform` | Force la plateforme. Sinon : `.claude/pr-reviewer.json`, puis URL / remote `origin`, sinon `local`. |
| `--base` | Branche cible du mode local (défaut : branche par défaut du remote). |
| `--dry-run` | N'écrit rien sur la plateforme : rapport local + payloads natifs qui auraient été envoyés. |
| `--request-changes` | Traduit un verdict `blocking` en statut natif « changements demandés ». Sans cette option, la review n'est **jamais** bloquante. |
| `--local` *(déprécié)* | Alias de `--platform local`. |
| `--inline` *(déprécié)* | Ignoré : publier sur la PR est le comportement par défaut. Le signaler à l'utilisateur. |

Configuration du repo relu : `${CLAUDE_PLUGIN_ROOT}/skills/review-pr/references/config.md`.

## Phase 1 — Collecte

Depuis la racine du clone du repo relu :

```bash
python3 "$PRR" collect [--platform <p>] [--ref <url|numéro|branche>] [--base <branche>]
```

Le script détecte la plateforme, vérifie la CLI et son authentification, récupère la PR, calcule le diff en
local, liste les CLAUDE.md à charger, les linters configurés et les risques de régression. Il renvoie un JSON.

- `ok: false` → afficher `error` à l'utilisateur et s'arrêter.
- Afficher chaque entrée de `messages` telle quelle. Si `fallback` est renseigné, la review continue **en mode
  local** : le dire clairement, avec la commande d'authentification (`fallback.auth_command`) quand elle existe.
- Garder `work_dir`, `context_file` et `agent_review_file` pour la suite.

## Phase 2 — Analyse par le cœur

Déléguer à l'agent `pr-reviewer` (`subagent_type: pr-reviewer:pr-reviewer`) avec ce prompt :

> Dossier du plugin : `${CLAUDE_PLUGIN_ROOT}`.
> `context_file` : `<context_file>`.
> `output_file` : `<agent_review_file>`.
> Lis d'abord `review-rules.md` puis `review-format.md` dans `${CLAUDE_PLUGIN_ROOT}/skills/review-pr/references/`,
> puis produis la review au format `agent-review.json`.

Ne rien ajouter qui concerne la plateforme : le cœur n'en a pas besoin.

Vérifier ensuite que `<agent_review_file>` existe. Sinon, relancer l'agent une fois en lui rappelant le chemin.

## Phase 3 — Publication

```bash
python3 "$PRR" publish --work-dir <work_dir> [--dry-run] [--request-changes]
```

Le script valide la review, ajoute les questions de régression, écarte les lignes hors diff vers la synthèse,
plafonne les commentaires inline (en gardant les plus sévères), retire ceux déjà postés, puis :

- **plateforme distante** : publie directement, sans confirmation préalable — une review inline et la synthèse
  (créée, ou mise à jour si elle existe déjà) ;
- **`local`** : écrit `reviews/<nom>-<horodatage>.md` et `.json` dans le repo relu ;
- **`--dry-run`** : écrit les mêmes fichiers plus `…-payload.json`, et ne fait **aucun appel d'écriture**.

Si `error` commence par « Review invalide », renvoyer la liste d'erreurs à l'agent `pr-reviewer` pour qu'il
corrige `<agent_review_file>`, puis relancer `publish` une seule fois.

## Phase 4 — Restitution

Afficher en français, sans recopier tout le JSON :

- le mode (`posted`, `local` ou `dry-run`) et la plateforme ;
- le verdict, le nombre de commentaires par sévérité, le nombre de commentaires postés en inline, le nombre déjà
  présents (`already_posted`) ;
- les liens (`url` de la PR) ou les chemins des fichiers écrits ;
- les `messages` (avertissements, repli de `REQUEST_CHANGES`, statut indisponible sur l'instance…) ;
- en `local` et en `--dry-run` : le contenu du rapport Markdown ; en `--dry-run`, les payloads natifs (`payloads`).

## Règles transverses

- **Langue** : tout en français.
- **Jamais d'approbation**, quel que soit le verdict.
- **Non bloquant par défaut** : seul `--request-changes` produit un statut bloquant, et seulement si le verdict
  est `blocking`.
- **Idempotence** : relancer la review sur la même PR ne reposte pas un commentaire déjà présent sur la même
  plage et met à jour la synthèse existante.
- **Aucun token** : le plugin s'appuie uniquement sur `gh`, `az` ou `glab` déjà authentifiés.
- **Une PR par invocation.**
