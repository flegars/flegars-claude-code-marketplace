---
name: backend-specialist
description: "Lance l'expert back-end PHP/Symfony du projet courant : analyse les patterns existants, qualifie le régime simplicité ↔ SOLID (jetable vs pérenne), propose une solution alignée et (optionnellement) implémente le code. Orchestre un flow en 6 phases : cadrage du besoin → qualification du régime → vérification stack → cartographie des patterns → délégation à l'agent backend-specialist → sortie. Déclencher quand l'utilisateur dit : /backend-specialist, 'propose une solution Symfony alignée', 'implémente cette feature côté back', 'analyse mon back', ou veut une intervention back-end qui respecte strictement les patterns du repo."
user_invocable: true
---

# Backend Specialist

Orchestre une intervention back-end PHP/Symfony qui s'aligne **strictement** sur les patterns du projet courant, en arbitrant explicitement le curseur **simplicité ↔ SOLID** en début de flow. Le plugin garantit que l'agent ne propose / n'implémente rien sans avoir d'abord lu la codebase **et** sans avoir confirmé le régime applicable.

## Vue d'ensemble du flow

1. **Cadrage** — Comprendre le besoin (analyse / proposition / implémentation)
2. **Qualification du régime** — Code jetable / utilitaire (régime `simple`) vs code pérenne / cœur métier (régime `perenne`)
3. **Vérification de la stack** — Symfony + extensions, DDD/CQRS, API Platform, Doctrine
4. **Cartographie des patterns** — Architecture, conventions, tests
5. **Intervention** — Déléguer à l'agent `backend-specialist` avec le contexte collecté
6. **Sortie** — Restituer / écrire le résultat selon le mode choisi

---

## Phase 1 — Cadrage

Si l'utilisateur n'a pas fourni de besoin en argument du slash command, demander via `AskUserQuestion` :

**« Quel est le besoin back-end à traiter ? »**

Une fois la réponse obtenue, déterminer le **mode** via `AskUserQuestion` :

- **`analyse`** — Cartographier les patterns back du projet, sans rien modifier.
- **`proposition`** — Produire un plan + des snippets prêts à coller, à valider par l'utilisateur. Aucun fichier touché.
- **`implementation`** — Produire la proposition, la faire valider, puis écrire / éditer les fichiers concernés.

Reformuler le besoin en 3-5 lignes et confirmer via `AskUserQuestion` : « Ma reformulation est-elle correcte ? » (Oui / Non, je précise).

---

## Phase 2 — Qualification du régime simplicité ↔ SOLID

Cette phase est **obligatoire et toujours explicite**, même si le besoin semble évident. Le régime conditionne tout le reste.

Poser via `AskUserQuestion` :

**« Quel régime appliquer pour cette intervention ? »**

