---
name: daily-activity
description: "Récapitule l'activité GitHub de l'utilisateur courant sur les dernières 24 heures glissantes : Pull Requests, commits, issues, threads de review. Source unique = `gh` CLI (`gh search`, `gh api`, feed d'événements). Orchestre un flow en 4 phases : préparation (fenêtre 24h, vérification de `gh`, résolution de l'identité) → collecte (recherche globale + feed d'événements) → filtrage par fenêtre temporelle → restitution (résumé groupé par type + timeline chronologique inversée). Déclencher quand l'utilisateur dit : /daily-activity, 'qu'est-ce que j'ai fait aujourd'hui sur GitHub', 'mon activité GitHub 24h', 'recap github', 'standup', 'prépare mon daily'."
user_invocable: true
---

# Daily Activity (GitHub)

Produit un récapitulatif **standardisé** de l'activité de l'utilisateur courant sur GitHub pour les **dernières 24 heures glissantes** (fenêtre `now − 24h` → `now`).

**Source** : `gh` CLI (GitHub CLI) — `gh search`, `gh api` (REST + GraphQL), feed d'événements utilisateur.

Cas d'usage typique : préparer son daily, retrouver ce sur quoi on a touché avant un changement de contexte, auditer ses propres traces. **Read-only** : uniquement des lectures (`gh search`, `gh pr list`, `gh api --method GET`). Aucune écriture côté GitHub.

## Vue d'ensemble du flow

1. **Préparation** — Calculer la fenêtre, vérifier `gh` (binaire / auth / compte actif), résoudre l'identité
2. **Collecte** — Agréger PRs / commits / issues / threads de review via recherche globale + feed d'événements
3. **Filtrage** — Ne garder que les événements dans la fenêtre 24h
4. **Restitution** — Rapport markdown : résumé groupé + timeline chronologique inversée

---

## Arguments du slash command

```
/daily-activity [--hours=N] [--repo=<owner/name>] [--org=<org>] [--host=<hostname>] [--save]
```

- `--hours=N` (optionnel) — Étend ou raccourcit la fenêtre glissante (défaut : `24`). Exemple : `--hours=48` pour un récap week-end.
- `--repo=<owner/name>` (optionnel) — Restreint la collecte à un seul dépôt (`org/repo`). Cumulable : `--repo=a/b --repo=c/d`.
- `--org=<org>` (optionnel) — Restreint la collecte aux dépôts d'une organisation (qualifier `org:<org>` dans les recherches).
- `--host=<hostname>` (optionnel) — Cible une instance GitHub Enterprise (défaut : `github.com`). Propagé via `--hostname` / `GH_HOST`.
- `--save` (optionnel) — Force la sauvegarde du rapport dans `daily-activity/YYYY-MM-DD.md`.

Aucun argument n'est obligatoire. Le mode par défaut = 24h, toute l'activité visible par le compte authentifié, sortie inline.

---

## Phase 1 — Préparation

### 1.1 Calculer la fenêtre temporelle

- `NOW_ISO` = timestamp courant UTC (ISO 8601, ex. `2026-09-02T08:00:00Z`).
- `SINCE_ISO` = `now − N heures` où `N` = valeur de `--hours` ou `24`.
- `SINCE_DATE` = date seule (`YYYY-MM-DD`) dérivée de `SINCE_ISO` — utile car certains qualifiers de recherche GitHub sont plus fiables à la journée qu'à la seconde.

```bash
NOW_ISO=$(date -u +%Y-%m-%dT%H:%M:%SZ)
SINCE_ISO=$(date -u -v-24H +%Y-%m-%dT%H:%M:%SZ)   # macOS ; GNU : date -u -d '24 hours ago' ...
SINCE_DATE=${SINCE_ISO%%T*}
```

Conserver ces bornes — toutes les comparaisons ultérieures se font dessus.

### 1.2 Vérifier la source `gh`

Tester dans cet ordre, **s'arrêter au premier échec** :

