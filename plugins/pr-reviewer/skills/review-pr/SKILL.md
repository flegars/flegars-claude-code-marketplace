---
name: review-pr
description: "Lance une review standardisée d'une Pull Request GitHub ou Azure DevOps. Orchestre un flow en 5 phases : cible de la PR → fetch PR + US/work items rattachés → détection de la stack → analyse via l'agent pr-reviewer → sortie (commentaires inline sur la PR ou fichier markdown local). Note /20 hybride (14 pts universels + 6 pts adaptatifs par stack). Déclencher quand l'utilisateur dit : /review-pr, 'review cette PR', 'fais une review', 'note ma PR', 'review la PR <url>', ou fournit une URL GitHub/Azure DevOps de PR."
user_invocable: true
---

# Review PR

Orchestre une review de Pull Request **standardisée**, exhaustive et reproductible : note /20 + ressenti général + axes d'amélioration + alignement explicite avec les User Stories ou work items rattachés.

Plateformes supportées : **GitHub** (via `gh` CLI) et **Azure DevOps** (via le MCP `devops` quand il est disponible).

## Vue d'ensemble du flow

1. **Cible** — Identifier la PR à reviewer
2. **Fetch** — Récupérer la PR + les US/work items rattachés
3. **Détection stack** — Identifier la sous-grille adaptative à appliquer
4. **Analyse** — Déléguer à l'agent `pr-reviewer`
5. **Sortie** — Publier en inline sur la PR ou écrire un fichier markdown local

---

## Arguments du slash command

```
/review-pr [url] [--inline | --local]
```

- `url` (optionnel) — URL de la PR (GitHub ou Azure DevOps). Si omis, voir Phase 1.
- `--inline` (optionnel) — Force le mode commentaires inline + commentaire global sur la PR.
- `--local` (optionnel) — Force le mode fichier markdown dans `reviews/`.

Si aucun mode n'est passé, demander à l'utilisateur en Phase 5.

---

## Phase 1 — Cibler la PR

### Si une URL a été fournie en argument

- Parser l'URL pour identifier la plateforme :
  - Host contient `github.com` → plateforme `github`, extraire `owner/repo` + `pr_number`
  - Host contient `dev.azure.com` ou `visualstudio.com` → plateforme `azure-devops`, extraire `organization/project/repo` + `pullRequestId`
- Si l'URL n'est ni l'un ni l'autre, demander confirmation/correction à l'utilisateur.

### Si aucune URL n'a été fournie

Détecter automatiquement dans l'ordre :

1. **Branche courante avec PR ouverte sur GitHub** :
   ```bash
   gh pr view --json url,number,title,state 2>/dev/null
   ```
   Si une PR existe pour la branche courante, proposer à l'utilisateur via `AskUserQuestion` : `Reviewer la PR <numéro> (<titre>) ?` (Oui / Non, j'en spécifie une autre).

2. **MCP `devops` disponible** (Azure DevOps) :
   - Lister les PR actives de l'utilisateur courant via le MCP.
   - Proposer la sélection via `AskUserQuestion` si plusieurs sont actives.

3. **Aucune détection** :
   - Demander l'URL via `AskUserQuestion` : « Quelle PR veux-tu reviewer ? (URL complète) ».

---

## Phase 2 — Fetch PR + US rattachés

### GitHub

Récupérer les métadonnées :

```bash
gh pr view <number> --json number,title,body,author,baseRefName,headRefName,url,labels,state,files
```

Récupérer le diff complet :

```bash
gh pr diff <number>
```

Identifier les **issues rattachées** :
- Parser le `body` de la PR pour les patterns : `closes #N`, `fixes #N`, `resolves #N`, `close #N`, `fix #N`, `resolve #N` (insensible à la casse).
- Pour chaque issue trouvée, récupérer son contenu :
  ```bash
  gh issue view <N> --json number,title,body,labels,state
  ```
- Inclure aussi les liens cross-repo `owner/repo#N` si présents.

Si le repo distant n'est pas `origin` ou si `gh` n'est pas authentifié pour ce repo, le signaler à l'utilisateur et demander une alternative.

### Azure DevOps

Utiliser le MCP `devops` (org `INTERINVEST` par défaut, configuré dans `~/.claude/config.json`). Si le MCP n'est pas disponible, signaler à l'utilisateur que la review ne peut pas se faire sans accès et stopper.

Récupérer (via les tools du MCP) :
1. **PR details** : titre, description, auteur, branches source/cible, état, fichiers modifiés.
2. **PR diff** : diff complet de la PR.
3. **Work items liés** : work items rattachés à la PR (lien explicite, ou détectés via les `#<id>` dans la description / les commits).
4. **Pour chaque work item lié** : titre, description, critères d'acceptance, état.

### Cas où aucune US/work item n'est rattaché

- Détecter le type de la PR via le titre/labels : `chore`, `docs`, `refactor`, `hotfix`, `fix`, `feat`.
- Si type ∈ {`chore`, `docs`, `refactor`} → ce sera signalé en Phase 4 et le critère « Alignement US » sera marqué `N/A 2/2`.
- Sinon → signaler à l'utilisateur via `AskUserQuestion` : « Aucune US/work item rattaché à cette PR. Veux-tu (a) en spécifier un manuellement, ou (b) lancer la review avec critère plafonné à 0 ? ».

---

## Phase 3 — Détecter la stack

Lire les fichiers de manifest à la racine du repo, dans cet ordre :

| Fichier détecté | Stack |
|---|---|
| `composer.json` mentionnant `symfony/*` ou `api-platform/core` | `symfony` |
| `go.mod` | `go` |
| `package.json` mentionnant `react` ou `next` | `typescript-react` |
| `pyproject.toml` ou `setup.py` ou `requirements.txt` (et pas de `go.mod`) | `python` |
| Aucun des ci-dessus, ou stack mixte ambiguë | `générique` |

