"""adminapi : API d'administration des conteneurs, version en lecture seule."""  # Description du module

# --- Imports
import os                                                 # Lecture des variables d'environnement
import json                                               # Encodage du filtre de labels envoyé à Docker
import requests                                           # Appels HTTP vers l'API Docker
from fastapi import FastAPI, HTTPException                # FastAPI : l'application ; HTTPException : renvoyer une erreur HTTP propre

# --- Configuration
DOCKER = os.environ.get("DOCKER_API_URL", "http://127.0.0.1:2375")  # Adresse de l'API Docker, lue dans l'environnement
TIMEOUT = 10                                              # Délai maximum d'attente d'une réponse de Docker, en secondes
LABEL = "adminapi.managed"                                # Label qui désigne les conteneurs gérés par l'API

# --- Session
docker = requests.Session()                               # Connexion réutilisée pour tous les appels à l'API Docker

# --- Application
app = FastAPI(title="adminapi")                           # Création de l'application ; le titre s'affiche dans /docs


# --- GET /health
@app.get("/health")                                       # Associe la fonction health à la route GET /health
def health():                                             # Fonction exécutée à chaque requête sur /health
    return {"status": "ok"}                               # Dictionnaire converti en JSON par FastAPI, avec le code 200



# --- Conversion d'un conteneur de la LISTE Docker au format du contrat
def depuis_liste(c):                                      # Reçoit un conteneur tel que le renvoie /containers/json
    return {                                              # Renvoie un dictionnaire au format du contrat
        "id": c["Id"],                                    # Identifiant complet de 64 caractères
        "name": c["Names"][0].lstrip("/"),                # Premier nom, sans le "/" ajouté par Docker
        "image": c["Image"],                              # Image du conteneur
        "state": c["State"],                              # État ; dans la liste, c'est directement une chaîne
    }


# --- GET /containers
@app.get("/containers")                                   # Associe la fonction lister à la route GET /containers
def lister():                                             # Fonction exécutée à chaque requête sur /containers
    filtre = json.dumps({"label": [f"{LABEL}=true"]})     # Filtre Docker encodé en JSON : seulement les conteneurs étiquetés
    r = docker.get(f"{DOCKER}/containers/json",           # Requête de la liste des conteneurs
                   params={"all": "true", "filters": filtre},  # all=true : y compris arrêtés ; filters : par label
                   timeout=TIMEOUT)                       # Abandon si aucune réponse dans le délai
    r.raise_for_status()                                  # Lève une erreur si Docker répond 4xx ou 5xx
    return [depuis_liste(c) for c in r.json()]            # Chaque conteneur converti au format du contrat
