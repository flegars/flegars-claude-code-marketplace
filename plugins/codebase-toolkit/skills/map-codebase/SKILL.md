---
name: map-codebase
description: "Produit une cartographie d'onboarding de la codebase courante : stack, démarrage rapide (installer / lancer / tester), architecture avec diagramme Mermaid, modules, flux principaux, conventions back et front, tests, CI/CD, glossaire métier, pièges connus. Orchestre un flow en 5 phases : cadrage → détection de stack → cartographie déléguée en parallèle aux agents backend-specialist et frontend-specialist (mode analyse) + partie transverse → assemblage selon un template figé → sortie (inline et/ou docs/codebase-map.md). Lecture seule sur le code. Déclencher quand l'utilisateur dit : /map-codebase, 'cartographie ce repo', 'fais-moi un onboarding de la codebase', 'explique-moi l'architecture du projet', 'je découvre ce repo', 'génère une doc d'onboarding'."
user_invocable: true
argument-hint: "[sous-dossier à cartographier]"
---

# Map Codebase

Produit une **cartographie d'onboarding** de la codebase courante : ce qu'il faut savoir pour être productif sur le repo, ancré sur des fichiers réellement lus. La structure est figée dans :
`${CLAUDE_PLUGIN_ROOT}/skills/map-codebase/references/codebase-map-template.md`

Le skill **décrit**, il n'évalue pas : pour un diagnostic de dette, utiliser `/codebase-toolkit:audit-codebase` ; pour le détail d'un flux, `/codebase-toolkit:trace-flow`.

## Vue d'ensemble du flow

1. **Cadrage** — Périmètre et public visé
2. **Détection de stack** — Côtés présents (back, front, infra)
3. **Cartographie** — Déléguée aux spécialistes en parallèle + partie transverse
4. **Assemblage** — Selon le template figé
5. **Sortie** — Inline, fichier, ou les deux

---

## Phase 1 — Cadrage

Si `$ARGUMENTS` contient un chemin, l'utiliser comme périmètre. Sinon, demander via `AskUserQuestion` :

1. **« Quel périmètre cartographier ? »** — Repo entier / Un sous-dossier (préciser).
2. **« Pour qui ? »** — Nouvel arrivant (accent sur démarrage rapide, glossaire, flux) / Revue d'architecture (accent sur modules, dépendances, conventions).

---

## Phase 2 — Détection de stack

Lire (s'ils existent) : `composer.json`, `package.json` (+ `pnpm-workspace.yaml`, `turbo.json`), `go.mod`, `pyproject.toml`, `docker-compose*.yml`, `Dockerfile*`, `Makefile`, `.github/workflows/*`, `azure-pipelines*.yml`, `.gitlab-ci.yml`, `CLAUDE.md`, `README.md`, `.env.dist` / `.env.example` (noms de variables uniquement).

En déduire :
- **Back Symfony présent ?** (`symfony/framework-bundle` dans `composer.json`)
- **Front React présent ?** (`react` dans un `package.json`) — noter le chemin racine du front (monorepo).
- **Autres stacks** (Go, Python, Next.js, React Native…) : hors périmètre des spécialistes → cartographiées par le skill lui-même en surface, et signalées en « Limitations ».

Récapituler (périmètre, public, côtés détectés) et confirmer avant de lancer la cartographie.

---

## Phase 3 — Cartographie

### 3.1 — Délégation aux spécialistes (en parallèle)

Lancer **dans un même message** les appels `Agent` pertinents :

- **Back Symfony** → `subagent_type=backend-specialist`, avec :
  - mode `analyse`, régime `perenne` (on décrit du code en place) ;
  - le périmètre (chemins) ;
  - l'instruction : « Lire `${CLAUDE_PLUGIN_ROOT}/skills/backend-specialist/references/symfony-pattern-checklist.md`, cartographier selon ses 9 axes, et retourner : (1) le bloc « Format de synthèse », (2) la liste des modules (nom, rôle en une ligne, chemins, points d'entrée, dépendances), (3) 3 à 6 flux principaux (déclencheur → étapes → effet, fichiers d'entrée), (4) les pièges et zones de dette repérés, (5) les termes métier récurrents. Ancrer chaque point sur `path:line`. Ne rien modifier. »
- **Front React** → `subagent_type=frontend-specialist`, avec :
  - mode `analyse` ;
  - la racine du front ;
  - l'instruction : « Lire `${CLAUDE_PLUGIN_ROOT}/skills/frontend-specialist/references/react-pattern-checklist.md`, cartographier selon ses 10 axes, et retourner : (1) le bloc « Format de synthèse », (2) les écrans / features principaux et l'API qu'ils consomment, (3) les pièges repérés. Ancrer chaque point sur `path:line`. Ne rien modifier. »

### 3.2 — Partie transverse (traitée par le skill)

Pendant ce temps, le skill couvre lui-même :
- **Démarrage rapide** : commandes réellement présentes (Makefile, scripts `composer` / `package.json`, README, jobs CI). Ne jamais exécuter de commande qui modifie l'environnement ; une commande non exécutée est marquée `[NON VÉRIFIÉ]`.
- **CI/CD & déploiement** : pipelines, jobs, environnements, feature flags.
- **Variables d'environnement** : noms seulement, depuis `.env.dist` / `.env.example` / config.
- **Services externes** : clients HTTP, SDK, brokers, IdP repérés dans la config.
- **Architecture d'ensemble** : diagramme Mermaid des composants (front, API, bases, brokers, services externes).

---

## Phase 4 — Assemblage

Lire `${CLAUDE_PLUGIN_ROOT}/skills/map-codebase/references/codebase-map-template.md` et assembler le document **dans l'ordre exact** du template, en fusionnant :
- les retours des spécialistes (sections 4 à 7, 9, 10) ;
- la partie transverse (sections 1 à 3, 8) ;
- les limitations (section 11) : stacks hors périmètre, sous-dossiers ignorés, commandes non vérifiées.

Selon le public choisi en Phase 1, développer davantage les sections d'accueil (2, 5, 9) ou d'architecture (3, 4, 6), sans jamais en supprimer.

Contrôler avant restitution : chaque affirmation sur le code est ancrée `path:line` ou marquée `[NON VÉRIFIÉ]` ; aucune valeur de secret n'apparaît.

---

## Phase 5 — Sortie

Demander via `AskUserQuestion` : **« Où restituer la cartographie ? »**
- **Inline**
- **Fichier `docs/codebase-map.md`**
- **Les deux**

Si le fichier existe déjà : ne **jamais** l'écraser silencieusement — demander s'il faut le remplacer ou écrire `docs/codebase-map-<YYYY-MM-DD>.md`. Après écriture, proposer (sans agir) de commiter via le skill `git-workflow`.

---

## Règles transverses

- **Langue** : tout le flow, toutes les questions et le document sont en français (termes techniques standards conservés).
- **Lecture seule** sur le code : seul le fichier de sortie peut être écrit, sur confirmation.
- **Pas d'invention** : un point non observable est déclaré comme tel, jamais extrapolé.
- **Pas de secret** : variables d'environnement par nom uniquement.
