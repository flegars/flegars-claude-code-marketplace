# Règles de review

Règles appliquées par l'agent `pr-reviewer`. Elles valent quel que soit l'hébergement du code.

## 1. Sources de règles : les CLAUDE.md du repo relu

- Lire **tous** les fichiers listés dans `context.claude_md` : le `CLAUDE.md` racine du repo relu et ceux des
  dossiers parents des fichiers modifiés. Les lire **au commit relu** : `git show <head_sha>:<chemin>`.
- Ne jamais utiliser le CLAUDE.md du plugin, ni celui de l'utilisateur, ni une préférence personnelle.
- Ces règles **priment** sur toute préférence générique. Un CLAUDE.md de sous-dossier précise ou remplace le
  CLAUDE.md racine pour les fichiers de ce sous-dossier.
- Tout commentaire qui découle d'une règle cite cette règle mot pour mot dans `rule_ref`, avec le chemin du
  CLAUDE.md, et prend `category: rule`.
- Si `context.claude_md` est vide : l'écrire dans `summary.notes` (« Aucun CLAUDE.md dans le repo ») et
  continuer avec les vérifications génériques.

## 2. Contexte fonctionnel (US)

- Seules comptent les US et issues **rattachées directement** à la PR : `context.linked_items`. Ne pas déduire
  d'US depuis le nom de branche, un commit ou une mention libre.
- Si au moins un élément est rattaché :
  - lire ses critères d'acceptation (`acceptance_criteria`, sinon les critères présents dans `body`) ;
  - lister dans `summary.us.uncovered_criteria` chaque critère que le diff ne couvre pas ;
  - lister dans `summary.us.out_of_scope` chaque modification du diff étrangère au périmètre de l'US, avec
    `fichier:ligne` ;
  - un critère non couvert ou une modification hors périmètre **localisable** dans le diff peut aussi faire
    l'objet d'un commentaire inline (`us_coverage` / `us_scope`, sévérité `important` au plus).
- Si aucun élément n'est rattaché : `summary.us.found = false` et une note dans `summary.notes`. Ne jamais
  bloquer pour ce motif.

## 3. Risques de régression

Calculés par script, pas par l'agent : `context.regression_risks` liste les lignes remplacées par la PR qui
ont été modifiées par un correctif (`fix`, `hotfix`, `bugfix`) dans la fenêtre configurée. Le plugin poste
lui-même une `question` pour chacune.

L'agent :
- ne crée **pas** de commentaire `regression` ;
- peut s'appuyer sur ces risques pour évaluer le reste du diff ;
- n'affirme **jamais** qu'il y a une régression.

## 4. Axes de review

### Duplication
Avant de signaler une duplication, chercher dans **tout le repo** au commit relu
(`git grep -n "<motif>" <head_sha>`), pas seulement dans le diff. Citer le chemin et la ligne du code
équivalent existant dans `evidence` et `justification`. Pas de chemin cité = pas de commentaire.

### Réutilisation
Si une classe, un service ou un helper existant résout le problème, le citer avec son chemin. Vérifier qu'il
existe **au commit relu** (`git show <head_sha>:<chemin>`) avant de le suggérer. Ne jamais suggérer un élément
non vérifié.

### Interfaces
Commenter **uniquement** si :
- une nouvelle interface n'a qu'une seule implémentation et aucun usage en test ni en injection qui justifie
  l'abstraction ;
- ou, à l'inverse, le code branche sur des types concrets (`instanceof`, `switch` sur un type) là où une
  abstraction existe déjà ou serait justifiée.

Dans tous les autres cas, ne rien dire sur les interfaces.

### Ce qu'on ne commente pas
- Le **style** dès qu'un linter ou un formatter est configuré dans le repo (`context.linters`) : indentation,
  ordre des imports, longueur de ligne, nommage couvert par une règle de lint…
- Les goûts personnels qui ne s'appuient sur aucune règle du repo, aucun fichier existant, aucun risque concret.
- Les lignes que la PR ne modifie pas, sauf si le changement les casse : alors le commentaire vise la ligne
  modifiée responsable.

## 5. Ancrage des commentaires

- Une ligne commentée doit appartenir à un hunk du diff : ligne ajoutée ou ligne de contexte côté `RIGHT`,
  ligne supprimée côté `LEFT`. Les numéros sont ceux de la version concernée.
- Un problème réel situé hors du diff peut être signalé : le plugin le basculera dans la synthèse avec
  `fichier:ligne`. Ne pas tordre l'ancrage pour le faire entrer dans un hunk.
- Un commentaire = un problème. Pas deux commentaires de même catégorie sur la même plage.
- Pas de plafond à gérer côté agent : produire tous les commentaires justifiés, le plugin priorise.

## 6. Rédaction

- Français ; termes techniques en anglais quand ils sont standards.
- Ton factuel, sans flatterie ni dramatisation.
- Ne jamais recopier un secret repéré dans le diff : le signaler en `bloquant` sans en citer la valeur.
