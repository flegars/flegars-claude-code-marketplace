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

### [`spec-writer`](./plugins/spec-writer)

> Rédaction de spec de bout en bout : User Stories standardisées (depuis la codebase **ou** un brief externe), découpage fonctionnel d'une US par critère d'acceptance enregistrable dans Azure DevOps, et découpage technique d'une US ou d'une spec en tasks par couche (back, front, infra, data, QA).

> ⚠️ **Migration depuis `us-writer`** — Le plugin s'appelait `us-writer` jusqu'en 0.3.0, et `/split-us-into-tasks` est devenu `/split-us-by-criteria`. Réinstaller : `/plugin uninstall us-writer@flegars-perso-marketplace` puis `/plugin install spec-writer@flegars-perso-marketplace`.

**À quoi ça sert** — Couvrir la production de spec de bout en bout : transformer un besoin en User Story complète et exhaustive (toujours structurée selon la **même** grille figée), puis la décomposer en plan de travail, soit fonctionnellement, soit par couche technique. Quatre points d'entrée selon l'étape :

- **Avec le code** (`/write-us-from-code`) — Rédiger l'US ancrée dans la codebase courante : forward US (feature à venir) ou reverse US (documenter une feature déjà implémentée).
- **Sans le code** (`/write-us-from-brief`) — Rédiger l'US à partir d'un brief externe (recueil de besoin, maquette, fichier, doc). Pensé pour **Claude cowork** ou le cadrage amont, quand aucun repo n'est monté.
- **Découpage fonctionnel** (`/split-us-by-criteria`) — Décomposer une US déjà rédigée en tasks atomiques rattachées à ses critères d'acceptance, et **proposer systématiquement de les créer dans Azure DevOps**, rattachées à l'US parente.
- **Découpage technique** (`/split-spec-by-layer`) — Décomposer une US **ou une spec libre** (spec technique, brief, epic) en tasks **par couche** (`BACK`, `FRONT`, `INFRA`, `DATA`, `QA`), articulées entre elles par des contrats d'interface explicites.

Chaque artefact suit un template figé — US, task fonctionnelle, task technique — pour garantir cohérence et exhaustivité d'un artefact à l'autre.

**Ce que ça apporte :**

- **Slash command `/write-us-from-code`** — US ancrée dans le code. Flow en 4 phases :
  1. **Cadrage** — Reformulation du besoin et choix forward / reverse US
  2. **Exploration codebase** — Identification des fichiers, endpoints, entités et events concernés
  3. **Rédaction** — Délégation à l'agent `us-writer` avec le contexte collecté
  4. **Sortie** — Écriture dans `docs/user-stories/US-<domaine>-<slug>.md`, rendu inline, ou les deux
- **Slash command `/write-us-from-brief`** — US à partir d'un brief, **sans accès à la codebase**. Flow en 4 phases :
  1. **Cadrage** — Reformulation du besoin (pas de forward / reverse : toujours prospectif)
  2. **Acquisition & lecture des sources** — Texte collé inline, description de maquette / UI, fichier local (`.md` / `.txt` / `.pdf`), URL de doc externe (Notion, Confluence…) récupérée via `WebFetch`, ou une **ancienne US à mettre à jour** (réécrite intégralement au format figé). Argument passé au slash command (`$ARGUMENTS`) auto-détecté : chemin / URL / texte
  3. **Rédaction** — Délégation à l'agent `us-drafter` avec la synthèse des sources
  4. **Sortie** — Écriture dans `docs/user-stories/US-<domaine>-<slug>.md`, rendu inline (défaut en cowork), ou les deux
- **Slash command `/split-us-by-criteria`** — Découpe fonctionnellement une US **déjà rédigée** en tasks, puis propose systématiquement de les enregistrer dans Azure DevOps. Flow en 4 phases :
  1. **Acquisition & cadrage** — Récupération de l'US depuis un work item Azure DevOps (`az boards work-item show`), une PR / issue GitHub (`gh`), ou un fichier `.md` local (fallback) ; choix du mode de découpage (fonctionnel pur / ancré codebase)
  2. **Découpage** — Délégation à l'agent `criteria-splitter` qui produit une liste ordonnée de tasks
  3. **Validation** — Présentation et ajustement du découpage (fusionner, scinder, réordonner, ré-estimer)
  4. **Enregistrement Azure DevOps** — Création des tasks via `az boards work-item create` (org `INTERINVEST`) et rattachement à l'US parente via `relation add --relation-type parent`, avec **garde-fou de confirmation** avant toute écriture (seul skill mutant de la marketplace)
