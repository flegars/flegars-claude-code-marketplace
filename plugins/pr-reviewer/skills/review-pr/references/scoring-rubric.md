# Grille de notation /20 — Hybride universelle + adaptative

Cette grille est la **référence unique** pour calculer la note d'une review. Le score est entier (0 à 20), pas de décimales.

La note est composée de **deux blocs** :

- **Bloc universel (14 points)** — Appliqué à toute PR, indépendamment de la stack.
- **Bloc adaptatif (6 points)** — Appliqué selon la stack détectée dans le repo. Si aucune stack n'est reconnue, fallback générique « architecture & cohérence avec les conventions du repo ».

---

## Bloc universel — 14 points

### 1. Qualité du code (3 pts)

Évalue la lisibilité fine, la cohérence du style, et la propreté.

| Sous-critère | Points |
|---|---|
| Nommage clair, intentions explicites | 0-1 |
| Pas de duplication évitable, pas de code mort | 0-1 |
| Fonctions courtes, responsabilités séparées | 0-1 |

### 2. Sécurité (2 pts)

Évalue les risques exploitables introduits par la PR.

| Sous-critère | Points |
|---|---|
| Aucune injection (SQL, XSS, command, path traversal) | 0-1 |
| Gestion correcte des secrets, auth, et données sensibles | 0-1 |

**Plafonné à 0** si une faille critique exploitable est introduite (à signaler en `🐛 Problèmes critiques`).

### 3. Tests (3 pts)

Évalue la couverture et la pertinence des tests ajoutés ou modifiés.

| Sous-critère | Points |
|---|---|
| Tests présents pour le code introduit | 0-1 |
| Tests couvrent le nominal **et** les cas limites/erreurs | 0-1 |
| Tests pertinents (unit vs intégration, isolation, assertions précises) | 0-1 |

**Plafonné à 1** si la PR introduit du code métier sans aucun test.

### 4. Lisibilité & maintenabilité (2 pts)

Évalue ce qu'un dev qui n'a pas écrit le code en comprend en 5 minutes.

| Sous-critère | Points |
|---|---|
| Structure compréhensible sans suivre le diff ligne par ligne | 0-1 |
| Commentaires utiles aux endroits non triviaux (et seulement là) | 0-1 |

### 5. Alignement avec les US/work items rattachés (2 pts)

Critère **central** du plugin. Évalue la correspondance entre ce que demande la spec et ce que livre le code.

| Sous-critère | Points |
|---|---|
| Le scope des US rattachées est entièrement couvert par la PR | 0-1 |
| Aucune dérive hors-scope (= la PR ne livre pas plus que ce que demandent les US sans justification) | 0-1 |

**Plafonné à 0** si la PR ne référence aucune US/work item alors que le repo a une convention (issues GitHub, work items Azure). Le signaler dans le rapport.
**N/A → 2 pts d'office** si la PR est explicitement marquée chore/docs/refactor sans US attendue.

### 6. Architecture & cohérence (2 pts)

Évalue le respect des frontières et de la cohérence globale du repo.

| Sous-critère | Points |
|---|---|
| Respect des couches/dossiers/conventions de structure | 0-1 |
| Pas de couplage inapproprié, pas de dépendance qui traverse les frontières | 0-1 |

---

## Bloc adaptatif — 6 points (sélectionner UNE seule sous-grille)

La détection se fait via les fichiers du repo (`composer.json`, `package.json`, `go.mod`, `pyproject.toml`, `Cargo.toml`, etc.).

Si plusieurs stacks coexistent (monorepo), choisir la stack **principale du diff** (la majorité des fichiers modifiés).

### Sous-grille A — Symfony / PHP / DDD / API Platform

Activée si `composer.json` mentionne `symfony/*` et/ou `api-platform/core` et/ou le repo expose une structure DDD (`src/Domain`, `src/Application`, `src/Infrastructure`).

