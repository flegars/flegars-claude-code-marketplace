# Template standardisé d'une User Story

> Ce template est la **structure de référence figée** utilisée par le plugin `codebase-to-us`. Toute US générée par le plugin DOIT respecter intégralement cette structure et l'ordre des sections.

Chaque section ci-dessous est obligatoire sauf mention explicite « *(si applicable)* ».

---

## Titre

Un titre concis mais descriptif qui résume l'action principale.

**Format obligatoire** : `[Domaine] Verbe + Complément`

Exemples :
- `[Société] Créer une société avec validation du SIRET`
- `[Partenaire] Consulter la liste des deals en cours`
- `[Webhook Hubspot] Traiter l'événement contact.created`

---

## Description

Format obligatoire :

```
En tant que [rôle précis avec contexte],
Je veux [action spécifique et mesurable],
Afin de [bénéfice métier concret et vérifiable].
```

**Règles strictes :**
- Le **rôle** doit être un persona identifié (jamais « utilisateur » générique). Exemples : « partenaire connecté via le portail », « administrateur back-office Inter Invest », « système externe via webhook Hubspot ».
- L'**action** doit être un verbe d'action précis avec son objet et ses contraintes.
- Le **bénéfice** doit expliquer le *pourquoi* métier, pas reformuler l'action.

---

## Contexte & Règles métier

Section détaillant :
- Le contexte fonctionnel (d'où vient le besoin, quel processus métier est concerné)
- Les règles métier applicables (avec références aux règles existantes si pertinent)
- Les contraintes réglementaires éventuelles
- Les définitions des termes métier utilisés (glossaire si nécessaire)

Si l'US est dérivée de la codebase, inclure un sous-bloc :

### Comportement actuel observé dans la codebase
- Fichiers analysés : `path/to/file.php:42`, `path/to/other.php`
- Comportement existant résumé en quelques lignes
- Gap fonctionnel à combler par cette US (ce qui manque ou doit changer)

---

## Critères d'acceptance (Given/When/Then)

Chaque critère suit le format **Gherkin obligatoirement** :

```gherkin
Scénario : [Nom descriptif du scénario]
  Étant donné [contexte initial précis avec données concrètes]
  Quand [action déclenchante avec paramètres exacts]
  Alors [résultat attendu mesurable et vérifiable]
  Et [résultat complémentaire si applicable]
```

**Règles strictes :**
- Utiliser des **valeurs concrètes** dans les exemples (pas « une valeur valide » mais `SIRET 12345678901234`).
- Chaque scénario a un **nom unique et descriptif**.
- Inclure **systématiquement** :
  - Au moins 1 scénario nominal (cas passant)
  - Les scénarios alternatifs pertinents
  - Les scénarios d'erreur (données invalides, droits insuffisants, entité inexistante, etc.)
  - Les scénarios de bord (limites de champs, caractères spéciaux, listes vides, etc.)

---

## Spécifications techniques *(si applicable)*

- **Endpoint API** : méthode HTTP, route exacte, format du payload
- **Champs** : nom, type, contraintes de validation, valeurs par défaut
- **Codes de retour HTTP** attendus pour chaque scénario
- **Événements émis** (RabbitMQ, webhooks) avec leur payload
- **Impact sur les entités existantes** : relations, cascades, migrations
- **Idempotence** : préciser si l'opération est idempotente ou non

---

## Maquettes / Exemples visuels *(si applicable)*

Si l'US concerne une interface utilisateur, décrire précisément :
- Les champs affichés avec leur label exact
- L'ordre des éléments
- Les états des composants (actif, désactivé, en erreur, en chargement)
- Les messages d'erreur exacts affichés à l'utilisateur

---

## Dépendances

- **US prérequises** (bloquantes) : `US-XXX`, `US-YYY`
- **US liées** (non bloquantes mais contextuelles)
- **Services / APIs externes** nécessaires
- **Données de référence** requises

---

## Notes de découpage

- **Epic / feature parente** : nom de l'epic
- **Scope IN** : ce qui est inclus dans cette US
- **Scope OUT** : ce qui est explicitement exclu (crucial pour éviter le scope creep)

---

## Estimation de complexité suggérée

Estimation en story points (1, 2, 3, 5, 8, 13) avec justification basée sur :
- Complexité technique
- Nombre de cas à gérer
- Intégrations nécessaires
- Risques identifiés

**Estimation : X points** — *Justification : …*

---

## Questions ouvertes *(si applicable)*

Toute hypothèse non confirmée doit apparaître ici, numérotée et classée par priorité. Chaque question propose des options avec leurs implications.

Toute hypothèse non confirmée doit être taguée `[HYPOTHÈSE]` directement dans le corps de l'US là où elle est utilisée.

---

## Anti-patterns à NE PAS reproduire

- ❌ « L'utilisateur peut gérer ses données » → Trop vague.
- ❌ « Le système doit être performant » → Non mesurable.
- ❌ « Les données doivent être validées » → Quelles données ? Quelles règles ?
- ❌ « Un message d'erreur approprié est affiché » → Quel message exactement ?
- ❌ « Le formulaire contient les champs habituels » → Lesquels précisément ?
- ❌ Utiliser « etc. », « et autres », « par exemple » sans liste exhaustive.
- ❌ Mélanger plusieurs fonctionnalités dans une seule US.
- ❌ Rédiger des critères d'acceptance non testables.
