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
