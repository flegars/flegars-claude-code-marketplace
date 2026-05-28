# flegars-claude-code-marketplace

Marketplace personnelle de plugins [Claude Code](https://claude.com/claude-code).

## Installation

Ajouter la marketplace dans Claude Code :

```bash
/plugin marketplace add legars-florian/flegars-claude-code-marketplace
```

> Remplacer par l'URL ou le chemin local effectif si la marketplace n'est pas (encore) publiée sur GitHub :
>
> ```bash
> /plugin marketplace add /Users/florian/projects/perso/flegars-claude-code-marketplace
> ```

Puis installer un plugin :

```bash
/plugin install <nom-du-plugin>@flegars-perso-marketplace
```

## Plugins disponibles

### [`codebase-to-us`](./plugins/codebase-to-us)

> Rédige des User Stories standardisées à partir de l'analyse de la codebase courante.

**À quoi ça sert** — Transformer un besoin métier (forward US) ou une feature déjà implémentée (reverse US) en User Story complète, ancrée dans le code existant. Toutes les US produites suivent **systématiquement** la même structure figée, ce qui garantit cohérence et exhaustivité d'une US à l'autre.

**Ce que ça apporte :**

- **Slash command `/write-us-from-code`** — Orchestre un flow en 4 phases :
  1. **Cadrage** — Reformulation du besoin et choix forward / reverse US
  2. **Exploration codebase** — Identification des fichiers, endpoints, entités et events concernés
  3. **Rédaction** — Délégation à l'agent `us-writer` avec le contexte collecté
  4. **Sortie** — Écriture dans `docs/user-stories/US-<domaine>-<slug>.md`, rendu inline, ou les deux
- **Agent `us-writer`** — Un Product Owner senior virtuel, rigoureux, qui rédige l'US en suivant à la lettre le template du plugin. Lit la codebase avant d'écrire (jamais de comportement supposé), marque toute hypothèse `[HYPOTHÈSE]`, et liste les questions ouvertes en fin d'US.
- **Template d'US figé** — Structure imposée : Titre `[Domaine] Verbe + Complément` / Description En tant que… / Contexte & Règles métier (avec sous-bloc « Comportement actuel observé dans la codebase ») / Critères d'acceptance Gherkin (nominal + alternatifs + erreurs + bords) / Spécifications techniques / Maquettes / Dépendances / Scope IN-OUT / Estimation en story points / Questions ouvertes.

**Quand l'utiliser** — Avant de démarrer une feature pour formaliser la spec, ou pour rattraper la documentation d'une feature existante.

### [`pr-reviewer`](./plugins/pr-reviewer)

> Review standardisée de Pull Requests GitHub ou Azure DevOps avec note /20, ressenti global, axes d'amélioration et alignement avec les User Stories rattachées.

**À quoi ça sert** — Produire des reviews de PR **reproductibles** : même grille, même structure, même rigueur quel que soit le repo. Le plugin se branche sur les connexions déjà disponibles (`gh` CLI pour GitHub, MCP `devops` pour Azure DevOps) pour récupérer la PR, son diff et ses User Stories / work items rattachés, puis confronte le code livré à ce que demandent les specs.

**Ce que ça apporte :**

- **Slash command `/review-pr [url] [--inline|--local]`** — Orchestre un flow en 5 phases :
  1. **Cible** — Détection auto via la branche courante (`gh pr view`) ou MCP `devops`, sinon URL passée en argument
  2. **Fetch** — PR + diff + US/work items rattachés (parsing `closes #N` côté GitHub, liens explicites côté Azure)
  3. **Détection stack** — `composer.json` / `package.json` / `go.mod` / `pyproject.toml` pour activer la sous-grille adaptative
  4. **Analyse** — Délégation à l'agent `pr-reviewer` avec tout le contexte
  5. **Sortie** — Commentaires inline + commentaire global sur la PR (mode `--inline`) ou fichier `reviews/PR-<id>.md` (mode `--local`)
- **Agent `pr-reviewer`** — Un reviewer senior multi-stack rigoureux, qui suit à la lettre la grille et le template figés du plugin. Cite des lignes précises (`path:line`), propose des fix copiables, refuse d'inventer des patterns « du projet » qu'il n'aurait pas lus.
- **Grille de notation hybride /20** — 14 points universels (qualité, sécurité, tests, lisibilité, **alignement US**, architecture) + 6 points adaptatifs activés selon la stack détectée (Symfony/DDD, Go, TypeScript/React, Python, ou fallback générique).
- **Template de rapport figé** — Structure imposée : titre `📊 Score: X/20 — <ressenti>` / 📋 Alignement avec les US / ✅ Points forts / ⚠️ Axes d'amélioration par sévérité (Critique / Important / Mineur) / 🐛 Problèmes critiques si applicable / 📚 Conformité architecture (sous-grille adaptative) / 💡 Recommandations actionnables / 🧮 Détail du score.

**Quand l'utiliser** — Pour reviewer une PR ouverte (avant ou après merge), pour standardiser les reviews d'équipe, ou pour s'auto-évaluer avant de demander une review humaine.

### [`frontend-specialist`](./plugins/frontend-specialist)

> Expert front-end React qui analyse les patterns du projet avant toute proposition et n'invente jamais une convention qui n'existe pas dans la codebase.

**À quoi ça sert** — Intervenir sur une codebase React (analyse, proposition ou implémentation) en s'alignant **strictement** sur les patterns observés : structure de dossiers, hooks custom, lib d'état (Redux / Zustand / Tanstack Query), conventions de tests (RTL / Vitest / Jest), styling. L'agent lit le code avant de proposer, et signale explicitement quand un pattern n'est pas observable plutôt que de l'inventer.

**Ce que ça apporte :**

- **Slash command `/frontend-specialist`** — Orchestre un flow en 5 phases :
  1. **Cadrage** — Reformulation du besoin et choix du mode (`analyse` / `proposition` / `implementation`)
  2. **Vérification stack** — Détection React + bundler + TS + lib d'état + lib de tests, mise en garde si Next.js / React Native (hors périmètre validé)
  3. **Cartographie des patterns** — Structure de dossiers, hooks, gestion d'état, tests, styling, typage — chaque item ancré sur des fichiers du repo
  4. **Intervention** — Délégation à l'agent `frontend-specialist` avec toute la cartographie
  5. **Sortie** — Rapport inline, proposition à valider, ou édition effective des fichiers (avec validation intermédiaire avant écriture)
- **Agent `frontend-specialist`** — Un développeur front senior qui refuse d'inventer un pattern : toute affirmation pointe un fichier précis (`src/path/file.tsx:42`). Présente des alternatives quand plusieurs approches sont raisonnables, recommande une option, et liste les risques.
- **Checklist de cartographie figée** — Référence `react-pattern-checklist.md` qui guide systématiquement l'analyse : stack, structure, composition, hooks, état (local/partagé/serveur), effets, erreurs, tests, typage, styling. Format de synthèse standardisé pour nourrir l'agent.

**Quand l'utiliser** — Onboarder sur une codebase React inconnue (mode `analyse`), préparer une feature front avec un plan validé avant code (mode `proposition`), ou implémenter directement une feature qui respecte les conventions du repo (mode `implementation`).

### [`backend-specialist`](./plugins/backend-specialist)

> Expert back-end PHP/Symfony qui privilégie la solution la plus simple alignée sur les patterns du projet, et applique SOLID strictement sur le code pérenne.

**À quoi ça sert** — Intervenir sur une codebase PHP/Symfony (analyse, proposition ou implémentation) avec un curseur **simplicité ↔ SOLID** arbitré explicitement en début de flow. L'agent ne complexifie jamais « pour le plaisir » : en régime `simple` (code jetable / utilitaire / one-shot), il défend la solution la plus directe et liste explicitement les abstractions volontairement non posées. En régime `perenne` (cœur métier / contrat public / longue durée de vie), il applique SOLID et les patterns hexagonal/CQRS du projet sans concession.

**Ce que ça apporte :**

- **Slash command `/backend-specialist`** — Orchestre un flow en 6 phases :
  1. **Cadrage** — Reformulation du besoin et choix du mode (`analyse` / `proposition` / `implementation`)
  2. **Qualification du régime** — `simple` vs `perenne`, avec une grille d'aide à la décision si l'utilisateur hésite
  3. **Vérification stack** — PHP + Symfony + Doctrine + API Platform + Messenger + tests + PHPStan
  4. **Cartographie des patterns** — Architecture (DDD/hexagonal ou classique), CQRS, API Platform, Doctrine, sécurité, Domain Events / outbox — chaque item ancré sur des fichiers du repo
  5. **Intervention** — Délégation à l'agent `backend-specialist` avec toute la cartographie + le régime
  6. **Sortie** — Rapport inline, proposition à valider, ou édition effective des fichiers (avec validation intermédiaire avant écriture, et checks PHPStan / PHPUnit ciblés)
- **Agent `backend-specialist`** — Un développeur back senior qui s'arrête et signale tout mismatch entre le régime déclaré et le périmètre réel (ex : régime `simple` demandé alors que le périmètre touche `src/Domain/`). En régime `simple`, il trace explicitement les abstractions non posées. En régime `perenne`, il applique SRP / OCP / LSP / ISP / DIP et respecte les patterns hexagonal/CQRS du projet.
- **Référence figée d'arbitrage `simplicity-vs-solid.md`** — Définition des deux régimes, tableau de décision rapide, liste des mismatches typiques, format de traçabilité des abstractions non posées.
- **Checklist de cartographie figée `symfony-pattern-checklist.md`** — Guide systématique : stack, structure, CQRS/Messenger, API Platform, Doctrine, tests, sécurité, Domain Events / outbox, conventions de code. Format de synthèse standardisé pour nourrir l'agent.

**Quand l'utiliser** — Pour toute intervention back où il faut éviter à la fois le **sur-engineering** (couches inutiles sur un script one-shot) et la **dette technique** (raccourcis SOLID sur du cœur métier). En particulier : nouvelle feature dans le Domain, refacto d'un service partagé, script CLI ponctuel, fix sur cœur métier.

### [`daily-activity`](./plugins/daily-activity)

> Récapitule l'activité Azure DevOps de l'utilisateur courant sur les dernières 24 heures glissantes.

**À quoi ça sert** — Préparer son daily, retrouver ce sur quoi on a touché avant un changement de contexte, ou auditer ses propres traces. Le plugin agrège **Pull Requests** (créées / mergées / commentées / en attente de review), **commits**, **work items** (créés / changés / commentés) et **threads de PR** (commentaires postés + réponses reçues). Source primaire : la **CLI `az`** avec l'extension `azure-devops` (org `INTERINVEST` par défaut). **Fallback** sur le MCP `devops` si `az` n'est pas installé / non authentifié. Read-only par construction (`list` / `show` / `query` / `az rest --method get` uniquement) : aucune écriture côté ADO.

**Ce que ça apporte :**

- **Slash command `/daily-activity [--hours=N] [--project=<name>] [--org=<org>] [--save]`** — Orchestre un flow en 4 phases :
  1. **Préparation** — Calcul de la fenêtre `now − N heures`, sélection de la source (`az` → MCP fallback), résolution de `@me`
  2. **Collecte multi-projets** — Pour chaque projet de l'org : PRs (`az repos pr list --creator/--reviewer`), commits (`az rest` sur `_apis/git/repositories/.../commits`), work items (`az boards query --wiql`), threads PR (`az rest` sur `.../pullRequests/<id>/threads`), groupés en parallèle quand possible
  3. **Filtrage côté client** — Re-filtrage strict sur la fenêtre `[since, now]` pour garantir la cohérence, déduplication des PRs croisées
  4. **Restitution** — Rapport markdown inline (par défaut) ou sauvegarde dans `daily-activity/YYYY-MM-DD.md` avec `--save`
- **Format de rapport figé** — Structure imposée : en-tête (fenêtre, org, utilisateur, projets scannés, source utilisée) / **📊 Résumé** chiffré / **🟢 Pull Requests** groupées par type d'implication / **📝 Commits** groupés par repo / **🎯 Work Items** par type d'action / **💬 Threads PR** (postés + réponses à traiter) / **⏱️ Timeline chronologique inversée** / **⚠️ Limitations** explicites si collecte partielle.
- **Robustesse** — Bascule automatique `az → MCP` si la CLI n'est pas opérationnelle (binaire / extension / auth / accès org), tolérance aux échecs partiels (un projet inaccessible n'arrête pas le flow, il est listé dans `⚠️ Limitations`), troncature à 200 caractères des extraits de commentaires, masquage automatique des secrets détectés, fallback explicite pour les commits si l'endpoint REST ne répond pas (dérivation depuis les PRs).

