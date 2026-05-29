---
name: audit-codebase
description: "Lance un audit back-end PHP/Symfony complet d'une codebase, module par module, et produit un rapport markdown structuré dans `docs/audit/`. Orchestre un flow en 6 phases : cadrage du périmètre → vérification de la stack → auto-détection des modules → confirmation → audit module par module (délégué à l'agent `backend-specialist`) → agrégation & sortie. Le rapport couvre 6 axes par module : ✅ points forts à conserver, ⚠️ risques & dette technique, 🪓 opportunités de simplification, 🧪 tests & qualité, 🚀 performance & scalabilité, 🧭 cohérence architecturale. Déclencher quand l'utilisateur dit : /audit-codebase, 'audit mon back', 'fais un audit complet de la codebase', 'génère un rapport d'audit', 'analyse de dette technique', ou 'identifie les simplifications possibles dans mon back'."
user_invocable: true
---

# Audit Codebase

Orchestre un **audit back-end PHP/Symfony complet**, module par module, qui produit un rapport markdown structuré : ce qui marche, ce qui pose problème, ce qui pourrait être simplifié, et comment le tout est testé / performe / s'aligne sur l'architecture revendiquée.

Le plugin **réutilise l'agent `backend-specialist`** (du plugin homonyme) pour la cartographie de chaque module, et applique la **grille figée** et le **template figé** définis dans les références.

## Vue d'ensemble du flow

1. **Cadrage** — Périmètre demandé (toute la codebase / liste de modules / un seul module)
2. **Vérification stack** — PHP / Symfony / Doctrine / API Platform / Messenger / tests
3. **Auto-détection des modules** — Bounded contexts / dossiers de premier niveau dans `src/`
4. **Confirmation** — L'utilisateur valide ou ajuste la liste avant de lancer l'audit profond
5. **Audit module par module** — Délégation à l'agent `backend-specialist` (mode `analyse`) pour chaque module, avec la grille `audit-grid.md` en input
6. **Agrégation & sortie** — Fusion des findings dans le template, écriture dans `docs/audit/<YYYY-MM-DD>-audit-codebase.md`

---

## Arguments du slash command

```
/audit-codebase [--modules=<liste>] [--full]
```

- `--modules=<liste>` (optionnel) — Liste de modules séparés par `,` (ex : `--modules=Auth,Billing`). Saute la confirmation de Phase 4.
- `--full` (optionnel) — Audite **tous** les modules auto-détectés sans demande de confirmation. À utiliser avec précaution sur les gros repos (coût en tokens élevé).

Sans argument : flow interactif normal.

---

## Phase 1 — Cadrage

Demander via `AskUserQuestion` :

**« Quel est le périmètre de l'audit ? »**

- **`tous-les-modules`** — Audit complet de toute la codebase. Recommandé pour un état des lieux global.
- **`modules-cibles`** — L'utilisateur fournit une liste de modules précis à auditer.
- **`un-seul-module`** — Audit ciblé sur un module unique. Recommandé pour préparer une refacto.

Si `modules-cibles` ou `un-seul-module` est choisi, demander la liste / le nom via `AskUserQuestion` ou prompt libre.

> ⚠️ Si l'argument `--modules` ou `--full` est passé en CLI, sauter cette phase et l'enregistrer comme périmètre.

---

## Phase 2 — Vérification de la stack

Lire :

- `composer.json` — versions PHP, Symfony, Doctrine, API Platform, Messenger, PHPStan, PHPUnit.
- `config/services.yaml` et `config/packages/*.yaml` (notamment `messenger.yaml`, `doctrine.yaml`, `api_platform.yaml`, `security.yaml`).
- `phpstan.neon` / `phpstan.dist.neon` (niveau, baseline).
- `phpunit.xml.dist` / `phpunit.xml`.
- `README.md` pour le contexte projet.

Synthétiser :

- Version PHP / Symfony.
- ORM (Doctrine ORM ? DBAL direct ? autre ?).
- CQRS : Messenger configuré avec command.bus / query.bus / event.bus, ou pas du tout.
- API : API Platform ? Controllers classiques ? Mix ?
- Tests : PHPUnit, structure, présence de fixtures, PHPStan / Psalm.

### Stop si la stack n'est pas Symfony

Si **aucun** des marqueurs Symfony n'est trouvé (`symfony/framework-bundle`, `symfony/console`, …), **s'arrêter** et signaler à l'utilisateur que le plugin `audit-codebase` est positionné sur PHP/Symfony. Proposer une alternative (ex : adapter manuellement, demander un plugin équivalent pour la stack détectée).

---

## Phase 3 — Auto-détection des modules

Inférer le découpage en modules à partir de la structure `src/` :