1. Binaire disponible : `command -v gh`
2. Authentification valide : `gh auth status` (afficher la sortie, elle liste les comptes et le compte actif)
3. Scopes suffisants : la sortie de `gh auth status` doit mentionner au minimum `repo` (et `read:org` si `--org` est utilisé). Si `repo` manque, signaler que l'activité sur dépôts privés sera invisible et le noter dans `⚠️ Limitations`.
4. API joignable : `gh api rate_limit --jq '.rate.remaining'` (échoue si réseau / token invalide ; sert aussi de garde-fou coût, cf. 2.6)

**Si une étape échoue → stopper le flow** avec ce message :

```
Source GitHub indisponible :
- `gh` CLI : <raison>
Installe GitHub CLI (`brew install gh`) puis authentifie-toi (`gh auth login`).
Si tu as plusieurs comptes (perso / pro), vérifie le compte actif avec `gh auth status`
et bascule si besoin avec `gh auth switch --user <login>`.
```

> ⚠️ **Multi-comptes** : `gh` peut être authentifié sur plusieurs comptes (perso + pro/EMU). Le rapport ne reflète que le **compte actif**. Si `gh auth status` en liste plusieurs, indiquer explicitement dans l'en-tête du rapport lequel a été utilisé, et le rappeler dans `⚠️ Limitations` si l'activité semble anormalement vide.

### 1.3 Résoudre l'identité

```bash
LOGIN=$(gh api user --jq .login)
gh api user --jq '{login, name, id, html_url}'
```

- Conserver `login`, `name`, `id`, `html_url`.
- `@me` est résolu côté serveur dans les qualifiers de recherche (`--author=@me`) — pas besoin de l'interpoler, mais `$LOGIN` reste nécessaire pour le feed d'événements et le filtrage côté client.

Si la résolution échoue : afficher l'erreur brute et stopper.

### 1.4 Déterminer le périmètre

Construire un **suffixe de qualifiers** réutilisé par toutes les recherches :

- `--repo` fourni → qualifier positionnel `repo:<owner/name>` passé en argument de `gh search` (répétable : `gh search prs 'repo:a/b repo:c/d' --author=@me`). `gh search` n'a **pas** de flag `--repo`.
- `--org` fourni → flag `--owner=<org>` sur `gh search` (répétable).
- Ni l'un ni l'autre → aucun filtre : toute l'activité visible par le compte authentifié.

