---
name: daily-activity
description: "Récapitule l'activité Azure DevOps de l'utilisateur courant sur les dernières 24 heures glissantes : Pull Requests, commits, work items, threads de PR. Source primaire = `az` CLI (extension `azure-devops`) ; fallback = MCP `devops` si `az` indisponible. Orchestre un flow en 4 phases : préparation (fenêtre 24h, vérification source, résolution `@me`) → collecte multi-projets → filtrage par fenêtre temporelle → restitution (résumé groupé par type + timeline chronologique inversée). Déclencher quand l'utilisateur dit : /daily-activity, 'qu'est-ce que j'ai fait aujourd'hui sur ADO', 'mon activité ADO 24h', 'recap ado', 'standup ado', 'prépare mon daily'."
user_invocable: true
---

# Daily Activity (Azure DevOps)

Produit un récapitulatif **standardisé** de l'activité de l'utilisateur courant sur Azure DevOps pour les **dernières 24 heures glissantes** (fenêtre `now − 24h` → `now`).

**Source primaire** : `az` CLI avec l'extension `azure-devops` (org `INTERINVEST` par défaut).
**Fallback** : MCP `devops` configuré dans `~/.claude/config.json` — utilisé uniquement si `az` est absent / non authentifié / si l'extension `azure-devops` n'est pas installée.

Cas d'usage typique : préparer son daily, retrouver ce sur quoi on a touché avant un changement de contexte, auditer ses propres traces. **Read-only** : aucune écriture côté ADO (uniquement `az ... list/show/query` et `az rest --method get`).

## Vue d'ensemble du flow

1. **Préparation** — Calculer la fenêtre, sélectionner la source (az → MCP fallback), résoudre l'identité `@me`
2. **Collecte** — Pour chaque projet de l'org, agréger PRs / commits / work items / threads
3. **Filtrage** — Ne garder que les événements dans la fenêtre 24h
4. **Restitution** — Rapport markdown : résumé groupé + timeline chronologique inversée

---

## Arguments du slash command

```
/daily-activity [--hours=N] [--project=<project>] [--org=<org>] [--save]
```

- `--hours=N` (optionnel) — Étend ou raccourcit la fenêtre glissante (défaut : `24`). Exemple : `--hours=48` pour un récap week-end.
- `--project=<project>` (optionnel) — Restreint la collecte à un seul projet ADO au lieu de scanner toute l'org. Match par nom exact (insensible à la casse) ou par id.
- `--org=<org>` (optionnel) — Surcharge l'org cible (défaut : `INTERINVEST`). Accepter le nom court ou l'URL complète `https://dev.azure.com/<org>`.
- `--save` (optionnel) — Force la sauvegarde du rapport dans `daily-activity/YYYY-MM-DD.md`.

Aucun argument n'est obligatoire. Le mode par défaut = 24h, toute l'org INTERINVEST, sortie inline.

---

## Phase 1 — Préparation

### 1.1 Calculer la fenêtre temporelle

- `now` = timestamp courant UTC (ISO 8601).
- `since` = `now − N heures` où `N` = valeur de `--hours` ou `24`.
- Conserver ces deux bornes — toutes les comparaisons ultérieures se font dessus.

### 1.2 Sélectionner la source (az CLI → MCP fallback)

**Tester la source primaire `az` CLI** dans cet ordre, **arrêter au premier échec et basculer en fallback MCP** :

