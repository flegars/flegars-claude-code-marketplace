---
name: daily-activity
description: "Récapitule l'activité Azure DevOps de l'utilisateur courant sur les dernières 24 heures glissantes : Pull Requests, commits, work items, threads de PR. Source = MCP `devops` (org INTERINVEST). Orchestre un flow en 4 phases : préparation (fenêtre 24h, vérification MCP, résolution `@me`) → collecte multi-projets → filtrage par fenêtre temporelle → restitution (résumé groupé par type + timeline chronologique inversée). Déclencher quand l'utilisateur dit : /daily-activity, 'qu'est-ce que j'ai fait aujourd'hui sur ADO', 'mon activité ADO 24h', 'recap ado', 'standup ado', 'prépare mon daily'."
user_invocable: true
---

# Daily Activity (Azure DevOps)

Produit un récapitulatif **standardisé** de l'activité de l'utilisateur courant sur Azure DevOps pour les **dernières 24 heures glissantes** (fenêtre `now − 24h` → `now`).

Source unique : le MCP `devops` configuré dans `~/.claude/config.json` (org `INTERINVEST` par défaut). Aucun fallback `az` CLI / API REST : si le MCP est indisponible, le skill s'arrête et le signale clairement.

Cas d'usage typique : préparer son daily, retrouver ce sur quoi on a touché avant un changement de contexte, auditer ses propres traces.

## Vue d'ensemble du flow

1. **Préparation** — Calculer la fenêtre, vérifier la disponibilité du MCP, résoudre l'identité `@me`
2. **Collecte** — Pour chaque projet de l'org, agréger PRs / commits / work items / threads
3. **Filtrage** — Ne garder que les événements dans la fenêtre 24h
4. **Restitution** — Rapport markdown : résumé groupé + timeline chronologique inversée

---

## Arguments du slash command

```
/daily-activity [--hours=N] [--project=<project>] [--org=<org>]
```

- `--hours=N` (optionnel) — Étend ou raccourcit la fenêtre glissante (défaut : `24`). Exemple : `--hours=48` pour un récap week-end.
- `--project=<project>` (optionnel) — Restreint la collecte à un seul projet ADO au lieu de scanner toute l'org. Match par nom exact (insensible à la casse) ou par id.
- `--org=<org>` (optionnel) — Surcharge l'org cible (défaut : org configurée dans le MCP, typiquement `INTERINVEST`).

Aucun argument n'est obligatoire. Le mode par défaut = 24h, toute l'org INTERINVEST.

---

## Phase 1 — Préparation

### 1.1 Calculer la fenêtre temporelle

- `now` = timestamp courant UTC (ISO 8601).
- `since` = `now − N heures` où `N` = valeur de `--hours` ou `24`.
- Conserver ces deux bornes — toutes les comparaisons ultérieures se font dessus.

### 1.2 Vérifier la disponibilité du MCP `devops`

- Le skill **dépend strictement** du MCP `devops`. Si aucun outil `mcp__*devops*__*` n'est exposé dans la session courante :
  - Afficher : « Le MCP `devops` n'est pas disponible dans cette session. Vérifie `~/.claude/config.json` puis relance Claude Code. »
  - **Stopper le flow.** Pas de fallback `az` CLI ou API REST direct.

### 1.3 Résoudre l'identité `@me`

- Utiliser la capacité du MCP qui retourne l'utilisateur authentifié (généralement un tool de type `core_get_identity_ids` / `user_get_authenticated` / équivalent).
- Conserver `descriptor`, `id`, `uniqueName` (email), `displayName` — ces champs sont nécessaires pour filtrer les commits, PRs et work items côté serveur quand l'API le permet (sinon filtrage côté client).
- Si la résolution échoue : afficher l'erreur brute du MCP et stopper.

### 1.4 Lister les projets cibles

- Si `--project` est fourni :
  - Récupérer ce seul projet via le MCP (`core_list_projects` puis match, ou `core_get_project`).
  - Si introuvable, demander via `AskUserQuestion` une correction parmi les projets proposés par le MCP.
- Sinon :
  - Lister tous les projets actifs de l'org via le MCP.
  - Conserver `id` et `name` pour chaque.

---

## Phase 2 — Collecte par projet

Pour **chaque projet retenu en Phase 1**, exécuter les sous-étapes ci-dessous **en parallèle quand c'est possible** (un appel MCP par sous-section, regroupés en un seul tour de tool calls par projet).

L'objectif n'est pas d'être exhaustif sur les noms exacts des tools MCP (ils peuvent évoluer) : utiliser **les capacités équivalentes** exposées par le MCP `devops` au moment de l'exécution. Si un tool attendu manque, le signaler dans le rapport final dans une section `⚠️ Limitations`.

### 2.1 Pull Requests

Récupérer les PRs où l'utilisateur courant est :

- **Auteur** — PRs créées ou mises à jour par `@me` dans la fenêtre.
- **Reviewer requis** — PRs où `@me` est dans la liste des reviewers.

