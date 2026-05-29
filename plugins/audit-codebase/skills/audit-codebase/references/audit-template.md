# Template figé du rapport d'audit

Tout rapport produit par le plugin `audit-codebase` **doit suivre ce template à la lettre**. Pas de section renommée, pas de section sautée si elle est obligatoire, pas de section inventée.

Le rapport est rédigé **en français**, sauf termes techniques (Command, Handler, Processor, Provider, Repository, Aggregate, Value Object, Domain Event, port, adapter, bus, payload).

---

## Front-matter (obligatoire)

Le fichier markdown commence par un front-matter YAML :

```yaml
---
projet: <nom du repo>
date_audit: <YYYY-MM-DD>
stack: <ex : "PHP 8.3 / Symfony 7.1 / Doctrine ORM 3.x / API Platform 4.x">
perimetre: <ex : "Back-end, modules: Auth, Billing, Onboarding (3/12 modules détectés)">
modules_audites:
  - <module 1>
  - <module 2>
modules_non_audites:
  - <module N> (raison: hors-scope demandé)
source_grille: ${CLAUDE_PLUGIN_ROOT}/skills/audit-codebase/references/audit-grid.md
---
```

---

## Titre (ligne après le front-matter)

Format strict :

```
# Audit codebase — <nom du projet> — <YYYY-MM-DD>
```

---

## Section 1 — `## 🧭 Synthèse exécutive` *(obligatoire)*

Bloc de 5-10 lignes qui résume :

- **Posture générale** — appréciation globale en une phrase (`Architecture saine avec dette ciblée`, `Risques structurels à adresser`, `Sur-engineering généralisé`, etc.).
- **Top 3 forces** — items issus de l'axe 1, agrégés et reformulés.
- **Top 3 risques** — items `bloquant` ou `important` issus de l'axe 2 ou 6.
- **Top 3 opportunités de simplification** — items issus de l'axe 3 avec le meilleur ROI (gain élevé, effort faible).

Puis tableau de scoring qualitatif par axe (un statut, pas une note) :

```markdown
| Axe | État | Commentaire (1 phrase) |
|---|---|---|
| ✅ Points forts à conserver | 🟢 Solide / 🟡 Partiel / 🔴 Limité | ... |
| ⚠️ Risques & dette technique | 🟢 Maîtrisée / 🟡 Présente / 🔴 Critique | ... |
| 🪓 Opportunités de simplification | 🟢 Code épuré / 🟡 Quelques poches / 🔴 Sur-engineering | ... |
| 🧪 Tests & qualité | 🟢 Couverture solide / 🟡 Lacunes / 🔴 Zones aveugles | ... |
| 🚀 Performance & scalabilité | 🟢 Pas de signal / 🟡 Goulots à surveiller / 🔴 Risques actifs | ... |
| 🧭 Cohérence architecturale | 🟢 Étanche / 🟡 Dérives ponctuelles / 🔴 Couches fuyantes | ... |
```

Pas de note chiffrée globale — l'objectif est de **qualifier**, pas de noter.

---

## Section 2 — `## 🗺️ Cartographie générale` *(obligatoire)*

Synthèse de la stack et de l'architecture observée :

```markdown
### Stack technique
- PHP <version>
- Symfony <version> (composants clés : <liste>)
- Doctrine ORM <version>
- API Platform <version> (ou "absent")
- Symfony Messenger : <buses configurés, ou "non configuré">
- PHPUnit <version>, PHPStan niveau <N>, <autre outil qualité>

### Architecture revendiquée
<ex : "DDD/hexagonal avec séparation Domain / Application / Infrastructure / UI, CQRS via Messenger (command.bus + query.bus + event.bus)">

### Découpage en modules (auto-détecté)
- **<Module 1>** — `src/.../Module1/` — N classes Domain, N Commands, N Queries, N tests
- **<Module 2>** — `src/.../Module2/` — ...
- ...
```

---

## Section 3 — `## 📦 Audit module par module` *(obligatoire)*

Pour **chaque module audité**, un sous-bloc complet avec **les 6 axes**, dans cet ordre exact. Aucun axe ne peut être omis : si rien à signaler sur un axe, écrire `_Aucun finding._`.

### Format imposé d'un module

```markdown
### 📦 Module : <Nom> (`src/.../<Module>/`)

**Patterns observés** : <3-5 lignes sur ce qui caractérise ce module — pattern CQRS appliqué ou pas, séparation des couches, conventions internes, etc. Ancré sur des fichiers du module.>

#### ✅ Points forts à conserver

- **<Titre court>** — `src/.../Foo.php:42`
  - Pourquoi c'est un point fort : ...
  - À préserver lors de : ...

(Lister 2-5 points forts. Si vraiment rien : `_Aucun finding marquant. Le module n'a pas de pattern à mettre en avant — c'est un signal qu'il faudrait peut-être en poser._`)

#### ⚠️ Risques & dette technique

##### Bloquant
- **[bloquant][effort: <S|M|L>] <Titre court>** — `src/.../Foo.php:42`
  - Constat : ...
  - Pourquoi c'est un risque : ...
  - Piste de fix : ...

