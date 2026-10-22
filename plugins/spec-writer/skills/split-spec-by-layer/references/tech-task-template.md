# Template standardisé d'une Task technique

> Ce template est la **structure de référence figée** utilisée par le skill `split-spec-by-layer` du plugin `spec-writer`. Toute task technique issue du découpage d'une US ou d'une spec DOIT respecter intégralement cette structure, l'ordre des sections et le référentiel des couches ci-dessous.

Le découpage produit une **liste ordonnée** de tasks techniques. Chaque task appartient à **une seule couche**, couvre une part précise des exigences de la source, et s'articule avec les autres tasks via des **contrats d'interface** explicites. Chaque section est obligatoire sauf mention explicite « *(si applicable)* ».

---

## Référentiel des couches (liste fermée)

Seules ces cinq couches existent. Aucune autre couche ne peut être inventée ; une couche peut en revanche être absente d'un découpage si la source ne la sollicite pas.

| Couche | Périmètre | Definition of Done socle (reprise telle quelle dans chaque task de la couche) |
|---|---|---|
| `BACK` | Domaine (entités, value objects, règles métier), application (commands, queries, handlers, services), exposition API (resources, providers, processors, contrôleurs), messaging (messages, handlers async, subscribers), adapters vers les systèmes externes. | Tests unitaires du domaine et tests d'intégration / fonctionnels de l'endpoint ou du handler écrits et verts · Analyse statique verte (PHPStan au niveau du projet) · Contrat d'interface produit conforme à la task (routes, payloads, codes d'erreur) · Aucune régression sur la suite existante. |
| `FRONT` | Composants, pages, routing, gestion d'état, appels API (clients, hooks de data fetching), formulaires et validations côté client, états de chargement / erreur / vide. | Tests de composants (rendu + interactions) écrits et verts · Typage strict sans `any` non justifié · Lint vert · États chargement / erreur / vide gérés · Contrat API consommé conforme à la task productrice. |
| `INFRA` | CI/CD, configuration d'environnement, secrets, conteneurs, orchestration et déploiement, feature flags, routage réseau, monitoring, alerting et logs. | Configuration versionnée (pas de modification manuelle non tracée) · Valeurs renseignées pour chaque environnement concerné · Secrets hors du dépôt · Pipeline vert · Procédure de rollback identifiée. |
| `DATA` | Migrations de schéma (tables, colonnes, contraintes, index), scripts de reprise / backfill / correction de données, vues et requêtes de reporting. | Migration réversible (`down()` écrite et testée) · Exécutée sur une base de dev à partir d'un état représentatif · Impact volumétrie / verrouillage évalué · Script de reprise idempotent (si applicable). |
| `QA` | Tests **transverses** uniquement : end-to-end, non-régression, jeux de données de recette, scénarios de recette fonctionnelle. | Scénarios e2e couvrant les exigences visées, verts en CI ou sur l'environnement de recette · Jeux de données de test documentés · Cas nominaux et cas d'erreur couverts. |

### Règles de frontière

- Les **tests unitaires et d'intégration** appartiennent à la task de dev de leur couche (`BACK`, `FRONT`), jamais à une task `QA`.
- Une **migration de schéma** est une task `DATA`, même si elle est déclenchée par une évolution d'entité `BACK` : la task `BACK` dépend alors de la task `DATA`.
- La **déclaration d'un feature flag** (création, valeurs par environnement) est `INFRA` ; son **utilisation dans le code** est dans la task `BACK` ou `FRONT` qui l'exploite.
- Une **variable d'environnement** nouvelle est déclarée dans une task `INFRA` et consommée par la task applicative concernée.
- En cas de doute entre deux couches, choisir celle qui **produit le livrable principal** de la task et le justifier dans « Objectif & périmètre ».

---

## En-tête du découpage

Avant la liste des tasks, fournir :

1. **Source** — Type (`US` ou `Spec`), titre, ID / URL si connu.
2. **Stack retenue** — Stack détectée dans le code (mode ancré codebase) ou présumée, marquée `[HYPOTHÈSE]` (mode spec pure).
3. **Exigences recensées** — Liste des exigences à couvrir :
   - Source US : noms des scénarios Gherkin des critères d'acceptance.
   - Source spec libre : exigences extraites et numérotées `EX-01`, `EX-02`… (une ligne chacune, formulation reprise de la source).
4. **Tableau récapitulatif** :

   | # | Couche | Titre | Dépend de | Estimation |
   |---|---|---|---|---|
   | T1 | DATA | `[DATA][Domaine] …` | — | X |
   | T2 | BACK | `[BACK][Domaine] …` | T1 | X |