1. **Cas DDD/hexagonal** — Si `src/Domain/`, `src/Application/`, `src/Infrastructure/` existent :
   - Lister les sous-dossiers de premier niveau de `src/Domain/` (chaque sous-dossier = un bounded context).
   - Si `src/Domain/` n'a pas de sous-découpage, regarder `src/Application/`.
2. **Cas classique** — Si `src/Controller/`, `src/Service/`, `src/Entity/` existent sans `Domain/` :
   - Lister les sous-dossiers de premier niveau de `src/` qui ne sont **pas** des dossiers techniques (`Controller`, `Service`, `Entity`, `Repository`, `Form`, `Security`, `EventSubscriber`, `Command`).
   - Si ce découpage ne fait pas sens, fallback : lister les entités Doctrine et grouper par préfixe métier.
3. **Cas bundle Symfony** — Si l'application est un bundle (présence de `src/<BundleName>Bundle.php` et `src/DependencyInjection/`), considérer le bundle comme un module unique sauf découpage interne explicite.
4. **Cas hybride / multi-bundles** — Lister chaque bundle métier comme un module distinct.

Pour chaque module détecté, compter :

- Nombre de classes Domain (entités + VO + events).
- Nombre de Commands / Queries / Handlers.
- Nombre de tests associés (`tests/<Type>/<Module>/`).

Produire un tableau récapitulatif (à présenter en Phase 4).

> Si l'auto-détection ne donne **rien** de probant (moins de 2 modules détectés sur une codebase non-triviale), passer en fallback : demander directement à l'utilisateur la liste des modules à auditer.

---

## Phase 4 — Confirmation des modules

Présenter à l'utilisateur la liste auto-détectée :

```
Modules détectés :
- Auth : 12 classes Domain, 4 Commands, 6 Queries, 18 tests
- Billing : 8 classes Domain, 3 Commands, 2 Queries, 11 tests
- Onboarding : 5 classes Domain, 2 Commands, 0 Queries, 4 tests
- ...
```

Demander via `AskUserQuestion` :

**« Quels modules veux-tu auditer ? »** (multiSelect ou prompt libre, selon ce qui rentre dans les contraintes du tool)

Si l'utilisateur a déjà cadré en Phase 1 sur une liste précise (`modules-cibles` ou `un-seul-module`), confirmer la résolution (matcher les noms saisis vs les noms détectés) et signaler les mismatches.

Si argument `--full` ou si l'utilisateur a choisi `tous-les-modules` en Phase 1 : auditer tous les modules détectés sans nouvelle question, **mais** avertir si plus de 6 modules sont détectés :

> ⚠️ « 9 modules détectés. Auditer tous va prendre plusieurs minutes et coûter en tokens. Continuer ? » (Oui / Non, j'en sélectionne un sous-ensemble).

---

## Phase 5 — Audit module par module

Pour **chaque module retenu**, dans l'ordre :

### 5.1 — Préparer le contexte du module

Collecter :

- Chemins racine du module (Domain, Application, Infrastructure pour ce module).
- Liste des fichiers représentatifs : 1 entité, 1 Command + Handler, 1 Query + Handler, 1 Repository, 1 Resource API Platform si applicable, 1-3 tests.
- Top 5 des plus gros fichiers du module (`Bash find ... -name "*.php" -exec wc -l {} + | sort -rn | head -5`).
- Présence ou absence de tests par couche (`tests/Unit/<Module>/`, `tests/Integration/<Module>/`, `tests/Functional/<Module>/`).

### 5.2 — Déléguer à l'agent `backend-specialist`

Appeler le tool `Agent` (subagent_type=`backend-specialist`) avec :

**Mode** : `analyse`

**Régime** : `perenne` (l'audit traite la codebase comme du code pérenne par défaut — un audit n'est pas un script jetable).

**Prompt à fournir à l'agent — inclure obligatoirement** :

1. **Besoin reformulé** :

   > « Audite le module `<Nom>` situé dans `<chemins>` en suivant **exactement** la grille `${CLAUDE_PLUGIN_ROOT}/skills/audit-codebase/references/audit-grid.md`. Couvre les 6 axes dans l'ordre : ✅ points forts, ⚠️ risques & dette, 🪓 opportunités de simplification, 🧪 tests & qualité, 🚀 performance & scalabilité, 🧭 cohérence architecturale. Pour chaque finding : ancrer sur `path:line`, donner sévérité (axes 2/4/5/6), effort (`S`/`M`/`L`), et action concrète. Pas de finding flottant, pas de jugement abstrait. Si un point n'est pas observable, le lister en `Questions ouvertes`. »

2. **Stack & patterns du projet** — résumé issu de la Phase 2.

3. **Contexte du module** — chemins, fichiers représentatifs, top 5 plus gros fichiers, couverture de tests par couche.

4. **Format de sortie attendu** — exactement le sous-bloc « Module » du template `${CLAUDE_PLUGIN_ROOT}/skills/audit-codebase/references/audit-template.md` (section 3, format imposé d'un module). L'agent doit produire ce bloc et **rien d'autre** : pas de synthèse globale, pas de roadmap (c'est le skill qui agrège).

5. **Périmètre d'édition** : `aucun` (mode `analyse` strict — l'agent ne touche à aucun fichier).

