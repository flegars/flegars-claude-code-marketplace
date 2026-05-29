# Grille d'audit back-end PHP/Symfony — référence figée

Toute analyse produite par le plugin `audit-codebase` **doit couvrir les 6 axes ci-dessous**, dans cet ordre, pour chaque module audité. Chaque finding doit être **ancré sur un fichier précis** (`src/.../Foo.php:42`) — pas de jugement abstrait, pas de jargon vide.

Vocabulaire :

- **Finding** = un constat précis, ancré sur du code observé.
- **Sévérité** = `bloquant` / `important` / `mineur` (utilisée pour les axes 2 et 6 essentiellement).
- **Effort** = `S` (< 1j) / `M` (1-5j) / `L` (> 5j ou refacto structurelle).

Pour chaque finding (sauf axe 1) : préciser sévérité + effort estimé.

---

## Axe 1 — ✅ Points forts à conserver

**Objectif** — Lister explicitement ce qui marche bien et qu'il **ne faut pas casser** lors d'évolutions futures. Cet axe est aussi important que les axes de dette : il sert d'ancre pour les arbitrages.

**Ce qu'on cherche** :

- Patterns sains et bien appliqués (CQRS clair, Domain isolé, Repository thin, Processor API Platform ≤ 30 lignes, …).
- Briques solides : tests robustes, fixtures bien maintenues, PHPStan haut niveau, suite verte.
- Conventions de code claires et tenues.
- Séparation des responsabilités effective (pas de fuite Infra dans le Domain).
- Sécurité bien appliquée (Voters, attributs, validation des inputs).
- Outbox / Domain Events bien câblés si présents.

**Comment chercher** :

- `Glob src/Domain/**/*.php` → repérer les entités, VO, events, ports.
- Lire 2-3 Commands/Queries + leurs Handlers pour valider le pattern CQRS.
- Lire 1-2 Resources API Platform + Processors pour valider la thin-ness.
- `Glob tests/**/*.php` pour cartographier la stratégie de tests.
- `Read phpstan.neon` / `phpstan.dist.neon` pour vérifier le niveau.

**Format de sortie attendu (par finding)** :

```markdown
- **<Titre court>** — `src/.../Foo.php:42`
  - Pourquoi c'est un point fort : ...
  - À préserver lors de : ... (mention explicite des évolutions qui pourraient le mettre en danger)
```

---

## Axe 2 — ⚠️ Risques & dette technique

**Objectif** — Identifier les zones fragiles, code smells, anti-patterns, couplages problématiques, dette qui s'accumule.

**Ce qu'on cherche** :

- **God classes** — classes > 300 lignes, > 15 méthodes, ou avec plusieurs raisons de changer.
- **Couplage fort** — instanciations en dur (`new Foo()` dans du code métier), services qui dépendent de 8+ autres services.
- **Fuites de couche** — Doctrine importé dans `src/Domain/`, types Symfony (`Request`, `Response`) dans la couche Application.
- **Logique métier dispersée** — règles métier dans des Controllers, Processors, Repositories.
- **Magic strings & numbers** — constantes magiques répétées qui devraient être des Enums ou Value Objects.
- **Exceptions trop génériques** — `throw new \Exception(...)` ou attrapage de `\Throwable` qui masque les vrais bugs.
- **Code mort** — méthodes / classes / fichiers non référencés.
- **Dépendances obsolètes** — vendor avec versions très anciennes, packages abandonnés (`composer outdated`).
- **TODO / FIXME / HACK** — comptés et listés (`Grep -n "TODO\|FIXME\|HACK"`).
- **Sécurité** — secrets en dur, requêtes SQL concaténées, pas de validation des inputs, exposition d'informations sensibles dans les logs ou les réponses.
- **Conformité** — gestion RGPD, données financières, contraintes réglementaires si signalées dans le contexte.

**Comment chercher** :

