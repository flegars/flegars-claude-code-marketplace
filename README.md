# flegars-claude-code-marketplace

Marketplace personnelle de plugins [Claude Code](https://claude.com/claude-code) de Florian Legars.

## Installation

Ajouter la marketplace dans Claude Code :

```bash
/plugin marketplace add legars-florian/flegars-claude-code-marketplace
```

> Remplacer par l'URL ou le chemin local effectif si la marketplace n'est pas (encore) publiée sur GitHub :
>
> ```bash
> /plugin marketplace add /Users/florian/projects/perso/flegars-claude-code-marketplace
> ```

Puis installer un plugin :

```bash
/plugin install <nom-du-plugin>@flegars-perso-marketplace
```

## Plugins disponibles

### [`codebase-to-us`](./plugins/codebase-to-us)

> Rédige des User Stories standardisées à partir de l'analyse de la codebase courante.

**À quoi ça sert** — Transformer un besoin métier (forward US) ou une feature déjà implémentée (reverse US) en User Story complète, ancrée dans le code existant. Toutes les US produites suivent **systématiquement** la même structure figée, ce qui garantit cohérence et exhaustivité d'une US à l'autre.

**Ce que ça apporte :**

- **Slash command `/write-us-from-code`** — Orchestre un flow en 4 phases :
  1. **Cadrage** — Reformulation du besoin et choix forward / reverse US
  2. **Exploration codebase** — Identification des fichiers, endpoints, entités et events concernés
  3. **Rédaction** — Délégation à l'agent `us-writer` avec le contexte collecté
  4. **Sortie** — Écriture dans `docs/user-stories/US-<domaine>-<slug>.md`, rendu inline, ou les deux
- **Agent `us-writer`** — Un Product Owner senior virtuel, rigoureux, qui rédige l'US en suivant à la lettre le template du plugin. Lit la codebase avant d'écrire (jamais de comportement supposé), marque toute hypothèse `[HYPOTHÈSE]`, et liste les questions ouvertes en fin d'US.
- **Template d'US figé** — Structure imposée : Titre `[Domaine] Verbe + Complément` / Description En tant que… / Contexte & Règles métier (avec sous-bloc « Comportement actuel observé dans la codebase ») / Critères d'acceptance Gherkin (nominal + alternatifs + erreurs + bords) / Spécifications techniques / Maquettes / Dépendances / Scope IN-OUT / Estimation en story points / Questions ouvertes.

**Quand l'utiliser** — Avant de démarrer une feature pour formaliser la spec, ou pour rattraper la documentation d'une feature existante.

### [`pr-reviewer`](./plugins/pr-reviewer)

> Review standardisée de Pull Requests GitHub ou Azure DevOps avec note /20, ressenti global, axes d'amélioration et alignement avec les User Stories rattachées.

**À quoi ça sert** — Produire des reviews de PR **reproductibles** : même grille, même structure, même rigueur quel que soit le repo. Le plugin se branche sur les connexions déjà disponibles (`gh` CLI pour GitHub, MCP `devops` pour Azure DevOps) pour récupérer la PR, son diff et ses User Stories / work items rattachés, puis confronte le code livré à ce que demandent les specs.

**Ce que ça apporte :**

- **Slash command `/review-pr [url] [--inline|--local]`** — Orchestre un flow en 5 phases :
  1. **Cible** — Détection auto via la branche courante (`gh pr view`) ou MCP `devops`, sinon URL passée en argument
  2. **Fetch** — PR + diff + US/work items rattachés (parsing `closes #N` côté GitHub, liens explicites côté Azure)
  3. **Détection stack** — `composer.json` / `package.json` / `go.mod` / `pyproject.toml` pour activer la sous-grille adaptative
  4. **Analyse** — Délégation à l'agent `pr-reviewer` avec tout le contexte
  5. **Sortie** — Commentaires inline + commentaire global sur la PR (mode `--inline`) ou fichier `reviews/PR-<id>.md` (mode `--local`)
- **Agent `pr-reviewer`** — Un reviewer senior multi-stack rigoureux, qui suit à la lettre la grille et le template figés du plugin. Cite des lignes précises (`path:line`), propose des fix copiables, refuse d'inventer des patterns « du projet » qu'il n'aurait pas lus.
- **Grille de notation hybride /20** — 14 points universels (qualité, sécurité, tests, lisibilité, **alignement US**, architecture) + 6 points adaptatifs activés selon la stack détectée (Symfony/DDD, Go, TypeScript/React, Python, ou fallback générique).
- **Template de rapport figé** — Structure imposée : titre `📊 Score: X/20 — <ressenti>` / 📋 Alignement avec les US / ✅ Points forts / ⚠️ Axes d'amélioration par sévérité (Critique / Important / Mineur) / 🐛 Problèmes critiques si applicable / 📚 Conformité architecture (sous-grille adaptative) / 💡 Recommandations actionnables / 🧮 Détail du score.

**Quand l'utiliser** — Pour reviewer une PR ouverte (avant ou après merge), pour standardiser les reviews d'équipe, ou pour s'auto-évaluer avant de demander une review humaine.

## Structure

```
flegars-claude-code-marketplace/
├── .claude-plugin/
│   └── marketplace.json     # Manifest de la marketplace
├── plugins/
│   ├── codebase-to-us/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── agents/
│   │   │   └── us-writer.md
│   │   └── skills/
│   │       └── write-us-from-code/
│   │           ├── SKILL.md
│   │           ├── metadata.json
│   │           └── references/
│   │               └── us-template.md
│   └── pr-reviewer/
│       ├── .claude-plugin/
│       │   └── plugin.json
│       ├── agents/
│       │   └── pr-reviewer.md
│       └── skills/
│           └── review-pr/
│               ├── SKILL.md
│               ├── metadata.json
│               └── references/
│                   ├── review-template.md
│                   └── scoring-rubric.md
└── README.md
```

## Licence

MIT
