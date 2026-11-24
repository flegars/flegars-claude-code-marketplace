# Adaptateurs de plateforme

Chaque adaptateur (`scripts/prr/adapters/<plateforme>.py`) implémente le même contrat :

| Méthode | Rôle |
|---|---|
| `check()` | Vérifie que la CLI officielle est présente et authentifiée. Sinon : `PlatformUnavailable` avec la commande d'authentification, et bascule en mode local. |
| `fetch_pull_request(ref, base)` | Diff (calculé localement entre merge-base et head), SHA, titre, description, branches, US / issues rattachées directement, données natives utiles à la publication. |
| `list_existing_comments(context)` | Commentaires du plugin déjà présents (empreintes) et synthèse existante. |
| `build_payloads(review, context, existing, request_changes)` | Traduction pure vers le modèle natif. C'est ce que montre `--dry-run`. |
| `post_review(...)` | Envoie les payloads (jamais en `--dry-run`). |

Aucun token n'est manipulé : tout passe par la CLI déjà authentifiée. Ajouter une plateforme = ajouter un
module ici, l'enregistrer dans `adapters/__init__.py`, sans toucher au cœur.

## Matrice

| | GitHub | Azure DevOps *(expérimental)* | GitLab *(expérimental)* |
|---|---|---|---|
| CLI | `gh` | `az` + extension `azure-devops` | `glab` |
| Authentification | `gh auth login --hostname <host>` | `az login` (+ `az extension add --name azure-devops`) | `glab auth login --hostname <host>` |
| Commentaires inline | **une seule review** `POST /repos/{o}/{r}/pulls/{n}/reviews` avec `comments[]` (`path`, `line`, `side`, `start_line`/`start_side` pour les plages) | un thread par commentaire, `threadContext` (`filePath`, `rightFileStart`/`rightFileEnd` ou `left…`) + `pullRequestThreadContext` (itération, `changeTrackingId`) | une discussion par commentaire, `position` (`base_sha`, `start_sha`, `head_sha`, `new_path`/`old_path`, `new_line`/`old_line`, `position_type: text`) ; une plage est ancrée sur sa dernière ligne |
| Synthèse | commentaire de PR, créé puis mis à jour (`PATCH issues/comments/{id}`) | thread sans contexte de fichier, mis à jour (`PATCH …/threads/{id}/comments/{id}`) | note de MR, mise à jour (`PUT …/notes/{id}`) |
| Identification | marqueur `<!-- pr-reviewer:v2 kind=… fp=… -->` (invisible au rendu, vérifié) | `properties` du thread (`pr-reviewer.kind`, `pr-reviewer.fp`) + marqueur en secours (rendu du marqueur non documenté) | marqueur (invisible au rendu, documenté GLFM) |
| US rattachées | `closingIssuesReferences` + mots-clés de clôture de la description | work items liés à la PR (`az repos pr work-item list`), critères via `Microsoft.VSTS.Common.AcceptanceCriteria` | `closes_issues` de la MR |
| Ligne hors diff | 422 (atomicité de la review non documentée) | non documenté | 400 `line_code` |
| `--request-changes` (verdict `blocking`) | `event: REQUEST_CHANGES` ; repli `COMMENT` si refusé (sa propre PR) | vote « waiting for author » (`az repos pr set-vote --vote wait-for-author`) | mutation GraphQL `mergeRequestRequestChanges` (Premium/Ultimate, ≥ 17.3) ; sinon commentaire seul |
| Sans `--request-changes` | `event: COMMENT` | threads créés au statut `closed` (un thread `active` bloque la complétion sous la politique de résolution des commentaires) | discussions simples |
| Approbation | jamais | jamais | jamais |

Les lignes hors diff ne sont jamais envoyées : le cœur les filtre avant tout appel et les reporte dans la
synthèse. Si une API refuse malgré tout, l'envoi s'arrête à la première erreur et un rapport local est écrit.
Sur GitHub, la review (tous les commentaires inline) part avant la synthèse : un refus ne laisse rien en ligne.

## Mode local

Disponible partout, sans authentification : diff de la branche courante (commits uniquement, pas les
modifications non commitées) contre `--base` (défaut : branche par défaut du remote, sinon `main` / `master`).
Sortie : `reviews/<branche>-<horodatage>.md` + `.json` au format neutre.
