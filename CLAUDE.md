# CLAUDE.md

Ce fichier guide Claude Code lors du travail dans cette marketplace personnelle de plugins.

## Ce qu'est ce repo

`flegars-claude-code-marketplace` est une **marketplace Claude Code** personnelle (publique, GitHub) de Florian Legars. Elle n'embarque pas de code applicatif : uniquement des plugins (agents, skills, slash commands) versionnés et distribuables.

Repo associé : `legars-florian/flegars-claude-code-marketplace` sur GitHub.

## Identité à utiliser

C'est un repo **personnel**. Toujours utiliser :

- **Nom** : `Florian Legars`
- **Email** : `legars.florian@gmail.com` (email perso GitHub — **jamais** l'email pro `florian.legars@inter-invest.fr`)

Cette règle s'applique à tous les fichiers d'identité : `marketplace.json`, `plugin.json`, `metadata.json`, agents, README, CODEOWNERS, commits, etc.

## Structure imposée

```
flegars-claude-code-marketplace/
├── .claude-plugin/
│   └── marketplace.json          # Manifest racine — liste les plugins exposés
├── plugins/
│   └── <plugin-name>/
│       ├── .claude-plugin/
│       │   └── plugin.json       # Manifest du plugin
│       ├── agents/               # Agents .md (optionnel)
│       │   └── <agent-name>.md
│       └── skills/               # Skills (optionnel)
│           └── <skill-name>/
│               ├── SKILL.md
│               ├── metadata.json
│               └── references/   # Fichiers de référence chargés par le skill/agent
├── README.md
└── CLAUDE.md
```

Conventions :
- Noms en **kebab-case ASCII** partout (plugin, agent, skill, fichier).
- Les agents et skills sont rédigés **en français** (cohérence avec les autres marketplaces de Florian et avec le contexte projet par défaut Inter Invest pour le domaine métier).
- Un skill exposé via slash command doit avoir `user_invocable: true` dans son frontmatter et son slug devient automatiquement `/<skill-name>`.
- Une référence chargée par un skill ou agent depuis le plugin se résout via `${CLAUDE_PLUGIN_ROOT}/...`.

## Workflow : ajouter un nouveau plugin

Procédure à respecter, dans l'ordre :

1. **Créer l'arborescence** du plugin sous `plugins/<plugin-name>/` en suivant la structure ci-dessus.
2. **Écrire `plugins/<plugin-name>/.claude-plugin/plugin.json`** :
   ```json
   {
     "name": "<plugin-name>",
     "description": "...",
     "version": "0.1.0",
     "author": { "name": "Florian Legars", "email": "legars.florian@gmail.com" },
     "license": "MIT",
     "keywords": ["...", "..."]
   }
   ```
3. **Écrire les agents** sous `agents/` (frontmatter : `name`, `description`, `tools`, `model`, optionnel `color`).
4. **Écrire les skills** sous `skills/<skill-name>/SKILL.md` (frontmatter : `name`, `description`, `user_invocable` si exposé en slash command) + `metadata.json` à côté. Les références vont dans `references/`.
5. **Référencer le plugin dans `.claude-plugin/marketplace.json`** (à la racine) en ajoutant une entrée dans le tableau `plugins` :
   ```json
   {
     "name": "<plugin-name>",
     "source": "./plugins/<plugin-name>",
     "description": "...",
     "version": "0.1.0",
     "author": { "name": "Florian Legars" },
     "keywords": ["..."],
     "category": "productivity"
   }
   ```
6. **⚠️ Mettre à jour le `README.md`** — ajouter une section `### \`<plugin-name>\`` sous « Plugins disponibles » avec :
   - Un sous-titre `>` qui résume en une phrase ce que fait le plugin
   - Un bloc « À quoi ça sert »
   - Un bloc « Ce que ça apporte » (slash commands, agents, fichiers de référence)
   - Un bloc « Quand l'utiliser »
7. **Mettre à jour `README.md` section Structure** si la forme du nouveau plugin enrichit l'arborescence (ex : premier plugin à ajouter un dossier `commands/`, `hooks/`, etc.).

## Workflow : modifier un plugin existant

1. Modifier les fichiers du plugin.
2. **Bumper `version`** dans `plugins/<plugin-name>/.claude-plugin/plugin.json` (semver : patch / minor / major selon l'impact).
3. **Bumper `version`** dans l'entrée correspondante du `.claude-plugin/marketplace.json` racine (si elle y figure).
4. **⚠️ Mettre à jour le `README.md`** si la description, les capacités, ou le contenu mis en avant du plugin changent. Ne pas laisser le README mentir sur ce que fait le plugin.

## Workflow : supprimer un plugin

1. Supprimer le dossier `plugins/<plugin-name>/`.
2. Retirer l'entrée correspondante du `.claude-plugin/marketplace.json` racine.
3. **⚠️ Retirer la section correspondante du `README.md`** sous « Plugins disponibles ».
4. Mettre à jour la section « Structure » du `README.md` si nécessaire.

## Règle d'or

> **Toute modification, ajout ou suppression de plugin doit être reflétée dans `README.md`.**
>
> Le `README.md` est la vitrine de la marketplace : il doit toujours être en cohérence stricte avec ce qui est réellement disponible dans `plugins/`. Si tu touches à un plugin, tu touches au README dans la même action.

Vérification rapide avant de considérer une modification comme terminée :

- [ ] `marketplace.json` à jour (entrée ajoutée / retirée / version bumpée)
- [ ] `plugin.json` à jour (version bumpée si modif)
- [ ] `README.md` à jour (section « Plugins disponibles » + « Structure » si pertinent)
- [ ] Identité = email perso `legars.florian@gmail.com`

## Tester un plugin en local

```bash
/plugin marketplace add /Users/florian/projects/perso/flegars-claude-code-marketplace
/plugin install <plugin-name>@flegars-perso-marketplace
```

Pour recharger après modification : `/plugin marketplace update flegars-perso-marketplace` puis `/plugin install ...` (ou désinstaller / réinstaller).

## Commits

Conventional Commits, scope obligatoire. Exemples :

- `feat(codebase-to-us): add reverse US mode`
- `fix(codebase-to-us): correct template path resolution`
- `docs(readme): document new plugin foo-bar`
- `chore(marketplace): bump codebase-to-us to 0.2.0`

Le plugin `git-workflow@elvest-marketplace` (déjà installé chez Florian) peut être utilisé pour générer ces commits.
