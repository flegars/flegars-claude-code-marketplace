---
name: frontend-specialist
description: "Lance l'expert front-end React du projet courant : analyse les patterns existants, propose une solution alignée, et (optionnellement) implémente le code. Orchestre un flow en 5 phases : cadrage du besoin → vérification stack → cartographie des patterns → délégation à l'agent frontend-specialist → sortie (analyse / proposition / implémentation). Couvre React générique, gestion d'état (Redux / Zustand / Tanstack Query) et tests (RTL / Vitest / Jest). Déclencher quand l'utilisateur dit : /frontend-specialist, 'analyse mon front', 'propose une solution React alignée sur le projet', 'implémente cette feature côté front', ou veut une intervention front-end qui respecte strictement les patterns du repo."
user_invocable: true
---

# Frontend Specialist

Orchestre une intervention front-end React qui s'aligne **strictement** sur les patterns du projet courant. Le plugin garantit que l'agent ne propose / n'implémente rien sans avoir d'abord lu la codebase et cartographié les conventions en place.

## Vue d'ensemble du flow

1. **Cadrage** — Comprendre le besoin (analyse / proposition / implémentation)
2. **Vérification de la stack** — Confirmer que la stack du projet est dans le périmètre du plugin
3. **Cartographie des patterns** — Identifier la structure, les conventions, la lib d'état, la lib de tests
4. **Intervention** — Déléguer à l'agent `frontend-specialist` avec le contexte collecté
5. **Sortie** — Restituer / écrire le résultat selon le mode choisi

---

## Phase 1 — Cadrage

Si l'utilisateur n'a pas fourni de besoin en argument du slash command, demander via `AskUserQuestion` :

**« Quel est le besoin front-end à traiter ? »**

Une fois la réponse obtenue, déterminer le **mode** via `AskUserQuestion` :

- **`analyse`** — Cartographier les patterns React du projet, sans rien modifier. Utile pour onboarding ou audit.
- **`proposition`** — Produire un plan + des snippets prêts à coller, à valider par l'utilisateur. Aucun fichier touché.
- **`implementation`** — Produire la proposition, la faire valider, puis écrire / éditer les fichiers concernés.

Reformuler le besoin en 3-5 lignes et confirmer via `AskUserQuestion` : « Ma reformulation est-elle correcte ? » (Oui / Non, je précise).

---

## Phase 2 — Vérification de la stack

Lire rapidement :

- `package.json` — version de React, présence de `next`, lib d'état (`@reduxjs/toolkit`, `zustand`, `@tanstack/react-query`), lib de tests (`vitest`, `jest`, `@testing-library/react`), bundler (`vite`, `react-scripts`, `webpack`).
- `tsconfig.json` (si présent) — TypeScript strict ou pas.
- `README.md` du projet pour le contexte.

**Si Next.js est détecté** (`next` dans les dépendances) :
- Le signaler à l'utilisateur via `AskUserQuestion` : « Le projet utilise Next.js, qui n'est pas dans le périmètre validé de l'agent. Continuer quand même (avec une mise en garde sur les patterns server/client) ou abandonner ? »
- Si l'utilisateur choisit de continuer, garder cette mise en garde dans le contexte passé à l'agent.

**Si React Native ou Remix est détecté** : même protocole, l'agent n'est pas calibré pour ces stacks.

---

## Phase 3 — Cartographie des patterns

Identifier les conventions du projet **avant** d'appeler l'agent. Cette phase nourrit le prompt de l'agent — elle évite que l'agent doive tout (re)découvrir lui-même.

1. **Structure de dossiers**
   - `Glob` sur `src/**` pour repérer `features/`, `pages/`, `components/`, `hooks/`, `lib/`, `store/`, `api/`.
   - Noter la convention principale (`features/` ou `pages/` ? colocation ou non ?).