5. **Ordre d'implémentation & lots parallélisables** — Séquence conseillée, en signalant les tasks réalisables en parallèle (ex. `T1 → T2 → (T3 ∥ T4) → T5`).
6. **Matrice de couverture** — Chaque exigence → la ou les tasks qui la couvrent. Aucune exigence orpheline.

   | Exigence | Tasks |
   |---|---|
   | EX-01 / Scénario « … » | T2, T4 |

7. **Total estimé** — Somme des estimations, par couche puis global.

---

## Bloc d'une task

Chaque task suit ce bloc, numéroté séquentiellement (`T1`, `T2`…) :

```
## T<N> — [COUCHE][Domaine] Verbe + complément

**Couche** : BACK | FRONT | INFRA | DATA | QA

### Objectif & périmètre
Ce que la task livre, en 2-4 lignes.
- **IN** : ce qui est fait dans cette task.
- **OUT** : ce qui ne l'est pas, avec renvoi à la task qui le couvre (ex. « affichage de l'erreur → T5 »).

### Exigences couvertes
- EX-XX / Scénario « … » — en quoi la task y contribue.

### Contrat d'interface *(si la task produit ou consomme un contrat)*
- **Produit** : définition complète du contrat, une seule fois dans tout le découpage.
  - API : `METHOD /path` · payload requête · payload réponse · codes HTTP et erreurs métier.
  - Event / message : nom · payload · producteur · consommateurs · sync / async.
  - Schéma : table · colonnes (type, nullabilité, défaut) · contraintes · index.
  - Configuration : nom de la variable / du flag · valeurs par environnement · défaut.
- **Consomme** : référence au contrat défini ailleurs (« contrat produit par T2 »), sans le redécrire.

### Détails d'implémentation
- Mode ancré codebase : fichiers à créer / modifier, avec ligne pertinente si connue (`path/to/file.php:42`), et pattern existant à suivre.
- Mode spec pure : composants / modules visés, sans inventer de chemin.

### Definition of Done
- [ ] Socle de la couche (copié depuis le référentiel des couches)
- [ ] Critère spécifique à la task, vérifiable objectivement
- [ ] …

### Dépendances
- **Tasks bloquantes** : T<N>, … (« Aucune » si indépendante).
- **Contrats consommés** : T<N> (si applicable).

### Estimation
**X h / X pts** — *Justification courte : complexité, nombre de cas, intégrations, incertitude.*

### Risques / points d'attention *(si applicable)*
- Risque technique, dépendance externe, volumétrie, point à valider avec le métier.
```

---

## Règles de cohérence

- **Une task = une couche.** Un livrable qui touche deux couches est scindé en deux tasks reliées par une dépendance et un contrat.
- **Grille de titre unique** : `[COUCHE][Domaine] Verbe à l'infinitif + complément`, le domaine étant repris tel quel de la source (ex. `[BACK][Souscription] Exposer l'endpoint de validation du dossier`).
- **Contrat défini une seule fois** : dans la task qui le produit. Toute task consommatrice y renvoie par son numéro. Deux descriptions d'un même contrat sont interdites.
- **Socle de DoD identique** pour toutes les tasks d'une même couche ; seuls les critères spécifiques varient.
- **Granularité homogène** : viser 0,5 à 2 jours par task ; scinder au-delà.
- **Unité d'estimation unique** sur tout le découpage (heures OU story points 1, 2, 3, 5, 8).
- **Couverture intégrale** : chaque exigence recensée est couverte par au moins une task.
- **Zéro chevauchement** : deux tasks ne réalisent pas le même périmètre.
- **Vocabulaire constant** : termes métier exacts de la source (ne pas renommer « société » en « entreprise »).
- **Périmètre strict** : aucune task ne crée de fonctionnalité absente de la source. Un besoin technique implicite (index, flag, migration) est légitime s'il sert une exigence recensée, et il est rattaché à celle-ci.

---

## Anti-patterns à NE PAS reproduire

- ❌ Task « Faire le back » / « Faire le front » / « Mettre en place l'infra » sans périmètre ni livrable précis.
- ❌ Task à cheval sur plusieurs couches (« Créer la table et l'endpoint »).
- ❌ Couche hors référentiel (`OPS`, `DEVOPS`, `MISC`…).
- ❌ Contrat décrit deux fois, ou décrit de façon divergente entre producteur et consommateur.
- ❌ Task `FRONT` qui consomme une API sans référencer la task `BACK` productrice.
- ❌ Task `QA` contenant les tests unitaires d'une autre couche.
- ❌ Task « Divers » / « Finalisation » / « Reste à faire ».
- ❌ DoD sans le socle de la couche, ou socle reformulé différemment d'une task à l'autre.
- ❌ Exigence de la source non couverte par la matrice.
- ❌ Chemin de fichier inventé en mode spec pure.
