# TP1 : exploration des API Docker et NetBox

## API Docker

| Commande | Code | Observation |
|---|---|---|
| `curl -i http://127.0.0.1:2375/version` | 200 | Docker 29.6.2, API 1.55 |
| `curl -X POST $D/containers/web1/stop` (1re fois) | 204 | conteneur arrêté |
| `curl -X POST $D/containers/web1/stop` (2e fois) | 304 | déjà arrêté, rien n'a changé |
| `curl $D/containers/existepas/json` | 404 | conteneur inconnu |

**Idempotence de `stop`** : oui, `stop` est idempotent. Qu'on l'appelle une ou dix fois, le
conteneur finit arrêté : l'état du serveur est le même. Le code change (204 puis 304) car il
décrit ce qui s'est passé lors de chaque appel, pas l'état final.
