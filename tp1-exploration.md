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

## API NetBox

| Commande | Code | Observation |
|---|---|---|
| `curl -X POST $N/users/tokens/provision/` (admin/admin) | 201 | renvoie key + token, token complet = nbt_<key>.<token>, rangé dans .env |
| `curl $N/status/` avec `Authorization: Bearer $NETBOX_TOKEN` | 200 | token valide |
| `curl $N/status/` sans token | 403 | NetBox renvoie 403 là où REST voudrait 401 (absence d'authentification) |
| `curl -X POST $N/virtualization/cluster-types/` `{"name": "Docker", "slug": "docker"}` | 201 | type de cluster créé, id 1 |
| `curl -X POST $N/virtualization/clusters/` `{"name": "docker-local", "type": id}` | 400 | JSON invalide (`id` au lieu de sa valeur) : corps illisible |
| `curl -X POST $N/virtualization/clusters/` `{"name": "docker-local", "type": 1}` | 201 | cluster docker-local créé |
