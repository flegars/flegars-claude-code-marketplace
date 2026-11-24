# Configuration : `.claude/pr-reviewer.json`

Fichier **optionnel**, placé dans le repo relu (pas dans le plugin). Sans lui, les valeurs par défaut
s'appliquent et la plateforme est déduite du remote `origin`.

```json
{
  "platform": "github",
  "host": "github.mon-entreprise.fr",
  "base": "develop",
  "regression_window_days": 14,
  "max_inline_comments": 15
}
```

| Clé | Défaut | Rôle |
|---|---|---|
| `platform` | déduite du remote | `github` \| `ado` \| `gitlab` \| `local`. Prioritaire sur la déduction depuis le remote ; `--platform` reste prioritaire sur elle. |
| `host` | déduit du remote | Domaine d'une instance auto-hébergée (GitHub Enterprise, GitLab self-managed). Nécessaire dès que le domaine n'est ni `github.com` ni `gitlab.com`. |
| `base` | branche par défaut du remote | Branche cible du mode local (équivalent de `--base`). |
| `regression_window_days` | `14` | Fenêtre de détection des correctifs récents. `0` désactive la détection. |
| `max_inline_comments` | `15` | Plafond de commentaires inline par exécution ; le surplus va dans la synthèse. |

Une clé inconnue ou une valeur invalide arrête la review avec un message explicite.

## Ordre de détection de la plateforme

1. Option `--platform`.
2. `platform` de ce fichier.
3. URL de PR passée en argument, si son domaine est reconnu.
4. URL du remote `origin` : `github.com` → `github` ; `dev.azure.com`, `ssh.dev.azure.com`, `*.visualstudio.com`
   → `ado` ; `gitlab.com` → `gitlab`.
5. Domaine inconnu ou pas de remote : mode `local`, avec l'explication de la configuration à ajouter.
