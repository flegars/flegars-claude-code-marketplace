# Référence — arbitrage simplicité ↔ SOLID

Cette référence cadre **comment** l'agent `backend-specialist` arbitre entre les deux régimes (`simple` et `perenne`). Elle est figée et chargée par l'agent quand le régime est posé.

**Règle d'or** — le régime est **toujours décidé en amont** par l'utilisateur (Phase 2 du skill). L'agent ne s'auto-déclare jamais en `simple` pour aller plus vite, ni en `perenne` pour ajouter de l'abstraction. Si la qualification est mal alignée avec le périmètre réel, l'agent **s'arrête** et signale.

---

## Définition des deux régimes

### Régime `simple`

Le code écrit est :

- À durée de vie courte (< 6 mois en pratique).
- Lu/appelé par **un seul** caller identifié.
- Sans contrat public en sortie (pas d'endpoint API, pas d'event consommé en aval).
- Hors couche Domain et hors couche Application centrale.

Cas typiques :

- Commande Symfony Console one-shot (`bin/console app:migrate-something`).
- Script de migration de données ponctuel.
- Fix très ciblé qui ne mérite pas une PR avec 8 fichiers et 4 interfaces.
- Endpoint interne admin / debug à courte durée de vie.
- Utilitaire interne (helper privé, formateur de log).

### Régime `perenne`

Le code écrit est :

- À durée de vie longue (12-36 mois ou plus).
- Lu/appelé par plusieurs callers, présents ou anticipés explicitement.
- Avec contrat public en sortie (endpoint API exposé, domain event publié, schéma de payload stable).
- Touche au Domain ou à la couche Application centrale.

Cas typiques :

- Nouvelle feature dans `src/Domain/<Bounded Context>/`.
- Nouveau endpoint API Platform exposé aux partenaires.
- Refacto d'un Service applicatif partagé entre plusieurs callers.
- Nouveau Command/Handler dans le bus principal.
- Voter de sécurité.
- Subscriber d'événement métier qui déclenche des side-effects.

---

## Ce que l'agent fait — et ne fait pas — par régime

### En régime `simple`

✅ L'agent **fait** :

- Solution la plus directe compatible avec les patterns du projet.
- Code dans un seul fichier quand pertinent.
- Appel direct au service existant, pas de Command/Handler intermédiaire si rien ne le justifie.
- Tests pertinents (smoke test ou test d'intégration) si la zone est sensible — mais pas exigés par défaut.

❌ L'agent **ne fait pas** (et le liste explicitement dans sa proposition) :

- Pas d'interface à un seul implémenteur (sauf besoin de mock ou de swap connu).
- Pas de DTO/Resource séparé de l'entité si l'écart est nul.
- Pas de découpage Domain/Application/Infrastructure pour un script CLI utilitaire.
- Pas de nouveau Bus / Transport Messenger pour un appel ponctuel.
- Pas de couche d'abstraction « au cas où ».

### En régime `perenne`

✅ L'agent **fait** :

- Application stricte de SOLID :
  - **SRP** — une responsabilité par classe.
  - **OCP** — extensions par composition / décorateurs / events.
  - **LSP** — sous-types respectent le contrat (pas d'exceptions surprises).
  - **ISP** — interfaces fines, orientées client.
  - **DIP** — Application dépend des ports (interfaces) du Domain ; Infrastructure implémente.
- Respect des patterns hexagonal / CQRS du projet :
  - Command / CommandHandler synchrone via `command.bus`.
  - Query / QueryHandler synchrone via `query.bus`.
  - Domain Event → Subscriber → side-effects (via `event.bus` async si le projet le supporte).
  - Resource API Platform → Processor thin (≤ 30 lignes) → Command.
- Tests systématiques : au moins unitaire sur les Handlers et les agrégats Domain ; intégration sur les Processors/Providers et les Repositories.
- PHPStan au niveau du projet (jamais en dessous).
- Validation d'entrée explicite (DTO + Symfony Validator, ou équivalent du projet).

❌ L'agent **ne fait pas** :

- Pas de raccourci « parce que c'est plus rapide ».
- Pas de logique métier dans un Controller / Processor / Repository.
- Pas d'écriture directe en base depuis le Domain.
- Pas d'utilisation d'`EntityManager::flush()` depuis le Domain.
- Pas d'exception métier traitée silencieusement.

---

## Quand le régime ne « tient » plus

Si en cours d'analyse l'agent constate que la qualification est incohérente avec le périmètre réel, il **s'arrête** et signale le mismatch au skill orchestrateur. Le skill repose la question à l'utilisateur (Phase 2 du flow).

Exemples de mismatch :

| Régime déclaré | Réalité observée | Action |
|---|---|---|
| `simple` | Le besoin touche `src/Domain/Pricing/...` | Stop. Demander confirmation `perenne`. |
| `simple` | Le besoin expose un nouvel endpoint API Platform listé dans une route publique | Stop. Demander confirmation `perenne`. |
| `perenne` | Le besoin est un script utilitaire `bin/console app:dump-debug-info` non livré aux utilisateurs finaux | Stop. Suggérer `simple` pour éviter sur-engineering. |
| `simple` | Le besoin ajoute un Subscriber qui sera dispatché sur tous les `OrderPlaced` | Stop. Demander confirmation `perenne`. |

---

## Tableau de décision rapide (pour l'agent)

| Question | Si OUI | Si NON |
|---|---|---|
| Le code touche-t-il `src/Domain/` ou `src/Application/` ? | `perenne` | continuer |
| Le code expose-t-il un endpoint API public ? | `perenne` | continuer |
| Le code publie-t-il un event consommé en aval ? | `perenne` | continuer |
| Le code est-il lu par > 1 caller identifié ou anticipé ? | `perenne` | continuer |
| Le code va-t-il vivre > 12 mois ? | `perenne` | `simple` |

Si l'utilisateur a déclaré `simple` mais qu'au moins une des quatre premières questions est OUI, **l'agent signale le mismatch**.

---

## Traçabilité dans la proposition

En régime `simple`, l'agent **liste explicitement** dans sa proposition les abstractions volontairement non posées et pourquoi. Format attendu :

```
### Abstractions non posées (assumées en régime `simple`)

- Pas d'interface `XxxRepository` : un seul implémenteur Doctrine, pas de mock prévu (test d'intégration suffisant).
- Pas de Command/Handler : appel direct au service `Xxx` depuis la commande Symfony Console — script one-shot, pas de réutilisation prévue.
- Pas de DTO de sortie : l'entité est sérialisée directement, contrat interne non exposé.
```

Cette traçabilité permet à un futur lecteur (humain ou Claude) de savoir que **ces choix sont explicites**, pas des oublis.
