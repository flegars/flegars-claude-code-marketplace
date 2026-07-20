# Template standardisé d'une Task

> Ce template est la **structure de référence figée** utilisée par le skill `split-us-into-tasks` du plugin `us-writer`. Toute task issue du découpage d'une User Story DOIT respecter intégralement cette structure et l'ordre des sections.

Le découpage produit une **liste ordonnée** de tasks. Chaque task est autonome, testable, et couvre une part précise du périmètre de l'US parente. Chaque section ci-dessous est obligatoire sauf mention explicite « *(si applicable)* ».

---

## En-tête du découpage

Avant la liste des tasks, rappeler en quelques lignes :
- **US parente** : titre `[Domaine] …` (et ID du work item ADO si connu).
- **Ordre d'implémentation global** : la séquence conseillée des tasks (par numéro), en tenant compte des dépendances.
- **Couverture** : confirmer que l'ensemble des critères d'acceptance de l'US est couvert par au moins une task (aucun critère orphelin).

---

## Bloc d'une task

Chaque task suit ce bloc, numéroté séquentiellement :

```
## [Task N] Titre

**Format du titre** : `[Domaine] Verbe court + Complément`

### Description
Ce que la task réalise concrètement, en 2-4 lignes. Périmètre précis : ce qui est fait, ce qui ne l'est pas (renvoyé à une autre task si besoin).

### Definition of Done
Checklist de critères vérifiables objectivement (cases à cocher) :
- [ ] critère mesurable 1
- [ ] critère mesurable 2
- [ ] tests couvrant la task écrits et passants (si applicable)

### Critères d'acceptance couverts
Liste des scénarios / critères de l'US parente que cette task adresse (référencer par nom de scénario Gherkin). Garantit la traçabilité task → US.

### Fichiers concernés *(si découpage ancré codebase)*
Fichiers du repo à créer ou modifier, avec ligne pertinente si connue :
- `path/to/file.php:42`
- `path/to/other.ts`

### Dépendances
- **Tasks prérequises** (bloquantes) : par numéro (ex. `Task 1`, `Task 3`). « Aucune » si la task est indépendante.

### Estimation
Estimation en **heures** OU en **story points** (1, 2, 3, 5, 8) — rester cohérent sur l'ensemble du découpage.

**Estimation : X h / X pts** — *Justification courte : complexité technique, nombre de cas, intégrations.*
```

---

## Règles de découpage

- **Atomicité** : une task = un livrable testable et mergeable indépendamment autant que possible. Pas de task fourre-tout.
- **Couverture intégrale** : chaque critère d'acceptance de l'US doit être rattaché à au moins une task. Aucun critère orphelin.
- **Zéro chevauchement** : deux tasks ne redéveloppent pas le même périmètre.
- **Ordonnancement explicite** : les dépendances entre tasks sont déclarées ; l'ordre d'implémentation global est donné dans l'en-tête.
- **Granularité homogène** : éviter de mélanger une task de 30 min avec une task de 3 jours ; scinder les tasks trop grosses.

---

## Anti-patterns à NE PAS reproduire

- ❌ Task « Divers » / « Finalisation » / « Reste à faire » → périmètre non défini.
- ❌ Task sans Definition of Done.
- ❌ Task ne référençant aucun critère d'acceptance de l'US.
- ❌ Découpage laissant un critère d'acceptance non couvert.
- ❌ Task dont le titre décrit une couche technique sans livrable métier (« Faire le back », « Faire le front ») sans périmètre précis.
- ❌ Estimation absente ou non justifiée.
