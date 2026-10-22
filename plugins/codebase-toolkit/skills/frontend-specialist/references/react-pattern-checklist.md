# Checklist d'analyse des patterns React du projet

Cette checklist guide la **cartographie** des conventions du projet courant. Elle est lue par le skill `/frontend-specialist` en phase 3 et par l'agent `frontend-specialist` quand il vérifie son alignement.

**Règle d'or** — chaque item de la checklist doit être renseigné par une observation **ancrée sur un fichier** (`path/file.tsx:line`). Si rien n'est observable pour un item, le noter `non observable` plutôt qu'inventer.

---

## 1. Stack & outillage

| Item | Comment vérifier | Exemple de constat |
|---|---|---|
| Version de React | `package.json` champ `dependencies.react` | `react@18.3.1` |
| Bundler | `package.json` scripts + `vite.config.ts` / `webpack.config.js` | `vite` |
| TypeScript | présence `tsconfig.json` + `strict: true` ? | `TS strict` ou `JS pur` |
| Linter / formatter | `.eslintrc*`, `.prettierrc*`, `package.json` | `eslint + prettier` |
| Gestionnaire de paquets | `package-lock.json` / `pnpm-lock.yaml` / `yarn.lock` | `pnpm` |

## 2. Structure de dossiers

| Item | Comment vérifier | Exemple de constat |
|---|---|---|
| Découpage racine | `Glob src/*` | `src/features/`, `src/components/`, `src/lib/` |
| Convention de feature | `Glob src/features/*` | colocation `feature/{Component.tsx, hook.ts, slice.ts, *.test.tsx}` |
| Tests | colocalisés ou dans `__tests__/` ou `tests/` ? | colocalisés `*.test.tsx` à côté du composant |
| Composants partagés | `src/components/`, `src/ui/`, `packages/ui/` ? | `src/components/ui/` |

## 3. Composition de composants

| Item | Comment vérifier | Exemple de constat |
|---|---|---|
| Taille moyenne | lire 3-5 composants représentatifs | ~ 80-150 lignes |
| Présentationnel vs Container | y a-t-il une séparation explicite ? | non, composants mixent UI + logique |
| Patterns récurrents | `children`, render props, slots, compound components | `compound components` pour `Tabs`, `Dialog` |
| Forms | `react-hook-form`, `formik`, contrôlé manuel ? | `react-hook-form` + `zod` resolver |

## 4. Hooks custom

| Item | Comment vérifier | Exemple de constat |
|---|---|---|
| Convention de placement | `src/hooks/`, ou par feature ? | par feature : `src/features/foo/useFoo.ts` |
| Facade au-dessus de la lib d'état | y a-t-il `useXxxQuery`/`useXxxMutation` qui encapsulent la lib ? | oui, facade Tanstack Query par domaine |
| Hooks utilitaires partagés | `useDebounce`, `useLocalStorage`, etc. | `src/hooks/useDebounce.ts` |

## 5. Gestion d'état

| Item | Comment vérifier | Exemple de constat |
|---|---|---|
| État local UI | `useState`, `useReducer` | majoritaire |
| État partagé client | Redux / Zustand / Context / autre | `zustand`, 3 stores |
| État serveur | Tanstack Query / SWR / fetch manuel | `@tanstack/react-query@5` |
| Persistance | `redux-persist`, `zustand/middleware`, localStorage manuel | `zustand/middleware/persist` |

## 6. Effets & side-effects

| Item | Comment vérifier | Exemple de constat |
|---|---|---|
| Fetchs réseau | dans hooks de query, dans `useEffect`, dans middleware ? | toujours dans Tanstack Query, pas de `useEffect` de fetch |
| Annulation | `AbortController` ? `signal` ? | géré par Tanstack Query, pas en direct |
| Abonnements externes | `useEffect` + cleanup, ou `useSyncExternalStore` ? | `useSyncExternalStore` dans un wrapper |

## 7. Gestion d'erreur

| Item | Comment vérifier | Exemple de constat |
|---|---|---|
| Error boundaries | `Grep ErrorBoundary` | `src/components/ErrorBoundary.tsx`, posé en root |
| Erreurs réseau | toast global, état `error` dans le hook, page d'erreur ? | toast global via `sonner` + état `error` exposé |
| Validation | `zod`, `yup`, manuel | `zod` + `react-hook-form` |

## 8. Tests

| Item | Comment vérifier | Exemple de constat |
|---|---|---|
| Outil | `vitest`, `jest` | `vitest` |
| Bibliothèque DOM | `@testing-library/react` | présent, custom `render` dans `test-utils.tsx` |
| Mocks réseau | MSW, `vi.mock`, `jest.mock` | `msw` v2 |
| Conventions `describe`/`it` | lire 2 tests | `describe('<Component />')` + `it('renders X when Y')` |
| Couverture | suite minimale, intégration, e2e (Playwright/Cypress) ? | unit + intégration RTL, e2e Playwright dans `e2e/` |

## 9. Typage

| Item | Comment vérifier | Exemple de constat |
|---|---|---|
| `type` vs `interface` pour les props | `Grep "type .*Props"` vs `"interface .*Props"` | `type Props = ...` partout |
| Génération types API | OpenAPI codegen, GraphQL codegen, manuel ? | `openapi-typescript`, types dans `src/api/types.ts` |
| Strict null checks | `tsconfig.json` | `strict: true` |

## 10. Styling

| Item | Comment vérifier | Exemple de constat |
|---|---|---|
| Approche | Tailwind, CSS Modules, styled-components, vanilla-extract, sass | `Tailwind` + `clsx` |
| Tokens design system | `tailwind.config.ts`, fichier de tokens, lib ? | `tailwind.config.ts` étend les couleurs `brand.*` |

---

## Format de synthèse

À la fin de la cartographie, produire un bloc court de ce type, à coller dans le prompt de l'agent :

```
Stack : React 18 + Vite + TS strict + pnpm
Structure : features/ par domaine, colocation tests
État partagé : zustand (3 stores)
État serveur : Tanstack Query v5, facade par domaine (src/features/*/api/*.ts)
Tests : vitest + RTL + MSW v2, custom render dans test-utils.tsx
Styling : Tailwind + clsx, tokens étendus dans tailwind.config.ts
Forms : react-hook-form + zod
Erreurs : ErrorBoundary root + toasts sonner + état error exposé
Non observable : pas de e2e, pas de Storybook
```

Ce bloc est l'input principal du prompt envoyé à l'agent.
