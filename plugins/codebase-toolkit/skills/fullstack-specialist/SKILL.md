---
name: fullstack-specialist
description: "Pilote une feature qui touche à la fois le back PHP/Symfony et le front React en partant d'un contrat d'API unique : cadrage (mode analyse / proposition / implementation, régime simple / perenne côté back) → vérification des deux stacks → rédaction du contrat d'API selon un template figé, validé par l'utilisateur AVANT toute délégation → délégation en parallèle aux agents backend-specialist (producteur du contrat) et frontend-specialist (consommateur) → contrôle de cohérence back ↔ front ↔ contrat → sortie. Accepte en entrée un découpage /spec-writer:split-spec-by-layer pour reprendre ses contrats. Déclencher quand l'utilisateur dit : /fullstack-specialist, 'implémente cette feature back et front', 'feature fullstack', 'il faut l'endpoint et l'écran', 'branche le front sur une nouvelle API', ou veut une intervention coordonnée back + front alignée sur les patterns du repo."
user_invocable: true
argument-hint: "[description de la feature | chemin d'un découpage split-spec-by-layer]"
---

# Fullstack Specialist

Coordonne les agents `backend-specialist` et `frontend-specialist` sur une feature **transverse**. La règle centrale : **le contrat d'API est écrit et validé d'abord**, puis il devient la source unique que le back produit et que le front consomme. Le contrat suit le template figé :
`${CLAUDE_PLUGIN_ROOT}/skills/fullstack-specialist/references/api-contract-template.md`

Pour une intervention sur un seul côté, utiliser directement `/codebase-toolkit:backend-specialist` ou `/codebase-toolkit:frontend-specialist`.

## Vue d'ensemble du flow

1. **Cadrage** — Besoin, mode, régime back, emplacement du front
2. **Vérification des stacks** — Back Symfony et front React
3. **Contrat d'API** — Rédigé selon le template, validé par l'utilisateur
4. **Délégation en parallèle** — Back (producteur) et front (consommateur)
5. **Contrôle de cohérence** — Back ↔ front ↔ contrat
6. **Sortie** — Selon le mode

---

## Phase 1 — Cadrage

### Récupérer le besoin

- Si `$ARGUMENTS` pointe un fichier de découpage produit par `/spec-writer:split-spec-by-layer` (`docs/specs/*-tech-tasks.md`), le lire : le besoin = la source du découpage, et les contrats d'interface des tasks `BACK` serviront de base en Phase 3. Ne traiter que les tasks `BACK` et `FRONT` ; signaler les tasks `DATA`, `INFRA`, `QA` comme hors périmètre de ce skill.
- Sinon, utiliser la description fournie, ou demander via `AskUserQuestion` : **« Quelle feature back + front traiter ? »**

Reformuler en 3-5 lignes (ce que voit l'utilisateur, ce que fait l'API) et confirmer.

### Choisir le cadrage

Poser via `AskUserQuestion` (une seule invocation) :
1. **« Quel mode ? »**
   - **`analyse`** — Cartographier les deux côtés et rédiger le contrat, sans rien modifier.
   - **`proposition`** — Contrat + plan et snippets des deux côtés, à valider. Aucun fichier touché.
   - **`implementation`** — Proposition validée, puis écriture des fichiers des deux côtés.
2. **« Quel régime côté back ? »** — `simple` / `perenne`, définis dans `${CLAUDE_PLUGIN_ROOT}/skills/backend-specialist/references/simplicity-vs-solid.md`. Une feature exposant un endpoint consommé par le front relève en général de `perenne` : le recommander, sans l'imposer.
3. **« Où est le front ? »** — Même repo (préciser la racine si monorepo) / Autre repo (chemin local).

---

## Phase 2 — Vérification des stacks

- **Back** : `composer.json` → Symfony, API Platform, Messenger, Doctrine, outils de test et d'analyse statique.
- **Front** : `package.json` à la racine du front → React, bundler, TypeScript, lib d'état serveur (Tanstack Query, RTK Query, SWR, fetch manuel), lib de tests.

Si l'un des côtés est hors périmètre (pas Symfony, pas React, ou Next.js / React Native), **s'arrêter** et le signaler : proposer de traiter le côté supporté seul via son skill dédié.

En parallèle, repérer les **conventions API existantes** qui serviront au contrat : une ou deux opérations comparables (Resource API Platform ou contrôleur), le format d'erreur (normalizer, `exception_to_status`), la pagination, la casse des champs, et côté front le client API utilisé (fichier qui centralise les appels, typage des réponses).

---

## Phase 3 — Contrat d'API

1. Lire `${CLAUDE_PLUGIN_ROOT}/skills/fullstack-specialist/references/api-contract-template.md`.
2. Rédiger le contrat : un bloc `OP-<N>` par opération, aligné sur les conventions repérées en Phase 2 (fichier de référence cité dans chaque bloc). Si un découpage `split-spec-by-layer` a été fourni, partir de ses contrats et les compléter au format du template.
3. Présenter le contrat et demander via `AskUserQuestion` : **« Ce contrat d'API te convient-il ? »**
   - **Valider**
   - **Ajuster** — préciser les champs, erreurs, droits ou routes à modifier.

