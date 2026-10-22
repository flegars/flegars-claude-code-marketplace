---
name: split-spec-by-layer
description: "Découpe une User Story ou une spec libre (spec technique, brief, epic) en tasks techniques par couche — BACK, FRONT, INFRA, DATA, QA — cohérentes entre elles grâce à un template de task technique figé (référentiel de couches fermé, contrats d'interface définis une seule fois, socle de Definition of Done par couche, matrice de couverture). Sources : work item Azure DevOps (id/URL), issue ou PR GitHub (URL), fichier .md local ou texte collé. Orchestre un flow en 4 phases : acquisition & cadrage → découpage via l'agent layer-splitter → validation → sortie (inline et/ou fichier docs/specs/). Lecture seule côté Azure DevOps et GitHub. Déclencher quand l'utilisateur dit : /split-spec-by-layer, 'découpe cette spec en tasks techniques', 'découpage back / front / infra', 'fais le découpage technique de cette US', 'répartis cette US par couche', 'quelles tasks techniques pour cette spec', ou fournit une US / spec à décomposer en tasks par couche technique."
user_invocable: true
argument-hint: "[url/id work item ADO | url issue/PR GitHub | chemin .md | spec collée]"
---

# Split Spec By Layer

Orchestre le découpage d'une **US ou d'une spec libre** en **tasks techniques par couche** (`BACK`, `FRONT`, `INFRA`, `DATA`, `QA`). Toutes les tasks suivent le template figé défini dans :
`${CLAUDE_PLUGIN_ROOT}/skills/split-spec-by-layer/references/tech-task-template.md`

Ce template garantit la cohérence des tasks entre elles : référentiel de couches fermé, grille de titre unique, contrats d'interface définis une seule fois, socle de Definition of Done identique par couche, matrice de couverture exigence → tasks.

> ℹ️ Pour un découpage **fonctionnel** d'une US par critère d'acceptance, avec enregistrement dans Azure DevOps, utiliser `/split-us-by-criteria`.

> 🔒 Ce skill est en **lecture seule** vis-à-vis d'Azure DevOps et de GitHub : il ne crée ni work item ni issue. Sa seule écriture possible est un fichier `.md` local, sur confirmation (Phase 4).

## Vue d'ensemble du flow

1. **Acquisition & cadrage** — Récupérer la source, choisir le mode, les couches actives et l'unité d'estimation
2. **Découpage** — Déléguer à l'agent `layer-splitter`
3. **Validation** — Présenter le découpage, ajuster jusqu'à validation
4. **Sortie** — Rendu inline, fichier `docs/specs/`, ou les deux

---

## Phase 1 — Acquisition & cadrage

### Récupérer la source

Si un argument a été passé au slash command (`$ARGUMENTS`), l'interpréter directement :
- **ID ou URL de work item Azure DevOps** (`https://dev.azure.com/<org>/<project>/_workitems/edit/<id>` ou un id numérique) → source **ADO** ;
- **URL d'issue ou de PR GitHub** (`https://github.com/<owner>/<repo>/(pull|issues)/<n>`) → source **GitHub** ;
- **chemin de fichier `.md`** (ex. `docs/user-stories/US-*.md`, `docs/specs/*.md`) → source **locale** ;
- **texte collé** → source **inline**.

Si la source n'est pas évidente, demander via `AskUserQuestion` : **« D'où vient la spec à découper ? »** (Work item Azure DevOps / Issue ou PR GitHub / Fichier local / Texte collé).

**Acquisition selon la source (lecture seule) :**

