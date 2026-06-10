# us-developer

> Développe une User Story au **périmètre strict** : ni plus, ni moins, avec une traçabilité critère d'acceptation → code → test.

## À quoi ça sert

Transformer une User Story (US) en code livré, en respectant **exactement** ce que l'US spécifie :

- **Rien de moins** : chaque critère d'acceptation doit être couvert par au moins un test, ou explicitement signalé comme non couvert avec une raison.
- **Rien de plus** : pas de feature « bonus », pas de refactor opportuniste, pas de modification hors périmètre, même si un bug est repéré à côté.

La commande gère **4 types de sources d'US** avec auto-détection :

1. **Lien GitHub** (issue ou PR) → récupération via la CLI `gh`, fallback API REST publique.
2. **Lien Azure DevOps** (work item) → récupération via le MCP `devops`, fallback `az boards work-item show`, fallback API REST avec PAT.
3. **Chemin de fichier `.md`** → lecture locale.
4. **Markdown collé directement** → utilisé tel quel.

Si le type de source ne peut pas être identifié sans ambiguïté, la commande **demande** à l'utilisateur (pas de devinette).

## Ce que ça apporte

- **Slash command `/us-developer:develop-us <source> [--auto]`** — Orchestre un flow en 7 étapes avec deux gates explicites :

  1. **Acquisition** — Détection auto du type de source, récupération du contenu brut.
  2. **Extraction structurée** — Objectif métier / Périmètre IN / Périmètre OUT / Critères d'acceptation testables (`AC-XX`) / Contraintes techniques explicites / Zones non spécifiées.
  3. **Gate clarification** — Stop si aucun critère identifié, ambiguïté bloquante ou contradiction interne. Pose les questions, jamais de périmètre inventé.
  4. **Plan** — Exploration codebase (CLAUDE.md, conventions) puis tableau de mapping `critère → fichiers à créer/modifier → test(s) prévu(s)`.
  5. **Gate validation** — Stop par défaut sur le plan + journal des hypothèses provisoire. **Si `--auto`** est présent : enchaîne sans s'arrêter (le gate clarification de l'étape 3 reste actif).
  6. **Implémentation** — Code écrit dans le thread principal, périmètre strict respecté.
  7. **Vérification + Rapport** — Test par critère, lint/typecheck, revue par `us-reviewer`, rapport final avec couverture, journal des hypothèses, hors-périmètre délibéré, bugs repérés non corrigés.

- **Agent `us-analyst`** — Lecture seule. Acquisition + extraction structurée + plan ancré dans la codebase. Ne devine jamais, signale toute ambiguïté.

- **Agent `us-reviewer`** — Lecture seule. Vérifie la couverture critère → test, l'absence de code hors-périmètre, l'exhaustivité du journal des hypothèses et la non-régression. Verdict ✅ / ⚠️ / ❌.

## Quand l'utiliser