- `Bash composer outdated --direct` (si lent : sauter et le noter).
- `Grep "new [A-Z]" src/Domain` — instanciations en dur dans le Domain.
- `Grep "Doctrine" src/Domain` — fuite ORM dans le Domain.
- `Grep "Symfony\\\\Component\\\\HttpFoundation" src/Application` — fuite HTTP dans Application.
- `Grep -rn "TODO\|FIXME\|HACK" src/`.
- `Bash find src -name "*.php" -exec wc -l {} + | sort -rn | head -20` — top 20 fichiers les plus gros (candidats god class).
- Lire les 3-5 plus gros fichiers du module et flagger ce qui dépasse la responsabilité unique.

**Format de sortie attendu (par finding)** :

```markdown
- **[<sévérité>][effort: <S|M|L>] <Titre court>** — `src/.../Foo.php:42`
  - Constat : ...
  - Pourquoi c'est un risque : impact métier + impact technique
  - Piste de fix : action concrète (idéalement avec snippet ou pointeur de pattern existant)
```

---

## Axe 3 — 🪓 Opportunités de simplification

**Objectif** — Détecter le **sur-engineering** : code complexe qui pourrait être remplacé par un pattern plus simple sans perdre en qualité.

**Ce qu'on cherche** :

- **Interfaces à un seul implémenteur** sans raison technique (pas de double impl, pas de test double justifiant l'interface, pas de swap prévu).
- **Couches d'indirection gratuites** — un service qui appelle un service qui appelle un service, sans logique propre.
- **Patterns posés "au cas où"** — Strategy à 1 stratégie, Factory à 1 produit, Observer sans subscriber autre que le composant qui dispatch.
- **Abstractions prématurées** — DTO identique à 1 caractère près à l'entité (`UserDto` ≈ `User`).
- **Wrappers triviaux** — méthodes qui ne font que déléguer (`return $this->foo->bar()`).
- **Configuration dépassant l'usage** — fichiers de config avec 10 toggles dont 1 seul est utilisé.
- **Sur-utilisation de Messenger / event-driven** — events dispatchés et consommés sync dans la même action sans bénéfice.
- **DDD light cargo-cult** — Value Objects qui wrappent juste un string sans invariant, agrégats à 1 entité, repositories `find/save` sans valeur ajoutée.
- **Tests sur-mockés** — tests d'intégration qui mockent tout et ne testent plus l'intégration.

**Heuristique de qualification** : avant de proposer une simplification, vérifier que **la complexité actuelle ne couvre pas un besoin réel** (ex : une interface peut sembler inutile mais elle existe pour permettre un test double — vérifier les tests avant de proposer de la retirer).

**Comment chercher** :

- `Grep -rn "interface [A-Z]" src/` puis pour chaque interface : `Grep -rn "implements <Nom>" src/` — si 1 seul implémenteur **et** pas d'utilisation dans les tests pour un double, candidat à supprimer.
- Lire les Services applicatifs / Handlers > 10 lignes de méthode qui ne contiennent que des appels délégués.
- Lire les VO / DTO et comparer aux entités sous-jacentes (`Read` les deux côte à côte).
- `Bash` pour compter les events dispatchés (`Grep "dispatch("`) et leurs handlers (`Grep -rn "EventSubscriber\|MessageHandler"`) — events sans handler ou avec un seul handler sync = suspect.

**Format de sortie attendu (par finding)** :

```markdown
- **[effort: <S|M|L>] <Titre court>** — `src/.../Foo.php:42`
  - Constat : la complexité posée actuellement.
  - Pourquoi c'est simplifiable : analyse de la valeur réelle vs valeur supposée.
  - Pattern de remplacement proposé : option plus simple compatible avec le reste du projet.
  - À vérifier avant de simplifier : (ex : "Vérifier qu'aucun test ne dépend de l'interface comme test double — `tests/Unit/FooTest.php` la mocke peut-être.")
```

> ⚠️ **Toute simplification proposée doit explicitement lister la condition de vérification**. On ne casse pas une couche d'indirection sans avoir confirmé qu'elle ne porte aucune valeur.

---

## Axe 4 — 🧪 Tests & qualité

**Objectif** — État du testing du module : couverture, fiabilité, zones non couvertes, qualité des tests existants.

**Ce qu'on cherche** :

- **Présence de tests** par couche : unitaire (Handlers, VO, services Domain), intégration (Repositories, Processors), fonctionnel (endpoints API).
- **Couverture qualitative** — pas un % chiffré (sauf si `phpunit --coverage` est dispo), mais une appréciation : chemins nominaux + alternatifs + erreurs + bords.
- **Tests fragiles** — tests qui dépendent de l'ordre d'exécution, de l'horloge système non mockée, de l'état d'une DB partagée, du contenu du filesystem.
- **Tests sur-mockés** — un test "d'intégration" qui mocke la DB et l'HTTP n'est plus un test d'intégration.
- **Tests qui testent l'implémentation** plutôt que le comportement (assertions sur l'ordre des appels mock plutôt que sur l'effet observable).
- **Fixtures** — présence, fraîcheur, taille (fixture de 5000 lignes = signal d'alarme).
- **PHPStan / Psalm** — niveau, suppressions inline (`@phpstan-ignore-line`), `baseline.neon`.
- **Linting / formatage** — `php-cs-fixer`, `phpcs`, conventions tenues.
- **Mutation testing** — présent (`infection`) ou pas.

**Comment chercher** :

- `Glob tests/**/*.php` pour cartographier la structure de tests.
- Pour chaque dossier du module audité, vérifier s'il existe `tests/Unit/<Module>/`, `tests/Integration/<Module>/`, `tests/Functional/<Module>/`.
- Lire 2-3 tests pour évaluer leur qualité (assertions, mocks, fixtures).
- `Read phpstan.neon` / `phpstan-baseline.neon` — la taille du baseline est un proxy de la dette de typage.
- `Grep -rn "@phpstan-ignore\|@psalm-suppress" src/` — suppressions inline.

**Format de sortie attendu (par finding)** :

```markdown
- **[<sévérité>][effort: <S|M|L>] <Titre court>** — `<chemin pertinent>`
  - Constat : ...
  - Risque : ...
  - Action proposée : ... (ex : "Ajouter un test d'intégration sur `CreateFooProcessor` couvrant les cas erreur 4xx — pas couverts aujourd'hui.")
```

Si une couche de tests est totalement absente sur le module : un finding **bloquant** par défaut.

---

## Axe 5 — 🚀 Performance & scalabilité

**Objectif** — Goulots potentiels, requêtes N+1, requêtes lentes, sérialisation coûteuse, configurations de cache absentes.

**Ce qu'on cherche** :

- **Requêtes N+1 Doctrine** — `findAll()` suivi d'un foreach qui accède à une relation, sans `fetch="EAGER"` ni `addSelect()` dans le QueryBuilder.
- **Requêtes sans index** — colonnes utilisées en `WHERE` / `ORDER BY` sans index Doctrine (`#[ORM\Index]`).
- **Boucles avec accès DB** — `foreach (...) { $em->persist(...); }` sans batch flush.
- **Pas de pagination** — endpoint listant qui retourne tout sans limite (`findAll`, `findBy([])` sans `setMaxResults`).
- **Sérialisation lourde** — Resources API Platform avec normalisations imbriquées non plafonnées (`groups` qui chargent des aggrégats entiers).
- **Cache absent** sur des données rarement modifiées (catalogues, configs, lookups).
- **Locks et concurrence** — opérations multi-étapes sans transaction, ou transactions trop larges.
- **Synchrone vs async** — opérations longues (envoi mail, appel API externe, génération PDF) faites en sync dans le request lifecycle au lieu de partir en transport async Messenger.
- **Logs verbeux** — `dump()` / `var_dump()` oubliés, logs DEBUG en prod, log de payloads volumineux.

**Comment chercher** :

- `Grep -rn "findAll\(\)" src/` — candidats potentiels.
- `Grep -rn "findBy\(\[\]" src/` — listings sans filtre.
- Lire les QueryBuilders > 5 lignes et chercher les JOIN sans `addSelect`.
- `Grep -rn "foreach.*persist\|foreach.*flush" src/`.
- Lire les Resources API Platform et chercher des `groups` qui exposent des collections.
- `Grep -rn "messenger\|MessageBus\|dispatch" src/` pour évaluer ce qui part en async vs sync.
- `Read config/packages/messenger.yaml` — transports configurés vs utilisés.

**Format de sortie attendu (par finding)** :

```markdown
- **[<sévérité>][effort: <S|M|L>] <Titre court>** — `src/.../Foo.php:42`
  - Constat : la requête / le code observé.
  - Impact potentiel : ordre de grandeur (ex : "N requêtes en plus par item listé").
  - Fix proposé : pattern + snippet copiable.
```

---

## Axe 6 — 🧭 Cohérence architecturale

**Objectif** — Respect des patterns du projet, dérives entre couches, alignement DDD / hexagonal / CQRS observé vs revendiqué.

**Ce qu'on cherche** :

- **Cohérence revendiquée vs effective** — si le projet revendique DDD/hexagonal, les couches doivent être étanches. Si CQRS revendiqué, Commands et Queries doivent être séparées.
- **Couches étanches** :
  - `src/Domain/` ne dépend de **rien** d'Infrastructure (pas de Doctrine, pas de Symfony HTTP, pas d'API Platform).
  - `src/Application/` dépend de `src/Domain/` via interfaces (ports), pas d'imports directs d'Infrastructure.
  - `src/Infrastructure/` implémente les ports du Domain (Adapters).
  - `src/UI/` (ou `src/Controller/`) reste mince et ne contient pas de logique métier.
- **CQRS appliqué** :
  - Commands en mode write, Queries en mode read.
  - Handlers `__invoke` (ou convention équivalente).
  - Pas de Command qui retourne plus que l'identifiant créé (ou rien).
  - Pas de Query qui modifie.
- **Domain Events** — dispatchés depuis le Domain, consommés par des Subscribers, side-effects (mails, calls externes) hors du flux principal.
- **Repositories** — interfaces dans le Domain, implémentations Doctrine dans Infrastructure. Pas de `QueryBuilder` exposé dans le Domain.
- **API Platform** — Resources DTO séparées des entités quand le contrat externe diffère, Processors thin (≤ 30 lignes) qui routent vers Commands.
- **Sécurité** — Voters dans `src/Security/Voter/` pour les règles métier sur les ressources, pas de `if ($user->getRole() === ...)` éparpillés.

**Comment chercher** :

- `Glob src/Domain/**/*.php` puis pour chacun : `Grep "use Doctrine\\\\\|use Symfony\\\\Component\\\\HttpFoundation\|use ApiPlatform"` — toute occurrence est une fuite.
- `Glob src/Application/**/*.php` puis vérifier que les dépendances passent par des interfaces.
- Lire 3-4 Commands + Queries pour vérifier la séparation read/write.
- Lire 2-3 Processors API Platform : compter les lignes de la méthode `process()`, vérifier la délégation à un Command.
- Lire les Repositories : interface dans le Domain ? `QueryBuilder` exposé en dehors d'`Infrastructure/` ?

**Format de sortie attendu (par finding)** :

```markdown
- **[<sévérité>][effort: <S|M|L>] <Titre court>** — `src/.../Foo.php:42`
  - Constat : la fuite ou la dérive observée.
  - Pattern revendiqué dans le projet : ... (où c'est documenté ou observé)
  - Impact : ce que la dérive empêche (testabilité, swap d'impl, évolution).
  - Action corrective : ... (avec pointeur de fichier de référence dans le projet quand pertinent).
```

---

## Règles transverses de l'audit

1. **Zéro invention** — Tout finding doit citer un fichier. Pas de "il manque probablement…", pas de "c'est sans doute…". Si un point n'est pas observable, le dire en `Question ouverte`.
2. **Patterns du projet > best practices générales** — Si le projet revendique un pattern X qui n'est pas le plus à la mode, on audite par rapport à X, pas par rapport à la mode.
3. **Sévérité honnête** — Un finding `bloquant` doit avoir un impact métier ou sécurité réel. Pas d'inflation pour faire peur.
4. **Effort honnête** — `S` = 1 dev en moins d'une journée. `M` = quelques jours. `L` = chantier qui mérite une US dédiée.
5. **Pas de jugement de personne** — On audite du code, pas des décisions humaines. Pas de "le dev a fait n'importe quoi".
6. **Reconnaître ce qui marche** — L'axe 1 n'est pas un cadeau, c'est une boussole pour les évolutions futures. À ne pas saboter.