1. Binaire disponible : `command -v az` (échoue si Azure CLI n'est pas installé)
2. Extension installée : `az extension show --name azure-devops` (échoue si l'extension n'est pas installée)
3. Authentification valide : `az account show --query user.name -o tsv` (échoue si non connecté)
4. Org joignable : `az devops project list --org https://dev.azure.com/<org> --query "value[0].name" -o tsv` (échoue si l'org est inaccessible ou le PAT/login n'a pas les droits)

**Si toutes les étapes 1-4 passent → mode `az`** (variable interne `source=az`).

**Si l'une échoue → fallback MCP `devops`** :
- Vérifier qu'au moins un tool `mcp__*devops*__*` est exposé dans la session.
- Si oui → mode `mcp` (variable interne `source=mcp`), et signaler à l'utilisateur dans le rapport final, section `⚠️ Limitations` : « Source utilisée : MCP `devops` (fallback) — la CLI `az` n'était pas opérationnelle. Détail : <message d'erreur de l'étape qui a échoué>. »
- Si non → **stopper le flow** avec ce message :
  ```
  Aucune source ADO disponible :
  - `az` CLI : <raison>
  - MCP `devops` : non exposé dans cette session
  Installe `az` + l'extension `azure-devops` (`az extension add --name azure-devops`)
  et connecte-toi (`az login` + `az devops login --org https://dev.azure.com/<org>`),
  ou vérifie `~/.claude/config.json` pour le MCP.
  ```

**Pour fixer les defaults `az` après détection** (uniquement en mode `az`) :
```bash
az devops configure --defaults organization=https://dev.azure.com/<org>
```
Cette ligne évite de répéter `--org` à chaque appel, mais elle est **optionnelle** : tous les appels qui suivent passent quand même `--org` explicitement pour rester reproductibles.

### 1.3 Résoudre l'identité `@me`

**Mode `az`** :
```bash
EMAIL=$(az account show --query user.name -o tsv)
az devops user show --user "$EMAIL" --org https://dev.azure.com/<org> -o json
```
- Conserver `uniqueName` (email), `displayName`, `descriptor`, `id`.
- Si `az devops user show` n'est pas disponible (ancienne version d'extension), se rabattre sur `$EMAIL` seul et le passer en `--creator` / `--reviewer` aux étapes suivantes.

**Mode `mcp`** :
- Appeler le tool MCP qui retourne l'utilisateur authentifié (`core_get_identity_ids` / `user_get_authenticated` / équivalent).
- Conserver les mêmes champs.

Si la résolution échoue : afficher l'erreur brute et stopper.

### 1.4 Lister les projets cibles

**Si `--project` est fourni** :
- Mode `az` : `az devops project show --project "<project>" --org <url> -o json` (match par nom ou id).
- Mode `mcp` : équivalent (`core_get_project` / `core_list_projects` + match).
- Si introuvable, demander via `AskUserQuestion` une correction parmi les projets disponibles.

**Sinon** :
- Mode `az` : `az devops project list --org <url> --query "value[].{id:id,name:name}" -o json`
- Mode `mcp` : `core_list_projects` équivalent.
- Conserver `id` et `name` pour chaque projet actif.

---

## Phase 2 — Collecte par projet

Pour **chaque projet retenu en Phase 1**, exécuter les sous-étapes ci-dessous **en parallèle quand c'est possible** (un groupe d'appels par projet, en un seul tour de tool calls).

L'objectif n'est pas d'être exhaustif sur les noms exacts des commandes — utiliser les capacités équivalentes exposées par la source au moment de l'exécution. Si une capacité manque, le signaler dans le rapport final dans une section `⚠️ Limitations`.

> **Toutes les commandes `az` ci-dessous sont read-only** (`list`, `show`, `query`, `az rest --method get`). Aucune commande mutante ne doit être lancée par ce skill.

### 2.1 Pull Requests

**Mode `az`** :

PRs créées par moi (sur la fenêtre) :
```bash
az repos pr list \
  --org https://dev.azure.com/<org> --project "<project>" \
  --creator "$EMAIL" \
  --status all \
  --output json
```

PRs où je suis reviewer :
```bash
az repos pr list \
  --org https://dev.azure.com/<org> --project "<project>" \
  --reviewer "$EMAIL" \
  --status all \
  --output json
```

Pour chaque PR retournée :
- Refiltrer côté client sur la fenêtre via `creationDate`, `closedDate`, `lastMergeCommit.committer.date`.
- Détailler si nécessaire : `az repos pr show --id <id> --org <url>` pour récupérer `lastMergeCommit` et le statut courant.

**Mode `mcp`** : utiliser les tools équivalents (`repo_list_pull_requests_by_creator`, `repo_list_pull_requests_by_reviewer`, etc.).

Pour chaque PR, conserver :
- `pullRequestId`, `title`, `repository.name`, `sourceRefName → targetRefName`
- `status` (`active` / `completed` / `abandoned`)
- `creationDate`, `closedDate` (si présent), `lastMergeCommit.committer.date`
- `url` web reconstruite : `https://dev.azure.com/<org>/<project>/_git/<repo>/pullrequest/<id>`
- Booléens : `j'ai créé`, `j'ai mergé`, `j'ai commenté` (dépend de 2.4), `je suis reviewer`

### 2.2 Commits

`az` n'expose **pas** de commande native pour lister les commits d'un repo. Deux stratégies, dans cet ordre :

**A. Via `az rest` (recommandé en mode `az`)** :

Lister les repos du projet :
```bash
az repos list --org <url> --project "<project>" --query "[].{id:id,name:name}" -o json
```

Pour chaque repo, requêter les commits filtrés par auteur et date côté serveur :
```bash
az rest --method get \
  --url "https://dev.azure.com/<org>/<project>/_apis/git/repositories/<repoId>/commits" \
  --url-parameters \
    "searchCriteria.author=$EMAIL" \
    "searchCriteria.fromDate=$SINCE_ISO" \
    "searchCriteria.toDate=$NOW_ISO" \
    "api-version=7.1"
```

Conserver : `commitId` (court 7 chars), `comment` (1re ligne uniquement), `<repo>`, `author.date`, `url` web reconstruite : `https://dev.azure.com/<org>/<project>/_git/<repo>/commit/<commitId>`.

**B. Fallback : dériver des PRs collectées en 2.1**

Si `az rest` échoue (permissions / API down / org auto-hébergée sans cette API) :
- Pour chaque PR où je suis auteur, récupérer `lastMergeCommit` + `commits` via `az repos pr show --id <id> --include-links -o json` quand l'option est disponible.
- Sinon, lister juste `lastMergeCommit` des PRs mergées par moi.
- **Marquer dans `⚠️ Limitations`** : « Liste des commits dérivée des PRs (l'endpoint REST commits n'a pas répondu). Commits directement poussés hors PR non visibles. »

**Mode `mcp`** : utiliser le tool équivalent si exposé (`repo_list_commits` ou nom similaire) ; sinon appliquer la stratégie B.

### 2.3 Work Items

Récupérer les WIs où l'utilisateur courant est intervenu dans la fenêtre :

- **Assigné à `@me`** avec `[System.ChangedDate] >= since`
- **Créé par `@me`** dans la fenêtre
- **Commenté par `@me`** dans la fenêtre (à corréler en 2.3.b)

**Mode `az`** — requête WIQL via `az boards query` :

```bash
az boards query \
  --org <url> --project "<project>" \
  --wiql "SELECT [System.Id], [System.WorkItemType], [System.Title], [System.State], [System.AssignedTo], [System.ChangedDate], [System.CreatedDate] \
          FROM WorkItems \
          WHERE ([System.AssignedTo] = @Me OR [System.CreatedBy] = @Me) \
            AND [System.ChangedDate] >= '$SINCE_ISO' \
          ORDER BY [System.ChangedDate] DESC" \
  -o json
```

> Le token `@Me` est résolu côté serveur ADO en fonction de l'utilisateur authentifié — il n'est **pas** nécessaire de l'interpoler.

Pour chaque WI retourné, récupérer les détails et l'historique :
```bash
az boards work-item show --id <id> --org <url> --expand all -o json
```

Et la liste des commentaires :
```bash
az rest --method get \
  --url "https://dev.azure.com/<org>/<project>/_apis/wit/workItems/<id>/comments?api-version=7.1-preview.4"
```
Filtrer ceux dont `createdBy.uniqueName == $EMAIL` et `createdDate >= since`.

**Mode `mcp`** : équivalent (`wit_my_work_items`, `wit_get_work_item`, `wit_get_work_item_comments`).

Pour chaque WI conserver : `id`, `workItemType` (Bug / User Story / Task / Feature), `title`, `state`, `assignedTo.displayName`, `changedDate`, `url` web reconstruite : `https://dev.azure.com/<org>/<project>/_workitems/edit/<id>`, et la liste des actions de `@me` (créé / changé d'état / commenté / réassigné) déduites de l'historique (`fields` diff entre révisions).

### 2.4 Threads / commentaires de PR

Pour chaque PR active du projet **et** chaque PR collectée en 2.1 (auteur ou reviewer) :

**Mode `az`** — pas de commande native, utiliser `az rest` :

```bash
az rest --method get \
  --url "https://dev.azure.com/<org>/<project>/_apis/git/repositories/<repoId>/pullRequests/<prId>/threads?api-version=7.1"
```

Pour chaque thread retourné :
- Conserver les commentaires dont `author.uniqueName == $EMAIL` et `publishedDate >= since`.
- Conserver aussi les threads où **quelqu'un a répondu après moi** dans la fenêtre (mes commentaires antérieurs + réponse récente d'un autre auteur). Utile pour identifier les demandes en attente.
- Conserver `pull_request.id` + `title`, `thread.id`, `threadContext.filePath`, `threadContext.rightFileStart.line` (ou `leftFileStart.line`), `comment.content` (tronqué à 200 chars dans le rapport), `publishedDate`, `url` web reconstruite : `https://dev.azure.com/<org>/<project>/_git/<repo>/pullrequest/<prId>?discussionId=<threadId>`.

**Mode `mcp`** : utiliser le tool équivalent (`repo_list_pull_request_threads` ou nom similaire).

⚠️ **Garde-fou coût** : cette étape peut être lourde sur une org large. Si la collecte dépasse ~30 secondes ou ~100 PRs scannées, s'arrêter et indiquer dans le rapport :
> « Threads collectés sur les N PRs où je suis auteur/reviewer seulement (collecte exhaustive interrompue pour limiter le temps). »

---

## Phase 3 — Filtrage final côté client

Même si certains appels acceptent un filtre `since` côté serveur, **toujours refiltrer côté client** sur la fenêtre `[since, now]` pour garantir la cohérence (les fuseaux et arrondis serveur ne sont pas toujours fiables).

Pour chaque type d'item, conserver uniquement ceux dont la **date d'activité pertinente** tombe dans la fenêtre :
- **PR** : `creationDate`, `closedDate`, ou date du dernier commentaire de `@me`
- **Commit** : `author.date`
- **Work Item** : `changedDate` OU date d'un commentaire de `@me`
- **Thread** : `publishedDate` du commentaire

Dédupliquer si une même PR est ressortie plusieurs fois (auteur + reviewer + commentateur). Priorité d'affectation : créée > mergée > commentée > en attente.

---

## Phase 4 — Restitution

Le rapport est **toujours écrit en français** et structuré comme suit. Si une section thématique est vide, ne pas la masquer : afficher `_Aucune activité sur cette fenêtre._`.

### 4.1 Structure du rapport

```markdown
# 🗓️ Activité Azure DevOps — <date locale, ex: 28/05/2026>

**Fenêtre** : <since ISO> → <now ISO> (<N> heures)
**Organisation** : <org>
**Utilisateur** : <displayName> (`<uniqueName>`)
**Projets scannés** : <liste ou « tous »>
**Source** : `az` CLI _ou_ MCP devops (fallback)

---

## 📊 Résumé

- 🟢 **Pull Requests** : <N créées> / <N mergées> / <N commentées> / <N en attente de mon review>
- 📝 **Commits** : <N> sur <M> repos
- 🎯 **Work Items** : <N créés> / <N changés d'état> / <N commentés>
- 💬 **Threads PR** : <N commentaires postés> / <N réponses reçues sur mes threads>

---

## 🟢 Pull Requests

### Créées par moi
- [`!<id>` <title>](<url>) — <repo> — créée à <HH:MM>, statut `<status>`

### Mergées par moi
- ...

### Commentées par moi (sans en être l'auteur)
- ...

### En attente de mon review
- ...

_(Si une sous-section est vide → la masquer ici uniquement, pas le bloc parent.)_

---

## 📝 Commits

Groupés par repo, chronologiques inversés à l'intérieur :

### <repo-name>
- `<sha7>` <subject> — <HH:MM>
- ...

---

## 🎯 Work Items

### Créés
- `<type> #<id>` <title> — état `<state>` — <HH:MM>

### Changements d'état
- `<type> #<id>` <title> : `<from>` → `<to>` — <HH:MM>

### Commentés
- `<type> #<id>` <title> — commentaire à <HH:MM>

---

## 💬 Threads PR

### Commentaires que j'ai postés
- PR `!<id>` <title> — <path:line si dispo> — <HH:MM>
  > « <extrait du commentaire, max 200 chars> »

### Réponses reçues sur mes threads (à traiter)
- PR `!<id>` <title> — <auteur de la réponse> a répondu à <HH:MM>
  > « <extrait, max 200 chars> »

---

## ⏱️ Timeline (chronologique inversée)

- `<HH:MM>` — <icône-type> <verbe court> <ressource> [<repo / projet>](<url>)
- `<HH:MM>` — ...

Légende d'icônes : 🟢 PR · 📝 commit · 🎯 work item · 💬 thread

---

## ⚠️ Limitations (si applicable)

- ...
```

### 4.2 Règles de mise en forme

- **Tri** : dans chaque sous-section thématique, ordre chronologique **inversé** (du plus récent au plus ancien).
- **Timestamps** : afficher l'heure locale au format `HH:MM` quand l'événement est dans les 24h ; ajouter la date `JJ/MM HH:MM` si la fenêtre `--hours` dépasse 24h.
- **URLs** : toutes les ressources doivent être cliquables (Markdown link). Si la source ne renvoie pas d'URL web, reconstruire :
  - PRs → `https://dev.azure.com/<org>/<project>/_git/<repo>/pullrequest/<id>`
  - Commits → `https://dev.azure.com/<org>/<project>/_git/<repo>/commit/<sha>`
  - Work items → `https://dev.azure.com/<org>/<project>/_workitems/edit/<id>`
- **Troncature** : aucun extrait de commentaire ne doit dépasser 200 caractères dans le rapport. Ajouter `…` si tronqué.
- **Pas de doublons** : une PR mentionnée dans « Créées » ne réapparaît pas dans « Commentées » (priorité : créée > mergée > commentée > en attente).

### 4.3 Sortie

Par défaut, **afficher le rapport inline dans la conversation** (pas d'écriture fichier).

Si l'utilisateur a passé `--save` ou demande explicitement à sauvegarder, écrire dans `daily-activity/YYYY-MM-DD.md` à la racine du repo courant (créer le dossier si besoin, jamais d'écrasement → suffixer `-HHhMM` si conflit).

Toujours conclure le rapport par une question courte via `AskUserQuestion` :

- « Veux-tu un focus sur une PR / un WI précis ? »
- « Veux-tu sauvegarder ce rapport en local ? »
- « Veux-tu étendre la fenêtre (ex: 48h, semaine) ? »

---

## Règles transverses

- **Langue** : tout le flow et le rapport final sont en **français**.
- **Read-only strict** : ce skill ne lance **que** des commandes de lecture (`az ... list/show/query`, `az rest --method get`, tools MCP de lecture). Aucune création, modification, suppression de PR / WI / commentaire / branche. Si l'utilisateur enchaîne avec une action d'écriture, lui rappeler que ce skill ne fait que lire.
- **Pas d'écriture sans accord** : aucune création de fichier sans demande explicite (`--save` ou réponse positive à la question finale).
- **Confidentialité** : ne pas recopier intégralement des commentaires longs (cf. troncature 200 chars). Si un commentaire contient ce qui ressemble à un secret (token, clé API, mot de passe, JWT), le masquer (`****`) et signaler dans `⚠️ Limitations`.
- **Une seule exécution par invocation** : pas de boucle « refresh toutes les N minutes » dans ce skill — pour cela utiliser le skill `loop` séparément.
- **Tolérance aux échecs partiels** : si un projet est inaccessible (perm denied), continuer avec les autres et lister le projet en `⚠️ Limitations` plutôt que d'échouer le flow complet.
- **Traçabilité de la source** : toujours indiquer dans l'en-tête du rapport quelle source a été utilisée (`az` ou `mcp` fallback), pour permettre à l'utilisateur de comprendre les éventuels écarts de complétude.