### 5.3 — Récupérer & stocker

Stocker la sortie de l'agent en mémoire (variable de travail du skill). Passer au module suivant.

> ⚠️ Si l'agent signale en cours d'analyse une **incohérence** (ex : module qui semblait DDD mais qui en réalité n'est qu'un dossier technique), arrêter le module concerné, le noter en Limitations, et passer au suivant. Ne pas inventer de findings pour combler.

---

## Phase 6 — Agrégation & sortie

### 6.1 — Construire le rapport

Assembler le rapport en suivant **strictement** `${CLAUDE_PLUGIN_ROOT}/skills/audit-codebase/references/audit-template.md` :

1. **Front-matter YAML** — projet, date (`YYYY-MM-DD`), stack synthétisée, périmètre, modules audités, modules non audités (+ raison), pointeur vers la grille source.
2. **Titre** — `# Audit codebase — <nom du projet> — <YYYY-MM-DD>`.
3. **Section 1 — Synthèse exécutive** — agréger les Top 3 forces / risques / simplifications à partir des findings collectés sur tous les modules. Construire le tableau de scoring qualitatif par axe.
4. **Section 2 — Cartographie générale** — stack technique + architecture revendiquée + tableau des modules détectés (audités ET non audités).
5. **Section 3 — Audit module par module** — concaténer les sous-blocs produits par l'agent en Phase 5, dans l'ordre de la liste retenue.
6. **Section 4 — Recommandations transverses** — identifier les findings qui apparaissent dans plusieurs modules ou qui touchent à la configuration globale (Messenger, services.yaml, PHPStan baseline, conventions de tests). Si rien : écrire `_Aucune recommandation transverse._`.
7. **Section 5 — Roadmap suggérée** — hiérarchiser les findings actionnables par horizon (court / moyen / long terme) selon sévérité + effort. **Un finding ne peut apparaître qu'une seule fois** dans la roadmap.
8. **Section 6 — Limitations de l'audit** — modules non audités, couches non analysées, outils non lancés, profondeur d'analyse, sources de vérité limitées.

### 6.2 — Écrire le fichier

1. Créer le dossier `docs/audit/` à la racine du repo audité si nécessaire (via `Bash mkdir -p docs/audit`).
2. Déterminer le nom de fichier :
   - Si `docs/audit/<YYYY-MM-DD>-audit-codebase.md` n'existe pas → utiliser ce nom.
   - Sinon → suffixer avec une heure : `docs/audit/<YYYY-MM-DD>T<HH>h<MM>-audit-codebase.md`. **Jamais d'écrasement** d'un audit existant.
3. Écrire le rapport via `Write`.
4. Afficher le chemin créé à l'utilisateur + un récap court (nombre de modules audités, nombre de findings par sévérité).

### 6.3 — Proposer la suite (sans agir)

Proposer (sans exécuter) :

- Commiter le rapport via le skill `git-workflow` si disponible.
- Ouvrir le rapport dans l'éditeur.
- Relancer un audit ciblé sur un module particulier si des `Questions ouvertes` méritent d'être approfondies.

---

## Règles transverses

- **Langue** : tout le flow, toutes les questions et le rapport final sont en **français**.
- **Pas de modification du repo audité** en dehors de `docs/audit/<...>.md`. Aucun fichier de code touché.
- **Pas d'invention** : tout finding du rapport final doit pouvoir être justifié par un fichier précis du repo audité. Si l'agent retourne un finding flottant, l'écarter ou le déplacer en `Questions ouvertes`.
- **Pas d'audit partiel masqué** : si un module n'a pas pu être audité, c'est dans la section **Limitations**, pas masqué.
- **Pas de note chiffrée globale** : le rapport qualifie par axe (🟢/🟡/🔴), il ne note pas sur 20. L'objectif est d'éclairer les décisions, pas de produire un classement.
- **Régime de l'audit toujours `perenne`** : l'agent `backend-specialist` est invoqué en régime `perenne` car on audite du code en place, pas un script jetable. Ne pas laisser l'agent rebasculer en régime `simple`.
- **Une seule passe d'audit par invocation** : si l'utilisateur veut auditer en plusieurs vagues, il relance le skill avec un périmètre différent. On ne chaîne pas plusieurs audits dans la même invocation.
- **Pas de publication ailleurs que dans le fichier markdown local** : pas de push, pas d'envoi vers un système externe. Le rapport reste dans `docs/audit/`.
