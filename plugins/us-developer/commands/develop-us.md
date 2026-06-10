---
description: "Développe une User Story au périmètre strict : acquisition multi-sources (GitHub / Azure DevOps / fichier .md / markdown collé), extraction des critères d'acceptation, plan, gates de clarification + validation, implémentation, tests critère-par-critère, rapport de traçabilité."
argument-hint: "<github-url | azure-url | chemin.md | markdown> [--auto]"
---

# /us-developer:develop-us

Développe la User Story passée en `$ARGUMENTS` en respectant son périmètre **strict** : rien de moins (chaque critère d'acceptation est couvert ou explicitement signalé), rien de plus (pas de gold-plating, pas de feature « bonus », pas de modification hors périmètre).

L'orchestration suit **7 étapes** dans l'ordre. Les **gates** sont des points d'arrêt explicites. Toute décision technique non spécifiée par l'US doit apparaître dans le **journal des hypothèses** du rapport final.

---

## 0. Lecture de `$ARGUMENTS`

`$ARGUMENTS` contient :

- **Source de l'US** (obligatoire) : URL GitHub / URL Azure DevOps / chemin de fichier `.md` / bloc markdown collé.
- **Flag `--auto`** (optionnel) : si présent, ne pas s'arrêter au gate de validation du plan (étape 5). Tous les autres gates (notamment le gate clarification de l'étape 3) restent actifs.

Extraire la source et le flag avant tout le reste. Si `$ARGUMENTS` est vide ou si le type de source ne peut pas être identifié sans ambiguïté, **demander à l'utilisateur** via `AskUserQuestion` plutôt que de deviner.

---

## 1. Acquisition

**Auto-détection du type de source** sur l'argument fourni :

| Forme reconnue | Type | Outil de récupération |
|---|---|---|
| URL `https://github.com/<owner>/<repo>/issues/<n>` | GitHub issue | `gh issue view <n> --repo <owner>/<repo> --json title,body,labels,number,url` |
| URL `https://github.com/<owner>/<repo>/pull/<n>` | GitHub PR | `gh pr view <n> --repo <owner>/<repo> --json title,body,labels,number,url` |
| URL `https://dev.azure.com/<org>/<project>/_workitems/edit/<id>` ou `https://<org>.visualstudio.com/.../_workitems/edit/<id>` | Azure DevOps work item | MCP `devops` (`work-item show`) → fallback `az boards work-item show --id <id> --org <org>` → fallback API REST avec PAT |
| Chemin se terminant par `.md` existant sur disque | Fichier markdown local | `Read` |
| Texte commençant par `#`, `##`, `En tant que`, ou contenant des sections markdown | Markdown collé | utiliser tel quel |

**Règles de fallback** :

1. **GitHub** : si `gh` est indisponible (`command -v gh` échoue) ou non authentifié (`gh auth status` KO), basculer sur l'API REST publique (`curl -fsSL https://api.github.com/repos/<owner>/<repo>/issues/<n>`) en signalant la limitation (rate limit, repo privé non accessible). Si le repo est privé et que `gh` n'est pas dispo, **s'arrêter** et le dire.
2. **Azure DevOps** : priorité au MCP `devops` (org INTERINVEST par défaut). Si MCP indisponible, tenter `az boards work-item show`. Si `az` indisponible aussi, tenter API REST (`https://dev.azure.com/<org>/<project>/_apis/wit/workitems/<id>?$expand=all&api-version=7.1`) en demandant le PAT à l'utilisateur. Si rien ne fonctionne, **s'arrêter** et le dire.
3. **Fichier .md** : si le chemin n'existe pas, **s'arrêter** et redemander.
4. **Type non identifiable** : `AskUserQuestion` parmi les 4 types possibles + « Aucun, je précise autrement ».

**Sortie de l'étape 1** : le contenu brut de l'US (markdown ou texte structuré), avec sa provenance et son identifiant lisible (ex : `GitHub #142 — owner/repo`, `ADO #1247 — INTERINVEST/CompanyManagement`, `docs/us/US-foo.md`, `inline`).

---

## 2. Extraction structurée

Déléguer à l'agent `us-analyst` (`subagent_type=us-analyst`) avec en entrée :

- La source identifiée à l'étape 1
- Le contenu brut

L'agent produit un **bloc structuré** comportant **exactement** les sections suivantes :

1. **Objectif métier** — Une à trois phrases, sans interprétation ajoutée.
2. **Périmètre IN** — Liste des éléments explicitement demandés par l'US.
3. **Périmètre OUT** — Liste des éléments explicitement exclus par l'US (ou présents dans une section « Scope OUT », « Hors périmètre », « Non couvert »).
4. **Critères d'acceptation** — Chaque critère reformulé en énoncé **testable** (sujet + action + résultat observable mesurable). Numéroter `AC-01`, `AC-02`, ...
5. **Contraintes techniques explicites** — Uniquement ce que l'US mentionne (perf, sécurité, API, format, idempotence...). **Ne pas inventer.**
6. **Zones non spécifiées / ambiguïtés** — Toute zone où l'US laisse une marge d'interprétation. Lister sous forme de questions précises.

