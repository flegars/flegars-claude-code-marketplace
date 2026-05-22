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

## Structure

```
flegars-claude-code-marketplace/
├── .claude-plugin/
│   └── marketplace.json     # Manifest de la marketplace
├── plugins/
│   └── codebase-to-us/
│       ├── .claude-plugin/
│       │   └── plugin.json
│       ├── agents/
│       │   └── us-writer.md
│       └── skills/
│           └── write-us-from-code/
│               ├── SKILL.md
│               ├── metadata.json
│               └── references/
│                   └── us-template.md
└── README.md
```

## Licence

MIT