**Quand l'utiliser** — Le matin avant le daily standup, le soir avant de fermer la machine, ou n'importe quand pour répondre à « qu'est-ce que j'ai poussé hier ? ». Particulièrement utile après un context-switch entre plusieurs projets.

**Pré-requis** — `az` CLI installé (`brew install azure-cli`) + extension `azure-devops` (`az extension add --name azure-devops`) + authentification (`az login` puis `az devops login --org https://dev.azure.com/<org>`). Si l'un manque, le plugin bascule automatiquement sur le MCP `devops`.

## Structure

```
flegars-claude-code-marketplace/
├── .claude-plugin/
│   └── marketplace.json     # Manifest de la marketplace
├── plugins/
│   ├── codebase-to-us/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── agents/
│   │   │   └── us-writer.md
│   │   └── skills/
│   │       └── write-us-from-code/
│   │           ├── SKILL.md
│   │           ├── metadata.json
│   │           └── references/
│   │               └── us-template.md
│   ├── pr-reviewer/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── agents/
│   │   │   └── pr-reviewer.md
│   │   └── skills/
│   │       └── review-pr/
│   │           ├── SKILL.md
│   │           ├── metadata.json
│   │           └── references/
│   │               ├── review-template.md
│   │               └── scoring-rubric.md
│   ├── frontend-specialist/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── agents/
│   │   │   └── frontend-specialist.md
│   │   └── skills/
│   │       └── frontend-specialist/
│   │           ├── SKILL.md
│   │           ├── metadata.json
│   │           └── references/
│   │               └── react-pattern-checklist.md
│   ├── backend-specialist/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── agents/
│   │   │   └── backend-specialist.md
│   │   └── skills/
│   │       └── backend-specialist/
│   │           ├── SKILL.md
│   │           ├── metadata.json
│   │           └── references/
│   │               ├── simplicity-vs-solid.md
│   │               └── symfony-pattern-checklist.md
│   └── daily-activity/
│       ├── .claude-plugin/
│       │   └── plugin.json
│       └── skills/
│           └── daily-activity/
│               ├── SKILL.md
│               └── metadata.json
└── README.md
```

## Licence

MIT