2. **Fichiers représentatifs**
   - 1 composant de feature (`src/features/*/...`)
   - 1 hook custom (`src/**/use*.ts` ou `.tsx`)
   - 1 test (`*.test.ts`, `*.test.tsx`, `*.spec.ts`)
   - 1 slice d'état ou queries (selon la lib utilisée)
   - Les lire via `Read` pour confirmer les patterns.

3. **Gestion d'état**
   - Si Redux Toolkit détecté → `Glob` sur `src/**/store/**`, `src/**/slices/**`, `src/**/*.slice.ts`.
   - Si Zustand → `Grep` sur `create(` issu de `zustand`.
   - Si Tanstack Query → `Grep` sur `useQuery`, `useMutation`, `QueryClient`.
   - Identifier qui gère QUOI (état UI local / état partagé / état serveur).

4. **Tests**
   - Confirmer outil (Vitest / Jest), conventions (`describe`/`it`, `render` depuis RTL vs custom render), présence de MSW.
   - Lire 1-2 tests pour calibrer le style attendu.

5. **Styling**
   - CSS Modules / Tailwind / styled-components / autre.

Synthétiser cette cartographie en notes courtes (chemins de fichiers + 1-2 lignes par item) pour la passer à l'agent.

Si la codebase est très petite ou récente et qu'un domaine n'est pas observable, le noter explicitement (l'agent en tiendra compte au lieu d'inventer).

---

## Phase 4 — Intervention via l'agent frontend-specialist

Déléguer à l'agent `frontend-specialist` via le tool `Agent` (subagent_type=`frontend-specialist`).

**Prompt à fournir à l'agent** — inclure :
- Le besoin reformulé et confirmé en Phase 1
- Le mode choisi (`analyse` / `proposition` / `implementation`)
- La cartographie de la Phase 3 (chemins + observations courtes)
- Le périmètre d'édition autorisé si mode `implementation` (dossiers / fichiers que l'agent peut toucher)
- Toute mise en garde issue de la Phase 2 (stack hors périmètre)

L'agent retourne :
- Mode `analyse` → rapport markdown structuré.
- Mode `proposition` → plan + fichiers impactés + snippets + alternatives + risques.
- Mode `implementation` → fichiers édités via `Write`/`Edit` + résumé des changements.

### Validation intermédiaire en mode `implementation`

Avant que l'agent écrive le moindre fichier, le skill doit présenter la proposition de l'agent à l'utilisateur via `AskUserQuestion` :

**« Appliquer cette proposition ? »**
- **Oui, applique tout** → l'agent passe en `implementation`.
- **Oui, mais en ajustant** → l'utilisateur précise, l'agent reformule.
- **Non, on s'arrête là** → on s'arrête en mode `proposition`.

---

## Phase 5 — Sortie

Selon le mode :

- **`analyse`** — Restituer le rapport inline dans la conversation. Si l'utilisateur le demande, proposer d'écrire dans `docs/frontend-patterns.md` (mais pas par défaut).
- **`proposition`** — Restituer inline. Si l'utilisateur veut conserver la proposition, proposer d'écrire dans `docs/proposals/frontend-<slug>.md`.
- **`implementation`** — Lister les fichiers touchés avec leur diff résumé. Proposer (sans agir) de commiter via le skill `git-workflow` si disponible.

---

## Règles transverses

- **Langue** : tout le flow et toutes les questions sont en français.
- **Pas d'écriture prématurée** : aucun fichier modifié avant validation explicite en Phase 4.
- **Pas d'invention de pattern** : si la cartographie de la Phase 3 ne suffit pas à trancher une décision, l'agent demande ou liste l'ambiguïté comme « Question ouverte » dans sa sortie.
- **Périmètre respecté** : l'agent n'édite jamais en dehors du périmètre autorisé fourni dans le prompt.
- **Une seule intervention par invocation** : si le besoin couvre plusieurs sujets, proposer à l'utilisateur de découper et relancer le skill par sujet.