L'agent ne devine **rien**. S'il manque une section dans l'US source, il l'écrit explicitement (« Non précisé dans la source »).

---

## 3. Gate clarification

Si l'étape 2 produit **au moins une** des conditions suivantes :

- Aucun critère d'acceptation identifié dans la source
- Au moins une **ambiguïté bloquante** (un critère ne peut pas être codé ni testé sans décision externe)
- Un contradiction interne dans l'US

→ **S'arrêter** et poser les questions à l'utilisateur via `AskUserQuestion`. Une fois les réponses obtenues, mettre à jour le bloc structuré (réintégrer les réponses dans les sections appropriées, marquer chaque clarification en `[CLARIFIÉ]`).

**Ne jamais** inventer un critère d'acceptation, un format, une valeur par défaut, un comportement d'erreur ou un périmètre.

Les ambiguïtés **non bloquantes** (préférence de naming, choix d'un helper interne équivalent, etc.) sont reportées dans le **journal des hypothèses** du rapport final, pas en gate.

---

## 4. Plan

Toujours via l'agent `us-analyst`, produire un **plan d'implémentation** :

1. **Exploration codebase** — Lire `CLAUDE.md` (racine + sous-dossiers s'il y en a), inspecter les conventions du repo (structure, framework, lib de test, lint/typecheck). Identifier les fichiers et symboles **directement liés** au périmètre IN.
2. **Mapping critère → fichiers → tests** — Sous forme de tableau :

   | Critère | Fichiers à créer/modifier (path) | Test(s) prévu(s) (path + nom) | Notes |
   |---|---|---|---|
   | AC-01 | `src/...` | `tests/...` | ... |
   | ... | ... | ... | ... |

3. **Décisions techniques par défaut à valider** — Lister tout choix qui n'est pas spécifié par l'US et qui devra apparaître dans le journal des hypothèses (ex : nom de la route, format précis du payload, code HTTP en erreur, mécanisme d'idempotence).
4. **Effets hors-périmètre identifiés** — Bugs ou améliorations repérés à proximité mais **délibérément non traités** (ils iront dans la section dédiée du rapport final).

**Ancrage** : tout fichier mentionné doit exister (ou être justifié comme création nécessaire) ; tout pattern « du projet » doit citer un fichier précis (`path:line`).

---

## 5. Gate validation

Restituer à l'utilisateur :

- Le **bloc structuré** (étape 2 + clarifications de l'étape 3)
- Le **plan** (étape 4)
- Le **journal des hypothèses provisoire** (décisions techniques par défaut)

Par défaut, **s'arrêter ici** via `AskUserQuestion` :

- **Implémenter le plan tel quel**
- **Implémenter avec ces ajustements** (l'utilisateur précise)
- **Annuler / re-cadrer l'US**

Si `--auto` est présent dans `$ARGUMENTS`, **ne pas s'arrêter** : enchaîner directement sur l'étape 6 en logguant le plan validé d'office. Le gate clarification (étape 3) reste actif même en `--auto`.

---

## 6. Implémentation

Coder le plan validé dans le **thread principal** (pas via sous-agent : c'est le contexte qui doit garder la main sur le code écrit).

Règles non négociables :

- **Ne rien ajouter** qui ne soit pas demandé par l'US. Pas de helper « bonus », pas d'abstraction prématurée, pas de refactor opportuniste, pas d'amélioration UX « tant que j'y suis ».
- **Ne rien omettre** : si un critère ne peut pas être implémenté (dépendance manquante, accès bloqué), **le signaler** dans le rapport final plutôt que de le sauter silencieusement.
- **Respecter les conventions du repo** (lint, formatage, structure de dossiers, naming, lib de test) identifiées à l'étape 4.
- **Ne pas modifier de code hors périmètre**, même si un bug est repéré à côté. Le bug part dans la section « Bugs hors-périmètre repérés » du rapport.
- **Idempotence et erreurs** : implémenter exactement ce que l'US dit. Si l'US ne précise pas un cas d'erreur, appliquer la convention par défaut du repo (ancrée sur un fichier) et l'écrire dans le journal des hypothèses.

Au fil de l'implémentation, mettre à jour la trace `critère → fichiers modifiés` pour le rapport final.

---

## 7. Vérification + Rapport

### 7.1 Vérification

Pour **chaque critère** `AC-XX` :

- Écrire ou compléter un test qui formalise le critère (unitaire, intégration, fonctionnel — selon la convention du repo).
- Exécuter la suite de tests ciblée sur les fichiers modifiés (commande détectée à l'étape 4 : `vendor/bin/phpunit`, `pnpm test`, `pytest`, etc.).
- Lancer lint + typecheck si configurés (PHPStan, Psalm, ESLint, tsc, mypy, ruff, etc.).
- Lancer LSP diagnostics si l'extension LSP est disponible dans le projet.

Si une commande de test/lint n'est pas identifiable depuis le repo, **le signaler** dans le rapport plutôt que d'inventer.

Ensuite, déléguer à l'agent `us-reviewer` (`subagent_type=us-reviewer`) avec en entrée :

- Le bloc structuré finalisé
- Le journal des hypothèses
- La liste des fichiers modifiés (`git diff --name-only` + diffs si volumineux)
- La liste des tests ajoutés/modifiés
- Le résultat des commandes de test / lint

L'agent vérifie :

1. **Couverture** — Chaque `AC-XX` est-il couvert par au moins un test ? Si non, lequel et pourquoi ?
2. **Périmètre strict** — Y a-t-il du code ajouté qui ne sert aucun `AC-XX` ? Listing.
3. **Hypothèses non documentées** — Y a-t-il des décisions techniques visibles dans le diff qui ne figurent pas dans le journal des hypothèses ? Listing.
4. **Régression** — Les tests existants passent-ils ?

Sortie : une **fiche de revue** structurée à intégrer au rapport final.

### 7.2 Rapport final

Restituer un rapport markdown dans la conversation, structuré ainsi :

```markdown
# Rapport d'implémentation — <identifiant lisible de l'US>

## 📋 Source
- Type : <github-issue | github-pr | azure-workitem | fichier-md | markdown-inline>
- Référence : <url ou chemin>

## 🎯 Objectif métier
<reproduction de l'étape 2>

## ✅ Couverture critère → implémentation → test

| Critère | Énoncé | Fichiers impactés | Tests | Statut |
|---|---|---|---|---|
| AC-01 | ... | `src/...:L42` | `tests/...:test_xxx` | ✅ Couvert |
| AC-02 | ... | ... | ... | ⚠️ Partiel — <raison> |
| AC-03 | ... | — | — | ❌ Non couvert — <raison> |

## 🧠 Journal des hypothèses
Décisions techniques **non spécifiées par l'US** que j'ai prises pour avancer.
Chaque ligne = une décision + sa justification + comment la remettre en cause.

- **<décision>** — <pourquoi cette valeur par défaut> — *À confirmer : <oui/non, avec qui>*
- ...

## 🚫 Hors périmètre (délibérément exclu)
Éléments **explicitement non traités** parce qu'absents du périmètre IN.

- ...

## 🐞 Bugs hors-périmètre repérés (non corrigés)
Anomalies vues en passant, **non corrigées** parce que hors US. Listées pour création de tickets.

- `path/file.ext:42` — <description courte>
- ...

## 🧪 Vérification
- Tests exécutés : <commande> → <résultat>
- Lint/typecheck : <commande> → <résultat>
- Revue par `us-reviewer` : <synthèse>

## ⚠️ Limitations
- ...
```

Si **un seul** critère est non couvert sans justification explicite, le marquer en `❌` et le faire ressortir en tête de rapport.

---

## Règles transverses

- **Langue** : tout en français (rapports, gates, questions). Termes techniques en anglais quand standards (issue, PR, work item, payload, endpoint, idempotence, lint...).
- **Pas de gold-plating** : si une décision « rendrait le code mieux » mais n'est pas demandée par l'US, elle n'est **pas** prise. Elle peut être notée dans `🐞 Bugs hors-périmètre repérés` ou dans `🧠 Journal des hypothèses` si elle a une conséquence visible.
- **Pas de devinette silencieuse** : tout ce qui n'est pas dans l'US et qui apparaît dans le code → journal des hypothèses.
- **Une seule US par invocation** : si la source contient en réalité plusieurs sujets (epic), s'arrêter au gate clarification et proposer un découpage (potentiellement via le plugin `codebase-to-us`).
- **Pas d'écriture prématurée** : avant le gate de validation (étape 5), **aucun fichier source du repo n'est modifié**. Les seules actions autorisées sont des lectures et des commandes en mode read-only.
- **Modifications de code hors périmètre interdites**, même cosmétiques. Tout findng latéral va dans le rapport.

## Pré-requis et fallbacks

| Source | Outil principal | Fallback 1 | Fallback 2 |
|---|---|---|---|
| GitHub | `gh` CLI authentifiée | API REST publique (sans auth) | s'arrêter et demander |
| Azure DevOps | MCP `devops` | `az boards work-item show` | API REST + PAT (demandé à l'utilisateur) |
| Fichier `.md` | `Read` | — | — |
| Markdown inline | passage direct | — | — |

Si un fallback est utilisé, **le signaler** dans la section `⚠️ Limitations` du rapport final.