- **Azure DevOps** — source primaire `az` :
  ```
  az boards work-item show --id <id> --org https://dev.azure.com/INTERINVEST --expand all -o json
  ```
  Fallback MCP `devops` (tool `wit_get_work_item` ou similaire) si `az` indisponible ; dernier recours REST + PAT (PAT demandé à l'utilisateur, **jamais deviné**) :
  ```
  curl -fsSL -u ":<PAT>" "https://dev.azure.com/INTERINVEST/<project>/_apis/wit/workitems/<id>?$expand=all&api-version=7.1"
  ```
- **GitHub** — via `gh` :
  ```
  gh issue view <n> --json title,body,url
  gh pr view <n> --json title,body,url
  ```
- **Locale** — `Read` le fichier `.md`.
- **Inline** — utiliser directement le texte collé.

**Qualifier la source :**
- **US** (présence de « En tant que… » et/ou de critères Gherkin) → les exigences sont les scénarios Gherkin.
- **Spec libre** (spec technique, brief, epic) → les exigences seront extraites et numérotées `EX-XX` par l'agent.

Si la source couvre manifestement plusieurs sujets indépendants (epic très large), le signaler et proposer de découper une partie à la fois.

### Choisir le cadrage

Poser via `AskUserQuestion` (une seule invocation, plusieurs questions) :

1. **« Comment ancrer le découpage ? »**
   - **Spec pure** — à partir du seul texte de la source, sans accès au code. Stack marquée `[HYPOTHÈSE]`.
   - **Ancré codebase** — l'agent explore le repo courant pour détecter la stack réelle et renseigner les fichiers concernés (nécessite un repo).
2. **« Quelles couches sont concernées ? »** (multiSelect) — `BACK`, `FRONT`, `INFRA`, `DATA`, `QA`. Pré-recommander les couches que la source sollicite visiblement ; en mode ancré codebase, tenir compte de ce que le repo contient (ex. pas de front dans un repo API seul).
3. **« Unité d'estimation ? »** — Heures / Story points (1, 2, 3, 5, 8).

Faire un récap bref (source, type US / spec, mode, couches, unité) et confirmer avant de découper.

---

## Phase 2 — Découpage via l'agent layer-splitter

Déléguer le découpage à l'agent `layer-splitter` via le tool `Agent` (subagent_type=`layer-splitter`).

**Prompt à fournir à l'agent** — inclure :
- Le **contenu complet de la source** (titre, description, règles métier, critères / exigences, specs techniques, scope IN/OUT si présents) et son **type** (US / spec libre).
- La référence de la source (ID / URL / chemin) si connue.
- Le **mode** (spec pure / ancré codebase), les **couches actives** et l'**unité d'estimation**.
- L'instruction explicite : « Lire d'abord `${CLAUDE_PLUGIN_ROOT}/skills/split-spec-by-layer/references/tech-task-template.md` puis produire le découpage en suivant ce template à la lettre : en-tête complet (dont tableau récapitulatif et matrice de couverture), un bloc par task, une seule couche par task, contrats définis une seule fois, socle de DoD de la couche repris tel quel. N'utiliser que les couches actives. En mode spec pure, ne jamais inventer de chemin de fichier. »

L'agent retourne le découpage en Markdown, avec d'éventuelles questions ouvertes.

---

## Phase 3 — Validation du découpage

Présenter à l'utilisateur le **tableau récapitulatif**, l'**ordre d'implémentation**, la **matrice de couverture**, le total estimé par couche, et les questions ouvertes éventuelles.

Contrôler avant présentation (et corriger avec l'agent si besoin) :
- aucune exigence orpheline ;
- aucune task multi-couches ni couche hors référentiel ;
- chaque contrat consommé référence une task productrice existante.

Demander via `AskUserQuestion` : **« Ce découpage te convient-il ? »**
- **Valider tel quel**
- **Ajuster** — fusionner, scinder, changer la couche d'une task, réordonner, ré-estimer, revoir un contrat.

Itérer (relancer l'agent ou éditer directement) jusqu'à validation. **Aucune écriture à ce stade.**

---

## Phase 4 — Sortie

Demander via `AskUserQuestion` : **« Où restituer le découpage ? »**
- **Inline** — afficher le découpage complet dans la conversation.
- **Fichier local** — écrire `docs/specs/<slug>-tech-tasks.md`.
- **Les deux**

### Si fichier local

- Slug : extrait du titre de la source (`[Domaine] …` pour une US) en kebab-case ASCII.
- Si le fichier existe déjà : ne **jamais** l'écraser silencieusement — demander s'il faut le remplacer ou suffixer le nom (`-v2`).
- `Write` le découpage complet (créer `docs/specs/` si absent).
- Afficher le chemin créé et proposer (sans agir) de commiter via le skill `git-workflow`.

---

## Règles transverses

- **Langue** : tout le flow et toutes les questions sont en français.
- **Lecture seule externe** : aucune création ni modification dans Azure DevOps ou GitHub. Pour enregistrer des tasks dans Azure DevOps, passer par `/split-us-by-criteria`.
- **PAT jamais deviné** : demandé uniquement si les fallbacks d'acquisition l'exigent.
- **Respect du périmètre** : le découpage couvre exactement la source, sans ajouter ni retirer de fonctionnalité. Chaque exigence est couverte par au moins une task.
- **Une source par invocation** : pour découper plusieurs US / specs, relancer le skill pour chacune.
