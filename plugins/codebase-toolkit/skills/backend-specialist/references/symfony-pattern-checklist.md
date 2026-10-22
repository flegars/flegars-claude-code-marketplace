# Checklist d'analyse des patterns PHP / Symfony du projet

Cette checklist guide la **cartographie** des conventions du projet courant (Phase 4 du skill `/backend-specialist`). Elle est aussi lue par l'agent `backend-specialist` quand il vérifie son alignement.

**Règle d'or** — chaque item doit être renseigné par une observation **ancrée sur un fichier** (`src/path/file.php:line` ou `config/packages/foo.yaml:line`). Si rien n'est observable pour un item, le noter `non observable` plutôt qu'inventer.

---

## 1. Stack & outillage

| Item | Comment vérifier | Exemple de constat |
|---|---|---|
| Version PHP | `composer.json` champ `require.php` | `php ^8.3` |
| Version Symfony | `composer.json` `symfony/framework-bundle` | `^7.1` |
| ORM | `composer.json` `doctrine/orm`, `doctrine/dbal` | `doctrine/orm ^3.0` |
| API Platform | `composer.json` `api-platform/core` | `^4.0` ou absent |
| Messenger | `composer.json` `symfony/messenger` | présent, `^7.1` |
| Tests | `composer.json` `phpunit/phpunit`, `dama/doctrine-test-bundle` | `phpunit ^11`, dama présent |
| Static analysis | `composer.json` `phpstan/phpstan`, niveau dans `phpstan.neon` | `phpstan niveau 8` |

## 2. Structure de dossiers

| Item | Comment vérifier | Exemple de constat |
|---|---|---|
| Découpage racine | `Glob src/*` | `Domain/`, `Application/`, `Infrastructure/`, `UI/` |
| Convention DDD | présence de Bounded Contexts dans `src/Domain/<Context>/` ? | `src/Domain/Pricing/`, `src/Domain/Catalog/` |
| Tests | `tests/Unit/`, `tests/Integration/`, `tests/Functional/` ? | les trois présents |
| Bin scripts | `bin/console`, `bin/*` custom ? | uniquement `bin/console` |

## 3. CQRS & Messenger

| Item | Comment vérifier | Exemple de constat |
|---|---|---|
| Buses configurés | `config/packages/messenger.yaml` | `command.bus`, `query.bus`, `event.bus` |
| Transports | `config/packages/messenger.yaml` | `sync` (default), `async` (RabbitMQ) |
| Routing | `routing:` dans messenger.yaml | events → async, commands sync sauf exceptions |
| Middlewares | `middleware:` dans messenger.yaml | `doctrine_transaction`, `validation`, custom outbox |
| Convention Handler | `Glob src/**/Handler/*.php` ou `*Handler.php` | `#[AsMessageHandler]` + méthode `__invoke` |

## 4. API Platform

| Item | Comment vérifier | Exemple de constat |
|---|---|---|
| Resources | `Glob src/**/Resource/*.php` ou `#[ApiResource]` sur entités | Resources DTO séparées des entités |
| Providers | `Glob src/**/Provider/*Provider.php` | `StateProviderInterface` thin → Query |
| Processors | `Glob src/**/Processor/*Processor.php` | `StateProcessorInterface` thin → Command |
| Convention thin | lire 1-2 Processors | ≤ 30 lignes, route vers Command sans logique |
| Filtres | `#[ApiFilter]` ou Filtres custom | Filtres custom dans `src/Infrastructure/Api/Filter/` |

## 5. Doctrine

| Item | Comment vérifier | Exemple de constat |
|---|---|---|
| Entities | `Glob src/Domain/**/*.php` avec `#[ORM\Entity]` ? Ou entités séparées dans `src/Infrastructure/Persistence/`? | entités Domain pures + mapping XML/PHP dans Infrastructure |
| Repositories | `Glob src/**/Repository/*Repository.php` | interface dans Domain, impl Doctrine dans Infrastructure |
| Agrégats | un Aggregate Root par dossier ? | oui : `src/Domain/Order/Order.php` est le root |
| Soft delete | extension Gedmo / trait custom ? | non, suppression hard |
| Migrations | `migrations/Version*.php` | Doctrine Migrations, naming standard |