- **Slash command `/split-spec-by-layer`** — Découpe une US ou une spec libre en tasks techniques par couche. **Lecture seule** côté Azure DevOps / GitHub. Flow en 4 phases :
  1. **Acquisition & cadrage** — Source auto-détectée (work item Azure DevOps, issue / PR GitHub, fichier `.md`, texte collé) et qualifiée US ou spec libre ; choix du mode (spec pure / ancré codebase), des couches actives et de l'unité d'estimation (heures / story points)
  2. **Découpage** — Délégation à l'agent `layer-splitter`
  3. **Validation** — Tableau récapitulatif, ordre d'implémentation, matrice de couverture et totaux par couche ; ajustements (fusionner, scinder, changer de couche, ré-estimer, revoir un contrat)
  4. **Sortie** — Rendu inline, fichier `docs/specs/<slug>-tech-tasks.md` (jamais d'écrasement silencieux), ou les deux
- **Agent `us-writer`** — Product Owner senior virtuel qui **lit la codebase** avant d'écrire (jamais de comportement supposé), suit à la lettre le template, marque toute hypothèse `[HYPOTHÈSE]` et liste les questions ouvertes.
- **Agent `us-drafter`** — Le pendant « sans code » : même rigueur, mais rédige à partir des seules sources fournies. Ne présume jamais d'un comportement système que le brief n'affirme pas ; le moindre trou du brief devient une question ouverte plutôt qu'une invention.
- **Agent `criteria-splitter`** — Découpe une US validée en tasks atomiques : couverture intégrale des critères d'acceptance (aucun critère orphelin), dépendances et ordre d'implémentation explicites, estimation par task, et mapping vers les fichiers du code en mode ancré codebase.
- **Agent `layer-splitter`** — Lead technique full-stack virtuel : une seule couche par task, contrats d'interface (API, event, schéma, configuration) définis une seule fois dans la task productrice et référencés par les consommatrices, ordre `DATA → BACK → FRONT` avec `INFRA` en parallèle et `QA` en dernier, stack réelle détectée en mode ancré codebase (jamais de chemin inventé).
- **Template d'US figé (partagé par les deux commandes de rédaction)** — Structure imposée : Titre `[Domaine] Verbe + Complément` / Description En tant que… / Contexte & Règles métier (avec, selon l'origine, un sous-bloc « Comportement actuel observé dans la codebase » **ou** « Sources analysées ») / Critères d'acceptance Gherkin (nominal + alternatifs + erreurs + bords) / Spécifications techniques / Maquettes / Dépendances / Scope IN-OUT / Estimation en story points / Questions ouvertes.
- **Template de task fonctionnelle figé** — Structure imposée pour chaque task issue du découpage : Titre `[Domaine] Verbe court` / Description / Definition of Done (checklist) / Critères d'acceptance couverts / Fichiers concernés (mode ancré codebase) / Dépendances / Estimation.
- **Template de task technique figé** — Référentiel **fermé** de 5 couches (`BACK` / `FRONT` / `INFRA` / `DATA` / `QA`) avec règles de frontière (tests unitaires dans la couche de dev, migration en `DATA`, déclaration de flag en `INFRA`…) et **socle de Definition of Done par couche**. En-tête imposé : source / stack / exigences recensées (Gherkin ou `EX-XX`) / tableau récapitulatif / ordre et lots parallélisables / matrice de couverture / totaux. Bloc de task imposé : Titre `[COUCHE][Domaine] Verbe + complément` / Objectif & périmètre IN-OUT / Exigences couvertes / Contrat d'interface / Détails d'implémentation / Definition of Done (socle + spécifique) / Dépendances / Estimation / Risques.

**Quand l'utiliser** — `/write-us-from-code` avant de démarrer une feature sur un repo existant, ou pour rattraper la doc d'une feature en place. `/write-us-from-brief` en amont (PO/PM sans code sous la main), en Claude cowork, ou pour formaliser une maquette / un compte-rendu de réunion en spec. `/split-us-by-criteria` une fois l'US validée, pour la transformer en plan de travail fonctionnel et créer les tasks dans Azure DevOps. `/split-spec-by-layer` pour préparer la répartition entre développeurs back, front, data, ops et QA, à partir d'une US ou d'une spec technique.

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