Vérifier qu'un `--repo` fourni existe et est lisible :
```bash
gh repo view <owner/name> --json nameWithOwner,visibility
```
Si introuvable, demander une correction via `AskUserQuestion` (proposer les dépôts récents de l'utilisateur : `gh repo list --limit 20`).

---

## Phase 2 — Collecte

Exécuter les sous-étapes ci-dessous **en parallèle quand c'est possible** (un seul tour de tool calls).

L'objectif n'est pas d'être exhaustif sur les noms exacts des commandes — utiliser les capacités équivalentes exposées par `gh` au moment de l'exécution. Si une capacité manque, le signaler dans le rapport final dans une section `⚠️ Limitations`.

> **Toutes les commandes ci-dessous sont read-only** (`gh search`, `gh pr list`, `gh api` en GET). Aucune commande mutante ne doit être lancée par ce skill.

### 2.1 Feed d'événements (socle de la collecte)

Le feed d'événements de l'utilisateur est la source la plus complète pour une fenêtre courte : il couvre les push, ouvertures/merges de PR, reviews, commentaires et issues, **y compris sur dépôts privés** quand le token porte le scope `repo`.

```bash
gh api "/users/$LOGIN/events?per_page=100" --paginate --jq \
  '.[] | select(.created_at >= "'"$SINCE_ISO"'") |
   {type, created_at, repo: .repo.name, payload}'
```

Types d'événements à exploiter :

| Type | Alimente |
|---|---|
| `PushEvent` | Commits (`payload.commits[]` : `sha`, `message`, `author`) |
| `PullRequestEvent` | PRs ouvertes / fermées / mergées (`payload.action`, `payload.pull_request`) |
| `PullRequestReviewEvent` | Reviews postées (`payload.review.state` : approved / changes_requested / commented) |
| `PullRequestReviewCommentEvent` | Commentaires de review inline (`payload.comment.path`, `.line`, `.body`) |
| `IssuesEvent` | Issues ouvertes / fermées / réassignées |
| `IssueCommentEvent` | Commentaires sur issue ou PR |
| `CreateEvent` / `DeleteEvent` | Branches créées / supprimées (contexte utile, section optionnelle) |

Limites connues à noter dans `⚠️ Limitations` si pertinent :
- Le feed ne remonte que les **300 derniers événements** / **90 derniers jours** — sans impact à 24h sauf activité très intense.
- Il peut accuser un **retard de quelques minutes** sur les événements les plus récents.
- Les événements sur dépôts privés d'une **organisation EMU** peuvent être absents selon la politique de l'org → croiser systématiquement avec 2.2–2.5.

### 2.2 Pull Requests

PRs créées par moi et mises à jour dans la fenêtre :
```bash
gh search prs --author=@me --updated=">=$SINCE_DATE" --limit 100 \
  --json number,title,repository,url,state,isDraft,createdAt,updatedAt,closedAt
```

PRs mergées par moi :
```bash
gh search prs --author=@me --merged-at=">=$SINCE_DATE" --limit 100 \
  --json number,title,repository,url,closedAt
```

PRs où j'ai été demandé en review :
```bash
gh search prs --review-requested=@me --state=open --limit 100 \
  --json number,title,repository,url,author,createdAt,updatedAt
```

PRs que j'ai reviewées ou commentées :
```bash
gh search prs --reviewed-by=@me --updated=">=$SINCE_DATE" --limit 100 --json number,title,repository,url,author,updatedAt
gh search prs --commenter=@me  --updated=">=$SINCE_DATE" --limit 100 --json number,title,repository,url,author,updatedAt
```

Ajouter le qualifier positionnel `repo:<owner/name>` ou le flag `--owner=<org>` selon le périmètre de 1.4.

> `--updated` filtre la **dernière mise à jour** de la PR, pas l'action précise : refiltrer côté client (Phase 3) en croisant avec le feed d'événements pour savoir **ce que j'ai fait** et **quand**.
>
> Sur une PR ouverte, `closedAt` vaut la sentinelle `0001-01-01T00:00:00Z` (et non `null`) — la traiter comme « non fermée », jamais comme une date.
>
> `state` vaut `open`, `closed` **ou `merged`** dans la sortie de `gh search prs` : ne pas déduire le merge de `closed`.

Pour chaque PR, conserver :
- `number`, `title`, `repository.nameWithOwner`, `url`
- `state` (`open` / `closed` / `merged`), `isDraft`
- `createdAt`, `updatedAt`, `closedAt`, date de merge si disponible
- Booléens : `j'ai créé`, `j'ai mergé`, `j'ai reviewé`, `j'ai commenté`, `je suis reviewer demandé`

Détail sur une PR précise si nécessaire :
```bash
gh pr view <number> --repo <owner/name> \
  --json number,title,url,state,mergedAt,mergedBy,headRefName,baseRefName,commits,reviews
```

### 2.3 Commits

**A. Depuis le feed d'événements (recommandé)** — `PushEvent.payload.commits[]` donne `sha`, `message`, `author.email`, et `repo.name`. C'est la source la plus fiable, y compris hors branche par défaut.

Reconstruire l'URL : `https://<host>/<owner/repo>/commit/<sha>`.

**B. Complément : recherche de commits**
```bash
gh search commits --author=@me --author-date=">=$SINCE_DATE" --limit 100 \
  --json sha,commit,repository,url
```

> ⚠️ La recherche de commits n'indexe **que la branche par défaut** de chaque dépôt : les commits poussés sur une branche de feature n'y apparaissent pas. Elle sert de **complément** au feed, jamais de remplacement. Le noter dans `⚠️ Limitations` si c'est la seule source ayant répondu.

**C. Fallback local** — Si le feed et la recherche échouent tous les deux, et si le répertoire courant est un dépôt Git :
```bash
git log --all --author="$LOGIN" --since="$SINCE_ISO" --pretty=format:'%h|%ad|%s' --date=iso
```
Marquer dans `⚠️ Limitations` : « Commits collectés depuis le dépôt local uniquement — l'activité sur les autres dépôts n'est pas visible. »

Conserver : `sha` (court, 7 chars), première ligne du message, `owner/repo`, date, URL web.

### 2.4 Issues

Récupérer les issues où l'utilisateur est intervenu dans la fenêtre :

```bash
gh search issues --author=@me    --updated=">=$SINCE_DATE" --limit 100 --json number,title,repository,url,state,createdAt,updatedAt,closedAt
gh search issues --assignee=@me  --updated=">=$SINCE_DATE" --limit 100 --json number,title,repository,url,state,updatedAt
gh search issues --commenter=@me --updated=">=$SINCE_DATE" --limit 100 --json number,title,repository,url,state,updatedAt
```

Croiser avec `IssuesEvent` / `IssueCommentEvent` du feed pour dater précisément **mes** actions (ouverture, fermeture, commentaire, assignation) plutôt que la dernière mise à jour globale de l'issue.

Commentaires détaillés d'une issue :
```bash
gh api "/repos/<owner>/<repo>/issues/<number>/comments" \
  --jq '.[] | select(.user.login == "'"$LOGIN"'" and .created_at >= "'"$SINCE_ISO"'") | {id, created_at, html_url, body}'
```

Labels utiles à conserver pour la restitution (`bug`, `enhancement`, etc.) : `gh issue view <n> --repo <owner/name> --json labels,state,title,url`.

Pour chaque issue conserver : `number`, `title`, `state`, `labels`, `repository.nameWithOwner`, `url`, et la liste des actions de l'utilisateur (créée / fermée / rouverte / commentée / assignée) déduite du feed.

### 2.5 Threads de review

Pour chaque PR collectée en 2.2 (auteur, reviewer ou commentateur) :

**Commentaires de review inline** :
```bash
gh api "/repos/<owner>/<repo>/pulls/<number>/comments" \
  --jq '.[] | {id, in_reply_to_id, user: .user.login, created_at, path, line, html_url, body}'
```

**Reviews (approve / changes requested / commented)** :
```bash
gh api "/repos/<owner>/<repo>/pulls/<number>/reviews" \
  --jq '.[] | {id, user: .user.login, state, submitted_at, html_url, body}'
```

**Commentaires de conversation** (non inline) :
```bash
gh api "/repos/<owner>/<repo>/issues/<number>/comments" \
  --jq '.[] | {id, user: .user.login, created_at, html_url, body}'
```

Pour chaque thread :
- Conserver les commentaires dont `user.login == $LOGIN` **et** `created_at >= SINCE_ISO`.
- Conserver aussi les threads où **quelqu'un a répondu après moi** dans la fenêtre : commentaire d'un autre auteur dont `in_reply_to_id` pointe vers un de mes commentaires, ou commentaire postérieur au mien dans le même `path`. Utile pour identifier les demandes en attente.
- Conserver : `owner/repo`, `number` + `title` de la PR, `path:line` si inline, `body` (tronqué à 200 chars dans le rapport), `created_at`, `html_url` (fourni directement par l'API — pas de reconstruction nécessaire).

### 2.6 Garde-fou coût

Cette étape peut être lourde si beaucoup de PRs sont concernées. Avant de boucler sur les PRs, vérifier le quota :
```bash
gh api rate_limit --jq '{core: .resources.core.remaining, search: .resources.search.remaining}'
```

L'API de recherche est plafonnée à **30 requêtes/minute** (`search.remaining`), bien plus basse que l'API core (5000/h) : enchaîner les `gh search` sans se soucier du quota fait échouer la collecte en milieu de flow. Limiter le nombre de recherches distinctes à celles listées en 2.2–2.4.

Si la collecte dépasse ~30 secondes, ~100 PRs scannées, ou si `core.remaining` descend sous 200 (ou `search.remaining` sous 5), s'arrêter et indiquer dans le rapport :
> « Threads collectés sur les N PRs les plus récentes où je suis auteur/reviewer seulement (collecte exhaustive interrompue pour limiter le temps / le quota API). »

---

## Phase 3 — Filtrage final côté client

Même si les qualifiers de recherche filtrent déjà côté serveur, **toujours refiltrer côté client** sur la fenêtre `[SINCE_ISO, NOW_ISO]` : les qualifiers `--updated` / `--author-date` s'appliquent à la journée et à la dernière mise à jour globale, pas à l'action précise de l'utilisateur.

Pour chaque type d'item, conserver uniquement ceux dont la **date d'activité pertinente de l'utilisateur** tombe dans la fenêtre :
- **PR** : `createdAt` (si je suis l'auteur), date de merge, date de ma review, ou date de mon dernier commentaire
- **Commit** : date de l'auteur / du push
- **Issue** : date de mon action (ouverture / fermeture / commentaire / assignation)
- **Thread** : `created_at` / `submitted_at` du commentaire ou de la review

Dédupliquer si une même PR est ressortie de plusieurs recherches (auteur + reviewer + commentateur). Priorité d'affectation : **créée > mergée > reviewée > commentée > en attente de mon review**.

---

## Phase 4 — Restitution

Le rapport est **toujours écrit en français** et structuré comme suit. Si une section thématique est vide, ne pas la masquer : afficher `_Aucune activité sur cette fenêtre._`.

### 4.1 Structure du rapport

```markdown
# 🗓️ Activité GitHub — <date locale, ex: 02/09/2026>

**Fenêtre** : <since ISO> → <now ISO> (<N> heures)
**Compte** : <name> (`<login>`) — <host>
**Périmètre** : <tous les dépôts visibles | org:<org> | liste des repos>

---

## 📊 Résumé

- 🟢 **Pull Requests** : <N créées> / <N mergées> / <N reviewées> / <N commentées> / <N en attente de mon review>
- 📝 **Commits** : <N> sur <M> dépôts
- 🎯 **Issues** : <N créées> / <N fermées> / <N commentées>
- 💬 **Threads de review** : <N commentaires postés> / <N réponses reçues sur mes threads>

---

## 🟢 Pull Requests

### Créées par moi
- [`<owner/repo>#<number>` <title>](<url>) — créée à <HH:MM>, statut `<state>`<, brouillon si isDraft>

### Mergées par moi
- ...

### Reviewées par moi
- [`<owner/repo>#<number>` <title>](<url>) — `<approved | changes_requested | commented>` à <HH:MM> — auteur : <login>

### Commentées par moi (sans en être l'auteur ni le reviewer)
- ...

### En attente de mon review
- ...

_(Si une sous-section est vide → la masquer ici uniquement, pas le bloc parent.)_

---

## 📝 Commits

Groupés par dépôt, chronologiques inversés à l'intérieur :

### <owner/repo>
- [`<sha7>`](<url>) <sujet> — <HH:MM> — branche `<ref>` si connue
- ...

---

## 🎯 Issues

### Créées
- [`<owner/repo>#<number>` <title>](<url>) — état `<state>` — <HH:MM>

### Fermées / rouvertes
- [`<owner/repo>#<number>` <title>](<url>) : `open` → `closed` — <HH:MM>

### Commentées
- [`<owner/repo>#<number>` <title>](<url>) — commentaire à <HH:MM>

---

## 💬 Threads de review

### Commentaires que j'ai postés
- [`<owner/repo>#<number>` <title>](<url>) — <path:line si dispo> — <HH:MM>
  > « <extrait du commentaire, max 200 chars> »

### Réponses reçues sur mes threads (à traiter)
- [`<owner/repo>#<number>` <title>](<url>) — <login> a répondu à <HH:MM>
  > « <extrait, max 200 chars> »

---

## ⏱️ Timeline (chronologique inversée)

- `<HH:MM>` — <icône-type> <verbe court> [<ressource>](<url>) — <owner/repo>
- `<HH:MM>` — ...

Légende d'icônes : 🟢 PR · 📝 commit · 🎯 issue · 💬 thread

---

## ⚠️ Limitations (si applicable)

- ...
```

### 4.2 Règles de mise en forme

- **Tri** : dans chaque sous-section thématique, ordre chronologique **inversé** (du plus récent au plus ancien).
- **Timestamps** : afficher l'heure locale au format `HH:MM` quand l'événement est dans les 24h ; ajouter la date `JJ/MM HH:MM` si la fenêtre `--hours` dépasse 24h.
- **URLs** : toutes les ressources doivent être cliquables (Markdown link). L'API GitHub renvoie `html_url` / `url` directement — l'utiliser. Reconstruire uniquement si absent :
  - PRs → `https://<host>/<owner>/<repo>/pull/<number>`
  - Commits → `https://<host>/<owner>/<repo>/commit/<sha>`
  - Issues → `https://<host>/<owner>/<repo>/issues/<number>`
- **Nommage** : toujours préfixer par `owner/repo` — une même numérotation `#123` existe dans plusieurs dépôts.
- **Troncature** : aucun extrait de commentaire ne doit dépasser 200 caractères dans le rapport. Ajouter `…` si tronqué.
- **Pas de doublons** : une PR mentionnée dans « Créées » ne réapparaît pas dans « Commentées » (priorité : créée > mergée > reviewée > commentée > en attente).

### 4.3 Sortie

Par défaut, **afficher le rapport inline dans la conversation** (pas d'écriture fichier).

Si l'utilisateur a passé `--save` ou demande explicitement à sauvegarder, écrire dans `daily-activity/YYYY-MM-DD.md` à la racine du repo courant (créer le dossier si besoin, jamais d'écrasement → suffixer `-HHhMM` si conflit).

Toujours conclure le rapport par une question courte via `AskUserQuestion` :

- « Veux-tu un focus sur une PR / une issue précise ? »
- « Veux-tu sauvegarder ce rapport en local ? »
- « Veux-tu étendre la fenêtre (ex: 48h, semaine) ? »

---

## Règles transverses

- **Langue** : tout le flow et le rapport final sont en **français**.
- **Read-only strict** : ce skill ne lance **que** des commandes de lecture (`gh search`, `gh pr list`, `gh issue list`, `gh api` en GET, `git log`). Aucune création, modification, suppression de PR / issue / commentaire / branche. Si l'utilisateur enchaîne avec une action d'écriture, lui rappeler que ce skill ne fait que lire.
- **Pas d'écriture sans accord** : aucune création de fichier sans demande explicite (`--save` ou réponse positive à la question finale).
- **Confidentialité** : ne pas recopier intégralement des commentaires longs (cf. troncature 200 chars). Si un commentaire contient ce qui ressemble à un secret (token, clé API, mot de passe, JWT), le masquer (`****`) et signaler dans `⚠️ Limitations`.
- **Une seule exécution par invocation** : pas de boucle « refresh toutes les N minutes » dans ce skill — pour cela utiliser le skill `loop` séparément.
- **Tolérance aux échecs partiels** : si un dépôt est inaccessible (404 / permission refusée), continuer avec les autres et le lister en `⚠️ Limitations` plutôt que d'échouer le flow complet.
- **Traçabilité du compte** : toujours indiquer dans l'en-tête du rapport le `login` utilisé et l'hôte, pour permettre de comprendre un rapport vide dû à un mauvais compte actif (`gh auth switch`).