- **`simple` — code jetable, utilitaire, one-shot, hors cœur métier** (recommandé pour : commande CLI ponctuelle, script de migration, fix ciblé, utilitaire interne, code à durée de vie < 6 mois). L'agent privilégiera la solution la plus directe et listera explicitement les abstractions volontairement non posées.
- **`perenne` — code cœur métier, contrat public, longue durée de vie** (recommandé pour : nouvelle feature dans le Domain, endpoint API exposé, refacto d'un service partagé, code qui sera maintenu et étendu). L'agent appliquera SOLID strictement et respectera les patterns hexagonal / CQRS du projet.

> ⚠️ Le régime est **arbitré une seule fois** au début. Si en cours d'analyse l'agent détecte un mismatch (ex : régime `simple` demandé alors que le périmètre touche le Domain), il s'arrêtera et le skill devra reposer la question.

### Heuristique d'aide à la décision (si l'utilisateur hésite)

Si l'utilisateur répond « je ne sais pas » via le bouton "Other", proposer la grille suivante :

| Signal | Régime indiqué |
|---|---|
| Le code va vivre **moins de 6 mois** | `simple` |
| Le code est lu / appelé par **un seul caller** identifié | `simple` |
| Pas de contrat public (API, event) à la sortie | `simple` |
| Touche au **Domain** ou à la couche **Application** | `perenne` |
| Expose un **endpoint API** ou un **event** consommé en aval | `perenne` |
| Sera **maintenu et étendu** sur 1-3 ans | `perenne` |
| Le projet a une obligation **réglementaire / financière** sur la zone | `perenne` |

En cas de doute persistant, défaut à `perenne`.

---

## Phase 3 — Vérification de la stack

Lire rapidement :

- `composer.json` — versions PHP, Symfony, doctrine/orm, api-platform/core, symfony/messenger, symfony/security-bundle, phpstan/phpstan, phpunit/phpunit.
- `config/services.yaml` et `config/packages/*.yaml` — buses Messenger, transports, API Platform, Doctrine, Security.
- `README.md` du projet pour le contexte.

Synthétiser :

- Version PHP et Symfony.
- ORM (Doctrine ORM ? DBAL direct ?).
- CQRS : Messenger configuré avec command.bus / query.bus / event.bus, ou pas du tout.
- API : API Platform Resources ? Controllers classiques ? Mix ?
- Tests : PHPUnit, présence d'intégration, présence de fixtures, PHPStan/Psalm.

---

## Phase 4 — Cartographie des patterns

Identifier les conventions du projet **avant** d'appeler l'agent. Cette phase nourrit le prompt de l'agent.

1. **Structure de dossiers**
   - `Glob src/*` pour repérer : `Domain/`, `Application/`, `Infrastructure/`, `UI/`, `Controller/`, `Entity/`, `Repository/`, `Resource/`, `Command/`, `Query/`, `Handler/`.
   - Identifier si le projet suit DDD/hexagonal (séparation `Domain` / `Application` / `Infrastructure`) ou plus classique (`Controller` / `Service` / `Entity` / `Repository`).

2. **Fichiers représentatifs**
   - 1 point d'entrée (Controller ou API Resource).
   - 1 Command + Handler si CQRS (ou 1 Service applicatif sinon).
   - 1 entité Domain.
   - 1 Repository (Doctrine).
   - 1 test (unitaire ou fonctionnel).
   - Les lire via `Read` pour confirmer les patterns.

3. **CQRS / Messenger**
   - Lire `config/packages/messenger.yaml`.
   - Identifier les buses, leur routing, les middlewares.
   - Confirmer la convention `__invoke` ou méthode nommée dans les Handlers.

4. **API Platform**
   - Resources DTO séparées des entités ou pas ?
   - Providers / Processors thin (≤ 30 lignes) qui routent vers Commands ?
   - Filtres et state options observés.

5. **Tests**
   - Outil (PHPUnit), structure (`tests/Unit/`, `tests/Integration/`, `tests/Functional/`).
   - Présence de PHPStan (`phpstan.neon`, niveau).
   - Conventions (`testFoo()` vs `it_does_x()`).

6. **Sécurité**
   - Voters dans `src/Security/Voter/` ?
   - Attributs `#[IsGranted]` ou `Security` ?
   - Keycloak ou autre IdP ?

7. **Domain Events / Outbox**
   - Y a-t-il une table outbox ?
   - Domain events dispatchés via Messenger ou via un dispatcher custom ?
   - Subscribers / Listeners et leur convention de placement.

Synthétiser cette cartographie en notes courtes (chemins de fichiers + 1-2 lignes par item).

Si un domaine n'est pas observable, le noter explicitement (l'agent en tiendra compte au lieu d'inventer).

---

## Phase 5 — Intervention via l'agent backend-specialist

Déléguer à l'agent `backend-specialist` via le tool `Agent` (subagent_type=`backend-specialist`).

**Prompt à fournir à l'agent** — inclure :
- Le besoin reformulé et confirmé en Phase 1
- Le **régime** confirmé en Phase 2 (`simple` ou `perenne`) — c'est l'input le plus important
- Le mode choisi (`analyse` / `proposition` / `implementation`)
- La cartographie de la Phase 4 (chemins + observations courtes)
- Le périmètre d'édition autorisé si mode `implementation` (dossiers / fichiers que l'agent peut toucher)

L'agent retourne :
- Mode `analyse` → rapport markdown structuré.
- Mode `proposition` → plan + fichiers impactés + snippets + alternatives + risques + (en régime `simple`) liste des abstractions non posées.
- Mode `implementation` → fichiers édités via `Write`/`Edit` + résumé des changements + checks lancés (PHPStan, PHPUnit ciblé).

### Validation intermédiaire en mode `implementation`

Avant que l'agent écrive le moindre fichier, le skill doit présenter la proposition de l'agent à l'utilisateur via `AskUserQuestion` :

**« Appliquer cette proposition ? »**
- **Oui, applique tout** → l'agent passe en `implementation`.
- **Oui, mais en ajustant** → l'utilisateur précise, l'agent reformule.
- **Non, on s'arrête là** → on s'arrête en mode `proposition`.

### Si l'agent signale un mismatch de régime

Si l'agent indique en cours d'analyse que le périmètre touche du cœur métier alors que le régime est `simple` (ou inversement), reposer la question de Phase 2 à l'utilisateur avant de continuer.

---

## Phase 6 — Sortie

Selon le mode :

- **`analyse`** — Restituer le rapport inline. Si l'utilisateur le demande, proposer d'écrire dans `docs/backend-patterns.md` (mais pas par défaut).
- **`proposition`** — Restituer inline. Si l'utilisateur veut conserver la proposition, proposer d'écrire dans `docs/proposals/backend-<slug>.md`.
- **`implementation`** — Lister les fichiers touchés avec leur diff résumé + résultats des checks (PHPStan, PHPUnit). Proposer (sans agir) de commiter via le skill `git-workflow` si disponible.

---

## Règles transverses

- **Langue** : tout le flow et toutes les questions sont en français.
- **Pas d'écriture prématurée** : aucun fichier modifié avant validation explicite en Phase 5.
- **Pas d'invention de pattern** : si la cartographie de la Phase 4 ne suffit pas à trancher une décision, l'agent demande ou liste l'ambiguïté comme « Question ouverte » dans sa sortie.
- **Régime toujours explicite** : aucune intervention sans régime confirmé en Phase 2. Si le régime change en cours de route, reposer la question.
- **Périmètre respecté** : l'agent n'édite jamais en dehors du périmètre autorisé fourni dans le prompt.
- **Une seule intervention par invocation** : si le besoin couvre plusieurs sujets, proposer à l'utilisateur de découper et relancer le skill par sujet.