##### Important
- **[important][effort: <S|M|L>] ...**

##### Mineur
- **[mineur][effort: <S|M|L>] ...**

(Si une catégorie est vide : `_Aucun._` — ne pas supprimer le sous-titre.)

#### 🪓 Opportunités de simplification

- **[effort: <S|M|L>] <Titre court>** — `src/.../Foo.php:42`
  - Constat : ...
  - Pourquoi c'est simplifiable : ...
  - Pattern de remplacement proposé : ...
  - À vérifier avant de simplifier : ...

#### 🧪 Tests & qualité

- **[<sévérité>][effort: <S|M|L>] <Titre court>** — `<chemin>`
  - Constat : ...
  - Risque : ...
  - Action proposée : ...

#### 🚀 Performance & scalabilité

- **[<sévérité>][effort: <S|M|L>] <Titre court>** — `src/.../Foo.php:42`
  - Constat : ...
  - Impact potentiel : ...
  - Fix proposé : ...

#### 🧭 Cohérence architecturale

- **[<sévérité>][effort: <S|M|L>] <Titre court>** — `src/.../Foo.php:42`
  - Constat : ...
  - Pattern revendiqué dans le projet : ...
  - Impact : ...
  - Action corrective : ...

#### ❓ Questions ouvertes (optionnel)

Tout point qui n'a pas pu être tranché par lecture seule (pattern peu observable, conventions implicites, intention floue) :

- Question 1 — ce que le rapport ne peut pas déduire seul.
- Question 2 — ...

```

---

## Section 4 — `## 🔁 Recommandations transverses` *(obligatoire)*

Findings qui touchent **plusieurs modules** ou qui sont structurels (config Messenger globale, conventions de test à harmoniser, montée de version PHP, etc.). Format :

```markdown
- **[<sévérité>][effort: <S|M|L>] <Titre court>**
  - Modules concernés : <liste>
  - Constat : ...
  - Action proposée : ...
```

Si rien de transverse : `_Aucune recommandation transverse — les findings sont localisés par module._`

---

## Section 5 — `## 🛣️ Roadmap suggérée` *(obligatoire)*

Hiérarchisation actionnable des findings, par horizon. **Important** : un finding ne peut apparaître qu'une seule fois (pas de doublon entre horizons).

```markdown
### 🚨 Court terme (sprint en cours / prochaine itération) — actions à effort `S`, sévérité `bloquant` ou impact sécurité/données
1. **<Action prioritaire>** — module <X>, finding référencé en section 3.
2. ...

### 🛠️ Moyen terme (1-3 mois) — actions `M`, sévérité `important`, ou simplifications à fort ROI
1. ...

### 🏗️ Long terme (3-12 mois) — refactos structurelles, montées de version, chantiers transverses
1. ...
```

---

## Section 6 — `## ⚠️ Limitations de l'audit` *(obligatoire)*

Tout ce que l'audit **n'a pas pu** couvrir, pour la traçabilité :

```markdown
- Modules non audités : <liste + raison>
- Couches non analysées (ex : front, infra IaC, scripts ops) — raison
- Outils non lancés (ex : PHPStan non exécuté, coverage non mesurée) — raison
- Profondeur d'analyse : <ex : "Lecture des 3 plus gros fichiers par module + tous les Handlers, mais pas l'intégralité des classes de support">
- Source de vérité limitée : <ex : "Pas d'accès aux logs prod, pas de profil de perf — les findings de l'axe 5 sont des suspicions à confirmer par mesure">
```

---

## Règles de rédaction

- **Ancrage obligatoire** — chaque finding cite un fichier (`path:line` quand pertinent). Pas de findings flottants.
- **Sévérité utilisée seulement quand elle existe dans la grille** (axes 2, 4, 5, 6 + transverses). Pas de sévérité sur les axes 1 et 3.
- **Effort indiqué sur tout finding actionnable** (`S` / `M` / `L`).
- **Pas de flatterie** — ni gratuite, ni à charge. On décrit, on pointe, on propose.
- **Pas de jugement de personne** — on audite du code, pas des décisions humaines.
- **Pas de "il faudrait probablement…"** — si pas observable, lister en `Questions ouvertes` du module.
- **Snippets prêts à coller** quand un fix est proposé — pas de pseudo-code.

---

## Cas particuliers

### Module sans aucun finding sur un axe

Écrire `_Aucun finding._` — ne pas supprimer le sous-titre de l'axe. La structure reste constante d'un module à l'autre.

### Audit sur un seul module

Les sections 1, 2, 4, 5, 6 restent obligatoires. La section 3 contient un seul sous-bloc. Le périmètre dans le front-matter doit clairement indiquer le scope restreint.

### Stack non Symfony détectée

Le plugin est positionné sur PHP/Symfony : si la stack détectée n'est pas Symfony, **stopper et signaler** à l'utilisateur que le plugin n'est pas le bon. Ne pas produire de rapport partiel.

### Pas d'accès à la suite de tests / lints

Le signaler clairement en section 6 (Limitations). Tous les findings de l'axe 4 doivent être marqués comme déduits de la lecture du code, pas d'une mesure réelle.
