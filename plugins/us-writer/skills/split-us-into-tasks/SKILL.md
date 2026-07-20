---
name: split-us-into-tasks
description: "Découpe une User Story déjà rédigée en plusieurs tasks atomiques, puis propose systématiquement de les enregistrer dans Azure DevOps rattachées à l'US parente. Sources de l'US : work item Azure DevOps (id/URL), PR ou issue GitHub (URL), ou fichier .md local / markdown collé en fallback. Orchestre un flow en 4 phases : acquisition de l'US → découpage en tasks via l'agent us-splitter → validation du découpage → enregistrement Azure DevOps (proposé systématiquement). Chaque task suit la structure figée du plugin (titre, Definition of Done, dépendances, estimation). Déclencher quand l'utilisateur dit : /split-us-into-tasks, 'découpe cette US en tasks', 'crée les tasks de cette US', 'split cette US', 'décompose l'US en tâches ADO', 'génère les work items de cette US', ou fournit une US (work item ADO / PR GitHub / fichier) à décomposer en tasks."
user_invocable: true
argument-hint: "[url/id work item ADO | url PR ou issue GitHub | chemin US.md]"
---

# Split US Into Tasks

Orchestre le découpage d'une **User Story déjà rédigée** en plusieurs tasks atomiques et actionnables, puis **propose systématiquement** de créer ces tasks dans Azure DevOps en les rattachant à l'US parente.

C'est l'étape qui suit la rédaction (`/write-us-from-code`, `/write-us-from-brief`) : on part d'une US validée et on produit le plan de travail exécutable. Chaque task suit la structure figée définie dans :
`${CLAUDE_PLUGIN_ROOT}/skills/split-us-into-tasks/references/task-template.md`

> ⚠️ Contrairement aux autres skills de la marketplace (lecture seule), ce skill **écrit dans Azure DevOps**. Aucune création n'a lieu sans confirmation explicite (voir Phase 4).

## Vue d'ensemble du flow

1. **Acquisition de l'US & cadrage** — Récupérer l'US et choisir le mode de découpage
2. **Découpage en tasks** — Déléguer à l'agent `us-splitter` avec l'US et le mode
3. **Validation du découpage** — Présenter les tasks, ajuster jusqu'à validation
4. **Enregistrement Azure DevOps** — Proposer systématiquement de créer les tasks (rattachées à l'US)

---

## Phase 1 — Acquisition de l'US & cadrage du découpage

### Récupérer l'US

Si un argument a été passé au slash command (`$ARGUMENTS`), l'interpréter directement :
- **ID ou URL de work item Azure DevOps** (`https://dev.azure.com/<org>/<project>/_workitems/edit/<id>` ou un id numérique) → source **ADO** ;
- **URL de PR ou d'issue GitHub** (`https://github.com/<owner>/<repo>/(pull|issues)/<n>`) → source **GitHub** ;
- **chemin de fichier `.md`** (souvent `docs/user-stories/US-*.md`) ou **markdown collé** → source **locale** (fallback).

Si la source n'est pas évidente, demander via `AskUserQuestion` : **« D'où vient l'US à découper ? »** (Work item Azure DevOps / PR ou issue GitHub / Fichier local ou US collée).

**Acquisition selon la source :**

- **Azure DevOps** — source primaire `az` :
  ```
  az boards work-item show --id <id> --org https://dev.azure.com/INTERINVEST --expand all -o json
  ```
  Fallback MCP `devops` (tool `wit_get_work_item` ou similaire) si `az` indisponible ; dernier recours REST + PAT (PAT demandé à l'utilisateur, **jamais deviné**) :
  ```
  curl -fsSL -u ":<PAT>" "https://dev.azure.com/INTERINVEST/<project>/_apis/wit/workitems/<id>?$expand=all&api-version=7.1"
  ```
  **Mémoriser** : l'**ID du work item US** (= futur parent des tasks) et le **projet** ADO.

- **GitHub** — via `gh` :
  ```
  gh issue view <n> --json title,body,url
  gh pr view <n> --json title,body,url
  ```
  Aucun ID parent ADO n'est disponible dans ce cas (à demander en Phase 4 si l'utilisateur veut rattacher les tasks).

- **Locale** — `Read` le fichier `.md`, ou utiliser directement le markdown collé.

Extraire de l'US : **titre**, **description**, **critères d'acceptance** (Gherkin), **spécifications techniques**, **scope IN / OUT**.

### Choisir le mode de découpage

Demander via `AskUserQuestion` : **« Comment découper l'US ? »**
- **Fonctionnel pur** — découpage à partir du seul texte de l'US (pas d'accès au code). Fonctionne partout, même sans repo.
- **Ancré codebase** — l'agent explore le repo courant pour mapper chaque task aux fichiers concernés (tasks plus actionnables ; nécessite un repo).

Faire un récap bref du périmètre (US + mode) et confirmer avant de découper.

---

## Phase 2 — Découpage en tasks via l'agent us-splitter