- À chaque démarrage d'implémentation d'une US existante (GitHub issue, ADO work item, spec markdown).
- Pour éviter à la fois le **sur-périmètre** (« tant que j'y suis ») et le **sous-périmètre** (un critère oublié).
- Pour produire automatiquement un **rapport de traçabilité** critère → code → test à joindre à la PR.

## Pré-requis (et fallbacks)

| Source | Outil principal | Fallback 1 | Fallback 2 |
|---|---|---|---|
| **GitHub** | `gh` CLI authentifiée (`gh auth status`) | API REST publique `curl` (limites de rate, repos privés inaccessibles) | s'arrêter et demander |
| **Azure DevOps** | MCP `devops` (org INTERINVEST par défaut) | `az boards work-item show` | API REST + PAT (demandé à l'utilisateur) |
| **Fichier `.md`** | `Read` | — | — |
| **Markdown inline** | passage direct | — | — |

Tout fallback utilisé est signalé dans la section `⚠️ Limitations` du rapport final.

## Exemples

### Exemple 1 — GitHub issue

```text
/us-developer:develop-us https://github.com/elvest-engineering/foo-service/issues/142
```

Flow :

1. `gh issue view 142 --repo elvest-engineering/foo-service` récupère l'US.
2. `us-analyst` produit le bloc structuré (4 critères `AC-01` à `AC-04`).
3. Aucune ambiguïté bloquante → on passe au plan.
4. Plan : 2 fichiers à créer (`src/Foo/CreateFooCommand.php`, `src/Foo/CreateFooHandler.php`), 1 fichier à modifier (`src/Foo/FooController.php`), 4 tests dans `tests/Foo/`.
5. Gate validation : tu approuves le plan.
6. Implémentation.
7. Tests + PHPStan verts, revue `us-reviewer` ✅, rapport final affiché.

### Exemple 2 — Azure DevOps work item, mode `--auto`

```text
/us-developer:develop-us https://dev.azure.com/INTERINVEST/CompanyManagement/_workitems/edit/1247 --auto
```

Flow :

1. MCP `devops` récupère le work item ADO #1247.
2. `us-analyst` produit le bloc structuré (3 critères `AC-01` à `AC-03`, 1 ambiguïté bloquante : « format exact du code d'erreur »).
3. **Gate clarification activé même en `--auto`** : la commande s'arrête et te demande le format.
4. Tu réponds → reprise.
5. Plan produit, **pas de pause** (à cause de `--auto`).
6. Implémentation.
7. Vérification + rapport.

### Exemple 3 — Fichier markdown local

```text
/us-developer:develop-us docs/user-stories/US-societe-creer-avec-validation-siret.md
```

Flow identique aux précédents, source lue depuis le disque.

### Exemple 4 — Markdown collé directement

```text
/us-developer:develop-us "# [Société] Créer une société avec validation SIRET

En tant que partenaire authentifié...

## Critères d'acceptance
- Étant donné un SIRET valide...
- Étant donné un SIRET invalide..."
```

Le contenu est utilisé tel quel.

## Le flag `--auto`

Par défaut, la commande s'arrête au **gate de validation** (étape 5) pour te laisser confirmer le plan avant écriture.

Avec `--auto`, ce gate est **désactivé** : la commande enchaîne directement sur l'implémentation après le plan.

⚠️ Ce qui **reste actif** même avec `--auto` :

- Le **gate clarification** (étape 3) — si un critère d'acceptation est manquant ou ambigu, la commande s'arrête quand même. Le strict ne se négocie pas.
- Le **rapport final** complet — couverture critère par critère, journal des hypothèses, hors-périmètre, etc.

Utilise `--auto` quand :

- L'US est très claire (zéro ambiguïté attendue)
- Tu fais confiance au plan automatique pour cette nature de tâche
- Tu lis le rapport final attentivement pour valider à posteriori

N'utilise **pas** `--auto` quand :

- L'US est complexe ou touche le cœur métier
- Le repo a des conventions qui peuvent piéger l'agent (architecture hexagonale stricte, code legacy, contraintes invisibles dans `CLAUDE.md`)
- Tu veux pouvoir ajuster le plan avant que le code soit écrit

## Règles non négociables

1. **Pas de gold-plating** — Ne rien ajouter qui ne soit pas demandé par l'US.
2. **Pas d'omission silencieuse** — Tout critère est couvert ou explicitement marqué non couvert avec raison.
3. **Hypothèses tracées** — Toute décision technique non spécifiée par l'US apparaît dans le journal des hypothèses.
4. **Critère ambigu = stop** — Demander, jamais trancher en silence.
5. **Pas de modif hors périmètre** — Même si un bug est repéré à côté, il est signalé dans le rapport, pas corrigé.

## Installation

```bash
/plugin marketplace add legars-florian/flegars-claude-code-marketplace
/plugin install us-developer@flegars-perso-marketplace
```

Ou en local pendant le développement :

```bash
/plugin marketplace add /Users/florian/projects/perso/flegars-claude-code-marketplace
/plugin install us-developer@flegars-perso-marketplace
```

## Licence

MIT