| Critère | Points |
|---|---|
| Respect DDD : entities dans le bon domaine, value objects pertinents | 0-1 |
| Pattern Manager pour les writes (pas d'appel direct au repository pour persister) | 0-1 |
| API Platform : Processors/Providers (pas de Controllers), Resources avec `fromModel()`, payloads validés | 0-1 |
| Repository : interface de domaine type-hintée, query building fluide | 0-1 |
| Events : OutEvent publié pour les changements d'agrégats, outbox respecté | 0-1 |
| Conventions : UUID exposé (pas l'ID interne), `DateTimeImmutable`, Webmozart Assert pour la validation | 0-1 |

### Sous-grille B — Go

Activée si `go.mod` est présent.

| Critère | Points |
|---|---|
| Gestion des erreurs : wrapping (`fmt.Errorf("...: %w", err)`), pas d'erreur ignorée | 0-1 |
| Propagation du `context.Context` sur les frontières I/O | 0-1 |
| Concurrence safe : pas de data race évidente, goroutines tracées, channels fermés | 0-1 |
| Idiomes Go : interfaces définies côté consommateur, pas de generics gratuits | 0-1 |
| Tests : table-driven tests, `t.Helper()`, `t.Cleanup()` quand pertinent | 0-1 |
| Structure : packages cohérents, pas de cycles, exports minimaux | 0-1 |

### Sous-grille C — TypeScript / React

Activée si `package.json` contient `react` et/ou `next`.

| Critère | Points |
|---|---|
| Typage strict : pas de `any` injustifié, types partagés réutilisés | 0-1 |
| Règles des hooks respectées (dépendances exhaustives, pas d'appel conditionnel) | 0-1 |
| Composants : responsabilité unique, props typées, pas de logique métier dans la vue | 0-1 |
| Gestion d'état adaptée (local vs remote vs global), pas d'effets de bord cachés | 0-1 |
| Accessibilité : rôles ARIA, labels, contrastes, navigation clavier | 0-1 |
| Tests : composants testés via comportement utilisateur (Testing Library), pas d'implémentation interne | 0-1 |

### Sous-grille D — Python

Activée si `pyproject.toml` ou `setup.py` ou `requirements.txt` est présent (et que ce n'est pas un projet Go avec script Python).

| Critère | Points |
|---|---|
| Type hints sur les signatures publiques (mypy/pyright compatibles) | 0-1 |
| Gestion des exceptions : pas de `except:` nu, exceptions spécifiques, contexte préservé | 0-1 |
| Idiomes Python : compréhensions, context managers, dataclasses/pydantic appropriés | 0-1 |
| Packaging : imports propres, pas de side-effects à l'import | 0-1 |
| Tests : `pytest` avec fixtures, paramétrisation pour les cas multiples | 0-1 |
| Conformité PEP8 / formateur (`black`, `ruff`) | 0-1 |

### Sous-grille E — Fallback générique (stack non reconnue)

Activée si aucune des sous-grilles A-D ne s'applique.

| Critère | Points |
|---|---|
| Respect des conventions visibles dans le repo (style, structure) | 0-2 |
| Cohérence architecturale (couches, séparation des responsabilités) | 0-2 |
| Idiomes du langage utilisé (pas d'anti-patterns évidents) | 0-2 |

---

## Synthèse — Échelle de ressenti général

| Score | Ressenti |
|---|---|
| **18-20** | Exemplaire — Mergeable en l'état, à part détails mineurs |
| **15-17** | Très bon — Quelques améliorations possibles, pas de blockers |
| **12-14** | Bon — Plusieurs points à corriger avant merge |
| **9-11** | À retravailler — Refactor partiel nécessaire |
| **6-8** | Problèmes significatifs — Reprise large requise |
| **0-5** | Critique — Ne répond pas aux standards minimum |

Le ressenti général en titre du rapport **doit refléter cette échelle** et expliquer le « pourquoi » de la note en une phrase.

---

## Règles de calcul

1. Calcule chaque sous-critère honnêtement, sans arrondi favorable.
2. Somme bloc universel + bloc adaptatif → score sur 20.
3. Applique les **plafonnements** quand ils s'appliquent (faille de sécurité, absence de tests, US non référencées).
4. Note finale = entier, jamais de demi-point.
5. Si tu hésites entre deux notes, choisis la plus basse et justifie en commentaire de section.
