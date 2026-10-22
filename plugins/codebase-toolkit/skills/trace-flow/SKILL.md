---
name: trace-flow
description: "Trace un flux de bout en bout dans la codebase courante — écran front → appel API → handler → domaine → base de données → events / appels externes — à partir d'un point d'entrée (route HTTP, URL, composant front, commande console, message Messenger) ou d'une description fonctionnelle. Restitue un résumé, un diagramme de séquence Mermaid, le tableau des étapes ancrées fichier:ligne, les effets de bord, les branches d'erreur et les points d'attention, selon un template figé. Orchestre un flow en 4 phases : cadrage → résolution du point d'entrée → traçage via l'agent flow-tracer → sortie (inline et/ou docs/flows/). Lecture seule. Utile pour déboguer, préparer une revue ou rédiger une US. Déclencher quand l'utilisateur dit : /trace-flow, 'trace ce flux', 'que se passe-t-il quand on appelle POST /api/…', 'suis le parcours de ce bouton jusqu'en base', 'explique-moi ce endpoint de bout en bout', 'qui consomme ce message'."
user_invocable: true
argument-hint: "[route HTTP | composant | commande console | message | description du flux]"
---

# Trace Flow

Suit un flux **réel** dans la codebase courante, depuis son point d'entrée jusqu'à ses effets finaux, et le restitue selon le template figé :
`${CLAUDE_PLUGIN_ROOT}/skills/trace-flow/references/flow-template.md`

Chaque étape est ancrée sur un fichier lu ; toute incertitude est marquée `[RUPTURE]` plutôt que comblée par une supposition. Le skill est en **lecture seule** sur le code.

## Vue d'ensemble du flow

1. **Cadrage** — Point d'entrée, scénario, profondeur
2. **Résolution du point d'entrée** — Le localiser dans le code et le faire confirmer
3. **Traçage** — Déléguer à l'agent `flow-tracer`
4. **Sortie** — Inline, fichier, ou les deux

---

## Phase 1 — Cadrage

Si `$ARGUMENTS` est fourni, l'interpréter :
- commence par une méthode HTTP ou `/` → **route HTTP** ;
- URL complète → en extraire le chemin → **route HTTP** ;
- `PascalCase` se terminant par `Command`, `Message`, `Event`, `Query` → **message Messenger** ;
- contient `:` sans espace (ex. `app:import-clients`) → **commande console** ;
- autre `PascalCase` → **composant front** (à confirmer) ;
- phrase libre → **description fonctionnelle**.

Puis poser via `AskUserQuestion` (une seule invocation) :
1. **« Quel scénario suivre ? »** — Nominal / Un cas d'erreur précis (à décrire).
2. **« Jusqu'où aller ? »** — S'arrêter à la frontière du repo / Décrire aussi les appels sortants (payloads envoyés, réponses attendues).

---

## Phase 2 — Résolution du point d'entrée

Localiser le point d'entrée par une recherche rapide (`Grep` / `Glob`) :
- route : attributs `#[Route]`, opérations API Platform, `config/routes*` ;
- composant : définition du composant et route front qui le monte ;
- commande : `#[AsCommand]` ;
- message : classe du message et ses handlers ;
- description fonctionnelle : chercher les termes métier dans les routes, contrôleurs, processors, composants, et proposer **au plus 3 candidats**.

Présenter le point d'entrée retenu (type, identifiant, `path:line`) et le faire confirmer via `AskUserQuestion`. S'il y a plusieurs candidats, demander lequel suivre. Ne jamais lancer le traçage sur un point d'entrée deviné.

---

## Phase 3 — Traçage via l'agent flow-tracer

Déléguer à l'agent `flow-tracer` via le tool `Agent` (subagent_type=`flow-tracer`).

**Prompt à fournir à l'agent** — inclure :
- Le point d'entrée confirmé (type, identifiant, `path:line`).
- Le scénario et la profondeur retenus.
- La racine du front si le flux part d'un écran (monorepo).
- L'instruction explicite : « Lire d'abord `${CLAUDE_PLUGIN_ROOT}/skills/trace-flow/references/flow-template.md`, puis tracer le flux en suivant ce template à la lettre. N'inclure que des étapes réellement lues ; marquer `[RUPTURE]` toute incertitude. Ne modifier aucun fichier. »

Si l'agent revient avec plusieurs candidats ou une rupture bloquante dès le départ, la présenter à l'utilisateur et relancer avec sa réponse.

---

## Phase 4 — Sortie

Présenter le résumé, le diagramme et le nombre de `[RUPTURE]` relevées, puis demander via `AskUserQuestion` : **« Où restituer le traçage ? »**
- **Inline**
- **Fichier `docs/flows/<slug>.md`** — slug en kebab-case ASCII dérivé du nom métier du flux
- **Les deux**

Si le fichier existe déjà : ne **jamais** l'écraser silencieusement — demander s'il faut le remplacer ou suffixer (`-v2`). Après écriture, proposer (sans agir) de commiter via le skill `git-workflow`.

Si des `[RUPTURE]` restent ouvertes, proposer de relancer `/trace-flow` sur le point de rupture une fois le doute levé.

---

## Règles transverses

- **Langue** : tout le flow et le document sont en français.
- **Lecture seule** : aucune modification du code ; seul le fichier de sortie peut être écrit, sur confirmation.
- **Pas d'invention** : une étape non lue n'existe pas ; une incertitude est une `[RUPTURE]`.
- **Un flux et un scénario par invocation.**
- **Suites possibles** : `/codebase-toolkit:backend-specialist` ou `/codebase-toolkit:frontend-specialist` pour agir sur un point d'attention ; `/spec-writer:write-us-from-code` pour formaliser une évolution du flux.
