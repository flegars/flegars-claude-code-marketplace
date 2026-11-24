# Changelog — pr-reviewer

Format : [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/), versionnement [SemVer](https://semver.org/lang/fr/).

## [2.0.0] — 2026-11-24

Refonte : le plugin passe d'une **notation de PR** à une **review de code** qui relève des problèmes concrets en
commentaires inline, quelle que soit la plateforme d'hébergement.

### ⚠️ Changements cassants

- **Plus de note /20 ni de rapport figé.** La grille de notation (`scoring-rubric.md`), le template de rapport
  (`review-template.md`), la détection de stack et les sections « Points forts » / « Recommandations » sont
  supprimés.
- **Le commentaire global noté est remplacé** par une synthèse unique, mise à jour à chaque passage, sans note.
- **Azure DevOps passe par la CLI `az`** (extension `azure-devops`) au lieu du MCP `devops`.
- **Options** : `--inline` est ignoré (publier est le comportement par défaut) ; `--local` devient un alias
  déprécié de `--platform local`.
- **Plus de question sur le mode de sortie ni de confirmation avant publication**, y compris sur GitHub.
- **Fichiers locaux** : `reviews/PR-<id>.md` devient `reviews/<pr-id|branche>-<horodatage>.md`, accompagné d'un
  `.json` au format neutre.

### Ajouté

- Commentaires inline structurés : sévérité (`bloquant` | `important` | `suggestion` | `question`), problème,
  justification (règle CLAUDE.md, fichier existant ou commit cité), proposition.
- Application des `CLAUDE.md` **du repo relu** (racine + dossiers parents des fichiers modifiés), citation de
  la règle (`rule_ref`) dans chaque commentaire qui en découle.
- Contexte fonctionnel limité aux US / issues **rattachées directement** à la PR : critères non couverts et
  modifications hors périmètre.
- Détection de risque de régression : `git blame` des lignes remplacées, question posée quand un correctif
  (`fix`, `hotfix`, `bugfix`) les a modifiées dans les 14 derniers jours (configurable).
- Axes de review : duplication et réutilisation vérifiées dans tout le repo, interfaces (deux cas précis),
  silence sur le style couvert par un linter configuré.
- Architecture cœur / adaptateurs : format interne neutre, adaptateurs **GitHub** (une seule review via
  `POST …/pulls/{n}/reviews`), **Azure DevOps** et **GitLab** (expérimentaux).
- Détection de la plateforme : `--platform`, puis `.claude/pr-reviewer.json`, puis remote `origin` ; domaine
  inconnu → mode local.
- **Mode local** universel, sans authentification (`--platform local`, `--base`).
- **`--dry-run`** : rapport local + payloads natifs, aucun appel d'écriture.
- **`--request-changes`** : statut natif « changements demandés » si le verdict est `blocking`. Sans cette
  option, la review n'est jamais bloquante. Le plugin n'approuve jamais.
- Plafond de commentaires inline (15 par défaut), priorisés par sévérité ; surplus et lignes hors diff dans la
  synthèse.
- Idempotence : marqueur caché `<!-- pr-reviewer:v2 … -->` (et `properties` de thread sur Azure DevOps), pas de
  doublon sur la même plage, synthèse mise à jour.
- Fichier de configuration `.claude/pr-reviewer.json` (`platform`, `host`, `base`, `regression_window_days`,
  `max_inline_comments`).
- Tests (`skills/review-pr/tests`) : analyse du diff, sélection, payloads des trois adaptateurs, absence
  d'approbation, cœur sans référence de plateforme, mode local de bout en bout.

### Migration depuis la v1 (0.x)

| v1 | v2 |
|---|---|
| `/review-pr <url>` (note + commentaires) | `/review-pr <url>` (commentaires inline + synthèse) |
| `/review-pr --inline` | `/review-pr` (option ignorée) |
| `/review-pr --local` | `/review-pr --platform local` (l'ancienne forme reste acceptée) |
| Question « mode de sortie » / confirmation GitHub | Publication directe ; `--dry-run` pour voir avant de poster |
| MCP `devops` pour Azure DevOps | `az login` puis `az extension add --name azure-devops` |
| Note /20 et grille par stack | Supprimées ; la synthèse donne le nombre de problèmes par sévérité et un verdict |
| `reviews/PR-<id>.md` | `reviews/pr-<id>-<horodatage>.md` + `.json` (mode local et `--dry-run`) |

Les anciens commentaires notés de la v1 ne sont ni modifiés ni supprimés : la v2 ne gère que ses propres
commentaires, reconnus par leur marqueur.

Prérequis : Python 3.10+ (bibliothèque standard uniquement) et `git`. Pour publier : `gh`, `az` ou `glab`
authentifié.
