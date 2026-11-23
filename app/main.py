"""adminapi : API d'administration des conteneurs."""    # Description du module

from fastapi import FastAPI                               # Classe qui crée l'application
from app import docker_client                             # Module qui regroupe tous les appels à Docker

app = FastAPI(title="adminapi")                           # Création de l'application ; le titre s'affiche dans /docs


@app.get("/health")                                       # Route GET /health
def health():                                             # Fonction exécutée à chaque requête sur /health
    return {"status": "ok"}                               # Réponse 200, sans appeler Docker


@app.get("/containers")                                   # Route GET /containers
def lister():                                             # Fonction exécutée à chaque requête sur /containers
    return docker_client.lister()                         # Liste des conteneurs gérés, au format du contrat


@app.get("/containers/{id}")                              # Route GET /containers/{id}
def detail(id: str):                                      # FastAPI place la valeur de {id} dans la variable id
    return docker_client.lire(id)                         # Conteneur géré, ou 404 s'il est inconnu ou non géré