Si plusieurs stacks coexistent (monorepo) : appliquer la stack **majoritaire dans les fichiers modifiés du diff**. Si toujours ambigu, demander confirmation via `AskUserQuestion`.

Garder la stack identifiée pour la passer à l'agent.

---

## Phase 4 — Analyse via l'agent `pr-reviewer`

Déléguer à l'agent `pr-reviewer` via le tool `Agent` (subagent_type=`pr-reviewer`).

**Prompt à fournir à l'agent** — inclure obligatoirement :

1. **PR metadata** :
   - url
   - plateforme (`github` ou `azure-devops`)
   - id
   - titre
   - description (body)
   - auteur
   - branche source → branche cible
   - labels
   - état

2. **Diff complet** — tel que récupéré en Phase 2.

3. **US/Work items rattachés** — pour chacun : id, titre, description, critères d'acceptance, état. Ou la mention explicite « Aucun rattaché — type <X> » selon la Phase 2.

4. **Stack détectée** — `symfony` / `go` / `typescript-react` / `python` / `générique`, déterminée en Phase 3.

5. **Mode de sortie** — `inline` ou `local`, déterminé en Phase 5 (à demander **avant** l'appel à l'agent).

6. **Instruction explicite** :
   > « Lis d'abord `${CLAUDE_PLUGIN_ROOT}/skills/review-pr/references/scoring-rubric.md` et `${CLAUDE_PLUGIN_ROOT}/skills/review-pr/references/review-template.md`. Produis le rapport en respectant strictement ces deux références. Pas de section renommée, pas de section sautée si obligatoire. »

L'agent retourne :
- Le **rapport complet en markdown** (titre + sections du template).
- Si mode `inline` : en plus, une liste structurée de commentaires inline (path, line, severity, body).

---

## Phase 5 — Sortie

**Demander le mode de sortie via `AskUserQuestion` si non précisé en argument** :

- **Commentaires inline sur la PR (recommandé)** — Rapport global + commentaires inline directement sur la PR distante.
- **Fichier markdown local** — Écrit dans `reviews/PR-<id>.md` à la racine du repo courant. Pas de pollution de la PR distante.
- **Les deux** — Inline ET fichier local.

### Si mode `inline`

#### GitHub

1. Poster le rapport global comme commentaire sur la PR :
   ```bash
   gh pr comment <number> --body-file <fichier_temp_du_rapport>
   ```

2. Poster chaque commentaire inline via l'API GitHub (le `gh pr comment` standard ne supporte pas l'inline — il faut passer par `gh api`) :
   ```bash
   gh api -X POST repos/<owner>/<repo>/pulls/<number>/comments \
     -f body="<body du commentaire>" \
     -f commit_id="<head_sha>" \
     -f path="<file path>" \
     -F line=<line> \
     -f side="RIGHT"
   ```
   Où `<head_sha>` vient de `gh pr view <number> --json headRefOid -q .headRefOid`.

3. Confirmer à l'utilisateur les ressources créées (URL du commentaire global + nombre de commentaires inline).

#### Azure DevOps

1. Poster le rapport global comme commentaire de la PR via le MCP `devops` (créer un thread de discussion sans contexte fichier).
2. Pour chaque commentaire inline, créer un thread de discussion attaché à `path:line` du PR iteration courant via le MCP.
3. Confirmer à l'utilisateur les ressources créées.

#### Si publication impossible (auth, permissions, MCP indisponible)

- Ne pas perdre le rapport : **fallback automatique en mode `local`** + message explicite à l'utilisateur expliquant pourquoi l'inline a échoué.

### Si mode `local`

1. Créer le dossier `reviews/` à la racine du repo si nécessaire.
2. Déterminer le nom du fichier :
   - Si `reviews/PR-<id>.md` n'existe pas → utiliser ce nom.
   - Sinon → suffixer avec timestamp `reviews/PR-<id>-YYYY-MM-DDTHHhMM.md` (jamais d'écrasement).
3. Préfixer le rapport avec le front-matter défini dans `review-template.md` (pr, plateforme, auteur, branche, date_review, us_rattachees).
4. `Write` le fichier.
5. Afficher le chemin créé à l'utilisateur.
6. Proposer (sans agir) de commiter via le skill `git-workflow` si disponible.

### Si mode `les deux`

Exécuter d'abord `local` (pas de risque), puis `inline`. Si `inline` échoue, l'utilisateur a déjà le fichier local.

---

## Règles transverses

- **Langue** : tout le flow, toutes les questions, et le rapport final sont en **français**.
- **Pas de modification du repo courant** sans accord explicite : seul l'écriture dans `reviews/` est autorisée en mode `local`, et la création de ce dossier est explicite.
- **Pas de publication silencieuse** : en mode `inline`, toujours confirmer à l'utilisateur ce qui va être posté **avant** la publication. Lui montrer le rapport et lui demander une dernière confirmation `AskUserQuestion` : « Publier la review sur la PR ? » (Oui / Non, montrer en local seulement / Modifier avant de publier).
- **Pas d'invention de US** : si aucune n'est rattachée, le rapport doit l'indiquer explicitement (pas de bricolage).
- **Confidentialité** : ne pas inclure dans un commentaire public d'éventuelles infos sensibles vues dans le repo (clés API, secrets) — si tu en repères dans le diff, le signaler en `🐛 Problèmes critiques` du rapport mais sans recopier la valeur.
- **Une seule review par invocation** : ne pas enchaîner sur plusieurs PR en série. Une PR = un appel du skill.
