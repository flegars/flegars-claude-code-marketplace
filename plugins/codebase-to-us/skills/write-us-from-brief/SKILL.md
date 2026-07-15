---
name: write-us-from-brief
description: "Rédige une User Story standardisée à partir d'un brief externe, sans accès à la codebase. Sources acceptées : texte de recueil de besoin collé inline, description de maquette / UI, fichier local (.md/.txt/.pdf), ou URL de doc partagée (Notion, Confluence…). Orchestre un flow en 4 phases : cadrage du besoin → acquisition & lecture des sources → rédaction via l'agent us-drafter → sortie (fichier docs/user-stories/ ou inline). Toutes les US suivent obligatoirement la structure figée du plugin. Pensé pour Claude cowork ou le cadrage amont, quand le code n'est pas disponible. Déclencher quand l'utilisateur dit : /write-us-from-brief, 'écris une US sans le code', 'rédige une US à partir de cette maquette', 'transforme ce recueil de besoin en User Story', 'US à partir de ce doc', ou fournit un brief/maquette/URL à formaliser en spec."
user_invocable: true
---

# Write US From Brief

Orchestre la rédaction d'une User Story standardisée à partir d'un **brief externe**, **sans accès à la codebase**. C'est le pendant « sans code » du skill `write-us-from-code` : même template figé (`references/us-template.md`, partagé), même exigence de rigueur, mais la matière première est un recueil de besoin, une maquette, un fichier ou une doc externe.

Cas d'usage typiques : **Claude cowork** (pas de repo monté), cadrage amont par un PO/PM, formalisation d'une maquette ou d'un compte-rendu de réunion en spec.

Le résultat suit **systématiquement** la structure figée définie dans :
`${CLAUDE_PLUGIN_ROOT}/skills/write-us-from-code/references/us-template.md`

## Vue d'ensemble du flow

1. **Cadrage** — Comprendre le besoin et reformuler
2. **Acquisition & lecture des sources** — Récupérer la matière (inline / fichier / URL / maquette décrite)
3. **Rédaction** — Déléguer à l'agent `us-drafter` avec le contexte collecté
4. **Sortie** — Demander où écrire le résultat (fichier, inline, ou les deux)

---

## Phase 1 — Cadrage

Si l'utilisateur n'a pas fourni de description en argument du slash command, demander via `AskUserQuestion` :

**« Quel est le besoin métier à transformer en US ? »**

Reformuler le besoin en 3-5 lignes (persona, déclencheur, résultat attendu) et confirmer avec `AskUserQuestion` : « Ma reformulation est-elle correcte ? » (Oui / Non, je précise).

> Ce skill ne propose pas le choix forward / reverse US : sans codebase, il n'y a pas de « reverse » (documenter du code existant). On rédige toujours une US prospective ancrée dans le brief.

---

## Phase 2 — Acquisition & lecture des sources

Identifier **d'où vient la matière** puis la récupérer. Si la source n'est pas évidente, demander via `AskUserQuestion` : **« Quelle est la source du besoin ? »** (choix multiple) :

- **Texte collé inline** — résumé de recueil de besoin, notes de réunion, description libre déjà dans la conversation.
- **Description de maquette / UI** — écran(s) décrits (champs, ordre, états, messages) pour dériver les critères UI.
- **Fichier local** — un `.md` / `.txt` / `.pdf` dans le répertoire de travail (à lire avec `Read` ; localiser avec `Glob`/`Grep` au besoin ; un PDF se lit via `Read` avec le paramètre de pages).
- **URL / doc externe** — Notion, Confluence, doc partagée (à récupérer avec `WebFetch`).

Récupérer effectivement le contenu des sources retenues (lecture fichier, fetch URL). **Ne pas explorer de codebase** : ce skill part du brief, même si un repo est présent.

Garder en mémoire :
- La liste des sources exploitées (avec identifiant lisible : nom de fichier, titre de maquette, URL)
- Les éléments concrets retenus de chaque source (champs, écrans, règles, contraintes)
- Le **besoin / gap** à combler tel qu'il ressort des sources
- Les **zones muettes** des sources (ce qu'elles ne précisent pas) → deviendront des « Questions ouvertes »

Si une ambiguïté ne peut être levée qu'en lisant du code, le noter : suggérer à l'utilisateur le skill `write-us-from-code` (mode codebase) pour cette partie.

---

## Phase 3 — Rédaction via l'agent us-drafter

Déléguer la rédaction à l'agent `us-drafter` via le tool `Agent` (subagent_type=`us-drafter`).

**Prompt à fournir à l'agent** — inclure :
- Le besoin reformulé et confirmé en Phase 1
- Le persona ciblé
- La synthèse des sources (sources exploitées + éléments retenus + gap + zones muettes)
- Le contenu brut pertinent des sources (texte collé, extraits de fichier, contenu fetché)
- L'instruction explicite : « Lire d'abord `${CLAUDE_PLUGIN_ROOT}/skills/write-us-from-code/references/us-template.md` puis rédiger l'US en suivant ce template à la lettre, en utilisant le sous-bloc « Sources analysées » (pas « Comportement actuel observé dans la codebase »). »

L'agent retourne l'US complète en Markdown.

---

## Phase 4 — Sortie

Demander à l'utilisateur via `AskUserQuestion` :

**« Où écrire l'US ? »**
- **Fichier `docs/user-stories/US-<domaine>-<slug>.md` dans le répertoire courant** (recommandé si un répertoire de travail est disponible)
- **Inline dans la conversation uniquement** (par défaut en Claude cowork si aucun répertoire n'est monté)
- **Les deux**

### Convention de nommage du fichier

- Domaine : extrait du titre `[Domaine] …`, en kebab-case (`Société` → `societe`, `Webhook Hubspot` → `webhook-hubspot`).
- Slug : 3-6 mots résumant l'action, en kebab-case ASCII (`creer-avec-validation-siret`).
- Nom complet : `US-<domaine>-<slug>.md` (ex : `US-societe-creer-avec-validation-siret.md`).

Si `docs/user-stories/` n'existe pas, le créer.

### Si sortie fichier

- `Write` le fichier
- Afficher à l'utilisateur le chemin créé
- Proposer (sans agir) de commiter via le skill `git-workflow` si disponible

### Si sortie inline

Restituer directement l'US dans la réponse, formatée en Markdown.

---

## Règles transverses

- **Langue** : tout le flow et toutes les questions sont en français.
- **Sans codebase par construction** : ce skill n'explore jamais de code. Pour ancrer une US dans du code existant, utiliser `write-us-from-code`.
- **Pas d'écriture prématurée** : aucun fichier n'est créé avant la Phase 4.
- **Pas de devinette** : si les sources ne suffisent pas à lever une ambiguïté, l'agent `us-drafter` la liste en « Questions ouvertes » (et tague `[HYPOTHÈSE]` dans le corps) plutôt que d'inventer.
- **Une seule US par invocation** : si le besoin couvre plusieurs sujets, proposer à l'utilisateur de le découper et relancer le skill pour chaque US.
