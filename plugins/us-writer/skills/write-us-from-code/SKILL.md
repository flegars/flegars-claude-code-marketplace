---
name: write-us-from-code
description: "Rédige une User Story standardisée à partir de l'analyse de la codebase courante. Orchestre un flow en 4 phases : cadrage du besoin → exploration codebase → rédaction via l'agent us-writer → sortie (fichier docs/user-stories/ ou inline). Toutes les US suivent obligatoirement la structure figée du plugin. Déclencher quand l'utilisateur dit : /write-us-from-code, 'écris une US', 'rédige une US à partir du code', 'transforme ce besoin en User Story', ou veut formaliser une feature en spec ancrée dans le code existant."
user_invocable: true
argument-hint: "[description du besoin | domaine + feature à spécifier]"
---

# Write US From Code

Orchestre la rédaction d'une User Story standardisée à partir de l'analyse de la codebase courante. Le résultat suit **systématiquement** la structure figée définie dans `references/us-template.md`.

## Vue d'ensemble du flow

1. **Cadrage** — Comprendre le besoin (forward US ou reverse US)
2. **Exploration codebase** — Identifier le code concerné
3. **Rédaction** — Déléguer à l'agent `us-writer` avec le contexte collecté
4. **Sortie** — Demander où écrire le résultat (fichier, inline, ou les deux)

---

## Phase 1 — Cadrage

Si l'utilisateur n'a pas fourni de description en argument du slash command, demander via `AskUserQuestion` :

**« Quel est le besoin métier à transformer en US ? »**

Une fois la réponse obtenue, déterminer le **mode** via `AskUserQuestion` :

- **Forward US** — L'US décrit une feature à venir (codebase = contexte/contraintes existantes).
- **Reverse US** — L'US documente une feature **déjà implémentée** (pour rattrapage documentaire).

Reformuler le besoin en 3-5 lignes (persona, déclencheur, résultat attendu) et confirmer avec `AskUserQuestion` : « Ma reformulation est-elle correcte ? » (Oui / Non, je précise).

---

## Phase 2 — Exploration codebase

Identifier les artefacts du code pertinents pour l'US **avant** de la rédiger.

1. **Stack du projet** — Lire rapidement `composer.json`, `package.json`, `README.md`, ou équivalent, pour identifier la techno et adapter les spécifications techniques.
2. **Recherche ciblée** — Selon le besoin formulé :
   - Endpoints API existants liés → `Grep` sur les routes / contrôleurs
   - Entités / agrégats concernés → `Glob` sur `src/Domain/`, `src/Entity/`, etc.
   - Events / messages liés → `Grep` sur `Event`, `Message`, `Handler`
   - Tests existants couvrant la zone → `Glob` sur `tests/`
3. **Comportement actuel** — `Read` les 2-5 fichiers les plus pertinents pour comprendre le comportement existant.

Garder en mémoire :
- La liste des fichiers consultés (avec lignes pertinentes : `path/file.php:42`)
- Le résumé du comportement actuel observé
- Le **gap fonctionnel** entre l'existant et le besoin

Si la codebase ne contient rien de pertinent (feature totalement neuve), le noter et continuer.

---

## Phase 3 — Rédaction via l'agent us-writer

Déléguer la rédaction à l'agent `us-writer` via le tool `Agent` (subagent_type=`us-writer`).

**Prompt à fournir à l'agent** — inclure :
- Le besoin reformulé et confirmé en Phase 1
- Le mode (forward / reverse)
- Le persona ciblé
- La synthèse de l'exploration codebase (fichiers consultés + comportement actuel observé + gap)
- L'instruction explicite : « Lire d'abord `${CLAUDE_PLUGIN_ROOT}/skills/write-us-from-code/references/us-template.md` puis rédiger l'US en suivant ce template à la lettre. »

L'agent retourne l'US complète en Markdown.

---

## Phase 4 — Sortie

Demander à l'utilisateur via `AskUserQuestion` :

**« Où écrire l'US ? »**
- **Fichier `docs/user-stories/US-<domaine>-<slug>.md` dans le repo courant** (recommandé)
- **Inline dans la conversation uniquement**
- **Les deux**

### Convention de nommage du fichier

- Domaine : extrait du titre `[Domaine] …`, en kebab-case (`Société` → `societe`, `Webhook Hubspot` → `webhook-hubspot`).
- Slug : 3-6 mots résumant l'action, en kebab-case ASCII (`creer-avec-validation-siret`).
- Nom complet : `US-<domaine>-<slug>.md` (ex : `US-societe-creer-avec-validation-siret.md`).

Si `docs/user-stories/` n'existe pas dans le repo, le créer.

### Si sortie fichier

- `Write` le fichier
- Afficher à l'utilisateur le chemin créé
- Proposer (sans agir) de commiter via le skill `git-workflow` si disponible

### Si sortie inline

Restituer directement l'US dans la réponse, formatée en Markdown.

---

## Règles transverses

- **Langue** : tout le flow et toutes les questions sont en français.
- **Pas d'écriture prématurée** : aucun fichier n'est créé avant la Phase 4.
- **Pas de devinette** : si l'exploration codebase ne suffit pas à lever une ambiguïté du besoin, l'agent `us-writer` la liste en « Questions ouvertes » dans l'US plutôt que d'inventer.
- **Une seule US par invocation** : si le besoin couvre plusieurs sujets, proposer à l'utilisateur de le découper et relancer le skill pour chaque US.