Déléguer le découpage à l'agent `us-splitter` via le tool `Agent` (subagent_type=`us-splitter`).

**Prompt à fournir à l'agent** — inclure :
- Le **contenu complet de l'US** (titre, description, contexte & règles métier, tous les critères d'acceptance, specs techniques, scope IN/OUT).
- Le **mode retenu** (fonctionnel pur / ancré codebase).
- L'ID/URL de l'US parente si connu (pour rappel dans l'en-tête).
- L'instruction explicite : « Lire d'abord `${CLAUDE_PLUGIN_ROOT}/skills/split-us-into-tasks/references/task-template.md` puis produire le découpage en suivant ce template à la lettre. En mode ancré codebase, explorer le repo (`Grep`/`Glob`/`Read`) pour renseigner les fichiers concernés ; en mode fonctionnel pur, omettre cette section. »

L'agent retourne une **liste ordonnée de tasks** en Markdown (en-tête de découpage + un bloc par task conforme au template).

---

## Phase 3 — Validation du découpage

Présenter la liste des tasks à l'utilisateur (titres, DoD, dépendances, estimations, couverture des critères).

Demander via `AskUserQuestion` : **« Ce découpage te convient-il ? »**
- **Valider tel quel**
- **Ajuster** — fusionner, scinder, réordonner, retirer des tasks, ou revoir les estimations.

Itérer (relancer l'agent ou éditer directement) jusqu'à validation. **Aucune écriture (Azure DevOps ou fichier) à ce stade.**

---

## Phase 4 — Enregistrement dans Azure DevOps (proposé systématiquement)

Une fois le découpage validé, **toujours** demander via `AskUserQuestion` :

**« Enregistrer ces N tasks dans Azure DevOps ? »**
- **Oui** — créer les tasks dans Azure DevOps
- **Non** — garder le découpage en local uniquement (rendu inline)
- **Oui + fichier local** — créer les tasks ET écrire `docs/user-stories/US-<slug>-tasks.md`

### Si création Azure DevOps

**Garde-fou (skill mutant)** : avant tout appel `az`, afficher le **récap exact** de ce qui sera créé (nombre de tasks, titres, projet cible, work item parent) et exiger une **confirmation explicite**. Le PAT n'est jamais deviné : le demander uniquement si les fallbacks l'imposent.

1. **Détecter `az`** (source primaire pour l'écriture, comme le plugin `azure-devops`) :
   ```
   command -v az
   az extension show --name azure-devops
   az account show --query user.name -o tsv
   ```
   Si `az` indisponible → fallback MCP `devops` (tools `wit_*` de création de work item). Org par défaut : `INTERINVEST`.

2. **Déterminer le projet** :
   - Connu si l'US vient d'Azure DevOps (repris de Phase 1).
   - Sinon lister et demander : `az devops project list -o table`.

3. **Déterminer le parent** :
   - ID de l'US repris de Phase 1 si source ADO.
   - Si source GitHub / fichier : demander l'ID du work item US parent dans Azure DevOps (ou créer des tasks **sans parent** si l'utilisateur n'en fournit pas).

4. **Créer chaque task** (récupérer l'`id` retourné) :
   ```
   az boards work-item create --type Task \
     --title "<titre de la task>" \
     --description "<description + Definition of Done>" \
     --org https://dev.azure.com/INTERINVEST \
     --project "<projet>" \
     -o json
   ```
   Optionnel selon la demande utilisateur : `--assigned-to "<email>"`, `--iteration "<Projet\\Sprint>"`.

5. **Rattacher chaque task à l'US parente** (si parent connu) :
   ```
   az boards work-item relation add --id <TASK_ID> \
     --relation-type parent --target-id <US_ID> \
     --org https://dev.azure.com/INTERINVEST
   ```

6. **Restituer** un tableau récapitulatif : ID de chaque task créée + URL `https://dev.azure.com/INTERINVEST/<project>/_workitems/edit/<id>`.

### Si fichier local demandé

- Slug : extrait du titre de l'US `[Domaine] …` en kebab-case ASCII (même convention que `write-us-from-code`).
- `Write` le découpage dans `docs/user-stories/US-<slug>-tasks.md` (créer `docs/user-stories/` si absent).
- Afficher le chemin créé et proposer (sans agir) de commiter via le skill `git-workflow`.

---

## Règles transverses

- **Langue** : tout le flow et toutes les questions sont en français.
- **Garde-fou écriture** : aucune création Azure DevOps ni fichier avant la Phase 4, et jamais sans confirmation explicite de l'utilisateur. Ce skill est le seul de la marketplace à modifier Azure DevOps.
- **PAT jamais deviné** : demandé uniquement si les fallbacks l'exigent.
- **Respect du périmètre** : le découpage couvre exactement l'US, sans ajouter ni retirer de fonctionnalité. Chaque critère d'acceptance est couvert par au moins une task.
- **Une seule US par invocation** : pour découper plusieurs US, relancer le skill pour chacune.