Itérer jusqu'à validation. **Aucune délégation avant validation du contrat.** En mode `analyse`, le skill peut s'arrêter ici après la cartographie des deux côtés (Phase 4 en mode `analyse`).

---

## Phase 4 — Délégation en parallèle

Lancer **dans un même message** les deux appels `Agent` :

- **Back** → `subagent_type=backend-specialist`, avec :
  - le besoin reformulé, le **régime**, le **mode** ;
  - le **contrat validé** intégral, avec la consigne : « Tu **produis** ce contrat : routes, payloads, validations, codes d'erreur et droits doivent y correspondre exactement. Tu ne modifies pas le contrat ; si tu constates qu'il est irréalisable avec les patterns du projet, tu t'arrêtes et tu le signales. » ;
  - l'instruction de lire d'abord `${CLAUDE_PLUGIN_ROOT}/skills/backend-specialist/references/simplicity-vs-solid.md` et `${CLAUDE_PLUGIN_ROOT}/skills/backend-specialist/references/symfony-pattern-checklist.md` ;
  - le périmètre d'édition autorisé (mode `implementation`).
- **Front** → `subagent_type=frontend-specialist`, avec :
  - le besoin reformulé (côté écran), le **mode**, la racine du front ;
  - le **contrat validé** intégral, avec la consigne : « Tu **consommes** ce contrat : types de requête / réponse, appels et traitement de **chaque** erreur listée doivent y correspondre exactement, avec les états chargement / erreur / vide. Tu ne modifies pas le contrat ; s'il manque une information pour l'écran, tu t'arrêtes et tu le signales. » ;
  - l'instruction de lire d'abord `${CLAUDE_PLUGIN_ROOT}/skills/frontend-specialist/references/react-pattern-checklist.md` ;
  - le périmètre d'édition autorisé (mode `implementation`).

### Validation intermédiaire en mode `implementation`

Les deux agents produisent d'abord leur **proposition**. Les présenter ensemble, puis demander via `AskUserQuestion` : **« Appliquer ces propositions ? »**
- **Oui, les deux**
- **Back seulement** / **Front seulement**
- **Ajuster** — l'utilisateur précise, l'agent concerné reformule.
- **Non, on s'arrête là** — sortie en mode `proposition`.

Seulement ensuite, relancer les agents en `implementation` sur le périmètre validé. En cas d'implémentation des deux côtés, l'ordre est indifférent puisque le contrat est figé ; les lancer en parallèle.

Si l'un des agents signale que le contrat est irréalisable ou incomplet, **revenir en Phase 3** : amender le contrat, le refaire valider, puis relancer les deux côtés concernés.

---

## Phase 5 — Contrôle de cohérence

Comparer les deux sorties au contrat validé, opération par opération :

| Point de contrôle | Back | Front |
|---|---|---|
| Méthode + chemin | route exposée | URL appelée |
| Champs de requête (nom, type, obligatoire) | DTO / validations | type de la requête envoyée |
| Champs de réponse (nom, type, nullable) | sérialisation | type de la réponse consommée |
| Codes d'erreur | exceptions → codes HTTP | chaque erreur traitée à l'écran |
| Sécurité | rôles / voter | gestion du 401 / 403 |
| Pagination / filtres | paramètres acceptés | paramètres envoyés |

Restituer ce tableau avec ✅ / ❌ par ligne et par opération. Tout ❌ est corrigé (relance ciblée de l'agent concerné) ou présenté à l'utilisateur avec la décision à prendre.

---

## Phase 6 — Sortie

Selon le mode :
- **`analyse`** — Contrat validé + cartographies back et front, inline. Proposer (sans l'imposer) d'écrire le contrat dans `docs/api-contracts/<slug>.md`.
- **`proposition`** — Contrat + propositions des deux côtés + tableau de cohérence, inline. Proposer d'écrire l'ensemble dans `docs/proposals/fullstack-<slug>.md`.
- **`implementation`** — Fichiers touchés de chaque côté avec un diff résumé, tableau de cohérence, résultats des checks **ciblés** (PHPStan / PHPUnit côté back, lint / typecheck / tests côté front). Proposer (sans agir) de commiter via le skill `git-workflow`, idéalement un commit par côté.

Ne jamais écraser silencieusement un fichier de sortie existant.

---

## Règles transverses

- **Langue** : tout le flow et toutes les questions sont en français.
- **Contrat d'abord** : aucune délégation avant validation du contrat ; aucun changement de contrat sans revalidation.
- **Pas d'écriture prématurée** : aucun fichier modifié avant la validation intermédiaire de la Phase 4.
- **Pas d'invention de pattern** : chaque côté suit les conventions de son repo ; une convention non observée est signalée, pas inventée.
- **Régime toujours explicite** côté back, comme dans `/codebase-toolkit:backend-specialist`.
- **Une feature par invocation** : si le besoin couvre plusieurs features, proposer de découper (éventuellement via `/spec-writer:split-spec-by-layer`) et relancer le skill par feature.