Pour chacune, conserver :
- `id`, `title`, `repository`, `sourceRefName → targetRefName`
- `status` (`active`, `completed`, `abandoned`)
- `createdDate`, `closedDate` (si présent), `lastMergeCommit.committer.date` (proxy de la dernière activité de l'auteur)
- `url` web (pour le clic dans le rapport)
- Booléens : `j'ai créé`, `j'ai mergé`, `j'ai commenté`, `je suis reviewer`

### 2.2 Commits

Pour chaque repo du projet :
- Récupérer les commits dont l'auteur (ou le committer) est `@me` et dont la date est ≥ `since`.
- Conserver : `commitId` (court 7 chars), `comment` (1re ligne uniquement), `repository`, `committer.date`, `url` web.

⚠️ Si le MCP n'expose pas de tool `repo_list_commits` direct, fallback : **lister les push records** de l'utilisateur sur la fenêtre, ou récupérer les commits via les PRs déjà collectées en 2.1. Marquer dans `⚠️ Limitations` que la liste des commits est dérivée des PRs si c'est le cas.

### 2.3 Work Items

Récupérer les WIs où l'utilisateur courant est intervenu dans la fenêtre :

- **Assigné à `@me`** avec `System.ChangedDate ≥ since`
- **Créé par `@me`** dans la fenêtre
- **Commenté par `@me`** dans la fenêtre

Utiliser une requête WIQL équivalente si le MCP expose ce tool, sinon les tools type `wit_my_work_items`.

Pour chaque WI conserver : `id`, `type` (Bug / User Story / Task / Feature), `title`, `state`, `assignedTo`, `changedDate`, `url` web, et la liste des actions effectuées par `@me` (créé / changé d'état / commenté / réassigné).

### 2.4 Threads / commentaires de PR

Pour chaque PR active du projet (pas seulement celles collectées en 2.1) :
- Lister les threads de discussion.
- Conserver uniquement les commentaires dont l'auteur est `@me` et dont `publishedDate ≥ since`.
- Conserver aussi les threads où **quelqu'un a répondu à un commentaire de `@me`** dans la fenêtre (utile pour savoir si on est attendu).

Pour chacun : `pull_request.id` + `title`, `thread.id`, `path:line` du contexte si présent, `comment.content` (tronqué à 200 chars dans le rapport), `publishedDate`, `url` web.

⚠️ Cette étape peut être coûteuse sur une org large. Si la collecte dépasse ~30 secondes ou ~100 PRs scannées, s'arrêter et indiquer dans le rapport « Threads collectés sur les N PRs où je suis auteur/reviewer seulement (collecte exhaustive interrompue pour limiter le temps) ».

---

## Phase 3 — Filtrage final côté client

Même si certains tools MCP acceptent un filtre `since` côté serveur, **toujours refiltrer côté client** sur la fenêtre `[since, now]` pour garantir la cohérence.

- Pour chaque type d'item, conserver uniquement ceux dont la **date d'activité pertinente** tombe dans la fenêtre :
  - PR : `createdDate`, `closedDate`, ou date du dernier commentaire de `@me`
  - Commit : `committer.date`
  - Work Item : `changedDate` OU date d'un commentaire de `@me`
  - Thread : `publishedDate` du commentaire

- Dédupliquer si une même PR est ressortie plusieurs fois (auteur + reviewer + commentateur).

---

## Phase 4 — Restitution

Le rapport est **toujours écrit en français** et structuré comme suit. Si une section est vide, ne pas la masquer : afficher `_Aucune activité sur cette fenêtre._`.

### 4.1 Structure du rapport

```markdown
# 🗓️ Activité Azure DevOps — <date locale, ex: 28/05/2026>

**Fenêtre** : <since ISO> → <now ISO> (<N> heures)
**Organisation** : <org>
**Utilisateur** : <displayName> (`<uniqueName>`)
**Projets scannés** : <liste ou « tous »>

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
- **URLs** : toutes les ressources doivent être cliquables (Markdown link). Si le MCP ne renvoie pas d'URL web, reconstruire l'URL `https://dev.azure.com/<org>/<project>/_git/<repo>/pullrequest/<id>` (PRs), `_workitems/edit/<id>` (WIs), `_git/<repo>/commit/<sha>` (commits) — uniquement si toutes les composantes sont connues.
- **Troncature** : aucun extrait de commentaire ne doit dépasser 200 caractères dans le rapport. Ajouter `…` si tronqué.
- **Pas de doublons** : une PR mentionnée dans « créées » ne réapparaît pas dans « commentées » (priorité : créée > mergée > commentée > en attente).

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
- **Pas d'écriture sans accord** : aucune création de fichier sans demande explicite (`--save` ou réponse positive à la question finale).
- **Pas d'action côté serveur ADO** : ce skill est **read-only**. Aucun `PATCH`, aucun commentaire, aucune assignation, aucune création de WI. Si l'utilisateur enchaîne avec une action d'écriture, lui rappeler que ce skill ne fait que lire.
- **Confidentialité** : ne pas recopier intégralement des commentaires longs (cf. troncature 200 chars). Si un commentaire contient ce qui ressemble à un secret (token, clé API, mot de passe), le masquer (`****`) et signaler dans `⚠️ Limitations`.
- **Une seule exécution par invocation** : pas de boucle « refresh toutes les N minutes » dans ce skill — pour cela utiliser le skill `loop` séparément.
- **Tolérance aux échecs partiels** : si un projet est inaccessible (perm denied), continuer avec les autres et lister le projet en `⚠️ Limitations` plutôt que d'échouer le flow complet.
