# Template figé — Contrat d'API entre back et front

> Ce template est la **structure de référence figée** utilisée par le skill `fullstack-specialist` du plugin `codebase-toolkit`. Le contrat est rédigé et **validé par l'utilisateur avant toute délégation** : il devient la **source unique** que le back produit et que le front consomme.
>
> Il détaille la section « Contrat d'interface » des tasks techniques produites par `/spec-writer:split-spec-by-layer` : un contrat issu d'une task `BACK` s'y transpose champ pour champ.

## Règles

- **Un bloc par opération** (une méthode + un chemin). Une feature peut en contenir plusieurs.
- **Aligné sur l'existant** : nommage des routes, casse des champs (`camelCase` / `snake_case`), format d'erreur, pagination et format de date sont **repris des conventions API observées** dans le repo, avec un fichier de référence cité. Une convention non observée est marquée `[HYPOTHÈSE]`.
- **Types explicites** : chaque champ a un type, sa nullabilité et son caractère obligatoire. Pas de `object` ou `any` non détaillé.
- **Toutes les erreurs** que le front doit traiter sont listées, avec le code HTTP et le code / message métier.
- Une fois validé, le contrat **ne change plus** sans nouvelle validation explicite de l'utilisateur.

---

## Bloc d'une opération

~~~markdown
### OP-<N> — <METHOD> <path>

**Objet** : ce que fait l'opération, en une phrase métier.
**Convention de référence** : `path/to/existing/Resource.php` (opération existante dont on reprend le style)

#### Sécurité
- Authentification : <JWT Keycloak | session | publique>
- Autorisation : rôles / voter requis (`ROLE_…`, `SouscriptionVoter::EDIT`)

#### Requête
- Paramètres de chemin : `id` (uuid, obligatoire)
- Paramètres de query : `page` (int ≥ 1, défaut 1), `status` (enum `draft|validated`, optionnel)
- Corps (`application/json`) :

| Champ | Type | Obligatoire | Nullable | Contraintes de validation |
|---|---|---|---|---|
| `montant` | decimal (string) | oui | non | > 0, 2 décimales |

#### Réponse succès
- Code : `200` | `201` | `204`
- Corps :

| Champ | Type | Nullable | Description |
|---|---|---|---|

- Pagination (si collection) : format observé (Hydra `hydra:member` / `hydra:totalItems`, ou `items` / `total`…)

#### Erreurs

| Code HTTP | Code / type métier | Condition | Message ou forme du corps | Traitement attendu côté front |
|---|---|---|---|---|
| 400 | — | payload mal formé | … | message générique |
| 422 | `montant` | violation de contrainte | violations par champ | erreur affichée sous le champ |
| 403 | — | droit manquant | … | redirection / message |
| 404 | — | ressource absente | … | état vide / message |

#### Compatibilité
- Nouvelle opération / modification d'une opération existante (champs ajoutés, renommés, supprimés).
- Impact sur les consommateurs existants et stratégie (champ optionnel, versionnement, feature flag).

#### Exemple
Requête :
```http
POST /api/… HTTP/1.1
Content-Type: application/json

{ … }
```
Réponse :
```json
{ … }
```
~~~

---

## Anti-patterns à NE PAS reproduire

- ❌ Champ sans type ou sans indication obligatoire / nullable.
- ❌ Format d'erreur inventé alors que le projet en a déjà un.
- ❌ Erreur métier gérée par le back mais absente du contrat (le front ne saura pas la traiter).
- ❌ Contrat modifié pendant l'implémentation sans revalidation.
- ❌ Exemple incohérent avec les tableaux de champs.
