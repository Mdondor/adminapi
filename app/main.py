"""adminapi : API d'administration des conteneurs."""    # Description du module

from typing import Literal                                # Literal : n'accepter qu'une liste fermée de valeurs
from fastapi import FastAPI, Response                     # FastAPI : l'application ; Response : réponse 204 sans corps
from pydantic import BaseModel, Field                     # BaseModel : décrire un corps JSON ; Field : ajouter des contraintes
from app import docker_client                             # Module qui regroupe tous les appels à Docker

app = FastAPI(title="adminapi")                           # Création de l'application ; le titre s'affiche dans /docs


# --- Corps attendu par POST /containers
Image = Literal["nginx:alpine", "redis:alpine", "httpd:alpine"]  # Liste blanche : seules ces trois images sont acceptées


class ConteneurACreer(BaseModel):                         # Forme du JSON attendu à la création
    name: str = Field(pattern=r"^[a-z][a-z0-9-]{1,30}$",  # Une minuscule, puis 1 à 30 minuscules, chiffres ou tirets
                      examples=["web2"])                  # Exemple affiché dans /docs
    image: Image                                          # Doit être l'une des trois images autorisées


@app.get("/health")                                       # Route GET /health
def health():                                             # Fonction exécutée à chaque requête sur /health
    return {"status": "ok"}                               # Réponse 200, sans appeler Docker


@app.get("/containers")                                   # Route GET /containers
def lister():                                             # Fonction exécutée à chaque requête sur /containers
    return docker_client.lister()                         # Liste des conteneurs gérés, au format du contrat


@app.get("/containers/{id}")                              # Route GET /containers/{id}
def detail(id: str):                                      # FastAPI place la valeur de {id} dans la variable id
    return docker_client.lire(id)                         # Conteneur géré, ou 404 s'il est inconnu ou non géré


@app.post("/containers", status_code=201)                 # Route POST /containers ; code 201 en cas de succès
def creer(demande: ConteneurACreer):                      # Corps validé par le modèle ; sinon 422 automatique
    return docker_client.creer(demande.name, demande.image)  # Conteneur créé et démarré, au format du contrat


@app.post("/containers/{id}/stop")                        # Route POST /containers/{id}/stop ; code 200 par défaut
def arreter(id: str):                                     # FastAPI place la valeur de {id} dans la variable id
    return docker_client.arreter(id)                      # Conteneur arrêté, 409 s'il l'était déjà, 404 s'il n'est pas géré


@app.post("/containers/{id}/start")                       # Route POST /containers/{id}/start ; code 200 par défaut
def demarrer(id: str):                                    # FastAPI place la valeur de {id} dans la variable id
    return docker_client.demarrer(id)                     # Conteneur démarré, 409 s'il l'était déjà, 404 s'il n'est pas géré


@app.delete("/containers/{id}", status_code=204)          # Route DELETE /containers/{id} ; code 204 en cas de succès
def supprimer(id: str):                                   # FastAPI place la valeur de {id} dans la variable id
    docker_client.supprimer(id)                           # Suppression, ou 404 si le conteneur n'est pas géré
    return Response(status_code=204)                      # Réponse 204, sans aucun corps
