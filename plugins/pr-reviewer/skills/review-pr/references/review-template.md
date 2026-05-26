# Template figé du rapport de review

Toute review produite par le plugin `pr-reviewer` **doit suivre ce template à la lettre**. Pas de section renommée, pas de section sautée si elle est obligatoire, pas de section inventée.

Le rapport est rédigé **en français**, sauf termes techniques (PR, work item, endpoint, payload, etc.).

---

## Structure obligatoire

### Titre (ligne 1)

Format strict :

```
📊 Score: X/20 — <ressenti général en une phrase>
```

- `X` est entier (0-20), calculé via `scoring-rubric.md`.
- Le ressenti général reflète l'échelle de la grille (`Exemplaire`, `Très bon`, `Bon`, `À retravailler`, `Problèmes significatifs`, `Critique`) et explique le « pourquoi » de la note en une phrase.

Exemples :
- `📊 Score: 17/20 — Très bon — Architecture solide, à compléter sur les tests d'erreur`
- `📊 Score: 11/20 — À retravailler — Le scope dépasse l'US et la couche infra fuit dans le domaine`

---

### Section 1 — `## 📋 Alignement avec les US/Work items rattachés` *(obligatoire)*

Pour chaque US/work item rattaché à la PR :

```
- **<ID ou titre>** — couverture : **complète** | **partielle** | **non couverte** | **hors-scope**
  - Critère couvert : ...
  - Critère non couvert : ... (justifier)
  - Dérive observée : ... (si la PR fait plus que ce que demande l'US)
```

Si **aucune US n'est rattachée** à la PR :
- Le signaler explicitement : `> ⚠️ Aucune US/work item rattaché à cette PR. Critère 5 plafonné à 0 (voir grille).`
- Sauf si la PR est marquée `chore`, `docs`, `refactor` dans le titre/labels : noter `> ℹ️ PR de type <type>, pas d'US attendue.`

---

### Section 2 — `## ✅ Points forts` *(obligatoire)*

Liste à puces, 3 à 6 items. Chaque item :
- Pointe un comportement précis observé dans le diff
- Référence des fichiers/lignes quand pertinent : `path/to/file.ext:42`
- Reste factuel, pas de flatterie générique

---

### Section 3 — `## ⚠️ Axes d'amélioration` *(obligatoire)*

Organisé par sévérité, dans cet ordre :

```
### Critique
- ...

### Important
- ...

### Mineur
- ...
```

Pour chaque item :
- Référence précise (`path/to/file.ext:42`)
- Explication du **pourquoi** c'est un problème
- Suggestion **actionable** (idéalement avec un snippet copiable)

Si une catégorie de sévérité est vide, écrire `_Aucun._` plutôt que de la supprimer.

---

### Section 4 — `## 🐛 Problèmes critiques` *(optionnelle — seulement si applicable)*

À utiliser **uniquement** pour les régressions/failles bloquantes :
- Faille de sécurité exploitable
- Casse une fonctionnalité existante
- Introduction d'un bug de logique métier
- Non-respect d'une contrainte légale/conformité

Chaque item doit avoir : description, impact, et fix proposé.

Si pas de problème critique : **ne pas inclure la section**.

---

### Section 5 — `## 📚 Conformité architecture` *(obligatoire)*

Sous-section adaptative selon la stack détectée. Le titre du sous-bloc précise la grille appliquée :

```
### Grille appliquée : <Symfony/DDD | Go | TypeScript/React | Python | Générique>
```

Lister les critères de la sous-grille avec un statut visuel :
- ✅ Critère respecté
- ⚠️ Critère partiellement respecté (préciser)
- ❌ Critère non respecté (préciser, avec correctif)

---

### Section 6 — `## 💡 Recommandations actionnables` *(obligatoire)*

Synthèse en 3-5 actions concrètes, hiérarchisées :

```
1. **<Action prioritaire>** — pourquoi, où, comment.
2. ...
```

Chaque action doit pouvoir devenir un TODO dans une autre PR ou un commit suivant.

---

### Section 7 — `## 🧮 Détail du score` *(obligatoire)*

Tableau qui justifie la note pour traçabilité :

```
| Bloc | Critère | Note |
|---|---|---|
| Universel | Qualité du code | X/3 |
| Universel | Sécurité | X/2 |
| Universel | Tests | X/3 |
| Universel | Lisibilité & maintenabilité | X/2 |
| Universel | Alignement US | X/2 |
| Universel | Architecture & cohérence | X/2 |
| Adaptatif (<stack>) | <Critère 1> | X/1 |
| ... | ... | ... |
| **Total** | | **X/20** |
```

Mentionner explicitement tout **plafonnement** appliqué (sécurité, tests, US absentes).

---

## Format pour le mode `--inline` (commentaires sur la PR)

Le rapport global (titre + sections) est posté comme **commentaire principal** de la PR.

Les axes d'amélioration et problèmes critiques liés à des lignes précises sont **dupliqués en commentaires inline** sur les lignes concernées. Format inline (court) :

```
**[<Sévérité>]** <description courte>

<snippet du fix proposé si pertinent>
```

Un commentaire inline ne reprend **pas** tout le contexte global : il complète, il ne remplace pas.

---

## Format pour le mode `--local` (fichier markdown)

Le rapport complet est écrit dans `reviews/PR-<id>.md` à la racine du repo courant.

Si le dossier `reviews/` n'existe pas, le créer. Le `<id>` est :
- L'ID numérique de la PR pour GitHub (ex : `PR-1234.md`)
- L'ID numérique de la PR pour Azure DevOps (ex : `PR-5678.md`)

Si une review existe déjà pour cette PR, suffixer avec un timestamp : `PR-1234-2026-05-26T14h30.md` (toujours ajouter, ne jamais écraser).

Le rapport contient en tête, avant le titre `📊 Score: …` :

```
---
pr: <url complète>
plateforme: <github|azure-devops>
auteur: <auteur de la PR>
branche: <branche source → branche cible>
date_review: <YYYY-MM-DD>
us_rattachees:
  - <id ou url>
---
```