## 6. Tests

| Item | Comment vérifier | Exemple de constat |
|---|---|---|
| Outil | `phpunit.xml.dist`, `phpunit.xml` | PHPUnit 11 |
| Découpage | `tests/Unit/`, `tests/Integration/`, `tests/Functional/` | les trois |
| Fixtures | `Doctrine\Bundle\FixturesBundle` ou maison ? | Doctrine fixtures, dans `src/DataFixtures/` |
| Convention de naming | lire 2 tests | `testItDoesSomething()` ou `it_does_something()` |
| Test web | `WebTestCase`, `ApiTestCase` (API Platform) ? | `ApiTestCase` pour API Platform |
| Niveau PHPStan | `phpstan.neon` | niveau 8 ou max |

## 7. Sécurité

| Item | Comment vérifier | Exemple de constat |
|---|---|---|
| Voters | `Glob src/**/Voter/*Voter.php` | présents par domaine |
| Attributs | `#[IsGranted]`, `Security` sur Controllers/Resources | `#[IsGranted('ROLE_X')]` sur Resources |
| IdP | `config/packages/security.yaml`, `composer.json` keycloak/jose | Keycloak via `lcobucci/jwt` |
| Tokens | OAuth2, JWT, session | JWT stateless |

## 8. Domain Events / Outbox

| Item | Comment vérifier | Exemple de constat |
|---|---|---|
| Domain events | classes dans `src/Domain/**/Event/*Event.php` ? | oui, `OrderPlaced`, `OrderCancelled` |
| Dispatch | post-flush via subscriber Doctrine ? Messenger direct ? | subscriber `PostFlush` + dispatch sur `event.bus` |
| Outbox | table outbox + worker ? | oui, table `outbox_messages` + worker async |
| Subscribers | `Glob src/**/Subscriber/*Subscriber.php` | un Subscriber par side-effect, dans `Application/` |

## 9. Conventions de code

| Item | Comment vérifier | Exemple de constat |
|---|---|---|
| PSR-12 | `.php-cs-fixer.php` | présent, PSR-12 + custom |
| Suffixes | grep des suffixes `*Command.php`, `*Handler.php`, `*Repository.php` | conformes |
| Convention `__invoke` ou méthode nommée | lire 2 Handlers | `__invoke` partout |
| Readonly classes | usage de `final readonly class` ? | oui sur Commands, Queries, DTOs |
| Strict types | `declare(strict_types=1);` partout ? | oui, vérifié par php-cs-fixer |

---

## Format de synthèse

À la fin de la cartographie, produire un bloc court de ce type, à coller dans le prompt de l'agent :

```
Stack : PHP 8.3 + Symfony 7.1 + Doctrine ORM 3 + API Platform 4 + Messenger
Structure : DDD/hexagonal, Bounded Contexts dans src/Domain/<Context>/
CQRS : 3 buses (command/query/event), middleware doctrine_transaction + validation + outbox custom
API : Resources DTO séparées, Processors thin (≤ 30 lignes) routent vers Commands
Doctrine : entités Domain pures + mapping XML dans Infrastructure, agrégats explicites
Tests : PHPUnit 11, tests Unit + Integration + Functional, ApiTestCase pour API Platform, PHPStan niveau 8
Sécurité : Keycloak + JWT stateless + Voters par domaine
Events : Domain Events + Subscriber Post-flush + table outbox + worker async
Conventions : final readonly class sur Commands/Queries/DTOs, __invoke partout, strict_types=1
Non observable : pas de soft delete, pas de fixtures maison (Doctrine fixtures uniquement)
```

Ce bloc est l'input principal du prompt envoyé à l'agent.