### [`codebase-toolkit`](./plugins/codebase-toolkit)

> Boîte à outils pour travailler sur la codebase courante en s'alignant strictement sur ses patterns : experts back Symfony et front React, feature fullstack pilotée par un contrat d'API, audit back-end, cartographie d'onboarding et traçage d'un flux de bout en bout.

> ⚠️ **Migration** — Ce plugin regroupe les anciens plugins `frontend-specialist`, `backend-specialist` et `audit-codebase` (noms de skills et d'agents inchangés). Les désinstaller (`/plugin uninstall <nom>@flegars-perso-marketplace`), puis `/plugin install codebase-toolkit@flegars-perso-marketplace`. Les commandes complètes sont préfixées : `/codebase-toolkit:backend-specialist`, etc.

**À quoi ça sert** — Intervenir sur un repo existant sans jamais inventer de convention : chaque skill lit le code avant de proposer, ancre ses affirmations sur `path:line` et signale explicitement ce qui n'est pas observable. Six points d'entrée :

- **Comprendre** — `/map-codebase` (cartographie d'onboarding du repo) et `/trace-flow` (suivi d'un flux réel, de l'écran à la base de données).
- **Intervenir** — `/backend-specialist` (Symfony, curseur simplicité ↔ SOLID), `/frontend-specialist` (React) et `/fullstack-specialist` (feature back + front autour d'un contrat d'API validé d'abord).
- **Évaluer** — `/audit-codebase` (audit back-end module par module).

Les trois agents (`backend-specialist`, `frontend-specialist`, `flow-tracer`) sont mutualisés : `/map-codebase`, `/audit-codebase` et `/fullstack-specialist` délèguent aux deux spécialistes plutôt que de dupliquer leur expertise.

**Ce que ça apporte :**

#### Expert back-end — `/backend-specialist`

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

#### Expert front-end — `/frontend-specialist`

- **Slash command `/frontend-specialist`** — Orchestre un flow en 5 phases :
  1. **Cadrage** — Reformulation du besoin et choix du mode (`analyse` / `proposition` / `implementation`)
  2. **Vérification stack** — Détection React + bundler + TS + lib d'état + lib de tests, mise en garde si Next.js / React Native (hors périmètre validé)
  3. **Cartographie des patterns** — Structure de dossiers, hooks, gestion d'état, tests, styling, typage — chaque item ancré sur des fichiers du repo
  4. **Intervention** — Délégation à l'agent `frontend-specialist` avec toute la cartographie
  5. **Sortie** — Rapport inline, proposition à valider, ou édition effective des fichiers (avec validation intermédiaire avant écriture)
- **Agent `frontend-specialist`** — Un développeur front senior qui refuse d'inventer un pattern : toute affirmation pointe un fichier précis (`src/path/file.tsx:42`). Présente des alternatives quand plusieurs approches sont raisonnables, recommande une option, et liste les risques.
- **Checklist de cartographie figée** — Référence `react-pattern-checklist.md` qui guide systématiquement l'analyse : stack, structure, composition, hooks, état (local/partagé/serveur), effets, erreurs, tests, typage, styling. Format de synthèse standardisé pour nourrir l'agent.

#### Feature fullstack — `/fullstack-specialist`

- **Slash command `/fullstack-specialist`** — Feature back Symfony + front React, **contrat d'API d'abord**. Flow en 6 phases :
  1. **Cadrage** — Besoin, mode (`analyse` / `proposition` / `implementation`), régime back (`simple` / `perenne`), emplacement du front (même repo ou autre repo). Accepte en entrée un découpage `/spec-writer:split-spec-by-layer` et reprend ses contrats
  2. **Vérification des stacks** — Symfony côté back, React côté front ; arrêt explicite si un côté est hors périmètre ; repérage des conventions API existantes (format d'erreur, pagination, casse, client API front)
  3. **Contrat d'API** — Rédigé selon le template figé et **validé par l'utilisateur avant toute délégation**
  4. **Délégation en parallèle** — `backend-specialist` produit le contrat, `frontend-specialist` le consomme ; validation intermédiaire avant toute écriture ; retour au contrat si un agent le juge irréalisable
  5. **Contrôle de cohérence** — Tableau ✅ / ❌ par opération : route, champs de requête et de réponse, codes d'erreur traités à l'écran, sécurité, pagination
  6. **Sortie** — Selon le mode, avec checks ciblés des deux côtés
- **Template figé `api-contract-template.md`** — Un bloc par opération : sécurité / requête (types, obligatoire, nullable, validations) / réponse / erreurs avec leur traitement front attendu / compatibilité / exemple. Aligné sur les conventions observées, cohérent avec la section « Contrat d'interface » de `spec-writer`.

#### Audit back-end — `/audit-codebase`

- **Slash command `/audit-codebase [--modules=<liste>] [--full]`** — Orchestre un flow en 6 phases :
  1. **Cadrage** — Périmètre : toute la codebase / liste de modules / un seul module
  2. **Vérification stack** — PHP + Symfony + Doctrine + API Platform + Messenger + tests + PHPStan (arrêt explicite si stack non Symfony)
  3. **Auto-détection des modules** — Bounded contexts DDD si présents, fallback sur dossiers métier de `src/`, ou bundles
  4. **Confirmation** — L'utilisateur valide ou ajuste la liste des modules à auditer
  5. **Audit module par module** — Délégation à l'agent `backend-specialist` (en régime `perenne`, mode `analyse`) avec la grille d'audit figée en input
  6. **Agrégation & sortie** — Fusion des findings dans le template, écriture dans `docs/audit/<YYYY-MM-DD>-audit-codebase.md` (jamais d'écrasement)
- **Grille d'audit figée `audit-grid.md`** — 6 axes obligatoires par module, dans l'ordre : ✅ **Points forts à conserver** (boussole pour les évolutions futures) / ⚠️ **Risques & dette technique** (god classes, fuites de couche, magic strings, sécurité, TODO/FIXME) / 🪓 **Opportunités de simplification** (interfaces à 1 impl, indirections gratuites, DDD cargo-cult, abstractions prématurées — avec condition de vérification systématique avant de proposer de retirer) / 🧪 **Tests & qualité** (couverture par couche, fragilité, sur-mock, PHPStan, fixtures) / 🚀 **Performance & scalabilité** (N+1, pagination absente, sync vs async Messenger, sérialisation) / 🧭 **Cohérence architecturale** (couches étanches, CQRS effectif, Domain Events bien câblés). Chaque finding est ancré sur `path:line`, avec **sévérité** (`bloquant`/`important`/`mineur`) et **effort** (`S`/`M`/`L`).
- **Template figé du rapport `audit-template.md`** — Structure imposée : front-matter YAML / titre / 🧭 **Synthèse exécutive** (Top 3 forces/risques/simplifications + tableau de scoring qualitatif par axe) / 🗺️ **Cartographie générale** (stack + architecture + tableau des modules) / 📦 **Audit module par module** (un sous-bloc complet avec les 6 axes par module, dans l'ordre) / 🔁 **Recommandations transverses** (findings inter-modules) / 🛣️ **Roadmap suggérée** (Court / Moyen / Long terme — chaque finding une seule fois) / ⚠️ **Limitations de l'audit** (ce qui n'a pas été couvert, traçabilité).
- **Réutilisation du `backend-specialist`** — Pas d'agent dédié dupliqué : le skill délègue chaque module à l'agent `backend-specialist` du même plugin, avec la grille en input et le format de sortie imposé par le template.

#### Cartographie d'onboarding — `/map-codebase`

- **Slash command `/map-codebase [sous-dossier]`** — Lecture seule. Flow en 5 phases :
  1. **Cadrage** — Périmètre (repo entier / sous-dossier) et public (nouvel arrivant / revue d'architecture)
  2. **Détection de stack** — `composer.json`, `package.json`, Docker, Makefile, CI, `.env.dist` (noms de variables uniquement)
  3. **Cartographie** — Déléguée **en parallèle** à `backend-specialist` et `frontend-specialist` (mode `analyse`, avec leurs checklists), le skill couvrant lui-même le transverse (démarrage, CI/CD, variables, services externes, diagramme d'architecture)
  4. **Assemblage** — Selon le template figé
  5. **Sortie** — Inline et/ou `docs/codebase-map.md` (jamais d'écrasement silencieux)
- **Template figé `codebase-map-template.md`** — 11 sections : stack / démarrage rapide / architecture (Mermaid) / modules / flux principaux / conventions back et front / tests / CI/CD & déploiement / glossaire métier / pièges & zones de dette / limitations. Toute affirmation est ancrée `path:line` ou marquée `[NON VÉRIFIÉ]` ; aucun secret recopié.

#### Traçage de flux — `/trace-flow`

- **Slash command `/trace-flow <point d'entrée>`** — Lecture seule. Point d'entrée : route HTTP / URL, composant front, commande console, message Messenger, ou description fonctionnelle (au plus 3 candidats proposés). Flow en 4 phases :
  1. **Cadrage** — Scénario (nominal ou une erreur précise) et profondeur (frontière du repo ou appels sortants décrits)
  2. **Résolution du point d'entrée** — Localisé dans le code et confirmé par l'utilisateur, jamais deviné
  3. **Traçage** — Délégation à l'agent `flow-tracer`
  4. **Sortie** — Inline et/ou `docs/flows/<slug>.md`
- **Agent `flow-tracer`** — Suit le chemin d'exécution fichier après fichier ; une étape n'existe que si elle a été lue, et toute incertitude (plusieurs handlers possibles, appel dynamique, code hors repo) est marquée `[RUPTURE]` avec la façon de la lever.
- **Template figé `flow-template.md`** — Résumé / point d'entrée / diagramme de séquence Mermaid / tableau des étapes `# | Couche | Fichier:ligne | Rôle | Données` / effets de bord (base, events, appels externes, frontière transactionnelle) / branches d'erreur / points d'attention / fichiers lus.

**Quand l'utiliser** — `/map-codebase` à l'arrivée sur un repo ou avant une revue d'architecture. `/trace-flow` pour déboguer, préparer une revue ou rédiger une US à partir d'un comportement existant. `/backend-specialist` et `/frontend-specialist` pour une intervention d'un seul côté qui doit éviter à la fois le sur-engineering et la dette. `/fullstack-specialist` dès qu'une feature exige un endpoint et un écran. `/audit-codebase` pour un état des lieux back-end ou pour cadrer un chantier de réduction de complexité.

### [`daily-activity`](./plugins/daily-activity)

> Récapitule l'activité GitHub de l'utilisateur courant sur les dernières 24 heures glissantes.

**À quoi ça sert** — Préparer son daily, retrouver ce sur quoi on a touché avant un changement de contexte, ou auditer ses propres traces. Le plugin agrège **Pull Requests** (créées / mergées / reviewées / commentées / en attente de review), **commits**, **issues** (créées / fermées / commentées) et **threads de review** (commentaires postés + réponses reçues). Source unique : la **CLI `gh`** — recherche globale (`gh search prs|commits|issues`), API REST (`gh api`) et **feed d'événements utilisateur** (`/users/<login>/events`) comme socle de collecte. Read-only par construction (`gh search`, `gh api` en GET, `git log`) : aucune écriture côté GitHub.

**Ce que ça apporte :**

- **Slash command `/daily-activity [--hours=N] [--repo=<owner/name>] [--org=<org>] [--host=<hostname>] [--save]`** — Orchestre un flow en 4 phases :
  1. **Préparation** — Calcul de la fenêtre `now − N heures`, vérification de `gh` (binaire / auth / scopes / quota API), résolution de l'identité (`gh api user`)
  2. **Collecte** — Feed d'événements comme socle (`PushEvent`, `PullRequestEvent`, `PullRequestReviewEvent`, `IssueCommentEvent`…), croisé avec les recherches ciblées (`--author=@me`, `--reviewed-by=@me`, `--review-requested=@me`, `--commenter=@me`) et les threads de review (`/pulls/<n>/comments`, `/reviews`)
  3. **Filtrage côté client** — Re-filtrage strict sur la fenêtre `[since, now]` (les qualifiers de recherche s'appliquent à la journée et à la dernière mise à jour globale, pas à l'action précise), déduplication des PRs croisées
  4. **Restitution** — Rapport markdown inline (par défaut) ou sauvegarde dans `daily-activity/YYYY-MM-DD.md` avec `--save`
- **Format de rapport figé** — Structure imposée : en-tête (fenêtre, compte + hôte, périmètre) / **📊 Résumé** chiffré / **🟢 Pull Requests** groupées par type d'implication / **📝 Commits** groupés par dépôt / **🎯 Issues** par type d'action / **💬 Threads de review** (postés + réponses à traiter) / **⏱️ Timeline chronologique inversée** / **⚠️ Limitations** explicites si collecte partielle.
- **Robustesse** — Garde-fou multi-comptes (`gh auth status` : le rapport ne reflète que le compte actif, rappelé dans l'en-tête pour éviter le faux rapport vide sur un compte perso/pro EMU), garde-fou coût sur le quota API (`gh api rate_limit`), tolérance aux échecs partiels (un dépôt inaccessible n'arrête pas le flow, il est listé dans `⚠️ Limitations`), troncature à 200 caractères des extraits de commentaires, masquage automatique des secrets détectés, chaîne de fallback explicite pour les commits (feed d'événements → `gh search commits`, qui n'indexe que la branche par défaut → `git log` local).

**Quand l'utiliser** — Le matin avant le daily standup, le soir avant de fermer la machine, ou n'importe quand pour répondre à « qu'est-ce que j'ai poussé hier ? ». Particulièrement utile après un context-switch entre plusieurs dépôts.

**Pré-requis** — GitHub CLI installé (`brew install gh`) et authentifié (`gh auth login`), avec au minimum le scope `repo` (et `read:org` pour `--org`). En multi-comptes, vérifier le compte actif avec `gh auth status` et basculer avec `gh auth switch --user <login>`. Pour une instance GitHub Enterprise, passer `--host=<hostname>`.

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
│   ├── spec-writer/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── agents/
│   │   │   ├── us-writer.md          # US ancrée dans le code
│   │   │   ├── us-drafter.md         # US à partir d'un brief (sans code)
│   │   │   ├── criteria-splitter.md  # découpage fonctionnel d'une US par critère
│   │   │   └── layer-splitter.md     # découpage technique par couche
│   │   └── skills/
│   │       ├── write-us-from-code/
│   │       │   ├── SKILL.md
│   │       │   ├── metadata.json
│   │       │   └── references/
│   │       │       └── us-template.md   # template d'US figé partagé par les deux skills de rédaction
│   │       ├── write-us-from-brief/
│   │       │   ├── SKILL.md
│   │       │   └── metadata.json
│   │       ├── split-us-by-criteria/
│   │       │   ├── SKILL.md
│   │       │   ├── metadata.json
│   │       │   └── references/
│   │       │       └── task-template.md        # template de task fonctionnelle figé
│   │       └── split-spec-by-layer/
│   │           ├── SKILL.md
│   │           ├── metadata.json
│   │           └── references/
│   │               └── tech-task-template.md   # template de task technique figé
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
│   ├── codebase-toolkit/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── agents/
│   │   │   ├── backend-specialist.md
│   │   │   ├── frontend-specialist.md
│   │   │   └── flow-tracer.md          # traçage d'un flux (lecture seule)
│   │   └── skills/
│   │       ├── backend-specialist/
│   │       │   ├── SKILL.md
│   │       │   ├── metadata.json
│   │       │   └── references/
│   │       │       ├── simplicity-vs-solid.md
│   │       │       └── symfony-pattern-checklist.md
│   │       ├── frontend-specialist/
│   │       │   ├── SKILL.md
│   │       │   ├── metadata.json
│   │       │   └── references/
│   │       │       └── react-pattern-checklist.md
│   │       ├── fullstack-specialist/
│   │       │   ├── SKILL.md
│   │       │   ├── metadata.json
│   │       │   └── references/
│   │       │       └── api-contract-template.md
│   │       ├── audit-codebase/
│   │       │   ├── SKILL.md
│   │       │   ├── metadata.json
│   │       │   └── references/
│   │       │       ├── audit-grid.md
│   │       │       └── audit-template.md
│   │       ├── map-codebase/
│   │       │   ├── SKILL.md
│   │       │   ├── metadata.json
│   │       │   └── references/
│   │       │       └── codebase-map-template.md
│   │       └── trace-flow/
│   │           ├── SKILL.md
│   │           ├── metadata.json
│   │           └── references/
│   │               └── flow-template.md
│   ├── daily-activity/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   └── skills/
│   │       └── daily-activity/
│   │           ├── SKILL.md
│   │           └── metadata.json
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
