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
  5. **Sortie** — Commentaires inline + commentaire global sur la PR (mode `--inline`) ou fichier `reviews/PR-<id>.md` (mode `--local`). **Sur Azure DevOps, publication inline d'office** : la review est postée directement sur la PR sans redemander le mode ni confirmation préalable (`--local` pour forcer le fichier local ; GitHub garde sa confirmation avant publication)
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

### [`audit-codebase`](./plugins/audit-codebase)

> Audit back-end PHP/Symfony complet, module par module, qui produit un rapport markdown structuré.

**À quoi ça sert** — Obtenir un **état des lieux exhaustif et standardisé** d'une codebase Symfony : ce qui marche et qu'il faut conserver, ce qui pose risque ou accumule de la dette, ce qui pourrait être simplifié (code "complexe" remplaçable par un pattern plus simple), ce qui manque côté tests, ce qui risque de coûter en perf, et où l'architecture revendiquée fuit en pratique. Le rapport est volontairement **qualifié** par axe (🟢/🟡/🔴) plutôt que noté sur 20 — l'objectif est d'éclairer les décisions, pas de classer.

**Ce que ça apporte :**

- **Slash command `/audit-codebase [--modules=<liste>] [--full]`** — Orchestre un flow en 6 phases :
  1. **Cadrage** — Périmètre : toute la codebase / liste de modules / un seul module
  2. **Vérification stack** — PHP + Symfony + Doctrine + API Platform + Messenger + tests + PHPStan (arrêt explicite si stack non Symfony)
  3. **Auto-détection des modules** — Bounded contexts DDD si présents, fallback sur dossiers métier de `src/`, ou bundles
  4. **Confirmation** — L'utilisateur valide ou ajuste la liste des modules à auditer
  5. **Audit module par module** — Délégation à l'agent `backend-specialist` (en régime `perenne`, mode `analyse`) avec la grille d'audit figée en input
  6. **Agrégation & sortie** — Fusion des findings dans le template, écriture dans `docs/audit/<YYYY-MM-DD>-audit-codebase.md` (jamais d'écrasement)
- **Grille d'audit figée `audit-grid.md`** — 6 axes obligatoires par module, dans l'ordre : ✅ **Points forts à conserver** (boussole pour les évolutions futures) / ⚠️ **Risques & dette technique** (god classes, fuites de couche, magic strings, sécurité, TODO/FIXME) / 🪓 **Opportunités de simplification** (interfaces à 1 impl, indirections gratuites, DDD cargo-cult, abstractions prématurées — avec condition de vérification systématique avant de proposer de retirer) / 🧪 **Tests & qualité** (couverture par couche, fragilité, sur-mock, PHPStan, fixtures) / 🚀 **Performance & scalabilité** (N+1, pagination absente, sync vs async Messenger, sérialisation) / 🧭 **Cohérence architecturale** (couches étanches, CQRS effectif, Domain Events bien câblés). Chaque finding est ancré sur `path:line`, avec **sévérité** (`bloquant`/`important`/`mineur`) et **effort** (`S`/`M`/`L`).
- **Template figé du rapport `audit-template.md`** — Structure imposée : front-matter YAML / titre / 🧭 **Synthèse exécutive** (Top 3 forces/risques/simplifications + tableau de scoring qualitatif par axe) / 🗺️ **Cartographie générale** (stack + architecture + tableau des modules) / 📦 **Audit module par module** (un sous-bloc complet avec les 6 axes par module, dans l'ordre) / 🔁 **Recommandations transverses** (findings inter-modules) / 🛣️ **Roadmap suggérée** (Court / Moyen / Long terme — chaque finding une seule fois) / ⚠️ **Limitations de l'audit** (ce qui n'a pas été couvert, traçabilité).
- **Réutilisation du `backend-specialist`** — Pas d'agent dédié dupliqué : le skill délègue chaque module à l'agent `backend-specialist` (du plugin homonyme), avec la grille en input et le format de sortie imposé par le template. Le `backend-specialist` doit donc être installé en parallèle pour utiliser le plugin.

**Quand l'utiliser** — Pour un état des lieux à la prise de poste sur une codebase Symfony, avant un gros refacto pour identifier la dette et les simplifications, pour préparer un dossier d'arbitrage technique (« qu'est-ce qu'on garde, qu'est-ce qu'on simplifie, qu'est-ce qu'on retravaille »), ou pour cadrer un chantier de réduction de complexité.

**Pré-requis** — Le plugin `backend-specialist@flegars-perso-marketplace` doit être installé (le slash command délègue à son agent).

### [`us-developer`](./plugins/us-developer)

> Développe une User Story au périmètre **strict** (GitHub / Azure DevOps / fichier .md / markdown collé) avec traçabilité critère d'acceptation → code → test.

**À quoi ça sert** — Transformer une US (issue GitHub, work item Azure DevOps, fichier markdown local, ou markdown collé directement) en code livré, **sans dépasser ni omettre** son périmètre. Chaque critère d'acceptation est numéroté `AC-XX`, mappé à un fichier et à au moins un test. Toute décision technique non spécifiée par l'US est tracée dans un **journal des hypothèses**. Tout bug repéré à côté est listé dans le rapport, **jamais corrigé en passant**. Le résultat est un rapport markdown final qu'on peut joindre tel quel à la PR.

**Ce que ça apporte :**

- **Slash command `/us-developer:develop-us <source> [--auto]`** — Orchestre un flow en 7 étapes avec **deux gates** explicites :
  1. **Acquisition** — Auto-détection du type de source : GitHub (`gh issue/pr view` → fallback API REST), Azure DevOps (MCP `devops` → fallback `az boards work-item show` → fallback API REST + PAT), fichier `.md` local, ou markdown collé. Si ambigu, la commande **demande** plutôt que de deviner.
  2. **Extraction structurée** — 6 sections obligatoires : Objectif métier / Périmètre IN / Périmètre OUT / Critères d'acceptation reformulés testables (`AC-XX`) / Contraintes techniques explicites / Zones non spécifiées.
  3. **Gate clarification** — Stop si aucun critère identifié, ambiguïté bloquante, ou contradiction interne. Reste actif même en `--auto` — le strict ne se négocie pas.
  4. **Plan** — Exploration codebase (`CLAUDE.md`, conventions, lib de test) puis tableau de mapping `critère → fichiers (modif/création) → test(s) prévu(s)`, + décisions techniques par défaut à valider, + effets hors-périmètre identifiés, + commandes de vérification détectées.
  5. **Gate validation** — Stop par défaut (plan + journal des hypothèses provisoire à valider). Désactivé si `--auto`.
  6. **Implémentation** — Coder dans le thread principal, périmètre strict respecté, conventions du repo suivies, aucun fichier hors périmètre touché.
  7. **Vérification + Rapport** — Test par critère, lint/typecheck/LSP, revue par `us-reviewer`, rapport final avec couverture critère → code → test, journal des hypothèses, hors-périmètre délibéré, bugs hors-périmètre repérés (non corrigés).
- **Agent `us-analyst`** — Lecture seule. Acquisition + extraction structurée + plan ancré dans la codebase. Ne devine jamais : toute zone non spécifiée par l'US est signalée explicitement, toute citation de pattern « du projet » pointe un `path:line` lu.
- **Agent `us-reviewer`** — Lecture seule. Vérifie strictement : couverture critère → test (✅/⚠️/❌), absence de code en trop, hypothèses non documentées dans le diff, non-régression. Verdict tranché : `✅ conforme` / `⚠️ avec réserves` / `❌ écarts bloquants`.

**Quand l'utiliser** — Au démarrage de toute implémentation d'US existante (issue, work item, spec). Pour éviter à la fois le **sur-périmètre** (« tant que j'y suis ») et le **sous-périmètre** (un critère oublié). Pour produire automatiquement un **rapport de traçabilité** critère → code → test à joindre à la PR. Avec `--auto`, pour enchaîner sans gate intermédiaire quand l'US est claire et que le rapport final suffit comme contrôle a posteriori (le gate clarification reste actif quoi qu'il arrive).

**Pré-requis** — Au moins l'une des sources doit être accessible : `gh` CLI authentifiée pour GitHub, MCP `devops` ou `az` CLI pour Azure DevOps, ou un fichier `.md` local, ou un markdown collé.

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
│   ├── daily-activity/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   └── skills/
│   │       └── daily-activity/
│   │           ├── SKILL.md
│   │           └── metadata.json
│   ├── audit-codebase/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   └── skills/
│   │       └── audit-codebase/
│   │           ├── SKILL.md
│   │           ├── metadata.json
│   │           └── references/
│   │               ├── audit-grid.md
│   │               └── audit-template.md
│   └── us-developer/
│       ├── .claude-plugin/
│       │   └── plugin.json
│       ├── agents/
│       │   ├── us-analyst.md
│       │   └── us-reviewer.md
│       ├── commands/
│       │   └── develop-us.md
│       └── README.md
└── README.md
```

## Licence

MIT
